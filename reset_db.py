from app.db.database import engine, Base
from app.core.config import settings
import os

def reset_database():
    # Drop all tables
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    # Recreate all tables
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Database reset complete!")

if __name__ == "__main__":
    reset_database()
