########## Modules ##########
import enum

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Integer, Numeric, Enum

##### Company #####
class Company_Subscription_Status(enum.Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, nullable=False)

    country_code = Column(String, default="pe")

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    code = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)

    is_active = Column(Boolean, default=False)
    is_suspended = Column(Boolean, default=False)
    
    subscription_status = Column(Enum(Company_Subscription_Status), default=Company_Subscription_Status.TRIAL)

    max_users = Column(Integer, default=1)

    is_business = Column(Boolean, default=False)
    is_formal = Column(Boolean, default=False)

    start_date = Column(DateTime(timezone=True), default=func.now())

    subscription_ends_at = Column(DateTime(timezone=True), nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    business_id = Column(String, ForeignKey("business.id"), nullable=True)
    plan_type_id = Column(String, ForeignKey("company_plans.id"), nullable=True)

    ## Relationships ##
    business = relationship("Business")
    company_plan = relationship("Company_Plan")

    sales = relationship("Sale", back_populates="company")
    products = relationship("Product", back_populates="company")
    expenses = relationship("Expense", back_populates="company")
    suppliers = relationship("Supplier", back_populates="company")
    categories = relationship("Category", back_populates="company")
    billings = relationship("Company_Billing", back_populates="company")
    invitations = relationship("Company_Invitation", back_populates="company")
    user_associations = relationship("User_Company_Association", back_populates="company")

##### Company Plan #####
class Plan_Cicle(enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Company_Plan(Base):
    __tablename__ = "company_plans"

    id = Column(String, primary_key=True, nullable=False)

    name = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=False)

    position = Column(Integer, nullable=False, default=0)

    highlight = Column(Boolean, default=False)
    highlight_title = Column(String, nullable=True)
    highlight_subtitle = Column(String, nullable=True)

    plan_cycle = Column(Enum(Plan_Cicle), default=Plan_Cicle.MONTHLY, nullable=False)

    public = Column(Boolean, default=True, nullable=False)

    role_id = Column(String, ForeignKey("user_roles.id"), nullable=False)

    date = Column(DateTime(timezone=True), default=func.now())

    ## Relationships ##
    role = relationship("User_Role")

##### Company Billing #####
class Billing_Status(enum.Enum):
    ACCEPTED = "accepted"
    PENDING = "pending"
    REJECTED = "rejected"

class Company_Billing(Base):
    __tablename__ = "company_billings"

    id = Column(String, primary_key=True)
    invoice_number = Column(String, nullable=True)

    amount = Column(Numeric(10,2), nullable=False)
    currency = Column(String(3), default="PEN")

    status = Column(Enum(Billing_Status), default=Billing_Status.PENDING, nullable=False) 

    payment_method = Column(String, nullable=True)  

    reference = Column(String, nullable=True)  

    paid_at = Column(DateTime(timezone=True), nullable=True)

    billing_cycle = Column(Enum(Plan_Cicle), nullable=False)

    date = Column(DateTime(timezone=True), default=func.now())

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    plan_id = Column(String, ForeignKey("company_plans.id"), nullable=False)

    ## Relationships ##
    plan = relationship("Company_Plan")
    company = relationship("Company", back_populates="billings")

##### Company Invitation #####
class Company_Invitation(Base):
    __tablename__ = "company_invitations"

    id = Column(String, primary_key=True, nullable=False)

    email = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    date = Column(DateTime(timezone=True), default=func.now())

    user_inviter = Column(String, ForeignKey("users.id"), nullable=False)

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    role_id = Column(String, ForeignKey("user_roles.id"), nullable=False)

    ## Relationships ##
    role = relationship("User_Role")
    company = relationship("Company", back_populates="invitations")
