########## Modules ##########
from fastapi import APIRouter, Request, Depends

from sqlalchemy import or_
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User, User_Role, Company_Origin, Company, User_Company_Invitation

from core.i18n import translate
from core.generator import get_uuid
from core.db_management import add_db
from core.responses import custom_response
from core.permissions import check_permissions
from core.validators import read_json_body, validate_required_fields

########## Variables ##########
router = APIRouter()

########## Get Companies ##########
@router.get("/")
async def get_companies(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    companies = []

    plan = {
        "available": False
    }

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.companies.read")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Operations ###
    companies_data = db.query(Company).all()

    for company in companies_data:
        invited_by = None
        if company.referred_by_user_id:
            invited_by = db.query(User).filter(User.id == company.referred_by_user_id).first()

        in_charge = db.query(User).filter(User.email == company.email).first()

        companies.append({
            "id": company.id,
            "name": company.name,
            "active": company.is_active,
            "suspended": company.is_suspended,
            "plan": plan,
            "in_charge": {
                "username": in_charge.username,
                "fullname": in_charge.fullname,
                "email": in_charge.email
            },
            "origin": company.origin,
            "invited_by": {
                "username": invited_by.username if invited_by else None,
                "fullname": invited_by.fullname if invited_by else None,
                "email": invited_by.email if invited_by else None
            },
            "date": company.date.strftime("%d %B %Y")
        })
        
    return custom_response(status_code=200, message=translate(lang, "platform.companies.get"), data={
        "companies": companies
    })

########## Get roles to select - Create Company ########## Gonna be fix --> plans
@router.get("/get_roles")
async def roles_generate_company(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    roles = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.companies.create")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Operations ###
    filters = [
        User_Role.platform_level == True,
        User_Role.hidden == False
    ]

    role_access, _ = check_permissions(db, request, "platform.users.role")

    if role_access:
        filters = [
            or_(
                User_Role.platform_level.is_(True),
                User_Role.hidden.is_(True)
            )
        ]

    roles_data = db.query(User_Role).filter(*filters).all()

    for role in roles_data:
        roles.append({
            "id": role.id,
            "name": role.name,
            "hidden": role.hidden
        })
        
    return custom_response(status_code=200, message=translate(lang, "platform.companies.get_roles"), data={
        "roles": roles
    })

########## Create Company and Generate Invitation ########## gonna be fix --> plans
@router.post("/create")
async def generate_invitation(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Get Body ###
    new_company_values, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.companies.create")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Validations ###
    required_fields, error = validate_required_fields(new_company_values, ["name", "email", "role_id", "notes"], lang)
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    check_user_exist = db.query(User).filter(User.email == new_company_values.email.lower()).first()

    if not check_user_exist:
        return custom_response(status_code=400, message=translate(lang, "platform.companies.generate_invitation.user_not_exist"))
    
    check_user_role = db.query(User_Role).filter(User_Role.id == new_company_values.role_id).first()

    if not check_user_role:
        return custom_response(status_code=400, message=translate(lang, "platform.companies.generate_invitation.invalid_role_id"))

    new_company = Company(
        id = get_uuid(db, Company),
        name = new_company_values.name,
        code = get_uuid(db, Company),
        email = new_company_values.email,
        origin = Company_Origin.STAFF,
        referred_by_user_id = user.get("id")
    )

    add_db(db, new_company)

    new_user_invitation = User_Company_Invitation(
        id = get_uuid(db, User_Company_Invitation),
        notes = new_company_values.notes,
        user_invited = check_user_exist.id,
        company_id = new_company.id,
        role_id = check_user_role.id
    )
    add_db(db, new_user_invitation)

    ## To implement (send email)

    return custom_response(status_code=200, message=translate(lang, "platform.companies.generate_invitation.success"), data={
        "company_id": new_company.id
    })
