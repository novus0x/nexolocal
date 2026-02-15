########## Modules ##########
from db.model import Company, Sale

from services.tax_engine.utils import *

from services.tax_engine.pe import pe

########## Process ##########
async def process(db, company_id, sale):
    #
    print("processing")

    return
