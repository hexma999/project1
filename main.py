import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session 
from pydantic import BaseModel
from typing import Optional

# DB 및 의존성
from database import Base, engine
from dependencies import get_db

# 라우터 및 데이터 모듈
from routers import auth, memos, orders, chatbot
from data import cart, products as product_data
from data import auth as auth_data
from data import orders as order_data
from data import reviews as review_data  # [추가] 리뷰 데이터 모듈

load_dotenv()

app = FastAPI()

# 세션 설정
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# DB 테이블 생성 (필요 시)
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(auth.router)
app.include_router(memos.router)
app.include_router(orders.router)
app.include_router(chatbot.router)
app.include_router(cart.router)

class ReviewRequest(BaseModel):
    content: str

# --- 메인 페이지 ---
@app.get("/") 
async def main_page(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    featured_products = product_data.get_featured_products(db)
    
    return templates.TemplateResponse("main.html", {
        "request": request, 
        "username": username,
        "featured_products": featured_products
    })

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# --- 상품 상세 ---
@app.get("/products/{product_id}")
async def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    username = request.session.get("username")

    product = product_data.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    # [수정] review_data 모듈 사용
    reviews = review_data.get_reviews_by_product_id(db, product_id)

    return templates.TemplateResponse("product_detail.html", {
        "request": request,
        "username": username,
        "product": product,
        "reviews": reviews
    })

# --- 리뷰 작성 ---
@app.post("/products/{product_id}/review")
async def create_review(request: Request, product_id: int, review: ReviewRequest, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        return {"message": "로그인이 필요한 서비스입니다."}

    user = auth_data.get_user_by_username(db, username)
    if not user:
        return {"message": "사용자 정보를 찾을 수 없습니다."}

    # [수정] review_data 모듈 사용
    review_data.create_review(db, product_id, user.id, review.content)
    
    return {"message": "소중한 후기가 등록되었습니다!"}

# --- 마이페이지 ---
@app.get("/mypage")
async def mypage(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    
    user = auth_data.get_user_by_username(db, username)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # [수정] 주문 내역 (JOIN된 상세 정보 포함)
    my_orders = order_data.get_my_orders(db, user.id)

    return templates.TemplateResponse("mypage.html", {
        "request": request,
        "username": username,
        "user": user,
        "orders": my_orders
    })

# --- 상품 목록 (검색/카테고리) ---
@app.get("/products")
async def product_list(
    request: Request, 
    category: Optional[str] = None, 
    sub: Optional[str] = None, 
    keyword: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    username = request.session.get("username")

    # 소분류 한국어 매핑 (표시용)
    sub_names = {
        "clothes": "옷", "food": "사료", "snack": "간식", "leash": "끈 (리드줄)",
        "cushion": "방석", "house": "집 (하우스)", "harness": "하네스",
        "bird_clothes": "윙슈트", "bird_house": "집 (새장)"
    }
    
    if keyword:
        products = product_data.search_products(db, keyword)
        sub_name = f"'{keyword}' 검색 결과"
    elif category and sub:
        # [수정] JOIN된 카테고리 정보로 조회
        products = product_data.get_products_by_category(db, category, sub)
        sub_name = sub_names.get(sub, sub)
    else:
        products = []
        sub_name = "전체 상품"

    return templates.TemplateResponse("products.html", {
        "request": request,
        "username": username,
        "category": category,
        "sub": sub,
        "sub_name": sub_name,
        "products": products,
        "keyword": keyword
    })