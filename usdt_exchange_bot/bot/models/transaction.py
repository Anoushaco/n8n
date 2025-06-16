from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from .order import Order # Assuming Order model is in order.py

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    buy_order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    sell_order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    status = Column(String, nullable=False, default='pending_confirmation') # e.g., pending_confirmation, buyer_confirmed, seller_confirmed, completed, disputed, cancelled
    buyer_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    seller_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    buy_order = relationship("Order", foreign_keys=[buy_order_id])
    sell_order = relationship("Order", foreign_keys=[sell_order_id])

    def __repr__(self):
        return f"<Transaction(id={self.id}, buy_order_id={self.buy_order_id}, sell_order_id={self.sell_order_id}, status='{self.status}')>"
