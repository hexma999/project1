from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

# 메모 생성
def create_memo(db: Session, user_id: int, title: str, content: str):
    db.execute(
        text("INSERT INTO memo (user_id, title, content) VALUES (:user_id, :title, :content)"),
        {"user_id": user_id, "title": title, "content": content}
    )
    db.commit()

# 메모 목록 조회 (검색 + 내 글만 보기 필터 포함)
def get_memos_with_filters(
    db: Session, 
    keyword: Optional[str] = None, 
    search_type: Optional[str] = "title", 
    show_mine: bool = False, 
    current_user_id: int = None
):
    # 기본 쿼리 (작성자 이름 포함)
    sql_query = """
        SELECT m.*, u.username 
        FROM memo m 
        JOIN users u ON m.user_id = u.id 
        WHERE 1=1
    """
    params = {}

    # 내 글만 보기
    if show_mine and current_user_id:
        sql_query += " AND m.user_id = :current_user_id"
        params["current_user_id"] = current_user_id

    # 검색어 필터
    if keyword:
        if search_type == "title":
            sql_query += " AND m.title LIKE :keyword"
        elif search_type == "username":
            sql_query += " AND u.username LIKE :keyword"
        elif search_type == "content":
            sql_query += " AND m.content LIKE :keyword"
        
        params["keyword"] = f"%{keyword}%"

    # 최신순 정렬
    sql_query += " ORDER BY m.id DESC"

    return db.execute(text(sql_query), params).fetchall()

# 메모 수정
def update_memo(db: Session, memo_id: int, user_id: int, title: str, content: str):
    result = db.execute(
        text("UPDATE memo SET title = :title, content = :content WHERE id = :memo_id AND user_id = :user_id"),
        {"title": title, "content": content, "memo_id": memo_id, "user_id": user_id}
    )
    db.commit()
    return result.rowcount # 수정된 행의 개수 반환

# 메모 삭제
def delete_memo(db: Session, memo_id: int, user_id: int):
    result = db.execute(
        text("DELETE FROM memo WHERE id = :memo_id AND user_id = :user_id"),
        {"memo_id": memo_id, "user_id": user_id}
    )
    db.commit()
    return result.rowcount # 삭제된 행의 개수 반환