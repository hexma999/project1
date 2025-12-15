from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

# [헬퍼] 카테고리 ID 조회
def get_category_id(db: Session, main_type: str, sub_name: str):
    sql = """
        SELECT id FROM categories 
        WHERE main_type = :main AND sub_name = :sub
    """
    params = {"main": main_type, "sub": sub_name}
    cursor = db.execute(text(sql), params)
    result = cursor.fetchone()
    return result.id if result else None

# 1. 상품 등록
def create_product(db: Session, name: str, price: int, brand: str, 
                   detail: str, detail_img_url: str, image_url: str, 
                   main_cat: str, sub_cat: str, initial_stock: int):
    
    cat_id = get_category_id(db, main_cat, sub_cat)
    if not cat_id:
        raise ValueError(f"존재하지 않는 카테고리: {main_cat} > {sub_cat}")

    sql = """
        INSERT INTO products 
        (category_id, name, price, brand, detail, detail_img_url, image_url, initial_stock, stock, sales_count)
        VALUES 
        (:cat_id, :name, :price, :brand, :detail, :d_img, :img, :init_stock, :init_stock, 0)
    """
    params = {
        "cat_id": cat_id, "name": name, "price": price, 
        "brand": brand, "detail": detail, "d_img": detail_img_url, 
        "img": image_url, "init_stock": initial_stock
    }
    db.execute(text(sql), params)
    db.commit()

# 2. 카테고리별 상품 목록 조회 (JOIN 및 Alias 사용)
def get_products_by_category(db: Session, category: str, sub_category: str):
    # category='etc'인 경우 처리 로직 유지
    if category == 'etc':
        sql = """
            SELECT p.*, c.main_type AS category, c.sub_name AS sub_category 
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE c.main_type = :main
        """
        params = {"main": category}
    else:
        sql = """
            SELECT p.*, c.main_type AS category, c.sub_name AS sub_category 
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE c.main_type = :main AND c.sub_name = :sub
        """
        params = {"main": category, "sub": sub_category}

    cursor = db.execute(text(sql), params)
    return cursor.fetchall()

# 3. 상품 상세 조회
def get_product_by_id(db: Session, product_id: int):
    sql = """
        SELECT p.*, c.main_type AS category, c.sub_name AS sub_category
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.id = :pid
    """
    params = {"pid": product_id}
    cursor = db.execute(text(sql), params)
    return cursor.fetchone()

# 4. MD 추천 상품 (랜덤)
def get_featured_products(db: Session, request, limit: int = 12):

    username = "" #request.session.get("username", "")
    
    params = {}
    if username == "":
        # 로그인 하지 않은 경우
        sql = """
            SELECT p.*, c.main_type AS category, c.sub_name AS sub_category
            FROM products p
            JOIN categories c ON p.category_id = c.id
            ORDER BY RAND() LIMIT :limit
        """
        params = {"limit": limit}

    else:
        # 로그인 한 경우 
        gender = request.session["gender"]
        age_group = request.session["age_group"]

        sql = """
        SELECT p.*, c.main_type AS category, c.sub_name, a.gender, a.age_group AS sub_category
            FROM recommendation_products a
            JOIN products p
            ON a.product_id = p.id   
            JOIN categories c ON p.category_id = c.id
            WHERE a.gender = :gender
            AND a.age_group = :age_group
            ORDER BY RAND() LIMIT :limit
        """
        params = {"gender": gender, "age_group": age_group, "limit": limit}

    print(params)
    cursor = db.execute(text(sql), params)
    return cursor.fetchall()

# 5. 재고 감소 (products 테이블 사용)
def update_stock_and_sales(db: Session, product_id: int, quantity: int):
    sql = """
        UPDATE products 
        SET stock = stock - :qty, sales_count = sales_count + :qty 
        WHERE id = :pid
    """
    db.execute(text(sql), {"qty": quantity, "pid": product_id})
    db.commit()

# 6. 상품 검색
def search_products(db: Session, keyword: str):
    sql = """
        SELECT p.*, c.main_type AS category, c.sub_name AS sub_category
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.name LIKE :kw 
           OR p.brand LIKE :kw 
           OR c.sub_name LIKE :kw
    """
    cursor = db.execute(text(sql), {"kw": f"%{keyword}%"})
    return cursor.fetchall()