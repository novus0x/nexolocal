########## Modules ##########
from fastapi import APIRouter, Depends, Request

from sqlalchemy.orm import Session

from db.database import get_db
from db.model import Company, Company_Invitation, User_Company_Invitation, User_Role, User, User_Company_Association

from core.utils import time_ago
from core.i18n import translate
from core.generator import get_uuid
from core.responses import custom_response
from core.db_management import update_db, add_db
from core.validators import read_json_body, validate_required_fields

########## Variables ##########
router = APIRouter()

########## Invitations ##########
@router.get("/")
async def invitations(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    invitations = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    invitations_data = db.query(User_Company_Invitation).filter(
        User_Company_Invitation.user_invited == user.get("id"),
        User_Company_Invitation.used == False
    ).all()

    for invitation in invitations_data:
        company = db.query(Company).filter(
            Company.id == invitation.company_id
        ).first()

        role = db.query(User_Role).filter(
            User_Role.id == invitation.role_id
        ).first()

        company_invitation = db.query(Company_Invitation).filter(
            Company_Invitation.email == user.get("email")
        ).first()

        user_inviter = db.query(User).filter(
            User.id == company_invitation.user_inviter
        ).first()

        invitations.append({
            "id": invitation.id,
            "company_name": company.name,
            "inviter": user_inviter.fullname,
            "permissions": role.permissions,
            "date": time_ago(invitation.date)
        })

    return custom_response(status_code=200, message=translate(lang, "general.invitations.get"), data={
        "invitations": invitations
    })

########## Invitations ##########
@router.post("/accept")
async def accept_invitation(request: Request, db: Session = Depends(get_db)):
    ### Get Body ###
    invitation, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)
    
    ### Variables ###
    lang = request.state.lang
    
    ### Validations ###
    required_fields, error = validate_required_fields(invitation, ["invitation_id"], request.state.lang)
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    user_company_invitation = db.query(User_Company_Invitation).filter(
        User_Company_Invitation.id == invitation.invitation_id
    ).first()

    if not user_company_invitation:
        return custom_response(status_code=400, message=translate(lang, "general.invitations.accept.error"), details=required_fields)

    user_role = db.query(User_Role).filter(
        User_Role.id == user_company_invitation.role_id
    ).first()

    if not user_role:
        return custom_response(status_code=400, message=translate(lang, "general.invitations.accept.no_role"), details=required_fields)

    company = db.query(Company).filter(
        Company.id == user_company_invitation.company_id
    ).first()

    if not company:
        return custom_response(status_code=400, message=translate(lang, "general.invitations.accept.no_company"), details=required_fields)

    if user_company_invitation.used == True:
        return custom_response(status_code=400, message=translate(lang, "general.invitations.accept.already_used"), details=required_fields)

    user_company_invitation.accepted = True
    user_company_invitation.used = True
    update_db(db)

    user_company_association = User_Company_Association(
        id = get_uuid(db, User_Company_Association),
        user_id = user.get("id"),
        company_id = company.id,
        role_id = user_role.id
    )
    
    add_db(db, user_company_association)

    return custom_response(status_code=200, message=translate(lang, "general.invitations.accept.success"), data={
        "company_id": company.id
    })
