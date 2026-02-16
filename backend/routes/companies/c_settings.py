########## Modules ##########
from types import SimpleNamespace

from fastapi import APIRouter, Request, Depends, UploadFile, File

from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Company, Company_Plan

from core.i18n import translate
from core.generator import get_uuid
from core.responses import custom_response
from core.permissions import check_permissions
from core.db_management import add_db, update_db
from core.validators import read_json_body, validate_required_fields

########## Variables ##########
router = APIRouter()

########## Company Information - GET ##########
@router.get("/")
async def get_company_information(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    company_info = {
        "company": {},
        "plan": {
            "available": False
        },
        "tax_profile": {}
    }

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.settings.read", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)

    ### Operations ###
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    if not company:
        return custom_response(status_code=400, message=translate(lang, "company.settings.does_not_exist"))

    company_info["company"] = {
        "id": company.id,
        "country_code": company.country_code,
        "name": company.name,
        "description": company.description,
        "is_formal": company.is_formal,
        "email": company.email,
        "phone": company.phone,
        "address": company.address,
        "active": company.is_active,
        "status": company.subscription_status,
        "business": company.is_business,
    }

    ### Check Plan ###
    company_plan = db.query(Company_Plan).filter(
        Company_Plan.id == company.plan_type_id
    ).first()

    if company_plan:
        company_info["plan"] = {
            "available": True,

            "name": company_plan.name,
            "price": company_plan.price,
            "cicle": company_plan.plan_cycle
        }

    if company.is_formal:
        print("formal")

    return custom_response(status_code=200, message=translate(lang, "company.settings.get.success"), data={
        "information": company_info
    })

########## Company Information - POST ##########
@router.post("/update")
async def update_company_information(request: Request, file: UploadFile = File(None), db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    company_id = request.state.company_id

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "company.settings.update", company_id)
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Get Body ###
    form = await request.form()
    company_info = SimpleNamespace(**dict(form))

    required_fields, error = validate_required_fields(company_info, [
        "commercial_name", "description", "email", "phone", "is_formal",
        "legal_name", "tax_id", "address_line", "region", "city", "postal_code",
        "tax_user", "tax_password", "invoice_series", "invoice_number", "receipt_series",
        "receipt_number"
    ], lang)
    print(required_fields)

    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)    

    ### Operations ###
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    if not company:
        return custom_response(status_code=400, message=translate(lang, "company.settings.does_not_exist"))

    company.name = company_info.commercial_name
    company.email = company_info.email
    
    if company_info.description != "none":
        company.description = company_info.description
    else:
        company.description = None

    if company_info.phone != "none":
        company.phone = company_info.phone
    else:
        company.phone = None

    if company_info.is_formal == "1":
        print("Formal")
        
        file_content = await file.read()
        print(file_content.decode("utf-8"))

    update_db(db)

    return custom_response(status_code=200, message=translate(lang, "company.settings.update.success"))
