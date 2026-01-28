########## Modules ##########
from fastapi import APIRouter, Depends, Request

from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User, User_Role, Company, User_Company_Invitation, User_Company_Association

from core.i18n import translate
from core.responses import custom_response
from core.permissions import get_all_permissions_for_admin

########## Variables ##########
router = APIRouter()

########## Session ##########
@router.get("/user")
async def user(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    user_is_admin = request.state.user_is_admin
    company_id = request.state.company_id

    permisions_data = []
    invitations = {
        "exist": False,
        "quantity": 0
    }
    user_company_associations = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Get permissions ###
    if user_is_admin:
        permisions_data = get_all_permissions_for_admin()
    else:
        user_data = db.query(User).filter(
            User.id == user.get("id")
        ).first()

        if user_data.role_id:
            user_role_data = db.query(User_Role).filter(
                User_Role.id == user_data.role_id
            ).first()

            if user_role_data:
                print("role_id permissions exists")

        if company_id:
            user_company = db.query(User_Company_Association).filter(
                User_Company_Association.company_id == company_id,
                User_Company_Association.user_id == user.get("id")
            ).first()

            if user_company:
                user_roles_data_c = db.query(User_Role).filter(
                    User_Role.id == user_company.role_id
                ).first()

                if user_roles_data_c:

                    for permission in user_roles_data_c.permissions:

                        if not permission in permisions_data:
                            permisions_data.append(permission)

    ### ###
    user_company_association = db.query(User_Company_Association).filter(
        User_Company_Association.user_id == user.get("id")
    ).all()
    
    for company_association in user_company_association:
        company = db.query(Company).filter(
            Company.id == company_association.company_id
        ).first()

        user_company_associations.append({
            "id": company.id,
            "name": company.name
        })

    invitations_data = db.query(User_Company_Invitation).filter(
        User_Company_Invitation.user_invited == user.get("id"),
        User_Company_Invitation.used == False
    ).all()

    if len(invitations_data) > 0:
        invitations["exist"] = True
        invitations["quantity"] = len(invitations_data)    
    
    user["user_companies"] = user_company_associations
    
    return custom_response(status_code=200, message=translate(lang, "auth.session.success"), data={
        "user": user,
        "permissions": permisions_data,
        "invitations": invitations
    })
