from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from schemas import UserCreate, UserLogin, UserUpdate
from dependencies import get_db, get_password_hash, verify_password
from pydantic import BaseModel
from data import auth as auth_data

router = APIRouter(prefix="/auth", tags=["auth"])

class CheckIdRequest(BaseModel):
    username: str

@router.post("/check-id")
async def check_id(request: CheckIdRequest, db: Session = Depends(get_db)):
    existing_user = auth_data.get_user_by_username(db, request.username)
    if existing_user:
        raise HTTPException(status_code=409, detail="이미 사용 중인 아이디입니다.")
    return {"message": "사용 가능한 아이디입니다."}

@router.post("/signup")
async def signup(signup_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = auth_data.get_user_by_username(db, signup_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 가입된 사용자입니다.")

    hashed_password = get_password_hash(signup_data.password)

    try:
        auth_data.create_user(
            db, 
            signup_data.username, 
            signup_data.email, 
            hashed_password,
            signup_data.birthdate,
            signup_data.phone_number,
            signup_data.gender
        )
    except Exception as e:
        db.rollback()
        print(f"회원가입 에러: {e}")
        raise HTTPException(status_code=500, detail="회원가입 처리 중 오류가 발생했습니다.")

    return {"message": "회원가입 성공"}

@router.post("/login")
async def login(request: Request, signin_data: UserLogin, db: Session = Depends(get_db)):
    user = auth_data.get_user_by_username(db, signin_data.username)

    if user and verify_password(signin_data.password, user.hashed_password):
        request.session["username"] = user.username
        request.session["gender"] = user.gender
        request.session["age_group"] = user.age_group
        return {"message": "로그인 성공"}
    
    raise HTTPException(status_code=401, detail="로그인 실패")

@router.post("/logout")
async def logout(request: Request):
    request.session.pop("username", None)
    return {"message": "로그아웃 성공"}

@router.put("/me")
async def update_me(request: Request, update_data: UserUpdate, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    current_user = auth_data.get_user_by_username(db, username)
    if not current_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    updates = {}

    if update_data.email:
        if update_data.email != current_user.email:
            existing = auth_data.get_user_by_email(db, update_data.email)
            if existing:
                raise HTTPException(status_code=409, detail="이미 사용 중인 이메일입니다.")
            updates['email'] = update_data.email

    if update_data.phone_number:
        updates['phone_number'] = update_data.phone_number
        
    if update_data.password:
        updates['hashed_password'] = get_password_hash(update_data.password)

    if not updates:
        return {"message": "변경할 내용을 입력해주세요."}

    try:
        auth_data.update_user(db, current_user.id, updates)
    except Exception as e:
        db.rollback()
        print(f"업데이트 에러: {e}")
        raise HTTPException(status_code=500, detail="정보 수정 실패")

    return {"message": "회원 정보가 수정되었습니다."}