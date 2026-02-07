########## Modules ##########
import json, urllib.parse
from datetime import timezone, datetime

from fastapi import Request


from db.model import User, User_Session

from core.config import settings
from core.security import check_jwt
from core.db_management import update_db

########## Auth Middleware ##########
async def auth_middleware(request: Request, call_next):
    request.state.user = None
    request.state.user_error = None
    request.state.user_is_admin = False
    request.state.company_id = None

    company_value = request.cookies.get("company_id")
    if company_value:
        try:
            decoded = urllib.parse.unquote(company_value)
            json_str = decoded.replace("j:", "")
            obj = json.loads(json_str)

            request.state.company_id = obj.get("id")
        except:
            company_value = ""
              
    db = getattr(request.state, "db", None)
    # print("[AUTH] db =", hasattr(request.state, "db"))

    if db is None:
        return await call_next(request)

    token = request.cookies.get(settings.TOKEN_NAME)
    # print("Token: ", token)
    if not token:
        return await call_next(request) 

    token_data, error = check_jwt(token)
    if error:
        request.state.user_error = "auth.token.invalid"
        return await call_next(request)

    session_id = token_data.get("session_id")
    user_session = db.query(User_Session).filter(User_Session.id == session_id).first()

    if not user_session:
        request.state.user_error = "auth.token.invalid"
        return await call_next(request)

    if not user_session.is_active:
        request.state.user_error = "auth.session.expired"
        return await call_next(request)

    now = datetime.now(timezone.utc)

    if user_session.expires_at and user_session.expires_at <= now:
        user_session.is_active = False
        update_db(db)
        request.state.user_error = "auth.session.expired"
        return await call_next(request)

    user_session.last_used_at = now
    update_db(db)

    user_data = db.query(User).filter(User.id == user_session.user_id).first()

    if not user_data:
        request.state.user_error = "auth.token.invalid"
        return await call_next(request)

    request.state.user = {
        "id": user_data.id,
        "fullname": user_data.fullname,
        "username": user_data.username,
        "email": user_data.email,
        "email_verified": user_data.email_verified,
        "is_blocked": user_data.is_blocked,

        "date": user_data.date,
        "lang": getattr(user_data, "preferred_language", "en")
    }

    request.state.user_is_admin = user_data.is_platform_super_admin

    return await call_next(request)
