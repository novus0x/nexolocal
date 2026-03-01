########## Modules ##########
from datetime import timezone, datetime, timedelta

from fastapi import APIRouter, Depends, Request

from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User, User_Verification

from core.i18n import translate
from core.generator import get_uuid
from core.responses import custom_response
from core.db_management import add_db, update_db

from services.email.main import template_routes, get_html, send_mail

########## Variables ##########
router = APIRouter()

########## Verify Account ##########
@router.post("/verify-account")
async def verify_account(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Verify User ###
    user_data = db.query(User).filter(
        User.id == user.get("id")
    ).first()

    if user_data and not user_data.email_verified:
        ### Check Verification User ###
        now = datetime.now(timezone.utc)

        verification = db.query(User_Verification).filter(
            User_Verification.user_id == user.get("id"),
            User_Verification.used == False,
            User_Verification.expires_at > now
        ).first()

        if verification:
            new_user_verification = verification
            new_user_verification.expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

            update_db(db)
        else:
            ### Create Verification for User ###
            new_user_verification = User_Verification(
                id = get_uuid(db, User_Verification),
                user_id = user.get("id")
            )
            
            new_user_verification.expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

            add_db(db, new_user_verification)
    
        ### Send Mail ###
        html_body = await get_html(template_routes.account.verify, {
            "username": user_data.username,
            "verify_id": new_user_verification.id
        })

        await send_mail("no-reply", "Verifica tu cuenta", user_data.email, html_body)

    return custom_response(status_code=200, message=translate(lang, "auth.verify_account.sent"))

########## Verify Account ##########
@router.post("/verify-account/{verification_id}")
async def verify_account(request: Request, verification_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
   
    ### Check Verification ###
    check_verification = db.query(User_Verification).filter(
        User_Verification.id == verification_id
    ).first()

    if not check_verification:
        return custom_response(status_code=400, message=translate(lang, "auth.verify_account.error"))
    
    ### Get User data ###
    user_data = db.query(User).filter(
        User.id == check_verification.user_id
    ).first()

    ### Update Data
    user_data.email_verified = True
    check_verification.used = True

    ### Update DB ###
    update_db(db)

    return custom_response(status_code=200, message=translate(lang, "auth.verify_account.success"))
