from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ExtractedCard(Base):
    __tablename__ = "extracted_cards"

    id = Column(Integer, primary_key=True, index=True)
    issuer_id = Column(Integer, nullable=True)
    card_id = Column(Integer, nullable=True)
    issuer = Column(String(255), nullable=True)
    card_name = Column(String(255), nullable=True)
    promote_year = Column(Integer, nullable=True)
    promote_quarter = Column(String(2), nullable=True)
    quarter = Column(String(2), nullable=True)
    year = Column(Integer, nullable=True)
    source_filename = Column(String(255), nullable=True)

    min_apr = Column(String(50), nullable=True)
    max_apr = Column(String(50), nullable=True)
    penalty_apr = Column(String(255), nullable=True)
    cash_advance_apr = Column(Integer, nullable=True)
    annual_fee = Column(String(255), nullable=True)
    late_fee = Column(String(255), nullable=True)
    foreign_txn_fee = Column(String(255), nullable=True)
    cash_advance_fee = Column(String(255), nullable=True)
    balance_transfer_fee = Column(String(255), nullable=True)
    min_interest_charge = Column(String(255), nullable=True)
    
    base_score = Column(Integer, nullable=True)
    trend_bonus = Column(Integer, nullable=True)
    volatility_score = Column(Integer, nullable=True)
    volatility_penalty = Column(Integer, nullable=True)
    final_score = Column(Integer, nullable=True)
    grade = Column(String(255), nullable=True)

    rewards = Column(Text, nullable=True)
    exclusions = Column(Text, nullable=True)

    extraction_date = Column(DateTime, default=datetime.utcnow) 
    verified = Column(Boolean, default=False)

    card_type = Column(String(255), nullable=True)
    institution_type = Column(String(255), nullable=True)
    change_description = Column(String(255), nullable=True)
    change_type = Column(String(255), nullable=True)
    notable_exclusions = Column(Text, nullable=True)
    fee_structure = Column(Text, nullable=True)
    rewards_structure = Column(Text, nullable=True)
