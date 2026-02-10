########## Modules ##########
import enum

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Enum, Text, Boolean, Integer

##### Expense #####
class Expense_Category(enum.Enum):
    OFFICE_SUPPLIES = "OFFICE_SUPPLIES"
    SUPPLIES = "SUPPLIES"
    UTILITIES = "UTILITIES"
    SALARIES = "SALARIES"
    MARKETING = "MARKETING"
    TRAVEL = "TRAVEL"
    MAINTENANCE = "MAINTENANCE"
    RENT = "RENT"
    OTHER = "OTHER"

class Expense_Status(enum.Enum):
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    PAID = "PAID"

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String, primary_key=True, nullable=False)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    notes = Column(Text)

    amount = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False)

    category = Column(Enum(Expense_Category), nullable=False)
    subcategory = Column(String)

    status = Column(Enum(Expense_Status), default=Expense_Status.PENDING)
    receipt_url = Column(String)

    payment_date = Column(DateTime(timezone=True), default=func.now())

    is_recurring = Column(Boolean, default=False)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    approved_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=True)

    ## Relationships ##
    approver = relationship("User")
    supplier = relationship("Supplier")
    
    company = relationship("Company", back_populates="expenses")

##### Expense Recurring #####
class Expense_Recurring(Base):
    __tablename__ = "expenses_recurring"
    
    id = Column(String, primary_key=True, nullable=False)

    months = Column(Integer, nullable=False)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    expense_id = Column(String, ForeignKey("expenses.id"), nullable=False)

    ## Relationships ##
    expense = relationship("Expense")
