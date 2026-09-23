from database import Base, engine
from models.application import Application


Base.metadata.create_all(bind=engine)