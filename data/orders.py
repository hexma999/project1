from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict

# 1. 주문 생성 (트랜잭션)
def create_order(db: Session, user_id: int, items: List[Dict]):
    """
    items 구조: [{"product_id": 1, "price": 10000, "quantity": 2}, ...]
    """
    try:
        # A. 총 결제 금액 계산
        total_price = sum(item['price'] * item['quantity'] for item in items)
        
        # B. 주문서(Orders) 생성
        order_sql = "INSERT INTO orders (user_id, total_price) VALUES (:uid, :total)"
        result = db.execute(text(order_sql), {"uid": user_id, "total": total_price})
        order_id = result.lastrowid
        
        # C. 상세 내역 저장 및 재고 감소
        item_sql = """
            INSERT INTO order_items (order_id, product_id, quantity, price_snap)
            VALUES (:oid, :pid, :qty, :price)
        """
        stock_sql = """
            UPDATE products 
            SET stock = stock - :qty, sales_count = sales_count + :qty 
            WHERE id = :pid
        """
        
        for item in items:
            item_params = {
                "oid": order_id, 
                "pid": item['product_id'], 
                "qty": item['quantity'], 
                "price": item['price']
            }
            db.execute(text(item_sql), item_params)
            
            # 재고 감소
            db.execute(text(stock_sql), {"qty": item['quantity'], "pid": item['product_id']})
            
        db.commit()
        return order_id

    except Exception as e:
        db.rollback()
        raise e

# 2. 내 주문 내역 조회 (수정됨)
def get_my_orders(db: Session, user_id: int):
    # A. 주문서 목록 조회
    sql_orders = """
        SELECT id, user_id, total_price, 
               DATE_ADD(created_at, INTERVAL 9 HOUR) as created_at 
        FROM orders 
        WHERE user_id = :uid 
        ORDER BY created_at DESC
    """
    cursor = db.execute(text(sql_orders), {"uid": user_id})
    orders = cursor.fetchall()
    
    result = []
    
    # B. 상세 물품 조회
    sql_items = """
        SELECT oi.*, p.name AS product_name_snap, p.image_url, 
               c.main_type AS category_snap, c.sub_name AS sub_category_snap
        FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE oi.order_id = :oid
    """
    
    for order in orders:
        order_dict = dict(order._mapping)
        
        items_cursor = db.execute(text(sql_items), {"oid": order.id})
        items_rows = items_cursor.fetchall()
        items = [dict(row._mapping) for row in items_rows]
        
        # 템플릿 호환성을 위한 가공
        if items:
            order_dict['product_name_snap'] = items[0]['product_name_snap']
            if len(items) > 1:
                order_dict['product_name_snap'] += f" 외 {len(items)-1}건"
            order_dict['quantity'] = sum(i['quantity'] for i in items)
        
        # ★ 핵심 수정: 키 이름을 'items' -> 'order_items'로 변경 ★
        order_dict["order_items"] = items
        result.append(order_dict)
        
    return result

# 3. 특정 주문 상세 조회 (영수증용)
def get_order_detail(db: Session, order_id: int):
    # 1. 주문서(Orders) 조회 - 한국 시간(KST) 변환 적용
    order = db.execute(
        text("""
            SELECT id, user_id, total_price, 
                   DATE_ADD(created_at, INTERVAL 9 HOUR) as created_at 
            FROM orders 
            WHERE id = :oid
        """),
        {"oid": order_id}
    ).fetchone()
    
    if not order:
        return None
        
    # 2. 상세 품목(Order_Items) 조회
    items = db.execute(
        text("""
            SELECT oi.*, p.name AS product_name_snap, p.image_url, 
                   c.main_type AS category_snap, c.sub_name AS sub_category_snap
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE oi.order_id = :oid
        """),
        {"oid": order_id}
    ).fetchall()
    
    # 3. 딕셔너리로 변환 및 합치기
    order_dict = dict(order._mapping)
    order_dict["order_items"] = [dict(item._mapping) for item in items]
    
    return order_dict