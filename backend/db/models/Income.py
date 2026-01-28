########## Modules ##########
import enum

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Enum, Text, Boolean, Integer

##### Income #####
class Income_Status(enum.Enum):
    PENDING = "pending"
    RECEIVED = "received"

class Income(Base):
    __tablename__ = "incomes"

    id = Column(String, primary_key=True, nullable=False)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    notes = Column(Text)

    amount = Column(Numeric(10, 2), nullable=False)

    subcategory = Column(String)

    status = Column(Enum(Income_Status), default=Income_Status.PENDING)

    payment_date = Column(DateTime(timezone=True), nullable=True)

    is_recurring = Column(Boolean, default=False)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    approved_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    ## Relationships ##
    approver = relationship("User")
    company = relationship("Company")

##### Income Recurring #####
class Income_Recurring(Base):
    __tablename__ = "incomes_recurring"
    
    id = Column(String, primary_key=True, nullable=False)

    months = Column(Integer, nullable=False)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    income_id = Column(String, ForeignKey("incomes.id"), nullable=False)

    ## Relationships ##
    income = relationship("Income")
