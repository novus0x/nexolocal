########## Modules ##########
import enum

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Numeric, Integer, Enum

##### Product-Service type of duration #####
class Product_Service_Duration(enum.Enum):
    MINUTES = 'minutes'
    HOURS = 'hours'
    DAYS = 'days'
    WEEKS = 'weeks'
    MONTHS = 'months'
    YEARS = 'years'
    SESSIONS = 'sessions'

##### Product #####
class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, nullable=False)
    sku = Column(String, nullable=False)
    identifier = Column(String, nullable=False) # unique global

    name = Column(String, nullable=False)
    description = Column(Text, default="No description")
    price = Column(Numeric(10, 2), nullable=False)
    cost = Column(Numeric(10, 2), nullable=True)
    compare_price = Column(Numeric(10, 2), nullable=True)
    
    tax_included = Column(Boolean, default=False)

    stock = Column(Integer, default=0)
    low_stock_alert = Column(Integer, default=5)
    track_inventory = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    is_visible = Column(Boolean, default=True)
    weight = Column(Numeric(8, 2), default=0)
    dimensions = Column(String, default="0x0x0")

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    is_bulk = Column(Boolean, default=False)

    is_service = Column(Boolean, default=False)
    duration = Column(String, nullable=True)
    duration_type = Column(Enum(Product_Service_Duration), nullable=True)
    requires_staff = Column(Boolean, default=False)
    staff_role_required = Column(String, nullable=True)

    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    product_image_id = Column(String, ForeignKey("product_images.id"), nullable=True)

    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=True)

    ## Relationships ##
    supplier = relationship("Supplier")
    product_image = relationship("Product_Image")
    company = relationship("Company", back_populates="products")
    category = relationship("Category", back_populates="products")
    sale_items = relationship("Sale_Item", back_populates="product")

##### Product Batch #####
class Product_Batch(Base):
    __tablename__ = "product_batchs"

    id = Column(String, primary_key=True, nullable=False)

    stock = Column(Integer, default=0)
    price = Column(Numeric(10, 2), nullable=False)
    cost = Column(Numeric(10, 2)) # Comparar precio anterior

    stock_bonus = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    expiration_active = Column(Boolean, default=True)

    expiration_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    expense_id = Column(String, ForeignKey("expenses.id"), nullable=False)

    ## Relationships ##
    product = relationship("Product")
    expense = relationship("Expense")

##### Product Image #####
class Product_Image(Base):
    __tablename__ = "product_images"

    id = Column(String, primary_key=True, nullable=False)
    sku = Column(String, unique=True)

    name = Column(String, nullable=False)
    is_public = Column(Boolean, default=False)
    
    url = Column(String, nullable=False)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())
