from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from schemas import UserCreate, UserLogin
from dependencies import get_db, get_password_hash, verify_password
# 데이터 레이어 임포트
from data import auth as auth_data

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
async def signup(signup_data: UserCreate, db: Session = Depends(get_db)):
    # 1. 중복 확인 (Data 레이어 호출)
    existing_user = auth_data.get_user_by_username(db, signup_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 동일 사용자 이름이 가입되어 있습니다.")

    hashed_password = get_password_hash(signup_data.password)

    # 2. 회원 저장 (Data 레이어 호출)
    try:
        auth_data.create_user(db, signup_data.username, signup_data.email, hashed_password)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="회원가입 실패")

    return {"message": "회원가입 성공"}

@router.post("/login")
async def login(request: Request, signin_data: UserLogin, db: Session = Depends(get_db)):
    # 1. 사용자 조회 (Data 레이어 호출)
    user = auth_data.get_user_by_username(db, signin_data.username)

    if user and verify_password(signin_data.password, user.hashed_password):
        request.session["username"] = user.username
        return {"message": "로그인 성공"}
    
    raise HTTPException(status_code=401, detail="로그인 실패")

@router.post("/logout")
async def logout(request: Request):
    request.session.pop("username", None)
    return {"message": "로그아웃 성공"}