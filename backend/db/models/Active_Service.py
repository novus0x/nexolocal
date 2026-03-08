########## Modules ##########
import enum

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum, Numeric

from db.models.Product import Product_Service_Duration

##### Active Service #####
class Active_Service_Status(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    EXHAUSTED = "exhausted"
    NO_CUSTOMER = "no_customer"
    CANCELLED = "cancelled"

class Active_Service(Base):
    __tablename__ = "active_services"

    id = Column(String, primary_key=True, nullable=False)

    name = Column(String, nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False, default=1)

    duration = Column(Numeric(10, 3), nullable=True)
    duration_type = Column(Enum(Product_Service_Duration), nullable=True)

    sessions_total = Column(Integer, nullable=True)
    sessions_used = Column(Integer, default=0)

    status = Column(Enum(Active_Service_Status), default=Active_Service_Status.ACTIVE, nullable=False)

    starts_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_validated_at = Column(DateTime(timezone=True), nullable=True)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    sale_id = Column(String, ForeignKey("sales.id"), nullable=False)
    sale_item_id = Column(String, ForeignKey("sale_items.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    customer_id = Column(String, ForeignKey("company_customers.id"), nullable=True)

    ## Relationships ##
    company = relationship("Company", back_populates="active_services")
    sale = relationship("Sale", back_populates="active_services")
    sale_item = relationship("Sale_Item", back_populates="active_services")
    product = relationship("Product", back_populates="active_services")
    customer = relationship("Company_Customer", back_populates="active_services")
