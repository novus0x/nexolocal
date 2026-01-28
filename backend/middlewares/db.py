########## Modules ##########
from fastapi import Request

from db.database import SessionLocal

########## DB Session Middleware ##########
async def db_session_middleware(request: Request, call_next):
    request.state.db = SessionLocal()
    try:
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response
