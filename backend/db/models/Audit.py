########## Modules ##########
import enum

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text

##### Audit #####
class Audit_Scope(enum.Enum):
    COMPANY = "company"
    PLATFORM = "platform"
    SYSTEM = "system"

class Audit_Status(enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"

class Audit_Source(enum.Enum):
    WEB = "web"
    API = "api"
    WORKER = "worker"
    SYSTEM = "system"

class Audit_Log(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, nullable=False)

    scope = Column(Enum(Audit_Scope), nullable=False)
    status = Column(Enum(Audit_Status), default=Audit_Status.SUCCESS, nullable=False)
    source = Column(Enum(Audit_Source), default=Audit_Source.API, nullable=False)

    module = Column(String, nullable=False)
    action = Column(String, nullable=False)

    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=True)

    message = Column(Text, nullable=True)

    request_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)

    before_data = Column(JSONB, nullable=True)
    after_data = Column(JSONB, nullable=True)
    extra_data = Column(JSONB, nullable=True)

    actor_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=True)

    date = Column(DateTime(timezone=True), default=func.now())

    ## Relationships ##
    actor_user = relationship("User")
    company = relationship("Company")
