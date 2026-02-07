########## Modules ##########
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Request, Depends

from sqlalchemy import desc, and_
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User, User_Role

from core.config import settings

from core.i18n import translate
from core.generator import get_uuid
from core.responses import custom_response
from core.db_management import add_db, update_db
from core.validators import read_json_body, validate_required_fields
from core.permissions import check_permissions

########## Variables ##########
router = APIRouter()
TIMEZONE = settings.TIMEZONE

LOCAL_TZ = ZoneInfo(TIMEZONE)
UTZ_TZ = ZoneInfo("UTC")

########## Get Users ##########
@router.get("/")
async def users(request: Request, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user
    users = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))
    
    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.users.read")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Get permissions ###
    users_data = db.query(User).order_by(desc(User.date)).all()

    for user_value in users_data:
        users.append({
            "id": user_value.id,
            "fullname": user_value.fullname,
            "username": user_value.username,
            "email": user_value.email,
            "verified": user_value.email_verified,
            "block": user_value.is_blocked,
            "date": user_value.date.astimezone(LOCAL_TZ).strftime("%d %B %Y")
        })
        
    return custom_response(status_code=200, message=translate(lang, "platform.users.get"), data={
        "users": users
    })

########## Get User by ID ##########
@router.get("/get/{user_id}")
async def get_user_by_id(request: Request, user_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    user_role = {
        "available": False
    }

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.users.read")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Get User Data ###
    user_data = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user_data:
        return custom_response(status_code=400, message=translate(lang, "platform.users.update.error"))
    
    user_data.date = user_data.date.astimezone(LOCAL_TZ).strftime("%H:%M - %d %b %Y")

    ### Get User Role ###
    if user_data.role_id:
        user_role_data = db.query(User_Role).filter(
            User_Role.id == user_data.role_id
        ).first()

        user_role_data_value = {
            "id": user_role_data.id,
            "name": user_role_data.name,
            "platform_level": user_role_data.platform_level,
            "hidden": user_role_data.hidden,
        }

        if not user_role_data:
            user_data.role_id = ""
            update_db(db)
        else:
            user_role = {
                **user_role,
                **user_role_data_value
            }

            user_role["available"] = True
    
    return custom_response(status_code=200, message=translate(lang, "platform.users.get.unique"), data={
        "user": user_data,
        "role": user_role
    })

########## Update User - GET ##########
@router.get("/update/{user_id}")
async def update_user(request: Request, user_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    user_role = {
        "available": False
    }

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.users.update")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Get User Data ###
    user_data = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user_data:
        return custom_response(status_code=400, message=translate(lang, "platform.users.error"))
    
    user_data.date = user_data.date.astimezone(LOCAL_TZ).strftime("%H:%M - %d %b %Y")

    ### Get User Role ###
    if user_data.role_id:
        user_role_data = db.query(User_Role).filter(
            User_Role.id == user_data.role_id
        ).first()

        user_role_data_value = {
            "id": user_role_data.id,
            "name": user_role_data.name,
            "platform_level": user_role_data.platform_level,
            "hidden": user_role_data.hidden,
        }

        if not user_role_data:
            user_data.role_id = ""
            update_db(db)
        else:
            user_role = {
                **user_role,
                **user_role_data_value
            }

            user_role["available"] = True

    ### Get Available Roles ###
    filters = [
        and_(
            User_Role.platform_level.is_(True),
            User_Role.hidden.is_(True)
        )
    ]

    roles = db.query(User_Role).filter(*filters).all()

    return custom_response(status_code=200, message=translate(lang, "platform.users.get.unique"), data={
        "user": user_data,
        "role": user_role,
        "roles": roles
    })

########## Update User - POST ##########
@router.post("/update/{user_id}")
async def update_user(request: Request, user_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.users.update")
    
    if not access:
        return custom_response(status_code=400, message=message)
    
    ### Get User Data ###
    user_data = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user_data:
        return custom_response(status_code=400, message=translate(lang, "platform.users.update.error"))
    
    ### Get Body ###
    update_user, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)
    
    required_fields, error = validate_required_fields(update_user, ["username", "fullname", "email", "status", "role", "phone", "description"])
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)
    
    user_data.username = update_user.username
    user_data.fullname = update_user.fullname

    if update_user.email != "no_change":
        user_data.email = update_user.email

    change_status1, _ = check_permissions(db, request, "platform.users.block")
    change_status2, _ = check_permissions(db, request, "platform.users.unblock")

    if update_user.status == "suspended" and change_status1:
        user_data.is_blocked = True
    
    if update_user.status == "active" and change_status2:
        user_data.is_blocked = False

    user_new_role = update_user.role

    if user_new_role != "no_change":
        if user_new_role == "delete":
            user_data.role_id = None # Delete Role
        else:
            check_role = db.query(User_Role).filter(
                User_Role.id == user_new_role
            ).first()

            ### Only if role exist
            if check_role:
                user_data.role_id = check_role.id

    # Others opts later
    update_db(db)

    return custom_response(status_code=200, message=translate(lang, "platform.users.update.success"))
