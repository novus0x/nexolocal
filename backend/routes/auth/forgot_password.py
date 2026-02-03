########## Modules ##########
from datetime import timezone, datetime, timedelta

from fastapi import APIRouter, Depends, Request

from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User, User_Recover

from core.i18n import translate
from core.generator import get_uuid
from core.security import hash_password
from core.responses import custom_response
from core.db_management import add_db, update_db
from core.validators import read_json_body, validate_required_fields

from services.email.main import template_routes, get_html, send_mail

########## Variables ##########
router = APIRouter()

########## Forgot Password ##########
@router.post("/forgot-password")
async def forgot_password(request: Request, db: Session = Depends(get_db)):
    ### Get Body ###
    user, error = await read_json_body(request)

    if error: 
        return custom_response(status_code=400, message=error)
    
    ### Variables ###
    lang = request.state.lang
    
    ### Validations ###
    required_fields, error = validate_required_fields(user, ["email"], request.state.lang)
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    user_data = db.query(User).filter(User.email == user.email).first()

    if user_data:
        now = datetime.now(timezone.utc)

        active_recover = db.query(User_Recover).filter(
            User_Recover.user_id == user_data.id,
            User_Recover.used == False,
            User_Recover.expires > now
        )

        if active_recover:
            new_recover = User_Recover(
                id = get_uuid(db, User_Recover),
                expires = now + timedelta(minutes=10),
                user_id = user_data.id
            )

            add_db(db, new_recover)

            html_body = await get_html(template_routes.auth.reset_password, {
                "username": user_data.username,
                "recover_id": new_recover.id
            })

            await send_mail("no-reply", "Solicitud de restablecimiento de contraseña", user_data.email, html_body)

    return custom_response(status_code=200, message=translate(lang, "auth.forgot_password.success"))

########## Recover Account Verify ##########
@router.post("/recover-account-verify")
async def recover_account_verify(request: Request, db: Session = Depends(get_db)):
    ### Get Body ###
    recover, error = await read_json_body(request)

    if error: 
        return custom_response(status_code=400, message=error)
    
    ### Variables ###
    lang = request.state.lang
    
    ### Validations ###
    required_fields, error = validate_required_fields(recover, ["recover_id"], request.state.lang)
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    now = datetime.now(timezone.utc)

    recover_data = db.query(User_Recover).filter(
        User_Recover.id == recover.recover_id,
        User_Recover.used == False,
        User_Recover.expires > now
    ).first()

    if not recover_data:
        return custom_response(status_code=400, message=translate(lang, "auth.recover.invalid_or_expired"))

    return custom_response(status_code=200, message=translate(lang, "auth.recovery.valid"))

########## Recover Account ##########
@router.post("/recover-account")
async def recover_account(request: Request, db: Session = Depends(get_db)):
    ### Get Body ###
    recover, error = await read_json_body(request)

    if error: 
        return custom_response(status_code=400, message=error)
    
    ### Variables ###
    lang = request.state.lang
    
    ### Validations ###
    required_fields, error = validate_required_fields(recover, ["recover_id", "new_password", "confirm_new_password"], request.state.lang)
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    now = datetime.now(timezone.utc)

    recover_data = db.query(User_Recover).filter(
        User_Recover.id == recover.recover_id,
        User_Recover.used == False,
        User_Recover.expires > now
    ).first()

    if not recover_data:
        return custom_response(status_code=400, message=translate(lang, "auth.recover.invalid_or_expired"))
    
    if recover.new_password != recover.confirm_new_password:
        return custom_response(status_code=400, message=translate(lang, "auth.recover.pass_dont_match"))

    if len(recover.new_password) < 12:
        return custom_response(status_code=400, message=translate(lang, "auth.recover.min_char"))
    
    user = db.query(User).filter(
        User.id == recover_data.user_id
    ).first()

    user.password = hash_password(recover.new_password)
    recover_data.used = True
    update_db(db)

    return custom_response(status_code=200, message=translate(lang, "auth.recovery.success"))
