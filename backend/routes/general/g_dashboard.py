########## Modules ##########
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Request, Depends

from sqlalchemy import desc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User_Company_Association, Company

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

    companies = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check Companies Quantity ###
    companies_q = db.query(User_Company_Association).filter(
        User_Company_Association.user_id == user.get("id")
    ).count()

    ### Get Available Companies ###
    companies_association_data = db.query(User_Company_Association).filter(
        User_Company_Association.user_id == user.get("id")
    ).order_by(desc(User_Company_Association.date)).all()

    for association in companies_association_data:
        company = db.query(Company).filter(
            Company.id == association.company_id
        ).first()

        if company:
            companies.append({
                "id": company.id,
                "name": company.name
            })

    return custom_response(status_code=200, message=translate(lang, "general.dashboard.get"), data={
        "companies_q": companies_q,
        "companies": companies
    })
