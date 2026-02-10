########## Modules ##########
import enum

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Enum

##### Supplier #####
class Supplier_Type(enum.Enum):
    PRODUCT = "product"
    SERVICE = "service"
    MIXED = "mixed"
    OTHER = "other"

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String, primary_key=True, nullable=False)

    name = Column(String, nullable=False) # Nombre Comercial
    reason_name = Column(String, nullable=True) # Razon social
    document = Column(String, nullable=True) # RUC

    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    domain = Column(Text, nullable=True)

    type = Column(Enum(Supplier_Type), default=Supplier_Type.PRODUCT, nullable=False)
    is_active = Column(Boolean, default=True)

    date = Column(DateTime(timezone=True), default=func.now())

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    # Relationships
    company = relationship("Company", back_populates="suppliers")
