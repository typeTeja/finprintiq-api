from sqlalchemy.orm import Session
from app.db.models import ExtractedCard
import pandas as pd
import os
from app.core.config import settings
from app.db.database import SessionLocal


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
    db = SessionLocal()
    rows = db.query(ExtractedCard).all()

    data = []
    for r in rows:
        data.append({
            "issuer": r.issuer,
            "card_name": r.card_name,
           # "report_date": r.report_date,
            "min_apr": r.min_apr,
            "max_apr": r.max_apr,
           # "cash_advance_apr": r.cash_advance_apr,
            "late_fee": r.late_fee,
           # "anual_fee": r.anual_fee,
            "foreign_txn_fee": r.foreign_txn_fee,
            "rewards_structure": r.rewards_structure,
           # "category": r.category,
            "exclusions": r.exclusions,
            "card_type": r.card_type,
            "quarter": r.quarter,
            "year": r.year,
            "promote_quarter": r.promote_quarter,
            "promote_year": r.promote_year,
        })

    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(settings.OUTPUT_XLSX), exist_ok=True)
    df.to_excel(settings.OUTPUT_XLSX, index=False)

    return settings.OUTPUT_XLSX