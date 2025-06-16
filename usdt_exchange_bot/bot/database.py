# usdt_exchange_bot/bot/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "sqlite:///./usdt_exchange.db"  # TODO: Move to config.py

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} # check_same_thread is for SQLite only
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base() # This Base will be used by models to inherit from

def init_db():
    # Import all modules here that define models so that
    # they are registered properly on the metadata. Otherwise
    # you will have to import them first before calling init_db()
    # Base.metadata.create_all(bind=engine) # This line is commented out as models define their own Base for now.
    # To use a single Base, uncomment this and modify models.
    from .models import user, order, transaction # Import model modules

    # Create tables for each model's Base
    # This is a bit unconventional due to multiple Bases.
    # A single Base in models/__init__.py or in database.py is more standard.
    user.Base.metadata.create_all(bind=engine)
    order.Base.metadata.create_all(bind=engine)
    transaction.Base.metadata.create_all(bind=engine)
    print("Initialized the database.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
