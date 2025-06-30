import os
import zipfile
import shutil
import fitz  # PyMuPDF
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai import OpenAI

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import ExtractedCard

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class ProcessingStats:
    def __init__(self, total_files: int):
        self.total_files = total_files
        self.processed_files = 0
        self.start_time = time.time()
        self.last_update = self.start_time
    
    def update_progress(self, current_file: str = "") -> Dict[str, Any]:
        """Update progress and return current stats"""
        self.processed_files += 1
        progress = min(100, int((self.processed_files / self.total_files) * 100))
        
        # Calculate ETA
        current_time = time.time()
        time_elapsed = current_time - self.start_time
        time_per_file = time_elapsed / self.processed_files if self.processed_files > 0 else 0
        files_remaining = self.total_files - self.processed_files
        eta_seconds = int(files_remaining * time_per_file)
        
        # Only update if significant time has passed or it's the last file
        if current_time - self.last_update > 1 or self.processed_files == self.total_files:
            self.last_update = current_time
            
            return {
                "status": "processing" if self.processed_files < self.total_files else "completed",
                "progress": progress,
                "total_files": self.total_files,
                "processed_files": self.processed_files,
                "current_file": current_file,
                "eta_seconds": eta_seconds,
                "message": f"Processing {self.processed_files} of {self.total_files} files" + 
                          (f" - {current_file}" if current_file else "")
            }
        return None

def extract_text_from_pdf(path: str) -> str:
    text = ""
    doc = fitz.open(path)
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def ask_openai(text: str) -> dict:
    prompt = """Extract the following fields from this credit card agreement:
- Issuer
- Card Name
- Min APR (%)
- Max APR (%)
- Penalty APR (%)
- Annual Fee ($)
- Late Fee ($)
- Foreign Transaction Fee (%)
- Cash Advance Fee (%)
- Balance Transfer Fee (%)
- Minimum Interest Charge ($)
- Rewards Structure
- Notable Exclusions
- Card type
- Institution type
- Change Description
- Change type
- Fee structure
- Rewards structure

Return only a JSON object. Use "Not disclosed" for missing fields."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a document parser."},
            {"role": "user", "content": prompt + "\n\n" + text[:12000]}
        ],
        temperature=0
    )
    content = response.choices[0].message.content.strip()
    # strip markdown fences
    if content.startswith("```"):
        content = content.split("```")[1].strip()
    # strip leading "json"
    if content.lower().startswith("json"):
        content = content[4:].strip()
    return json.loads(content)

def clean_field(val):
    if isinstance(val, list):
        return "; ".join(val)
    if isinstance(val, dict):
        return json.dumps(val)
    return val or "Not disclosed"

async def process_zip_with_progress(zip_path: str, quarter: str, year: int, upload_id: str, progress_store: Dict[str, Any]):
    """Process zip file with progress tracking"""
    db = None
    try:
        db = SessionLocal()
        os.makedirs(settings.EXTRACT_DIR, exist_ok=True)
        
        # Initialize progress tracking
        progress_store[upload_id] = {
            "status": "processing",
            "progress": 0,
            "total_files": 0,
            "processed_files": 0,
            "current_file": "",
            "eta_seconds": 0,
            "message": "Starting file extraction...",
            "start_time": time.time()
        }
        
        # Extract ZIP file
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(settings.EXTRACT_DIR)
        
        # Find all PDF files
        pdf_files = []
        for root, _, files in os.walk(settings.EXTRACT_DIR):
            for fname in files:
                if fname.endswith(".pdf") and not fname.startswith("._"):
                    pdf_files.append(os.path.join(root, fname))
        
        total_files = len(pdf_files)
        if total_files == 0:
            progress_store[upload_id].update({
                "status": "failed",
                "progress": 100,
                "message": "No PDF files found in the archive"
            })
            return
        
        # Update progress with file count
        progress_store[upload_id].update({
            "total_files": total_files,
            "message": f"Found {total_files} PDF files to process..."
        })
        
        # Process each PDF
        processed_files = 0
        start_time = time.time()
        
        for i, pdf_path in enumerate(pdf_files, 1):
            try:
                filename = os.path.basename(pdf_path)
                
                # Calculate progress
                progress = int((i - 1) / total_files * 100)
                elapsed = time.time() - start_time
                eta = (elapsed / i) * (total_files - i) if i > 0 else 0
                
                # Update progress
                progress_store[upload_id].update({
                    "status": "processing",
                    "progress": progress,
                    "current_file": filename,
                    "processed_files": i - 1,
                    "eta_seconds": int(eta),
                    "message": f"Processing {i} of {total_files}: {filename}"
                })
                
                # Process the file
                process_pdf_file(pdf_path, quarter, year, db, filename)
                processed_files += 1
                
                # Small delay to allow UI updates
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing {pdf_path}: {str(e)}")
                db.rollback()
                # Continue with next file
                continue
        
        # Mark as completed
        progress_store[upload_id].update({
            "status": "completed",
            "progress": 100,
            "processed_files": processed_files,
            "current_file": "",
            "message": f"Successfully processed {processed_files} of {total_files} files.",
            "eta_seconds": 0
        })
        
    except Exception as e:
        print(f"Error in process_zip_with_progress: {str(e)}")
        if upload_id in progress_store:
            progress_store[upload_id].update({
                "status": "failed",
                "message": f"Processing failed: {str(e)}",
                "progress": 0
            })
    finally:
        # Clean up resources
        if db:
            db.close()
            
        # Clean up all temporary files
        try:
            print(f"Starting cleanup process...")
            
            # Remove the uploaded zip file
            if os.path.exists(zip_path):
                print(f"Removing zip file: {zip_path}")
                os.remove(zip_path)
                print(f"Successfully removed zip file")
            
            # Remove the extracted files directory if it exists
            if os.path.exists(settings.EXTRACT_DIR):
                print(f"Removing extracted files from: {settings.EXTRACT_DIR}")
                # First, ensure all files are writable
                for root, dirs, files in os.walk(settings.EXTRACT_DIR):
                    for name in files:
                        file_path = os.path.join(root, name)
                        try:
                            os.chmod(file_path, 0o777)  # Make file writable
                        except Exception as e:
                            print(f"Warning: Could not change permissions for {file_path}: {e}")
                # Then remove the directory tree
                shutil.rmtree(settings.EXTRACT_DIR, ignore_errors=True)
                print(f"Successfully removed extracted files directory")
            
            # Also clean up any files in the uploads directory (as a safety measure)
            uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
            if os.path.exists(uploads_dir):
                print(f"Cleaning up uploads directory: {uploads_dir}")
                for filename in os.listdir(uploads_dir):
                    file_path = os.path.join(uploads_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.chmod(file_path, 0o777)  # Make file writable
                            os.unlink(file_path)
                            print(f"Removed file: {file_path}")
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
                        
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            # Update progress with cleanup error if processing was successful
            if upload_id in progress_store and progress_store[upload_id].get("status") == "completed":
                progress_store[upload_id]["message"] += " (Note: Some temporary files might not have been cleaned up properly)"

def process_pdf_file(pdf_path: str, quarter: str, year: int, db: SessionLocal, filename: str = None):
    """Process a single PDF file and save to database"""
    if filename is None:
        filename = os.path.basename(pdf_path)
        
    text = extract_text_from_pdf(pdf_path)
    data = ask_openai(text)
    
    card = ExtractedCard(
        quarter=quarter,
        year=year,
        source_filename=filename,
        issuer=clean_field(data.get("Issuer")),
        card_name=clean_field(data.get("Card Name")),
        min_apr=clean_field(data.get("Min APR (%)")),
        max_apr=clean_field(data.get("Max APR (%)")),
        penalty_apr=clean_field(data.get("Penalty APR (%)")),
        annual_fee=clean_field(data.get("Annual Fee ($)")),
        late_fee=clean_field(data.get("Late Fee ($)")),
        foreign_txn_fee=clean_field(data.get("Foreign Transaction Fee (%)")),
        cash_advance_fee=clean_field(data.get("Cash Advance Fee (%)")),
        balance_transfer_fee=clean_field(data.get("Balance Transfer Fee (%)")),
        min_interest_charge=clean_field(data.get("Minimum Interest Charge ($)")),
        rewards=clean_field(data.get("Rewards Structure")),
        exclusions=clean_field(data.get("Notable Exclusions")),
        extraction_date=datetime.now(),
        card_type=clean_field(data.get("Card type")),
        institution_type=clean_field(data.get("Institution type")),
        change_description=clean_field(data.get("Change Description")),
        change_type=clean_field(data.get("Change type")),
        fee_structure=clean_field(data.get("Fee structure")),
        rewards_structure=clean_field(data.get("Rewards structure"))

    )
    db.add(card)
    db.commit()
    # optionally clean up extracted files
