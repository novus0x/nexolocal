########## Modules ##########
from datetime import datetime, timezone

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Integer, Numeric

##### Promotion #####
class Promotion(Base):
    __tablename__ = "promotions"

    id = Column(String, primary_key=True, nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(Text)

    promo_type = Column(String, nullable=False)
    promo_code = Column(String, nullable=True)

    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True)
    applies_automatically = Column(Boolean, default=True)

    date = Column(DateTime(timezone=True), default=func.now())

    ## Relationships ##
    items = relationship("Promotion_Item", back_populates="promotion", cascade="all, delete-orphan")
    actions = relationship("Promotion_Action", back_populates="promotion", cascade="all, delete-orphan")

##### Promotion Item #####
class Promotion_Item(Base):
    __tablename__ = "promotion_items"

    id = Column(String, primary_key=True, nullable=False)
    promotion_id = Column(String, ForeignKey("promotions.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)

    quantity_required = Column(Integer, default=1)

    ## Relationships ##
    promotion = relationship("Promotion", back_populates="items")
    product = relationship("Product")

##### Promotion Action #####
class Promotion_Action(Base):
    __tablename__ = "promotion_actions"

    id = Column(String, primary_key=True, nullable=False)

    action_type = Column(String, nullable=False)

    value = Column(Numeric(10, 2), nullable=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)

    ## Relationships ##
    promotion = relationship("Promotion", back_populates="actions")
