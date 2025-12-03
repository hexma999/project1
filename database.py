from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 데이터베이스 URL 정의
#DATABASE_URL = "mysql+pymysql://apple:1111@localhost:3307/aidetect"
DATABASE_URL = "mysql+pymysql://admin:dnjsgmlwhgdk@team-db.cf4wuo0gsigf.ap-southeast-2.rds.amazonaws.com:3306/aidetect"

# 엔진 생성
engine = create_engine(DATABASE_URL, echo=True)

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()
