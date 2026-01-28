########## Modules ##########
from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean

##### Supplier #####
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String, primary_key=True, nullable=False)

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    address = Column(Text)
    document = Column(String)

    is_active = Column(Boolean, default=True)

    date = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    company = relationship("Company", back_populates="suppliers")
    expenses = relationship("Expense", back_populates="supplier")
