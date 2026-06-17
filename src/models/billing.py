from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from src.models.user import Base

class Usage(Base):
    __tablename__ = 'usage'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    queries = Column(Integer, default=0)

class Invoice(Base):
    __tablename__ = 'invoices'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='KES')
    status = Column(String(32), default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    external_id = Column(String(128), nullable=True)  # e.g., Stripe invoice id
