########## Modules ##########
from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Integer

##### Company #####
class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, nullable=False)

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    code = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)

    is_active = Column(Boolean, default=False)
    is_suspended = Column(Boolean, default=False)
    plan_type = Column(String(20), default="basic")
    subscription_status = Column(String(20), default="active")

    max_users = Column(Integer, default=1)

    # trial = Column(Boolean, default=False)
    is_business = Column(Boolean, default=False)
    business_id = Column(String, ForeignKey("business.id"), nullable=True)

    is_formal = Column(Boolean, default=False)

    start_date = Column(DateTime(timezone=True), default=func.now())

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    ## Relationships ##
    business = relationship("Business")
    sales = relationship("Sale", back_populates="company")
    products = relationship("Product", back_populates="company")
    expenses = relationship("Expense", back_populates="company")
    suppliers = relationship("Supplier", back_populates="company")
    categories = relationship("Category", back_populates="company")
    invitations = relationship("Company_Invitation", back_populates="company")
    user_associations = relationship("User_Company_Association", back_populates="company")

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
