########## Modules ##########
from db.model import Company, Sale

from sqlalchemy.orm import Session

from core.config import settings

from services.tax_engine.utils import get_engine, get_tax_engine_credintials

########## Create Company ##########
async def create_company(db: Session, company_id, tax_profile, files):
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    country_code = company.country_code.lower()

    engine, message = get_engine(country_code)

    if not engine:
        return False, message
    
    ### Call Specific Function ###
    response, message = await engine.create_company(company, tax_profile, files)

    if not response:
        return False, message

    return response, ""

########## Get Tax Rate ##########
async def get_tax_rate(db: Session, company_id):
    company = db.query(Company).filter(
        Company.id == company_id
    ).first()

    country_code = company.country_code.lower()

    engine, message = get_engine(country_code)

    if not engine:
        return False, message
    
    ### Get Tax Function ###
    response = await engine.get_tax_rate()

    print(response)

########## Process ##########
async def process(db, company_id, sale):
    #
    print("processing")

    return
