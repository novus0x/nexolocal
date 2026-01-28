########## Modules ##########
from datetime import datetime, timezone

from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Numeric, Integer

##### Category #####
class Business(Base):
    __tablename__ = "business"

    id = Column(String, primary_key=True)

    name = Column(String, nullable=False)
    date = Column(DateTime(timezone=True), default=func.now())

    user_id = Column(String, ForeignKey("users.id"), nullable=True)

    ## Relationships ##
    user = relationship("User")
