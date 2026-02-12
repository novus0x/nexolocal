########## Modules ##########
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request, Depends

from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session

from db.database import get_db
from db.model import User, Ticket_Priority, Ticket_Category, Ticket_Source, Ticket_Status, Ticket_Waiting_For, Ticket_Close_Reason, Ticket, Ticket_Response

from core.config import settings

from core.i18n import translate
from core.generator import get_uuid
from core.responses import custom_response
from core.permissions import check_permissions
from core.db_management import add_db, update_db
from core.utils import is_int, pagination, normalize_search
from core.validators import read_json_body, validate_required_fields

########## Variables ##########
router = APIRouter()
TIMEZONE = settings.TIMEZONE

LOCAL_TZ = ZoneInfo(TIMEZONE)
UTZ_TZ = ZoneInfo("UTC")

########## Get Tickets - API ##########
@router.get("/tickets")
async def get_support_tickets(request: Request, q = None, priority: str = None, category: str = None, page = 1, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    tickets = []

    ### Params ###
    page = is_int(page)

    if not page:
        page = 1

    limit = 10
    page = max(page, 1)
    offset = (page - 1) * limit

    if q:
        q = q.strip()
        
        if len(q) < 2:
            q = None

    search = normalize_search(q)

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.support.tickets.manage")
    access2, _ = check_permissions(db, request, "platform.support.tickets.read")
    
    if not access:
        if not access2:
            return custom_response(status_code=400, message=message)
        
    ### Filters ###
    filters = []

    if search:
            filters.append(
                or_(
                    Ticket.code.ilike(f"%{search}%"),
                    Ticket.title.ilike(f"%{search}%")
                )
            )
    
    if priority:
        if priority in Ticket_Priority._value2member_map_:
            filters.append(Ticket.priority == Ticket_Priority(priority))

    if category:
        if category in Ticket_Category._value2member_map_:
            filters.append(Ticket.category == Ticket_Category(category))

    tickets_data = db.query(Ticket).filter(*filters).order_by(
        desc(Ticket.date)
    ).limit(limit).offset(offset).all()

    for ticket in tickets_data:
        user_tickets = {}

        user_data = db.query(User).filter(
            User.id == ticket.created_by_id
        ).first()

        if user_data:
            user_tickets["email"] = user_data.email

        tickets.append({
            "id": ticket.id,
            "code": ticket.code,
            "title": ticket.title,
            "priority": ticket.priority,
            "category": ticket.category,
            "user": user_tickets,
            "date": ticket.date
        })

    total_tickets = db.query(Ticket).filter(*filters).count()

    return custom_response(status_code=200, message=translate(lang, "platform.support.tickets.get"), data={
        "tickets": tickets,
        "pagination": pagination(total_tickets, limit, offset)
    })

########## Get Tickets - API ##########
@router.get("/tickets/get/{ticket_id}")
async def get_ticket_by_id(request: Request, ticket_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ticket = {}
    ticket_items = []

    user_value = {}
    companies_related = []

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.support.tickets.manage")
    access2, _ = check_permissions(db, request, "platform.support.tickets.read")
    
    if not access:
        if not access2:
            return custom_response(status_code=400, message=message)
        
    ### Main Ticket ###
    ticket_data = db.query(Ticket).filter(
        Ticket.code == ticket_id
    ).first()

    if not ticket_data:
        return custom_response(status_code=400, message=translate(lang, "platform.support.tickets.get.unique.error"))
    
    ### Check for User ###
    user_data = db.query(User).filter(
        User.id == ticket_data.created_by_id
    ).first()

    if user_data:
        user_value = {
            "id": user_data.id,
            "username": user_data.username,
            "fullname": user_data.fullname,
            "email": user_data.email,
            "verified": user_data.email_verified,
            "lang": user_data.preferred_language,
            "companies": companies_related
        }

    ticket_items_data = db.query(Ticket_Response).filter(
        Ticket_Response.ticket_id == ticket_data.id
    ).order_by(asc(Ticket_Response.date)).all()

    for ticket_item in ticket_items_data:
        user_ticket_item = {}

        user_ticket_item_data = db.query(User).filter(
            User.id == ticket_item.user_id
        ).first()

        if user_ticket_item_data:
            user_ticket_item = {
                "id": user_ticket_item_data.id,
                "fullname": user_ticket_item_data.fullname,
                "staff": ticket_item.staff_response
            }

        ticket_item_date = ticket_item.date.astimezone(LOCAL_TZ).strftime("%H:%M - %d %b %Y")
        
        ticket_items.append({
            "id": ticket_item.id,
            "content": ticket_item.content_html,
            "is_public": ticket_item.is_public,
            "is_final": ticket_item.is_final,
            "date": ticket_item_date,
            "user": user_ticket_item
        })

    ticket = {
        "id": ticket_data.id,
        "code": ticket_data.code,

        "title": ticket_data.title,
        "description": ticket_data.description,

        "priority": ticket_data.priority,
        "category": ticket_data.category,
        "waiting_for": ticket_data.waiting_for,

        "date": ticket_data.date,

        "client": user_value,
        "items": ticket_items
    }

    if ticket_data.status == Ticket_Status.NEW:
        ticket_data.status = Ticket_Status.OPEN

        update_db(db)

    return custom_response(status_code=200, message=translate(lang, "platform.support.ticket.create.success"), data={
        "ticket": ticket
    })

########## Create Response - API ##########
@router.post("/tickets/{ticket_id}/response/create")
async def create_new_ticket_response(request: Request, ticket_id: str, db: Session = Depends(get_db)):
    ### Variables ###
    lang = request.state.lang
    user = request.state.user

    ### Validation ###
    if user == None:
        return custom_response(status_code=400, message=translate(lang, "validation.require_auth"))

    ### Check permissions ###
    access, message = check_permissions(db, request, "platform.support.tickets.manage")
    access2, _ = check_permissions(db, request, "platform.support.tickets.response")
    
    if not access:
        if not access2:
            return custom_response(status_code=400, message=message)
        
    ### Check Ticket ###
    ticket_data = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket_data:
        return custom_response(status_code=400, message=translate(lang, "platform.support.tickets.get.unique.error"))
    
    ### Get Body ###
    check_new_response, error = await read_json_body(request)
    if error: 
        return custom_response(status_code=400, message=error)
        
    required_fields, error = validate_required_fields(check_new_response, ["description", "internal"])
    if error:
        return custom_response(status_code=400, message=translate(lang, "validation.required_f"), details=required_fields)

    new_response = Ticket_Response(
        id = get_uuid(db, Ticket_Response),
        content_html = check_new_response.description,
        staff_response = True,

        user_id = user.get("id"),
        ticket_id = ticket_data.id
    )

    if check_new_response.internal == "1":
        new_response.is_public = False

    ticket_data.waiting_for = Ticket_Waiting_For.CLIENT

    if ticket_data.status != Ticket_Status.IN_PROGRESS:
        ticket_data.status = Ticket_Status.IN_PROGRESS

    add_db(db, new_response)
    update_db(db)

    return custom_response(status_code=200, message=translate(lang, "platform.support.ticket.response.create.success"), data={})
