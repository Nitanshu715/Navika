from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("sqlite:///finance.db")
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    timestamp = Column(String)
    merchant = Column(String)
    category = Column(String)
    amount = Column(Float)

Base.metadata.create_all(engine)

def save_transaction(tx):
    session = Session()
    new_tx = Transaction(**tx)
    session.add(new_tx)
    session.commit()
    session.close()

def get_all_transactions():
    session = Session()
    txs = session.query(Transaction).all()
    session.close()

    return [
        {
            "timestamp": t.timestamp,
            "merchant": t.merchant,
            "category": t.category,
            "amount": t.amount,
        }
        for t in txs
    ]