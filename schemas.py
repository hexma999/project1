from pydantic import BaseModel
from typing import Optional

# 회원가입시 데이터 검증
class UserCreate(BaseModel):
    username: str
    email: str
    password: str # 해시전 패스워드를 받습니다.
    birthdate: str
    phone_number: str
    gender: str

# 회원로그인시 데이터 검증    
class UserLogin(BaseModel):
    username: str
    password: str # 해시전 패스워드를 받습니다.

class MemoCreate(BaseModel):
    title: str
    content: str
    
class MemoUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None    

# 내 정보 수정 요청 데이터
class UserUpdate(BaseModel):
    password: Optional[str] = None      # 비밀번호 변경 
    email: Optional[str] = None         # 이메일 변경
    phone_number: Optional[str] = None  # 전화번호 변경 

# 리뷰 작성 요청 데이터
class ReviewRequest(BaseModel):
    content: str