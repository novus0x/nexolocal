########## Modules ##########
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Request, Depends

from sqlalchemy import asc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Company_Plan

from core.config import settings

from core.i18n import translate
from core.responses import custom_response

########## Variables ##########
router = APIRouter()
TIMEZONE = settings.TIMEZONE

LOCAL_TZ = ZoneInfo(TIMEZONE)
UTZ_TZ = ZoneInfo("UTC")

########## Main Page ##########
@router.get("/")
async def welcome(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang

    plans = []

    ### Get Plans ###
    plans_data = db.query(Company_Plan).order_by(asc(Company_Plan.position)).all()

    for plan in plans_data:
        descriptions_data = plan.description.split("\n")    

        plans.append({
            "id": plan.id,
            "name": plan.name,
            "price": plan.price,
            "description": descriptions_data,
            "highlight": plan.highlight,
            "highlight_title": plan.highlight_title,
            "highlight_subtitle": plan.highlight_subtitle,
            "cycle": plan.plan_cycle
        })
        
    return custom_response(status_code=200, message=translate(lang, "general.plans.get"), data={
        "plans": plans
    })
