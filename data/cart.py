from sqlalchemy.orm import Session
from sqlalchemy import text

# 1. 장바구니에 상품 담기
def add_to_cart(db: Session, user_id: int, product_id: int, quantity: int):
    # 1-1. 유저의 장바구니가 없으면 생성
    cart = db.execute(text("SELECT id FROM carts WHERE user_id = :uid"), {"uid": user_id}).fetchone()
    
    if not cart:
        db.execute(text("INSERT INTO carts (user_id) VALUES (:uid)"), {"uid": user_id})
        db.commit()
        cart = db.execute(text("SELECT id FROM carts WHERE user_id = :uid"), {"uid": user_id}).fetchone()
    
    cart_id = cart.id

    # 1-2. 이미 담긴 상품인지 확인
    item = db.execute(
        text("SELECT id, quantity FROM cart_items WHERE cart_id = :cid AND product_id = :pid"),
        {"cid": cart_id, "pid": product_id}
    ).fetchone()

    if item:
        # 이미 있으면 수량 추가
        new_qty = item.quantity + quantity
        db.execute(
            text("UPDATE cart_items SET quantity = :qty WHERE id = :iid"),
            {"qty": new_qty, "iid": item.id}
        )
    else:
        # 없으면 새로 추가
        db.execute(
            text("INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (:cid, :pid, :qty)"),
            {"cid": cart_id, "pid": product_id, "qty": quantity}
        )
    db.commit()

# 2. 장바구니 목록 조회
def get_cart_items(db: Session, user_id: int):
    sql = """
        SELECT ci.id, ci.product_id, ci.quantity, 
               p.name, p.price, p.image_url, 
               (p.price * ci.quantity) as sub_total
        FROM cart_items ci
        JOIN carts c ON ci.cart_id = c.id
        JOIN products p ON ci.product_id = p.id
        WHERE c.user_id = :uid
    """
    return db.execute(text(sql), {"uid": user_id}).fetchall()

# 3. 장바구니 아이템 개수 조회 (배지용)
def get_cart_count(db: Session, user_id: int):
    sql = """
        SELECT SUM(quantity) as total_qty 
        FROM cart_items ci
        JOIN carts c ON ci.cart_id = c.id
        WHERE c.user_id = :uid
    """
    result = db.execute(text(sql), {"uid": user_id}).fetchone()
    return result.total_qty if result and result.total_qty else 0

# 4. 장바구니 비우기 (결제 후)
def clear_cart(db: Session, user_id: int):
    # 장바구니 ID 조회 후 아이템 삭제
    cart = db.execute(text("SELECT id FROM carts WHERE user_id = :uid"), {"uid": user_id}).fetchone()
    if cart:
        db.execute(text("DELETE FROM cart_items WHERE cart_id = :cid"), {"cid": cart.id})
        db.commit()

# 5. 특정 아이템 삭제
def remove_cart_item(db: Session, item_id: int):
    db.execute(text("DELETE FROM cart_items WHERE id = :iid"), {"iid": item_id})
    db.commit()