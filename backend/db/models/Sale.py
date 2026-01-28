########## Modules ##########
import enum

from datetime import datetime, timezone

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Enum, Integer, Boolean

##### Sale #####
class Sale_Status(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class Payment_Method(enum.Enum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    DIGITAL = "digital"

class Sale(Base):
    __tablename__ = "sales"

    id = Column(String, primary_key=True)
    invoice_number = Column(String)
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)

    client_name = Column(String, nullable=True)
    client_email = Column(String, nullable=True)
    client_phone = Column(String, nullable=True)

    status = Column(Enum(Sale_Status), default=Sale_Status.PENDING)
    payment_method = Column(Enum(Payment_Method))
    payment_status = Column(String, default="paid")

    sale_date = Column(DateTime(timezone=True), default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())
    
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    customer_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    seller_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    income_id = Column(String, ForeignKey("incomes.id"), nullable=False)

    ## Relationships ##
    income = relationship("Income")

    seller_user = relationship("User", foreign_keys=[seller_user_id])
    customer_user = relationship("User", foreign_keys=[customer_user_id])
    company = relationship("Company", back_populates="sales")
    items = relationship("Sale_Item", back_populates="sale", cascade="all, delete-orphan")

##### Sale Item #####
class Sale_Item(Base):
    __tablename__ = "sale_items"

    id = Column(String, primary_key=True, nullable=False)

    sale_id = Column(String, ForeignKey("sales.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)

    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)

    is_service = Column(Boolean, default=False)

    date = Column(DateTime(timezone=True), default=func.now())

    ## Relationships ##
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")
