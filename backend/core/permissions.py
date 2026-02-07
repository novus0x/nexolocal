########## Modules ##########
import json

from sqlalchemy.orm import Session

from db.model import User, User_Role, User_Company_Association

from core.i18n import translate

########## Variables ##########
_permissions = json.load(open("db/permissions.json"))

########## Get Permissions ##########
def get_permissions():
    return [_permissions.get("platform"), _permissions.get("company")]


def get_permission(type):
    # print(_permissions.get("meta"))
    # print(_permissions.get("platform"))
    # print(_permissions.get("company"))
    # print(_permissions.get("user"))

    return _permissions.get(type, _permissions.get("meta"))

########## Get all permisions in block ##########
def extract_permission_keys_from_block(block):
    keys = []

    if not block or "permissions" not in block:
        return keys

    for group in block["permissions"]:
        for perm in group.get("permissions", []):
            key = perm.get("key")
            if key:
                keys.append(key)

    return keys

########## Get all permissions for admin ##########
def get_all_permissions_for_admin():
    all_keys = []

    for section in ("platform", "company", "user"):
        block = _permissions.get(section)
        all_keys.extend(extract_permission_keys_from_block(block))

    return all_keys

########## Filter existing permissions ##########
def filter_existing_permissions(requested):
    if not requested:
        return []

    valid_keys = []

    for section in ("platform", "company", "user"):
        block = _permissions.get(section)
        valid_keys.extend(extract_permission_keys_from_block(block))

    return [p for p in requested if p in valid_keys]

########## Check Permissions ##########
def check_permissions(db: Session, request, permission, company_id = None):
    ### Variables ###
    user = request.state.user
    lang = request.state.lang
    is_admin = request.state.user_is_admin

    if is_admin:
        return True, ""
    else:
        ## Check available role (opt)
        user = db.query(User).filter(User.id == user.get("id")).first()

        if not user:
            return False, translate(lang, "validation.not_necessary_permission")
    
        if user.is_blocked:
            return False, translate(lang, "validation.account_suspended")
        
        if user.role_id:
            role = db.query(User_Role).filter(User_Role.id == user.role_id).first()

            if role:
                if permission in role.permissions:
                    return True, ""
                
        if company_id:
            company = db.query(User_Company_Association).filter(
                User_Company_Association.company_id == company_id,
                User_Company_Association.user_id == user.id
            ).first()

            if company:
                role_c = db.query(User_Role).filter(
                    User_Role.id == company.role_id
                ).first()

                if role_c:
                    if permission in role_c.permissions:
                        return True, ""        

    return False, translate(lang, "validation.not_necessary_permission")
