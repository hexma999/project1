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

# 2. 내 주문 내역 조회 (수정됨: 삭제된 상품 예외 처리 추가)
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
        
        # Row -> Dict 변환 및 안전한 데이터 처리
        items = []
        for row in items_rows:
            item_dict = dict(row._mapping)
            # 상품명이 없으면(삭제됨) '삭제된 상품'으로 대체
            if not item_dict.get('product_name_snap'):
                item_dict['product_name_snap'] = "삭제된 상품"
            items.append(item_dict)
        
        # 템플릿 호환성을 위한 가공 (마이페이지 목록용 요약)
        if items:
            first_name = items[0]['product_name_snap']
            if len(items) > 1:
                first_name += f" 외 {len(items)-1}건"
            
            order_dict['product_name_snap'] = first_name
            order_dict['quantity'] = sum(i['quantity'] for i in items)
        
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
    
    # 3. 딕셔너리로 변환 및 합치기 (삭제된 상품 처리 추가)
    order_dict = dict(order._mapping)
    safe_items = []
    for item in items:
        i_dict = dict(item._mapping)
        if not i_dict.get('product_name_snap'):
            i_dict['product_name_snap'] = "삭제된 상품"
        safe_items.append(i_dict)

    order_dict["order_items"] = safe_items
    
    return order_dict

# 4. 유통기한 알림 데이터 조회
def get_expiry_alerts(db: Session, user_id: int):
    """
    사용자가 구매한 상품 중 유통기한이 임박하거나 지난 상품을 카테고리별로 반환
    """
    from datetime import datetime, timedelta
    
    # 주문 아이템에서 상품 정보와 함께 조회 (최근 구매 기준)
    sql = """
        SELECT 
            oi.product_id,
            p.name AS product_name,
            p.expiration_days,
            c.main_type AS category,
            MAX(o.created_at) AS last_purchased_at
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN products p ON oi.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        WHERE o.user_id = :uid 
          AND p.expiration_days IS NOT NULL
          AND p.expiration_days > 0
        GROUP BY oi.product_id, p.name, p.expiration_days, c.main_type
        ORDER BY last_purchased_at DESC
    """
    
    rows = db.execute(text(sql), {"uid": user_id}).fetchall()
    
    # 카테고리별로 분류
    alerts = {"dog": [], "cat": [], "bird": []}
    now = datetime.now()
    
    for row in rows:
        category = row.category.lower() if row.category else "dog"
        if category not in alerts:
            continue
            
        # 유통기한 계산
        purchased_at = row.last_purchased_at
        expiry_date = purchased_at + timedelta(days=row.expiration_days)
        days_diff = (expiry_date - now).days
        
        # 15일 이내 또는 이미 지난 경우만 알림
        if days_diff <= 15:
            alerts[category].append({
                "product_id": row.product_id,
                "product_name": row.product_name,
                "expiration_days": row.expiration_days,
                "purchased_at": purchased_at,
                "display_days": abs(days_diff),
                "status": "over" if days_diff < 0 else "remaining"
            })
    
    # 각 카테고리별로 최대 5개까지만, 급한 순서대로 정렬
    for cat in alerts:
        alerts[cat] = sorted(alerts[cat], key=lambda x: (x["status"] == "remaining", x["display_days"]))[:5]
    
    return alerts