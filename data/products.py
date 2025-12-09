from sqlalchemy.orm import Session
from sqlalchemy import text

# 1. 카테고리별 상품 목록 조회 (products.html 용)
def get_products_by_category(db: Session, category: str, sub_category: str):
    # 'etc' 카테고리는 sub_category(동물 이름)만 맞으면 모든 품목을 가져옴
    if category == 'etc':
        sql = "SELECT * FROM pet_item WHERE category = :category AND sub_category = :sub_category"
    else:
        # 강아지/고양이는 category와 sub_category(품목) 둘 다 일치해야 함
        sql = "SELECT * FROM pet_item WHERE category = :category AND sub_category = :sub_category"
    
    return db.execute(text(sql), {"category": category, "sub_category": sub_category}).fetchall()

# 2. 상품 상세 정보 조회 (product_detail.html 용)
def get_product_by_id(db: Session, product_id: int):
    sql = "SELECT * FROM pet_item WHERE id = :product_id"
    result = db.execute(text(sql), {"product_id": product_id}).fetchone()
    return result

# 3. 상품별 리뷰 목록 조회 (작성자 이름 포함)
def get_reviews_by_product_id(db: Session, product_id: int):
    # created_at에 9시간을 더해서(INTERVAL 9 HOUR) 가져오도록 수정
    sql = """
        SELECT r.id, r.user_id, r.content, r.product_id, 
               DATE_ADD(r.created_at, INTERVAL 9 HOUR) as created_at, 
               u.username 
        FROM reviews r 
        JOIN users u ON r.user_id = u.id 
        WHERE r.product_id = :product_id 
        ORDER BY r.created_at DESC
    """
    return db.execute(text(sql), {"product_id": product_id}).fetchall()

# 4. 리뷰 등록 (이 함수가 없어서 문제였습니다!)
def create_review(db: Session, product_id: int, user_id: int, content: str):
    db.execute(
        text("INSERT INTO reviews (product_id, user_id, content) VALUES (:product_id, :user_id, :content)"),
        {
            "product_id": product_id,
            "user_id": user_id,
            "content": content
        }
    )
    db.commit()
    
# 5. MD 추천 상품 (랜덤 4개 조회)
def get_featured_products(db: Session, limit: int = 4):
    # RAND()를 사용해 매번 새로고침 할 때마다 다른 상품이 나오게 합니다.
    sql = "SELECT * FROM pet_item ORDER BY RAND() LIMIT :limit"
    return db.execute(text(sql), {"limit": limit}).fetchall()

# 6. 구매 발생 시 재고 감소 및 판매량 증가
def update_stock_and_sales(db: Session, product_id: int, quantity: int):
    # 재고는 줄이고(stock - quantity), 판매량은 늘림(sales_count + quantity)
    db.execute(
        text("UPDATE pet_item SET stock = stock - :quantity, sales_count = sales_count + :quantity WHERE id = :product_id"),
        {"quantity": quantity, "product_id": product_id}
    )
    db.commit()

# 상품 검색 기능
def search_products(db: Session, keyword: str):
    # 상품명 또는 설명에 키워드가 포함된 경우 조회
    sql = """
        SELECT * FROM pet_item 
        WHERE name LIKE :keyword OR description LIKE :keyword
    """
    return db.execute(text(sql), {"keyword": f"%{keyword}%"}).fetchall()