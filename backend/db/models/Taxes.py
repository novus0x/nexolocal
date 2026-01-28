########## Modules ##########
from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Numeric, JSON

##### Tax Profile #####
class Tax_Profile(Base):
    __tablename__ = "tax_profiles"

    id = Column(String, primary_key=True, nullable=False)

    legal_name = Column(String, nullable=False) # razon social
    fiscal_address = Column(Text, nullable=True)

    country_code = Column(String(2), default="PE")

    ### RUC = identificador de empresas ### 
    tax_id_type = Column(String, nullable=True) # RUC, DNI, VAT, ETC
    tax_id = Column(String, nullable=True) # RUC value
    tax_regime = Column(String, nullable=True) # NRUS RER RMT RG
    tax_provider = Column(String, default="none")

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    ## Relationships ##
    company = relationship("Company")

##### Tax Document #####
class Tax_Document(Base):
    __tablename__ = "tax_documents"

    id = Column(String, primary_key=True, nullable=False)
    sale_id = Column(String, ForeignKey("sales.id"), nullable=False)

    doc_type = Column(String, nullable=False)
    
    series = Column(String, nullable=False)
    number = Column(Integer, nullable=False)

    issue_date = Column(DateTime(timezone=True), nullable=False)
    currecy = Column(String(3), default="PEN")

    customer_name = Column(String, nullable=False)
    customer_tax_id_type = Column(String, nullable=False)
    customer_tax_id = Column(String, nullable=True)

    subtotal = Column(Numeric(12, 2), nullable=False)
    tax_total = Column(Numeric(12, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)

    status = Column(String, default="draft")

    provider_document_id = Column(String, nullable=True)
    provider_payload = Column(JSON, nullable=True)
    provider_response = Column(JSON, nullable=True)

    artifact_xml_url = Column(Text, nullable=True)
    artifact_pdf_url = Column(Text, nullable=True)
    artifact_cdr_url = Column(Text, nullable=True)
    
    date = Column(DateTime(timezone=True), default=func.now())

    # En caso de correccion
    affected_document_id = Column(String, ForeignKey("tax_documents.id"), nullable=True)
    note_reason = Column(Text, nullable=True)

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)

    ## Relationships ##
    company = relationship("Company")
    sale = relationship("Sale")
    items = relationship("Tax_Document_Item", back_populates="document")

##### Tax Document Item #####
class Tax_Document_Item(Base): # Details
    __tablename__ = "tax_document_items"

    id = Column(String, primary_key=True, nullable=False)
    tax_document_id = Column(String, ForeignKey("tax_documents.id"))

    description = Column(String, nullable=False)

    qty = Column(Numeric(12, 2), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)

    line_subtotal = Column(Numeric(12, 2), nullable=False)
    line_tax = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    document = relationship("Tax_Document", back_populates="items")

##### Tax Period #####
class Tax_Period(Base):
    __tablename__ = "tax_periods"

    id = Column(String, primary_key=True, nullable=False)
    company_id = Column(String, ForeignKey("companies.id"))

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    sales_base = Column(Numeric(12, 2), default=0)
    sales_tax = Column(Numeric(12, 2), default=0)

    purchases_base = Column(Numeric(12, 2), default=0)
    purchases_tax = Column(Numeric(12, 2), default=0)

    tax_payable = Column(Numeric(12, 2), default=0)

    status = Column(String, default="OPEN")
    # OPEN | CLOSED | DECLARED

    date = Column(DateTime(timezone=True), default=func.now())
