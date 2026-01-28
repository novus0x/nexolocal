########## Modules ##########
from fastapi import APIRouter, Depends, Request

from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User_Session

from core.config import settings

from core.i18n import translate
from core.responses import custom_response
from core.db_management import update_db
from core.security import check_jwt

########## Variables ##########
router = APIRouter()

########## Login ##########
@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    ### Get token ###
    token = request.cookies.get(settings.TOKEN_NAME)
    token_data, error = check_jwt(token)
    
    ### Variables ###
    lang = request.state.lang

    if token_data:
        user_session = db.query(User_Session).filter(User_Session.id == token_data["session_id"]).first()

        if user_session:
            user_session.is_active = False
            update_db(db)

    response = custom_response(status_code=200, message=translate(lang, "auth.logout.success"))
    response.delete_cookie(key=settings.TOKEN_NAME)
    return response
