from sqlalchemy import (
    create_engine, Column, Integer, Float, String, ForeignKey, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from passlib.hash import bcrypt
import uuid

engine = create_engine("sqlite:///finance.db")
Session = sessionmaker(bind=engine)
Base = declarative_base()


# ─────────────────────────────
# USERS
# ─────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    google_id = Column(String, nullable=True)

    transactions = relationship("Transaction", back_populates="user")

    def set_password(self, password):
        self.password_hash = bcrypt.hash(password)

    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)


# ─────────────────────────────
# TRANSACTIONS
# ─────────────────────────────
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(String)
    merchant = Column(String)
    category = Column(String)
    amount = Column(Float)

    user = relationship("User", back_populates="transactions")


Base.metadata.create_all(engine)