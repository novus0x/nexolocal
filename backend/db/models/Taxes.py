########## Modules ##########
import enum

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Numeric, JSON, Boolean, Enum

##### Tax Profile #####
class Tax_Environment_Type(enum.Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"

class Tax_Profile(Base):
    __tablename__ = "tax_profiles"

    id = Column(String, primary_key=True, nullable=False)

    legal_name = Column(String, nullable=False) # razon social
    country_code = Column(String(2), default="PE")

    address_line = Column(Text, nullable=True)
    region = Column(String, nullable=True)
    city = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)

    country = Column(String(2), default="PE")

    tax_id_type = Column(String, nullable=True) # RUC, DNI, VAT, ETC
    tax_id = Column(String, nullable=True) # RUC value
    tax_regime = Column(String, nullable=True) # NRUS RER RMT RG

    sol_user = Column(String, nullable=True)
    sol_password = Column(String, nullable=True)

    tax_provider = Column(String, default="none")
    environment = Column(Enum(Tax_Environment_Type), default=Tax_Environment_Type.SANDBOX)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    ## Relationships ##
    company = relationship("Company")

##### Tax Document Status #####
class Tax_Document_Status(enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ERROR = "error"
    CANCELLED = "cancelled"

class Tax_Document(Base):
    __tablename__ = "tax_documents"

    id = Column(String, primary_key=True, nullable=False)

    doc_type = Column(String, nullable=False)
    
    series = Column(String, nullable=False)
    number = Column(Integer, nullable=False)

    issue_date = Column(DateTime(timezone=True), nullable=False)
    currency = Column(String(3), default="PEN")

    customer_name = Column(String, nullable=False)
    customer_tax_id_type = Column(String, nullable=False)
    customer_tax_id = Column(String, nullable=True)

    subtotal = Column(Numeric(12, 2), nullable=False)
    tax_total = Column(Numeric(12, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)

    status = Column(Enum(Tax_Document_Status), default=Tax_Document_Status.DRAFT, nullable=False)
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    sent_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    hash = Column(String, nullable=True)

    provider_document_id = Column(String, nullable=True)
    provider_payload = Column(JSON, nullable=True)
    provider_response = Column(JSON, nullable=True)

    artifact_pdf_url = Column(Text, nullable=True)
    
    date = Column(DateTime(timezone=True), default=func.now())

    # En caso de correccion
    affected_document_id = Column(String, ForeignKey("tax_documents.id"), nullable=True)
    note_reason = Column(Text, nullable=True)

    sale_id = Column(String, ForeignKey("sales.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    ## Relationships ##
    sale = relationship("Sale")
    company = relationship("Company")
    items = relationship("Tax_Document_Item", back_populates="document")

##### Tax Document Item #####
class Tax_Document_Item(Base):
    __tablename__ = "tax_document_items"

    id = Column(String, primary_key=True, nullable=False)
    tax_document_id = Column(String, ForeignKey("tax_documents.id"))

    description = Column(String, nullable=False)

    qty = Column(Numeric(12, 2), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)

    line_subtotal = Column(Numeric(12, 2), nullable=False)
    line_tax = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    ## Relationships ##
    document = relationship("Tax_Document", back_populates="items")

##### Tax Period #####
class Tax_Period_Status(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    DECLARED = "declared"

class Tax_Period(Base):
    __tablename__ = "tax_periods"

    id = Column(String, primary_key=True, nullable=False)

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    sales_base = Column(Numeric(12, 2), default=0)
    sales_tax = Column(Numeric(12, 2), default=0)

    purchases_base = Column(Numeric(12, 2), default=0)
    purchases_tax = Column(Numeric(12, 2), default=0)

    tax_payable = Column(Numeric(12, 2), default=0)

    status = Column(Enum(Tax_Period_Status), default=Tax_Period_Status.OPEN)

    date = Column(DateTime(timezone=True), default=func.now())

    company_id = Column(String, ForeignKey("companies.id"))

    ## Relationships ##
    company = relationship("Company")

##### Tax Series #####
class Tax_Series(Base):
    __tablename__ = "tax_series"

    id = Column(String, primary_key=True, nullable=False)

    doc_type = Column(String, nullable=False) # 01 | 03
    series = Column(String, nullable=False)
    current_number = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    ## Relationships ##
    company = relationship("Company")

##### Tax Subscription #####
class Tax_Emission_Status(enum.Enum):
    AUTO = "auto"
    MANUAL = "manual"

class Tax_Subscription_Plan(enum.Enum):
    FREE = "free"
    PREMIUM = "premium"

class Tax_Subscription(Base):
    __tablename__ = "tax_subscriptions"

    id = Column(String, primary_key=True, nullable=False)

    emission_mode = Column(Enum(Tax_Emission_Status), default=Tax_Emission_Status.AUTO)

    plan_type = Column(Enum(Tax_Subscription_Plan), default=Tax_Subscription_Plan.FREE) # FREE | PREMIUM
    is_active = Column(Boolean, default=True, nullable=False)

    start_date = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    ## Relationships ##
    company = relationship("Company")

##### Tax Usage #####
class Tax_Usage(Base):
    __tablename__ = "tax_usage"

    id = Column(String, primary_key=True, nullable=False)

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    emissions_count = Column(Integer, default=0, nullable=False)

    date = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    ## Relationships ##
    company = relationship("Company")
