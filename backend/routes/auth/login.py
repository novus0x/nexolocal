########## Modules ##########
from datetime import timezone, datetime, timedelta

from fastapi import APIRouter, Depends, Request

from sqlalchemy import desc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User, User_Session

from core.config import settings

from core.i18n import translate
from core.responses import custom_response
from core.db_management import add_db
from core.generator import get_uuid, generate_jwt
from core.security import check_password
from core.validators import read_json_body, validate_required_fields

########## Variables ##########
router = APIRouter()

########## Login ##########
@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    ### Get Body ###
    user, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)
    
    ### Variables ###
    lang = request.state.lang
    
    ### Validations ###
    required_fields, error = validate_required_fields(user, ["email", "password", "expires"], request.state.lang)
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    user_data = db.query(User).filter(User.email == user.email).first()
    if not user_data:
        return custom_response(status_code=400, message=translate(lang, "auth.login.invalid_credentials"))
    
    if not check_password(user_data.password, user.password):
        return custom_response(status_code=400, message=translate(lang, "auth.login.invalid_credentials"))
    
    new_session = User_Session(
        id = get_uuid(db, User_Session),
        user_id = user_data.id,
        expires_at = None
    )

    if user.expires == "0":
        new_session.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    add_db(db, new_session)

    token = generate_jwt(new_session.id, expires=user.expires)
    response = custom_response(status_code=200, message=translate(lang, "auth.login.success"))
    response.set_cookie(
        key = settings.TOKEN_NAME,
        value = token,
        httponly = True,
        secure = False, # prod (change to True)
        max_age = new_session.expires_at
    )

    return response
