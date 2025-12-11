from sqlalchemy.orm import Session
from sqlalchemy import text

# 1. 리뷰 목록 조회
def get_reviews_by_product_id(db: Session, product_id: int):
    sql = """
        SELECT r.id, r.user_id, r.content, r.created_at, u.username 
        FROM reviews r 
        JOIN users u ON r.user_id = u.id 
        WHERE r.product_id = :pid 
        ORDER BY r.created_at DESC
    """
    cursor = db.execute(text(sql), {"pid": product_id})
    return cursor.fetchall()

# 2. 리뷰 작성
def create_review(db: Session, product_id: int, user_id: int, content: str):
    sql = """
        INSERT INTO reviews (product_id, user_id, content) 
        VALUES (:pid, :uid, :content)
    """
    params = {"pid": product_id, "uid": user_id, "content": content}
    db.execute(text(sql), params)
    db.commit()

# 3. 리뷰 삭제
def delete_review(db: Session, review_id: int, user_id: int):
    sql = "DELETE FROM reviews WHERE id = :rid AND user_id = :uid"
    db.execute(text(sql), {"rid": review_id, "uid": user_id})
    db.commit()