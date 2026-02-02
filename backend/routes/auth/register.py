########## Modules ##########
from datetime import timezone, datetime, timedelta

from fastapi import APIRouter, Depends, Request

from sqlalchemy import desc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User

from core.i18n import translate
from core.generator import get_uuid
from core.db_management import add_db
from core.security import hash_password
from core.responses import custom_response
from core.validators import read_json_body, validate_required_fields

from services.email.main import template_routes, get_html, send_mail

########## Variables ##########
router = APIRouter()

########## Register ##########
@router.post("/register")
async def register(request: Request, db: Session = Depends(get_db)):
    ### Get Body ###
    user, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)
    
    ### Variables ###
    lang = request.state.lang
    
    ### Validations ###
    required_fields, error = validate_required_fields(user, ["username", "fullname", "email", "password", "confirm_password", "birth"], lang)
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    user_data = db.query(User).filter(User.email == user.email).first()

    if user_data:
        return custom_response(status_code=400, message=translate(lang, "auth.register.email_in_use"))

    if user.password != user.confirm_password:
        return custom_response(status_code=400, message=translate(lang, "auth.register.pass_dont_match"))
        
    ### Improve Password ###
    if len(user.password) < 12:
        return custom_response(status_code=400, message=translate(lang, "auth.register.min_char"))
    
    try:
        birth_year = datetime.fromisoformat(user.birth).date()
    except:
        return custom_response(status_code=400, message=translate(lang, "auth.register.invalid_birth"))
        
    today = datetime.now(timezone.utc).date()

    try:
        max_date = today.replace(year=today.year - 124) - timedelta(days=164)
    except ValueError:
        max_date = today.replace(month=2, day=28, year=today.year - 124) - timedelta(days=164)

    if birth_year < max_date:
        return custom_response(status_code=400, message=translate(lang, "auth.register.too_long"))

    ### Save to DB ###
    new_user = User(
        id = get_uuid(db, User),
        username = user.username.lower(),
        fullname = user.fullname.lower(),
        email = user.email.lower(),
        password = hash_password(user.password),
        birth = user.birth
    )

    add_db(db, new_user)

    ### Send Email ###
    html_body = await get_html(template_routes.auth.welcome, {
        "username": new_user.username
    })

    await send_mail("no-reply", "Bienvenido a NexoLocal", new_user.email, html_body)

    return custom_response(status_code=201, message=translate(lang, "auth.register.success"))
