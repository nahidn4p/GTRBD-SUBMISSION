from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Phone(Base):
    __tablename__ = 'phones'
    
    model = Column(String, primary_key=True)
    release_date = Column(String, nullable=True)
    display = Column(String, nullable=True)
    battery = Column(String, nullable=True)
    camera = Column(String, nullable=True)
    ram = Column(String, nullable=True)
    storage = Column(String, nullable=True)
    price = Column(Integer, nullable=True)

def get_session(db_url):
    try:
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session  # Return the sessionmaker factory
    except Exception as e:
        raise ValueError(f"Failed to create database engine: {e}")