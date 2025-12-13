from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

# 1. 메모 생성
def create_memo(db: Session, user_id: int, title: str, content: str):
    sql = """
        INSERT INTO memo (user_id, title, content) 
        VALUES (:user_id, :title, :content)
    """
    params = {
        "user_id": user_id, 
        "title": title, 
        "content": content
    }
    
    db.execute(text(sql), params)
    db.commit()

# 2. 메모 목록 조회 (검색 + 필터 로직 유지)
def get_memos_with_filters(
    db: Session, 
    keyword: Optional[str] = None, 
    search_type: Optional[str] = "title", 
    show_mine: bool = False, 
    current_user_id: int = None
):
    # A. 기본 쿼리 구성 (작성자 이름 포함)
    sql = """
        SELECT m.*, u.username 
        FROM memo m 
        JOIN users u ON m.user_id = u.id 
        WHERE 1=1
    """
    params = {}

    # B. 동적 조건 추가
    # 내 글만 보기
    if show_mine and current_user_id:
        sql += " AND m.user_id = :current_user_id"
        params["current_user_id"] = current_user_id

    # 검색어 필터
    if keyword:
        if search_type == "title":
            sql += " AND m.title LIKE :keyword"
        elif search_type == "username":
            sql += " AND u.username LIKE :keyword"
        elif search_type == "content":
            sql += " AND m.content LIKE :keyword"
        
        params["keyword"] = f"%{keyword}%"

    # C. 정렬 및 실행
    sql += " ORDER BY m.id DESC"

    cursor = db.execute(text(sql), params)
    return cursor.fetchall()

# 3. 메모 수정
def update_memo(db: Session, memo_id: int, user_id: int, title: str, content: str):
    sql = """
        UPDATE memo 
        SET title = :title, content = :content 
        WHERE id = :memo_id AND user_id = :user_id
    """
    params = {
        "title": title, 
        "content": content, 
        "memo_id": memo_id, 
        "user_id": user_id
    }
    
    cursor = db.execute(text(sql), params)
    db.commit()
    
    return cursor.rowcount # 수정된 행의 개수 반환

# 4. 메모 삭제
def delete_memo(db: Session, memo_id: int, user_id: int):
    sql = """
        DELETE FROM memo 
        WHERE id = :memo_id AND user_id = :user_id
    """
    params = {
        "memo_id": memo_id, 
        "user_id": user_id
    }
    
    cursor = db.execute(text(sql), params)
    db.commit()
    
    return cursor.rowcount # 삭제된 행의 개수 반환