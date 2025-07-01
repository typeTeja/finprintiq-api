# # # app/core/utils.py

# # from sqlalchemy import text
# # from sqlalchemy.orm import Session

# # def get_card_and_issuer_ids(db: Session, issuer_name: str, card_name: str):
# #     query = text("""
# #         SELECT card_id, issuer_id
# #         FROM cards
# #         WHERE LOWER(name) LIKE :card_name AND LOWER(issuer) LIKE :issuer_name
# #         LIMIT 1
# #     """)
# #     result = db.execute(query, {
# #         "card_name": f"%{card_name.lower()}%",
# #         "issuer_name": f"%{issuer_name.lower()}%"
# #     }).fetchone()

# #     if result:
# #         return result.issuer_id, result.card_id
# #     return None, None

# from sqlalchemy.orm import Session
# from sqlalchemy import func
# # from app.db.external_models import Card, Issuer  # Adjust to match your model import path


# def get_card_and_issuer_ids(db: Session, issuer_name: str, card_name: str):
#     if not issuer_name or not card_name:
#         return None, None

#     issuer_name = issuer_name.lower()
#     card_name = card_name.lower()

#     result = (
#         db.query(Card.card_id, Issuer.issuer_id)
#         .join(Issuer, Card.issuer_id == Issuer.issuer_id)
#         .filter(func.lower(Card.name).like(f"%{card_name}%"))
#         .filter(func.lower(Issuer.name).like(f"%{issuer_name}%"))
#         .first()
#     )

#     if result:
#         return result.issuer_id, result.card_id
#     return None, None
from typing import Tuple
from sqlalchemy.orm import Session


def get_card_and_issuer_ids(db: Session, issuer_name: str, card_name: str) -> Tuple[int, int]:
    """
    Fetch the issuer_id and card_id for given issuer and card name.

    Returns (issuer_id, card_id) — if not found, values will be None.
    """
    try:
        # Look up issuer_id from issuers table
        issuer_id = db.execute(
            "SELECT issuer_id FROM issuers WHERE name = :name",
            {"name": issuer_name}
        ).scalar()

        # Look up card_id from cards table based on card_name and issuer_id
        card_id = db.execute(
            "SELECT card_id FROM cards WHERE name = :name AND issuer_id = :issuer_id",
            {"name": card_name, "issuer_id": issuer_id}
        ).scalar()

        return issuer_id, card_id

    except Exception as e:
        print(f"[get_card_and_issuer_ids] Error looking up IDs: {e}")
        return None, None
