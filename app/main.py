from fastapi import FastAPI, Request, UploadFile, Form, File, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil, os, uuid, json, asyncio
from typing import Dict, Any

from app.core.config import settings
from app.core.extractor import process_zip_with_progress
from app.db.database import init_db, SessionLocal
from app.db.crud import fetch_filtered_data, export_to_excel
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse

# In-memory storage for progress (in production, use Redis or similar)
progress_store: Dict[str, Dict[str, Any]] = {}

# Initialize DB
init_db()

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

# Static & Templates
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_year": settings.YEAR_DEFAULT
    })

@app.post("/upload")
async def upload_zip(
    zip_file: UploadFile = File(...),
    quarter: str = Form(...),
    year: int = Form(...)
):
    # Create a unique ID for this upload
    upload_id = str(uuid.uuid4())
    
    # Initialize progress tracking
    progress_store[upload_id] = {
        "status": "uploading",
        "progress": 0,
        "total_files": 0,
        "processed_files": 0,
        "current_file": "",
        "message": "Starting upload..."
    }
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    upload_path = os.path.join(settings.UPLOAD_DIR, f"{upload_id}_{zip_file.filename}")
    
    # Save the file
    with open(upload_path, "wb") as f:
        f.write(await zip_file.read())
    
    # Start processing in the background
    asyncio.create_task(process_zip_with_progress(upload_path, quarter, year, upload_id, progress_store))
    
    return {
        "message": "File uploaded and processing started",
        "upload_id": upload_id,
        "progress_url": f"/progress/{upload_id}"
    }

@app.get("/progress/{upload_id}")
async def get_progress(upload_id: str):
    """SSE endpoint for progress updates"""
    if upload_id not in progress_store:
        raise HTTPException(status_code=404, detail="Upload ID not found")
    
    async def event_generator():
        last_progress = -1
        
        while True:
            progress = progress_store[upload_id]
            
            # Only send if progress has changed
            if progress["progress"] != last_progress:
                yield f"data: {json.dumps(progress)}\n\n"
                last_progress = progress["progress"]
                
                # If processing is complete, clean up and exit
                if progress["status"] in ["completed", "failed"]:
                    # Keep the result for 5 minutes before cleaning up
                    await asyncio.sleep(300)
                    if upload_id in progress_store:
                        del progress_store[upload_id]
                    break
            
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/data")
def get_data(quarter: str = "", year: int = 0):
    db = SessionLocal()
    records = fetch_filtered_data(db, quarter, year)
    return JSONResponse(content=records)

@app.get("/export")
def export(quarter: str = "", year: int = 0):
    import io
    import pandas as pd
    from fastapi.responses import StreamingResponse
    
    # Get the data as a DataFrame
    db = SessionLocal()
    try:
        # Get the data as a list of dictionaries
        data = fetch_filtered_data(db, quarter, year)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Create a BytesIO buffer
        buffer = io.BytesIO()
        
        # Write Excel file to buffer
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Credit Card Data')
            
        # Move to the beginning of the buffer
        buffer.seek(0)
        
        # Create a streaming response
        filename = f"extracted_data_{f'Q{quarter}_' if quarter else ''}{year if year else 'all'}.xlsx"
        
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        )
    finally:
        db.close()
