########## Modules ##########
import enum

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Enum, Text, Boolean

from db.models.Sale import Payment_Method

##### Cash Sessions #####
class Cash_Session_Status(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"

class Cash_Session(Base):
    __tablename__ = "cash_sessions"

    id = Column(String, primary_key=True)

    initial_cash = Column(Numeric(10,2), default=0)

    expected_cash = Column(Numeric(10,2), default=0)
    counted_cash = Column(Numeric(10,2), nullable=True)
    difference = Column(Numeric(10,2), nullable=True)
    description = Column(Text, nullable=True)

    status = Column(Enum(Cash_Session_Status), default=Cash_Session_Status.OPEN)
    difference_exists = Column(Boolean, nullable=True)
    
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    opened_by_id = Column(String, ForeignKey("users.id"), nullable=False)

    closed_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), default=func.now())

    date = Column(DateTime(timezone=True), default=func.now())

    ## Relationships ##
    opened_by = relationship("User")
    company = relationship("Company")

##### Cash Movement #####
class Cash_Movement_Type(enum.Enum):
    SALE = "sale"
    INCOME = "income"
    EXPENSE = "expense"
    WITHDRAW = "withdraw"
    ADJUSTMENT = "adjustment"

class Cash_Movement(Base):
    __tablename__ = "cash_movements"

    id = Column(String, primary_key=True)

    type = Column(Enum(Cash_Movement_Type))
    amount = Column(Numeric(10,2), nullable=False)

    payment_method = Column(Enum(Payment_Method)) 
    description = Column(String)

    related_sale_id = Column(String, ForeignKey("sales.id"), nullable=True)
    related_income_id = Column(String, ForeignKey("incomes.id"), nullable=True)
    related_expense_id = Column(String, ForeignKey("expenses.id"), nullable=True)

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    cash_session_id = Column(String, ForeignKey("cash_sessions.id"), nullable=False)

    date = Column(DateTime(timezone=True), default=func.now())

    ## Relationships ##
    related_sale = relationship("Sale")
    related_income = relationship("Income")
    related_expense = relationship("Expense")

    company = relationship("Company")
    cash_session = relationship("Cash_Session")
