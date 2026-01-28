########## Modules ##########
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from db.database import Base, engine

from routes.general import welcome, invitations
from routes.platform import companies, roles, users
from routes.auth import login, register, sessions, logout
from routes.companies import company, products, finance, sales, c_dashboard, cash

from middlewares.i18n import i18n_middleware
from middlewares.auth import auth_middleware
from middlewares.db import db_session_middleware

from scripts.auto_migrate import auto_migrate

########## Create tables ##########
Base.metadata.create_all(bind=engine)

########## Events ##########
@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.AUTO_MIGRATE:
        print("Running Auto-Migrations")
        auto_migrate()

    yield
    # shutdown

########## Initializations ##########
app = FastAPI(
    lifespan = lifespan,
    title = "NexoLocal API",
    description = "Backend",
    version = "1.0.0",
)

########## CORS ##########
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

########## Middleware ##########
app.middleware("http")(i18n_middleware)  
app.middleware("http")(auth_middleware)    
app.middleware("http")(db_session_middleware) 

########## Routes ##########
app.include_router(login.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(register.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(sessions.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(logout.router, prefix="/api/auth", tags=["Authentication"])

app.include_router(companies.router, prefix="/api/platform/companies", tags=["Platform", "Companies"])
app.include_router(users.router, prefix="/api/platform/users", tags=["Platform", "Users"])
app.include_router(roles.router, prefix="/api/platform/roles", tags=["Platform", "Roles"])

app.include_router(c_dashboard.router, prefix="/api/company/dashboard", tags=["Dashboard", "Company"])
app.include_router(company.router, prefix="/api/company/companies", tags=["Companies", "Company"])
app.include_router(products.router, prefix="/api/company/products", tags=["Products", "Company"])
app.include_router(finance.router, prefix="/api/company/finance", tags=["Finance", "Company"])
app.include_router(sales.router, prefix="/api/company/sales", tags=["Sales", "Company"])
app.include_router(cash.router, prefix="/api/company/cash", tags=["Cash", "Company"])

app.include_router(invitations.router, prefix="/api/general/invitations", tags=["General", "Invitations"])

app.include_router(welcome.router, prefix="/api/public", tags=["Public"])
