########## Modules ##########
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Request, Depends

from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User_Company_Association

from core.config import settings

from core.i18n import translate
from core.responses import custom_response

########## Variables ##########
router = APIRouter()
TIMEZONE = settings.TIMEZONE

LOCAL_TZ = ZoneInfo(TIMEZONE)
UTZ_TZ = ZoneInfo("UTC")

########## Dashboard ##########
@router.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check Companies Quantity ###
    companies_q = db.query(User_Company_Association).filter(
        User_Company_Association.user_id == user.get("id")
    ).count()

    return custom_response(status_code=200, message=translate(lang, "general.dashboard.get"), data={
        "companies_q": companies_q
    })
