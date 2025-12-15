from sqlalchemy.orm import Session
from sqlalchemy import text

# 사용자 조회 (로그인, 중복 확인용)
def get_user_by_username(db: Session, username: str):
    return db.execute(
        text("SELECT A.* , (TIMESTAMPDIFF(YEAR, birthdate, CURDATE()) DIV 10) * 10 AS age_group FROM users A WHERE username = :username"),
        {"username": username}
    ).fetchone()

# 사용자 생성 (회원가입)
def create_user(db: Session, username: str, email: str, hashed_password: str, birthdate: str, phone_number: str, gender: str):
    db.execute(
        text("""
            INSERT INTO users (username, email, hashed_password, birthdate, phone_number, gender) 
            VALUES (:username, :email, :hashed_password, :birthdate, :phone_number, :gender)
        """),
        {
            "username": username, 
            "email": email, 
            "hashed_password": hashed_password,
            "birthdate": birthdate,
            "phone_number": phone_number,
            "gender": gender
        }
    )
    db.commit()

# 회원 정보 수정
def update_user(db: Session, user_id: int, update_data: dict):
    if not update_data:
        return # 업데이트할 내용이 없으면 종료

    # 1. 쿼리의 SET 부분 동적 생성 (예: "email = :email, phone_number = :phone_number")
    set_clauses = []
    params = {"user_id": user_id}

    for key, value in update_data.items():
        set_clauses.append(f"{key} = :{key}")
        params[key] = value

    # 2. 최종 SQL 조립
    sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = :user_id"
    
    # 3. 실행
    db.execute(text(sql), params)
    db.commit()

# 이메일 중복 확인용 조회 함수
def get_user_by_email(db: Session, email: str):
    return db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": email}
    ).fetchone()