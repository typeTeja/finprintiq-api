from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    DATABASE_URL: str
    UPLOAD_DIR: str = "uploads"
    EXTRACT_DIR: str = "extracted"
    OUTPUT_XLSX: str = "output/output.xlsx"
    YEAR_DEFAULT: int = int(os.getenv("DEFAULT_YEAR", __import__("datetime").datetime.now().year))

    class Config:
        env_file = ".env"

settings = Settings()
