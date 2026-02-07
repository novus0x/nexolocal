########## Modules ##########
from fastapi import APIRouter, Request, Depends

from sqlalchemy import and_
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User, User_Role, Company_Invitation, Company, User_Company_Invitation

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
        company_invitation = db.query(Company_Invitation).filter(
            Company_Invitation.id == company.code
        ).first()

        invited_by = db.query(User).filter(User.id == company_invitation.user_inviter).first()
        in_charge = db.query(User).filter(User.email == company.email).first()

        companies.append({
            "id": company.id,
            "name": company.name,
            "plan": company.plan_type,
            "active": company.is_active,
            "suspended": company.is_suspended,
            "in_charge": {
                "username": in_charge.username,
                "fullname": in_charge.fullname,
                "email": in_charge.email
            },
            "invited_by": {
                "username": invited_by.username,
                "fullname": invited_by.fullname,
                "email": invited_by.email
            },
            "date": company.date.strftime("%d %B %Y")
        })
        
    return custom_response(status_code=200, message=translate(lang, "platform.companies.get"), data={
        "companies": companies
    })

########## Get roles to select - Create Company ##########
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
    ]

    role_access, _ = check_permissions(db, request, "platform.users.role")

    if role_access:
        filters = [
            and_(
                User_Role.platform_level.is_(True),
                User_Role.hidden.is_(True)
            )
        ]

    roles_data = db.query(User_Role).filter(*filters).all()

    for role in roles_data:
        roles.append({
            "id": role.id,
            "name": role.name,
        })
        
    return custom_response(status_code=200, message=translate(lang, "platform.companies.get_roles"), data={
        "roles": roles
    })

########## Create Company and Generate Invitation ##########
@router.post("/create")
async def generate_invitation(request: Request, db: Session = Depends(get_db)):
    ### Get Body ###
    new_company_values, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)

    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.companies.create")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Validations ###
    required_fields, error = validate_required_fields(new_company_values, ["name", "email", "role_id", "notes"], request.state.lang)
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    check_user_exist = db.query(User).filter(User.email == new_company_values.email.lower()).first()

    if not check_user_exist:
        return custom_response(status_code=400, message=translate(lang, "platform.companies.generate_invitation.user_not_exist"))
    
    check_user_role = db.query(User_Role).filter(User_Role.id == new_company_values.role_id).first()

    if not check_user_role:
        return custom_response(status_code=400, message=translate(lang, "platform.companies.generate_invitation.invalid_role_id"))

    ### Generate invitation ###
    new_company_invitation = Company_Invitation(
        id = get_uuid(db, Company_Invitation),
        email = new_company_values.email,
        role_id = check_user_role.id,
        user_inviter = user.get("id")
    )

    new_company = Company(
        id = get_uuid(db, Company),
        name = new_company_values.name,
        code = new_company_invitation.id,
        email = new_company_values.email,
    )

    add_db(db, new_company)

    new_company_invitation.company_id = new_company.id
    add_db(db, new_company_invitation)

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
