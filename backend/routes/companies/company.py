########## Modules ##########
from fastapi import APIRouter, Request, Depends

from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Company, User_Company_Association

from core.i18n import translate
from core.generator import get_uuid
from core.db_management import add_db
from core.responses import custom_response
from core.validators import read_json_body, validate_required_fields

########## Variables ##########
router = APIRouter()

########## Validate Company id - Company ##########
@router.post("/validate_company_id")
async def validate_company_id(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Get Body ###
    company_check, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)
        
    required_fields, error = validate_required_fields(company_check, ["company_id"])
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    ### Operations ###
    company = db.query(Company).filter(
        Company.id == company_check.company_id
    ).first()

    if not company:
        return custom_response(status_code=400, message=translate(lang, "company.companies.verify.no_exist"))

    company_data = {
        "id": company.id,
        "name": company.name,
        "taxes": company.is_formal
    }

    return custom_response(status_code=200, message=translate(lang, "company.companies.verify.success"), data={
        "company": company_data
    })
