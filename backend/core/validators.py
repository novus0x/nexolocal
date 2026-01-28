########## Modules ##########
import json, datetime

from datetime import timezone

from types import SimpleNamespace

from fastapi import Request
from sqlalchemy.orm import Session

from db.model import User_Session, User

from core.i18n import translate
from core.config import settings
from core.security import check_jwt
from core.db_management import update_db

########## Read Json params ##########
async def read_params(request: Request):
    query_params = request.query_params
    return dict(query_params)

########## Read Json body ##########
async def read_json_body(request: Request):
    try:
        body = await request.body()
        data = json.loads(body)
        obj = SimpleNamespace(**data)
        return obj, None
    except json.JSONDecodeError:
        return None, "Invalid Json"

########## Validate required fields  ##########
def validate_required_fields(data: dict, fields: list, lang="en"):
    required_fields = []

    for field in fields:
        clean_name = field.replace("_", " ").capitalize()

        if not hasattr(data, field) or str(getattr(data, field)).strip() == "":
            msg = translate(lang, "validation.required").replace("{{field}}", clean_name)
            required_fields.append({"field": field, "message": msg})

    if len(required_fields) > 0:
        return required_fields, True

    return None, False

########## Get token ##########
async def get_token(request, db: Session, required = False):
    token = request.cookies.get(settings.TOKEN_NAME)
    if not token:
        return None, True

    if required == False:
        return {}, None

    token_data, error = check_jwt(token)

    if error:
        return None, "Invalid token"

    user_session = db.query(User_Session).filter(User_Session.id == token_data["session_id"]).first()
    
    if not user_session:
        return None, "Invalid token"

    return token_data["session_id"], False
