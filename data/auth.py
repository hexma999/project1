from sqlalchemy.orm import Session
from sqlalchemy import text

# 사용자 조회 (로그인, 중복 확인용)
def get_user_by_username(db: Session, username: str):
    return db.execute(
        text("SELECT * FROM users WHERE username = :username"),
        {"username": username}
    ).fetchone()

# 사용자 생성 (회원가입)
def create_user(db: Session, username: str, email: str, hashed_password: str):
    db.execute(
        text("INSERT INTO users (username, email, hashed_password) VALUES (:username, :email, :hashed_password)"),
        {"username": username, "email": email, "hashed_password": hashed_password}
    )
    db.commit()