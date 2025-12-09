from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

# 1. 주문 생성 (구매 내역 저장)
def create_order(db: Session, user_id: int, product_id: int, product_name: str, category: str, sub_category: str, price: int, quantity: int):
    total_price = price * quantity
    sql = """
        INSERT INTO orders (user_id, product_id, product_name_snap, category_snap, sub_category_snap, price_snap, quantity, total_price)
        VALUES (:user_id, :product_id, :name, :cat, :sub, :price, :qty, :total)
    """
    db.execute(text(sql), {
        "user_id": user_id, "product_id": product_id,
        "name": product_name, "cat": category, "sub": sub_category,
        "price": price, "qty": quantity, "total": total_price
    })
    db.commit()

# 2. 내 주문 내역 조회 (검색 포함) - ★ 한국 시간 적용 수정됨 ★
def get_orders_by_user(db: Session, user_id: int, keyword: Optional[str] = None):
    # SELECT * 대신 컬럼을 명시하고, created_at에 9시간을 더합니다.
    sql = """
        SELECT 
            id, user_id, product_id, product_name_snap, category_snap, sub_category_snap, price_snap, quantity, total_price, 
            DATE_ADD(created_at, INTERVAL 9 HOUR) as created_at
        FROM orders 
        WHERE user_id = :user_id
    """
    params = {"user_id": user_id}

    if keyword:
        sql += " AND product_name_snap LIKE :keyword"
        params["keyword"] = f"%{keyword}%"
    
    sql += " ORDER BY created_at DESC"
    return db.execute(text(sql), params).fetchall()