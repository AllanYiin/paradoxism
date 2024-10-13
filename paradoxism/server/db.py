
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# 初始化資料庫
DATABASE_URL = "sqlite:///./paradoxism.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
