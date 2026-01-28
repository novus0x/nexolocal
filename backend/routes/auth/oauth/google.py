########## Modules ##########
from fastapi import APIRouter, Depends, Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

########## Variables ##########
router = APIRouter(prefix="/google", tags=["OAuth - Google"])
oauth = OAuth()

##########  ##########

