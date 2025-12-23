from fastapi import APIRouter, Depends, Request, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from typing import Optional
from dependencies import get_db
from schemas import ReviewRequest
import shutil
import uuid
import os

# 데이터 모듈 임포트
from data import products as product_data
from data import auth as auth_data
from data import reviews as review_data

router = APIRouter(prefix="/products", tags=["products"])
templates = Jinja2Templates(directory="templates")

# --- 추가: 상품 등록 ---
@router.post("/")
async def create_product_with_image(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    brand: str = Form(...),
    detail: str = Form(...),
    price: int = Form(...),
    main_cat: str = Form(...),
    sub_cat: str = Form(...),
    initial_stock: int = Form(...),
    image: UploadFile = File(...),
    detail_image: UploadFile = File(...)
):
    # 1. 로그인 확인
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="상품을 등록하려면 로그인이 필요합니다.")

    # --- 이미지 파일 처리 함수 ---
    def save_upload_file(upload_file: UploadFile) -> str:
        # 허용할 이미지 확장자
        allowed_extensions = {"png", "jpg", "jpeg"}
        extension = upload_file.filename.split('.')[-1].lower()
        if extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"{upload_file.filename} 파일은 png, jpg, jpeg 형식만 가능합니다.")

        # 고유한 파일명 생성
        unique_filename = f"{uuid.uuid4()}.{extension}"
        file_path = os.path.join("static", "img", unique_filename)
        
        # 파일 저장
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
        finally:
            upload_file.file.close()
        
        return f"/static/img/{unique_filename}"

    # 2. 대표 이미지 및 상세 이미지 저장
    image_url = save_upload_file(image)
    detail_img_url = save_upload_file(detail_image)
    
    # 3. 데이터베이스에 상품 정보 저장
    try:
        product_data.create_product(
            db=db,
            name=name,
            price=price,
            brand=brand,
            detail=detail,
            detail_img_url=detail_img_url,
            image_url=image_url,
            category_id=int(sub_cat),
            initial_stock=initial_stock
        )
    except Exception as e:
        # DB 저장 실패 시 업로드된 파일들 삭제
        if os.path.exists(image_url.lstrip('/')):
            os.remove(image_url.lstrip('/'))
        if os.path.exists(detail_img_url.lstrip('/')):
            os.remove(detail_img_url.lstrip('/'))
        raise HTTPException(status_code=500, detail=f"상품 등록 중 오류 발생: {e}")

    return {"message": "상품이 성공적으로 등록되었습니다.", "image_url": image_url, "detail_img_url": detail_img_url}


# 1. 상품 목록 (검색/카테고리)
# URL: /products
@router.get("/")
async def product_list(
    request: Request, 
    category: Optional[str] = None, 
    sub: Optional[str] = None, 
    keyword: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    username = request.session.get("username")

    # [설명] 화면 표시용 소분류 한글 매핑
    sub_names = {
        "clothes": "옷", "food": "사료", "snack": "간식", "toy": "장난감",
        "house": "집", "bird_food": "새 먹이", "bird_house": "새장", "bird_item" : "용품", "bird_alpha" : "영양/치료제",
        "etc": "기타"
    }
    
    # [설명] 검색어가 있으면 검색, 없으면 카테고리 조회
    if keyword:
        products = product_data.search_products(db, keyword)
        sub_name = f"'{keyword}' 검색 결과"
    
    # [설명] 주-카테고리가 있으면 검색
    elif category and sub:
        # [수정] JOIN된 카테고리 정보로 조회
        products = product_data.get_products_by_category(db, category, sub)
        sub_name = sub_names.get(sub, sub)
    else:
        products = []
        sub_name = "상품"


    # [설명] HTML 렌더링 (products.html에 데이터(username, 주-카테고리, 서브-카테고리,영수증)를 보냄)
    # [파일] project1/templates/product_detail.html
    return templates.TemplateResponse("products.html", {
        "request": request,
        "username": username,
        "category": category,
        "sub": sub,
        "sub_name": sub_name,
        "products": products,
        "keyword": keyword
    })

# 2. 상품 상세
# URL: /products/{product_id}
@router.get("/{product_id}")
async def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    username = request.session.get("username")

    # [설명] 상품 ID로 상세 정보 조회
    # [이동] project1/data/products.py -> get_product_by_id()
    product = product_data.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    
    # text = product['detail'].join()
    # print(text)
    # [설명] 해당 상품의 리뷰 목록 조회만
    # [이동] project1/data/reviews.py -> get_reviews_by_product_id()
    reviews = review_data.get_reviews_by_product_id(db, product_id)

    # [설명] HTML 렌더링 (product_detail.html에 데이터(username, 제품정보, 리뷰정보)를 보냄)
    # [파일] project1/templates/product_detail.html
    return templates.TemplateResponse("product_detail.html", {
        "request": request,
        "username": username,
        "product": product,
        "reviews": reviews
    })


# 3. 리뷰 작성
# URL: /products/{product_id}/review
@router.post("/{product_id}/review")
async def create_review(request: Request, product_id: int, review: ReviewRequest, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        return {"message": "로그인이 필요한 서비스입니다."}

    user = auth_data.get_user_by_username(db, username)
    if not user:
        return {"message": "사용자 정보를 찾을 수 없습니다."}

    # [설명] 해당 상품의 리뷰 작성
    # [이동] project1/data/reviews.py -> create_review()
    review_data.create_review(db, product_id, user.id, review.content)
    
    return {"message": "소중한 후기가 등록되었습니다!"}