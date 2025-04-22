from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from database import Base

class Tabla(Base):
    __tablename__ = 