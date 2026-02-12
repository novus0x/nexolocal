########## Modules ##########
import enum

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Enum

##### Ticket #####
class Ticket_Priority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Ticket_Category(enum.Enum):
    TECHNICAL = "technical"
    GENERAL = "general"
    BILLING = "billing"
    ACCOUNT = "account"
    CONFIGURATION = "configuration"
    OTHER = "other"

class Ticket_Source(enum.Enum):
    USER = "user"
    SYSTEM = "system"
    STAFF = "staff"

class Ticket_Status(enum.Enum):
    NEW = "new"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class Ticket_Waiting_For(enum.Enum):
    SUPPORT = "support"
    CLIENT = "client"
    NONE = "none"

class Ticket_Close_Reason(enum.Enum):
    FIXED = "fixed"
    NO_RESPONSE = "no_response"
    USER_ERROR = "user_error"
    DUPLICATE = "duplicate"
    OTHER = "other"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True)
    code = Column(String, unique=True, index=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    priority = Column(Enum(Ticket_Priority), default=Ticket_Priority.MEDIUM, nullable=False)
    category = Column(Enum(Ticket_Category), default=Ticket_Category.GENERAL, nullable=False)

    status = Column(Enum(Ticket_Status), default=Ticket_Status.NEW, nullable=False)
    source = Column(Enum(Ticket_Source), default=Ticket_Source.USER, nullable=False)

    waiting_for = Column(Enum(Ticket_Waiting_For), default=Ticket_Waiting_For.SUPPORT, nullable=False)

    closed_reason = Column(Enum(Ticket_Close_Reason), nullable=True)
    closed_summary = Column(Text, nullable=True)
    
    closed_at = Column(DateTime(timezone=True), nullable=True)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    created_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(String, ForeignKey("users.id"), nullable=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=True)

    ## Relationships ##
    company = relationship("Company")
    created_by = relationship("User", foreign_keys=[created_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])

##### Ticket Response #####
class Ticket_Response(Base):
    __tablename__ = "ticket_responses"

    id = Column(String, primary_key=True, nullable=False)

    content_text = Column(Text, nullable=True)
    content_html = Column(Text, nullable=True)

    is_public = Column(Boolean, default=True)
    is_final = Column(Boolean, default=False)

    staff_response = Column(Boolean, default=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False)

    date = Column(DateTime(timezone=True), default=func.now())

    ## Relationships ##
    user = relationship("User")
    ticket = relationship("Ticket")
