import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from routers import auth, memos, orders, chatbot
from database import Base, engine
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session 
from dependencies import get_db  
from data import products as product_data
from pydantic import BaseModel
from data import auth as auth_data
from routers import auth, memos, orders
from data import orders as order_data
from typing import Optional
from fastapi.staticfiles import StaticFiles

# .env 파일 로드
load_dotenv()

class ReviewRequest(BaseModel):
    content: str
app = FastAPI()

# 환경 변수에서 SECRET_KEY 가져오기
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    SECRET_KEY = "default-secret-key" # 혹은 raise ValueError("SECRET_KEY missing")

# 이제 "/static" 경로로 들어오는 요청은 "static" 폴더에서 파일을 찾습니다.
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(auth.router)
app.include_router(memos.router)
app.include_router(orders.router)
app.include_router(chatbot.router)

@app.get("/") 
async def main_page(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    
    featured_products = product_data.get_featured_products(db)

    # 템플릿 렌더링 (username이 None이면 로그인 안 된 상태로 처리됨)
    return templates.TemplateResponse("main.html", {
        "request": request, 
        "username": username,
        "featured_products": featured_products
    })


@app.get("/about")
async def about():
    return {"message": "이것은 마이 메모 앱의 소개 페이지입니다."}

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/products")
async def product_list(request: Request, category: str, sub: str, db: Session = Depends(get_db)):
    username = request.session.get("username")

    # 1. 화면에 보여줄 소분류 이름 한글 변환 맵
    sub_names = {
        "clothes": "옷",
        "food": "사료",
        "snack": "간식",
        "leash": "끈 (리드줄)",
        "cushion": "방석",
        "house": "집 (하우스)",
        "harness": "하네스",
        "bird_clothes": "새 옷",
        "bird_house": "집 (새장)",

        # 기타 동물 (동물 이름)
        "hamster": "햄스터 전용관",
        "guinea_pig": "기니피그 전용관",
        "rabbit": "토끼 전용관",
        "ferret": "페럿 전용관",
        "fish": "물고기 수족관",
        "reptile": "파충류/양서류"
    }
    
    products = product_data.get_products_by_category(db, category, sub)

    return templates.TemplateResponse("products.html", {
        "request": request,
        "username": username,
        "category": category,      # 예: dog
        "sub": sub,                # 예: food
        "sub_name": sub_names.get(sub, sub), # 예: 맛있는 사료 (없으면 영어 그대로)
        "products": products # 상품 리스트
    })

#상세 제품 페이지
@app.get("/products/{product_id}")
async def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    # 0. 로그인 여부
    username = request.session.get("username")

    # 1. 상품 정보 조회
    product = product_data.get_product_by_id(db, product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    # 2. ★ 리뷰 목록 조회 ★
    reviews = product_data.get_reviews_by_product_id(db, product_id)

    # 3. 템플릿에 product와 reviews 둘 다 전달
    return templates.TemplateResponse("product_detail.html", {
        "request": request,
        "username": username,
        "product": product,
        "reviews": reviews  # 리뷰 데이터 전달
    })

@app.post("/products/{product_id}/review")
async def create_review(request: Request, product_id: int, review: ReviewRequest, db: Session = Depends(get_db)):
    # 1. 현재 세션(쿠키)에서 로그인한 사용자 이름 가져오기
    username = request.session.get("username")
    
    if not username:
        return {"message": "로그인이 필요한 서비스입니다."}

    # 2. 사용자 이름으로 DB에서 진짜 사용자 정보(ID 포함) 조회
    # (data/auth.py에 있는 함수 활용)
    user = auth_data.get_user_by_username(db, username)
    
    if not user:
        return {"message": "사용자 정보를 찾을 수 없습니다."}

    # 3. 찾은 user.id를 사용하여 리뷰 저장
    # HTML에서 id를 안 보내도, 서버가 알아서 찾아서 저장합니다.
    product_data.create_review(db, product_id, user.id, review.content)
    
    # (확인용 출력)
    print(f"===== 새 리뷰 저장 완료 =====")
    print(f"상품: {product_id}, 작성자: {user.username}(ID:{user.id})")

    return {"message": "소중한 후기가 등록되었습니다!"}

@app.get("/mypage")
async def mypage(request: Request, db: Session = Depends(get_db)):
    # 1. 로그인 여부 확인
    username = request.session.get("username")
    if not username:
        # 로그인 안 되어 있으면 로그인 페이지로 튕겨내기
        return RedirectResponse(url="/login", status_code=302)
    
    # 2. 사용자 정보 가져오기
    user = auth_data.get_user_by_username(db, username)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # 3. 구매 내역 가져오기 (data/orders.py 활용)
    my_orders = order_data.get_orders_by_user(db, user.id)

    # 4. 마이페이지 렌더링
    return templates.TemplateResponse("mypage.html", {
        "request": request,
        "username": username,
        "user": user,
        "orders": my_orders
    })

# ★ [수정] 상품 목록 및 검색 라우터
@app.get("/products")
async def product_list(
    request: Request, 
    category: Optional[str] = None, 
    sub: Optional[str] = None, 
    keyword: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    username = request.session.get("username")

    # 소분류 이름 맵 (기존 유지)
    sub_names = {
        "clothes": "옷", "food": "사료", "snack": "간식", "leash": "끈 (리드줄)",
        "cushion": "방석", "house": "집 (하우스)", "harness": "하네스",
        "bird_clothes": "새 옷", "bird_house": "집 (새장)",
        "hamster": "햄스터 전용관", "guinea_pig": "기니피그 전용관",
        "rabbit": "토끼 전용관", "ferret": "페럿 전용관",
        "fish": "물고기 수족관", "reptile": "파충류/양서류"
    }
    
    # 1. 검색어가 있는 경우 (검색 로직)
    if keyword:
        products = product_data.search_products(db, keyword)
        sub_name = f"'{keyword}' 검색 결과"
    
    # 2. 카테고리가 있는 경우 (기존 분류 로직)
    elif category and sub:
        products = product_data.get_products_by_category(db, category, sub)
        sub_name = sub_names.get(sub, sub)
        
    # 3. 아무것도 없는 경우 (잘못된 접근)
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
        "keyword": keyword # 템플릿에서 검색어 유지를 위해 전달
    })

#팀 소개 페이지(프로젝트 소개, 활용기술, 팀원, 코드 구성, )
@app.get("/teamIntroduce")
async def teamIntroduce():
    print("팀 소개 페이지입니다.")

#제휴브랜드 소개 페이지
@app.get("/brands")
async def brands():
    print("제휴 브랜드 페이지입니다.")

#고객센터 페이지
@app.get("/serviceCenter")
async def brands():
    print("고객센터 페이지입니다.")

#운영자 관리 페이지
@app.get("/operator")
async def brands():
    print("운영자 관리 페이지입니다.")