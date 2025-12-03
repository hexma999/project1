from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from schemas import UserCreate, UserLogin
from dependencies import get_db, get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
async def signup(signup_data: UserCreate, db: Session = Depends(get_db)):
    # username 중복 확인 (raw SQL)
    existing_user = db.execute(
        text("SELECT * FROM users WHERE username = :username"),
        {"username": signup_data.username}
    ).fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 동일 사용자 이름이 가입되어 있습니다.")

    hashed_password = get_password_hash(signup_data.password)

    # 회원 삽입 (raw SQL)
    try:
        db.execute(
            text("INSERT INTO users (username, email, hashed_password) VALUES (:username, :email, :hashed_password)"),
            {"username": signup_data.username, "email": signup_data.email, "hashed_password": hashed_password}
        )
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="회원가입 실패")

    return {"message": "회원가입 성공"}

@router.post("/login")
async def login(request: Request, signin_data: UserLogin, db: Session = Depends(get_db)):
    # 사용자 조회 (raw SQL)
    user = db.execute(
        text("SELECT * FROM users WHERE username = :username"),
        {"username": signin_data.username}
    ).fetchone()

    if user and verify_password(signin_data.password, user.hashed_password):
        request.session["username"] = user.username
        return {"message": "로그인 성공"}
    raise HTTPException(status_code=401, detail="로그인 실패")

@router.post("/logout")
async def logout(request: Request):
    request.session.pop("username", None)
    return {"message": "로그아웃 성공"}