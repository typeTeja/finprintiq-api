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
            "Issuer": r.issuer,
            "CardName": r.card_name,
         #  "report_date": r.report_date,
            "MinAPR": r.min_apr,
            "MaxAPR": r.max_apr,
            "CashAdvanceAPR": r.cash_advance_fee,
            "LateFee": r.late_fee,
            "AnnualFee": r.annual_fee,
            "ForeignTransactionFee": r.foreign_txn_fee,
            "RewardsCategories": r.rewards,
         #  "category": r.category,
            "NotableExclusions": r.exclusions,
            "card_type": r.card_type,
            "Quarter": r.quarter,
            "Year": r.year,
            "promote_quarter": r.promote_quarter,
            "promote_year": r.promote_year,
            "MinimumInterestCharge": r.min_interest_charge,
        }
        for r in rows
    ]


def export_to_excel(quarter: str = "", year: int = 0) -> str:
    """
    Export filtered card data to an Excel file.
    
    Args:
        quarter: Optional quarter filter (e.g., "Q1", "Q2")
        year: Optional year filter (e.g., 2023)
        
    Returns:
        str: Path to the generated Excel file
    """
    db = SessionLocal()
    try:
        # Apply filters directly in the query
        query = db.query(ExtractedCard)
        
        if year:
            query = query.filter(ExtractedCard.year == year)
        if quarter:
            query = query.filter(ExtractedCard.quarter == quarter)
            
        # Get the filtered data
        rows = query.all()
        
        # Convert to the required format
        data = [
            {
                "Issuer": r.issuer,
                "CardName": r.card_name,
                "MinAPR": r.min_apr,
                "MaxAPR": r.max_apr,
                "CashAdvanceAPR": r.cash_advance_fee,
                "LateFee": r.late_fee,
                "AnnualFee": r.annual_fee,
                "ForeignTransactionFee": r.foreign_txn_fee,
                "RewardsCategories": r.rewards,
                "NotableExclusions": r.exclusions,
                "card_type": r.card_type,
                "Quarter": r.quarter,
                "Year": r.year,
                "promote_quarter": r.promote_quarter,
                "promote_year": r.promote_year,
                "MinimumInterestCharge": r.min_interest_charge,
            }
            for r in rows
        ]
        
        # Export to Excel
        df = pd.DataFrame(data)
        os.makedirs(os.path.dirname(settings.OUTPUT_XLSX), exist_ok=True)
        df.to_excel(settings.OUTPUT_XLSX, index=False)
        
        return settings.OUTPUT_XLSX
    finally:
        db.close()
