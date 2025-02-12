from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

URL_DATABASE = 'postgresql://postgres:lzPostgre00@db:5432/tfm_db'

engine = create_engine(URL_DATABASE, echo= True)
Session = sessionmaker(engine)
Base = declarative_base() # ns 
