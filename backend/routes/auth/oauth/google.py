########## Modules ##########
import httpx

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Request

from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User, User_OAuth, User_Session

from core.config import settings

from core.i18n import translate
from core.db_management import add_db
from core.security import hash_password
from core.responses import custom_response
from core.validators import read_json_body, validate_required_fields
from core.generator import get_uuid, generate_jwt, generate_temp_password

from services.email.main import template_routes, get_html, send_mail

########## Variables ##########
router = APIRouter()

##########  ##########
@router.post("/google")
async def google_auth(request: Request, db: Session = Depends(get_db)):
    ### Get Body ###
    google_auth_data, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)
    
    ### Variables ###
    lang = request.state.lang
    
    user_id_v = ""

    user_info = {}
    create_link_account = True
    
    ### Validations ###
    required_fields, error = validate_required_fields(google_auth_data, ["code"], request.state.lang)
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    code = google_auth_data.code

    async with httpx.AsyncClient() as client:
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_SECRET_ID,
            "redirect_uri": "https://nexolocal.floua.app/oauth/google",
            "grant_type": "authorization_code",
        }

        token_res = await client.post(token_url, data=token_data)

        if token_res.status_code != 200:
            return custom_response(status_code=400, message=translate(lang, "oauth.google.error.token"))
    
        tokens = token_res.json()

        user_info_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )

        user_info = user_info_res.json()
    
    prov_id = user_info.get("sub")
    email = user_info.get("email")
    username = user_info.get("given_name")
    fullname = user_info.get("name")
    email_veried = user_info.get("email_verified")

    user_data = db.query(User).filter(User.email == email).first()

    if user_data:
        is_new_user = False

        check_oauth_status = db.query(User_OAuth).filter(
            User_OAuth.user_id == user_data.id,
            User_OAuth.provider_user_id == prov_id,
            User_OAuth.provider == "google",
            User_OAuth.email == email
        ).first()

        if check_oauth_status:
            create_link_account = False
        
        user_id_v = user_data.id

    else:
        generated_password = generate_temp_password()

        new_user = User(
            id = get_uuid(db, User),
            username = username,
            fullname = fullname,
            email = email,
            password = hash_password(generated_password)
        )

        add_db(db, new_user)

        user_id_v = new_user.id

        ### Send Email ###
        html_body = await get_html(template_routes.auth.welcome, {
            "username": new_user.username
        })

        await send_mail("no-reply", "Bienvenido a NexoLocal", new_user.email, html_body)

        ### Password Access ###
        html_body = await get_html(template_routes.oauth.google, {
            "username": new_user.username,
            "generated_password": generated_password
        })

        await send_mail("no-reply", "Tu contraseña de acceso", new_user.email, html_body)

    if create_link_account:
        new_link_oauth = User_OAuth(
            id = get_uuid(db, User_OAuth),

            provider = "google",
            provider_user_id = prov_id,
            email = email,

            user_id = user_id_v
        )

        add_db(db, new_link_oauth)

    ### Create Session ###
    new_session = User_Session(
        id = get_uuid(db, User_Session),
        user_id = user_id_v,
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    )

    add_db(db, new_session)

    token = generate_jwt(new_session.id, expires=True)
    response = custom_response(status_code=200, message=translate(lang, "oauth.google.success"))
    response.set_cookie(
        key = settings.TOKEN_NAME,
        value = token,
        httponly = True,
        secure = False, # prod (change to True)
        max_age = new_session.expires_at
    )

    return response
