from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel 
from typing import List, Annotated

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = FastAPI()

# class: define las distintas partes de fastapi

# URL de conexión a la base de datos PostgreSQL
URL_DATABASE = 'postgresql://postgres:lzPostgre00@localhost:5432/tfm_db'
engine = create_engine(URL_DATABASE)

# Crear una sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependencia para obtener la sesión de la base de datos


# Endpoints
@app.get('/')
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()