# # app/scripts/backfill_ids.py

# from app.db.database import SessionLocal
# from app.db.models import ExtractedCard
# from app.core.utils import get_card_and_issuer_ids


# def backfill_ids():
#     db = SessionLocal()
#     try:
#         # Fetch all cards that are missing either issuer_id or card_id
#         cards = db.query(ExtractedCard).filter(
#             (ExtractedCard.issuer_id == None) | (ExtractedCard.card_id == None)
#         ).all()

#         updated_count = 0

#         for card in cards:
#             if card.issuer and card.card_name:
#                 issuer_id, card_id = get_card_and_issuer_ids(db, card.issuer, card.card_name)
#                 if issuer_id is not None and card_id is not None:
#                     card.issuer_id = issuer_id
#                     card.card_id = card_id
#                     updated_count += 1

#         db.commit()
#         print(f"✅ Backfilled {updated_count} of {len(cards)} cards with missing IDs.")
#     except Exception as e:
#         db.rollback()
#         print(f"❌ Error during backfill: {e}")
#     finally:
#         db.close()


# if __name__ == "__main__":
#     backfill_ids()

from sqlalchemy import Column, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.db.database import SessionLocal  # Your current backend DB session
from app.db.models import ExtractedCard

# Use the same engine as your FastAPI backend
engine = SessionLocal().get_bind()
SessionMaker = sessionmaker(bind=engine)

# Temporary base for models
Base = declarative_base()

# Temporary Card model
class TempCard(Base):
    __tablename__ = 'cards'
    card_id = Column(Integer, primary_key=True)
    name = Column(String)
    issuer_id = Column(Integer)

# Temporary Issuer model
class TempIssuer(Base):
    __tablename__ = 'issuers'
    issuer_id = Column(Integer, primary_key=True)
    name = Column(String)

def get_card_and_issuer_ids(session, issuer_name: str, card_name: str):
    """Get matching issuer_id and card_id using fuzzy LIKE match."""
    if not issuer_name or not card_name:
        return None, None

    result = (
        session.query(TempCard.card_id, TempIssuer.issuer_id)
        .join(TempIssuer, TempCard.issuer_id == TempIssuer.issuer_id)
        .filter(func.lower(TempCard.name).like(f"%{card_name.lower()}%"))
        .filter(func.lower(TempIssuer.name).like(f"%{issuer_name.lower()}%"))
        .first()
    )
    if result:
        return result.issuer_id, result.card_id
    return None, None

def backfill_ids():
    session = SessionMaker()
    try:
        cards = session.query(ExtractedCard).filter(
            (ExtractedCard.issuer_id == None) | (ExtractedCard.card_id == None)
        ).all()

        updated = 0
        for card in cards:
            if card.issuer and card.card_name:
                issuer_id, card_id = get_card_and_issuer_ids(session, card.issuer, card.card_name)
                if issuer_id and card_id:
                    card.issuer_id = issuer_id
                    card.card_id = card_id
                    updated += 1

        session.commit()
        print(f"✅ Backfilled {updated} of {len(cards)} records.")
    except Exception as e:
        session.rollback()
        print("❌ Error during backfill:", e)
    finally:
        session.close()

if __name__ == "__main__":
    backfill_ids()
