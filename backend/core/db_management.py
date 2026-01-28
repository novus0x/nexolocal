########## Modules ##########
from sqlalchemy.orm import Session

########## Add to DB ##########
def add_db(db: Session, element):
    db.add(element)
    db.commit()
    db.refresh(element)

########## Add to DB - Multiple ##########
def add_multiple_db(db: Session, elements):
    db.add_all(elements)
    db.commit()

########## Update db ##########
def update_db(db: Session):
    db.commit()

########## Delete db ##########
def delete_db(db: Session, element):
    db.delete(element)
    db.commit()
