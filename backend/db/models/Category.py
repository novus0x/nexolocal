########## Modules ##########
from datetime import datetime, timezone

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Numeric, Integer

##### Category #####
class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True)

    name = Column(String, nullable=False)
    description = Column(Text)

    date = Column(DateTime(timezone=True), default=func.now())

    parent_id = Column(String, ForeignKey("categories.id"))
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    ## Relationships ##
    company = relationship("Company", back_populates="categories")
    products = relationship("Product", back_populates="category")
    children = relationship("Category", backref="parent", remote_side=[id])
