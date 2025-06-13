from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ExtractedCard(Base):
    __tablename__ = "extracted_cards"

    id = Column(Integer, primary_key=True, index=True)
    quarter = Column(String(2), nullable=False)
    year = Column(Integer, nullable=False)
    source_filename = Column(String(255), nullable=False)

    issuer = Column(String(255), nullable=True)
    card_name = Column(String(255), nullable=True)
    min_apr = Column(String(50), nullable=True)
    max_apr = Column(String(50), nullable=True)
    penalty_apr = Column(String(255), nullable=True)
    annual_fee = Column(String(255), nullable=True)
    late_fee = Column(String(255), nullable=True)
    foreign_txn_fee = Column(String(255), nullable=True)
    cash_advance_fee = Column(String(255), nullable=True)
    balance_transfer_fee = Column(String(255), nullable=True)
    min_interest_charge = Column(String(255), nullable=True)

    rewards = Column(Text, nullable=True)
    exclusions = Column(Text, nullable=True)

    extraction_date = Column(DateTime, default=datetime.utcnow)
    verified = Column(Boolean, default=False)
