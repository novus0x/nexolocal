########## Modules ##########
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request, Depends

from sqlalchemy.orm import Session

from db.database import get_db

from core.config import settings

from core.i18n import translate
from core.responses import custom_response
from core.billing import build_billing_overview

########## Variables ##########
router = APIRouter()
TIMEZONE = settings.TIMEZONE

LOCAL_TZ = ZoneInfo(TIMEZONE)

########## Dashboard ##########
@router.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Build Overview ###
    overview_data = build_billing_overview(db, user.get("id"), LOCAL_TZ)

    return custom_response(status_code=200, message=translate(lang, "general.dashboard.get"), data=overview_data)
