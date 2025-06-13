from sqlalchemy.orm import Session
from app.db.models import ExtractedCard
import pandas as pd
import os
from app.core.config import settings

def fetch_filtered_data(db: Session, quarter: str = "", year: int = 0):
    q = db.query(ExtractedCard)
    if year:
        q = q.filter(ExtractedCard.year == year)
    if quarter:
        q = q.filter(ExtractedCard.quarter == quarter)
    rows = q.all()
    return [
        {
            "issuer": r.issuer,
            "card_name": r.card_name,
            "min_apr": r.min_apr,
            "max_apr": r.max_apr,
            "late_fee": r.late_fee,
            "foreign_txn_fee": r.foreign_txn_fee,
            "quarter": r.quarter,
            "year": r.year
        }
        for r in rows
    ]

def export_to_excel():
    from app.db.database import SessionLocal
    db = SessionLocal()
    rows = db.query(ExtractedCard).all()
    data = []
    for r in rows:
        d = r.__dict__.copy()
        d.pop("_sa_instance_state", None)
        data.append(d)
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(settings.OUTPUT_XLSX), exist_ok=True)
    df.to_excel(settings.OUTPUT_XLSX, index=False)
    return settings.OUTPUT_XLSX
