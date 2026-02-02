########## Modules ##########
from db.database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Integer

##### User #####
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, nullable=False)

    username = Column(String, nullable=False)
    fullname = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    birth = Column(DateTime, nullable=False, default=func.now())
    email_verified = Column(Boolean, default=False)
    date = Column(DateTime(timezone=True), default=func.now())

    is_platform_super_admin = Column(Boolean, default=False)
    preferred_language = Column(String, default="en")

    # Extra #
    is_blocked = Column(Boolean, default=False)
    role_id = Column(String, ForeignKey("user_roles.id"), nullable=True) # opt
    
    ## Relationships ##
    verification = relationship("User_Verification", back_populates="user")
    sessions = relationship("User_Session", back_populates="user", cascade="all, delete-orphan")
    company_associations = relationship("User_Company_Association", back_populates="user")
    oauth_accounts = relationship("User_OAuth", back_populates="user")

##### User Verification #####
class User_Verification(Base):
    __tablename__ = "user_verification"

    id = Column(String, primary_key=True, nullable=False)

    used = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))
    date = Column(DateTime(timezone=True), default=func.now())

    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    ## Relationships ##
    user = relationship("User", back_populates="verification")

##### User Session #####
class User_Session(Base):
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, nullable=False)

    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), default=func.now())
    date = Column(DateTime(timezone=True), default=func.now())

    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    ## Relationships ##
    user = relationship("User", back_populates="sessions")

##### User Role #####
class User_Role(Base):
    __tablename__ = "user_roles"

    id = Column(String, primary_key=True, nullable=False)

    name = Column(String, nullable=False)
    description = Column(Text)
    permissions = Column(JSONB, default=list)

    platform_level = Column(Boolean, default=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=True)

    date = Column(DateTime(timezone=True), default=func.now())

##### User OAuth #####
class User_OAuth(Base):
    __tablename__ = "users_oauth"

    id = Column(String, primary_key=True, nullable=False)  

    provider = Column(String, nullable=False) 
    provider_user_id = Column(String, nullable=False)
    email = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)

    date = Column(DateTime(timezone=True), default=func.now())

    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    ## Relationships ##
    user = relationship("User", back_populates="oauth_accounts")

##### User Associations #####
class User_Company_Association(Base):
    __tablename__ = "user_company_associations"

    id = Column(String, primary_key=True, nullable=False)

    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    date = Column(DateTime(timezone=True), default=func.now())

    user_id = Column(String, ForeignKey("users.id"))
    company_id = Column(String, ForeignKey("companies.id"))
    role_id = Column(String, ForeignKey("user_roles.id"), nullable=True)

    is_customer = Column(Boolean, default=False)
    is_business = Column(Boolean, default=False)

    loyalty_points = Column(Integer, default=0)

    ## Relationships ##
    role = relationship("User_Role")
    user = relationship("User", back_populates="company_associations")
    company = relationship("Company", back_populates="user_associations")

##### Company Invitation #####
class User_Company_Invitation(Base):
    __tablename__ = "user_company_invitations"

    id = Column(String, primary_key=True, nullable=False)

    used = Column(Boolean, default=False)
    date = Column(DateTime(timezone=True), default=func.now())

    notes = Column(Text, nullable=True)
    accepted = Column(Boolean, default=False, nullable=False)
    user_invited = Column(String, ForeignKey("users.id"), nullable=False)

    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    role_id = Column(String, ForeignKey("user_roles.id"), nullable=False)

    ## Relationships ##
    user = relationship("User")
    role = relationship("User_Role")
    company = relationship("Company")
