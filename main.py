import os
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session 
from pydantic import BaseModel
from typing import Optional

# [설명] DB 엔진 및 세션 생성 함수 임포트
# [이동] project1/database.py, project1/dependencies.py
from database import Base, engine
from dependencies import get_db

# [설명] 기능별 라우터(컨트롤러) 모듈 임포트
# [이동] project1/routers/ 폴더 내 각 파일들
from routers import auth, memos, orders, chatbot, products
from routers import cart as cart_router

# [설명] 데이터베이스 처리(쿼리) 모듈 임포트
# [이동] project1/data/ 폴더 내 각 파일들
from data import products as product_data
from data import auth as auth_data
from data import orders as order_data
from data import reviews as review_data
from data import cart as cart_data  

# [설명] .env 파일에서 환경변수 로드 (DB 주소, 시크릿 키 등)
load_dotenv()

# [설명] FastAPI 앱 인스턴스 생성
app = FastAPI()

# [설명] 세션 미들웨어 설정 (로그인 정보 유지용)
# SECRET_KEY는 .env 파일에서 가져옴
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# [설명] 정적 파일(CSS, 이미지, JS) 경로 마운트
# [경로] http://주소/static/... -> project1/static/ 폴더 연결
app.mount("/static", StaticFiles(directory="static"), name="static")

# [설명] HTML 템플릿 엔진(Jinja2) 설정
# [경로] project1/templates/ 폴더 연결
templates = Jinja2Templates(directory="templates")

# [설명] DB 테이블 자동 생성 (서버 시작 시 모델에 정의된 테이블이 없으면 생성)
# [이동] project1/database.py의 Base, engine 사용
Base.metadata.create_all(bind=engine)

# [설명] 라우터 등록 (각 기능별 URL 연결)
# [이동] 각 routers/{파일이름}.py 파일의 router 객체를 메인 앱에 포함시킴
app.include_router(auth.router)         # 인증 (로그인/가입)
app.include_router(memos.router)        # 게시판
app.include_router(orders.router)       # 주문
app.include_router(chatbot.router)      # 챗봇
app.include_router(cart_router.router)  # 장바구니
app.include_router(products.router)

# --- 메인 페이지 ---
@app.get("/") 
async def main_page(request: Request, db: Session = Depends(get_db)):
    # [설명] 세션에서 로그인된 사용자 이름 가져오기
    username = request.session.get("username")

    # [설명] 추천 상품(또는 랜덤 상품) 목록 조회
    # [이동] project1/data/products.py -> get_featured_products() 호출
    featured_products = product_data.get_featured_products(db,request)
    
    # [설명] 로그인한 사용자의 유통기한 알림 데이터 조회
    expiry_alerts = {}
    if username:
        user = auth_data.get_user_by_username(db, username)
        if user:
            expiry_alerts = order_data.get_expiry_alerts(db, user.id)
    
    # [설명] HTML 렌더링 (main.html에 데이터(username, 제품특징)를 보냄)
    # [파일] project1/templates/main.html
    return templates.TemplateResponse("main.html", {
        "request": request, 
        "username": username,
        "featured_products": featured_products,
        "expiry_alerts": expiry_alerts
    })

# --- [라우트] 로그인 페이지 (화면만) ---
@app.get("/login")
async def login_page(request: Request):
    # [이동] project1/templates/home.html (로그인/가입 폼)
    return templates.TemplateResponse("home.html", {"request": request})

# --- 마이페이지 ---
@app.get("/mypage")
async def mypage(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")

    # [설명] 비로그인 상태면 로그인 페이지로 리다이렉트
    # [이동] main.py -> login 라우팅(로그인페이지로 이동하는 라우팅으로 이동)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    
    # [설명] 사용자 상세 정보 조회
    # [이동] project1/data/auth.py -> get_user_by_username()
    user = auth_data.get_user_by_username(db, username)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # [설명] 사용자의 주문 내역 조회 (상품 정보 JOIN 포함)
    # [이동] project1/data/orders.py -> get_my_orders()
    my_orders = order_data.get_my_orders(db, user.id)

    # [설명] HTML 렌더링 (mypage.html에 데이터(username, 사용자정보, 영수증)를 보냄)
    # [파일] project1/templates/product_detail.html
    return templates.TemplateResponse("mypage.html", {
        "request": request,
        "username": username,
        "user": user,
        "orders": my_orders
    })
