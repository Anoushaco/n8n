from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from .user import User # Assuming User model is in user.py

Base = declarative_base()

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    order_type = Column(String, nullable=False)  # 'buy' or 'sell'
    usdt_amount = Column(Float, nullable=False)
    irr_amount = Column(Float, nullable=False) # Amount in IRR
    commission_applied = Column(Float, nullable=False)
    status = Column(String, nullable=False, default='pending')  # e.g., pending, matched, completed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    matched_order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)

    user = relationship("User")
    matched_order = relationship("Order", remote_side=[id], uselist=False)


    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, type='{self.order_type}', usdt_amount={self.usdt_amount}, status='{self.status}')>"
