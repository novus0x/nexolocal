########## Modules ##########
from fastapi import APIRouter, Request, Depends

from sqlalchemy import desc, asc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User

from core.i18n import translate
from core.generator import get_uuid
from core.db_management import add_db
from core.responses import custom_response
from core.validators import read_json_body, validate_required_fields
from core.permissions import get_permissions, filter_existing_permissions

########## Variables ##########
router = APIRouter()

########## Get Users ##########
@router.get("/")
async def users(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    user_is_admin = request.state.user_is_admin
    users = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Get permissions ###
    if user_is_admin:
        users_data = db.query(User).order_by(desc(User.date)).all()

        for user_value in users_data:
            users.append({
                "id": user_value.id,
                "fullname": user_value.fullname,
                "username": user_value.username,
                "email": user_value.email,
                "verified": user_value.email_verified,
                "block": user_value.is_blocked,
                "date": user_value.date.strftime("%d %B %Y")
            })
    else:
        return custom_response(status_code=400, message=translate(lang, "validation.not_necessary_permission"))
        
    return custom_response(status_code=200, message=translate(lang, "platform.users.get"), data={
        "users": users
    })
