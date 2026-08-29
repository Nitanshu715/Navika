import os
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import declarative_base, sessionmaker

_here = os.path.dirname(os.path.abspath(__file__))
_DB_PATH = os.path.join(_here, "..", "finance.db")
engine = create_engine(f"sqlite:///{_DB_PATH}", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, default=1, index=True)
    timestamp = Column(String)
    merchant = Column(String)
    category = Column(String)
    amount = Column(Float)

Base.metadata.create_all(engine)

def save_transaction(tx, user_id: int = 1):
    session = Session()
    try:
        new_tx = Transaction(
            user_id=user_id,
            timestamp=tx.get("timestamp"),
            merchant=tx.get("merchant"),
            category=tx.get("category"),
            amount=float(tx.get("amount", 0)),
        )
        session.add(new_tx)
        session.commit()
    finally:
        session.close()

def get_all_transactions(user_id: int = None):
    session = Session()
    try:
        query = session.query(Transaction)
        if user_id:
            query = query.filter((Transaction.user_id == user_id) | (Transaction.user_id == None))
        txs = query.order_by(Transaction.id.desc()).all()
        return [
            {
                "id": t.id,
                "timestamp": t.timestamp,
                "merchant": t.merchant,
                "category": t.category,
                "amount": t.amount,
            }
            for t in txs
        ]
    finally:
        session.close()