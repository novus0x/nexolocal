########## Modules ##########
from fastapi import APIRouter, Request, Depends

from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User

from core.i18n import translate
from core.db_management import update_db
from core.responses import custom_response
from core.security import check_password, hash_password
from core.validators import read_json_body, validate_required_fields

from services.email.main import template_routes, get_html, send_mail

########## Variables ##########
router = APIRouter()

########## Check Sale - Company ##########
@router.post("/update-password")
async def update_password(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Get Body ###
    user_update_password, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    required_fields, error = validate_required_fields(user_update_password, [
        "current_password", "new_password", "confirm_new_password"
    ])

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    user_data = db.query(User).filter(
        User.id == user.get("id")
    ).first()

    if not check_password(user_data.password, user_update_password.current_password):
        return custom_response(status_code=400, message=translate(lang, "users.settings.update_password.incorrect_password"), details=required_fields)
    
    new_password = user_update_password.new_password
    confirm_new_password = user_update_password.confirm_new_password

    if new_password != confirm_new_password:
        return custom_response(status_code=400, message=translate(lang, "users.settings.update_password.passwords_dont_match"), details=required_fields)
    
    if len(new_password) < 12:
        return custom_response(status_code=400, message=translate(lang, "users.settings.update_password.min_char"), details=required_fields)

    new_password_value = hash_password(new_password)
    user_data.password = new_password_value

    update_db(db)

    ### Send Email ###
    html_body = await get_html(template_routes.account.password_updated, {
        "username": user_data.username
    })

    await send_mail("no-reply", "Contraseña cambiada satisfactoriamente", user_data.email, html_body)

    return custom_response(status_code=200, message=translate(lang, "users.settings.update_password.success"), data={})
