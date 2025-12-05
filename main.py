import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException # Depends, HTTPException 추가 필요
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from routers import auth, memos
from database import Base, engine
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session 
from dependencies import get_db  
from data import products as product_data
from pydantic import BaseModel
from data import auth as auth_data

# .env 파일 로드
load_dotenv()

class ReviewRequest(BaseModel):
    content: str
app = FastAPI()

# 환경 변수에서 SECRET_KEY 가져오기
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    SECRET_KEY = "default-secret-key" # 혹은 raise ValueError("SECRET_KEY missing")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(auth.router)
app.include_router(memos.router)

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/main")
async def main_page(request: Request, db: Session = Depends(get_db)): # db 추가됨
    # 1. 로그인 여부 확인
    username = request.session.get("username")
    
    if not username:
        return RedirectResponse(url="/")

    # 2. ★ MD 추천 상품 데이터 가져오기 (추가된 부분) ★
    featured_products = product_data.get_featured_products(db)

    # 3. 템플릿에 데이터 전달
    return templates.TemplateResponse("main.html", {
        "request": request, 
        "username": username,
        "featured_products": featured_products # HTML로 리스트를 보냅니다
    })

@app.get("/about")
async def about():
    return {"message": "이것은 마이 메모 앱의 소개 페이지입니다."}

@app.get("/products")
async def product_list(request: Request, category: str, sub: str, db: Session = Depends(get_db)):
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
        "category": category,      # 예: dog
        "sub": sub,                # 예: food
        "sub_name": sub_names.get(sub, sub), # 예: 맛있는 사료 (없으면 영어 그대로)
        "products": products # 상품 리스트
    })

#상세 제품 페이지
@app.get("/products/{product_id}")
async def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    # 1. 상품 정보 조회
    product = product_data.get_product_by_id(db, product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    # 2. ★ 리뷰 목록 조회 (추가된 부분) ★
    reviews = product_data.get_reviews_by_product_id(db, product_id)

    # 3. 템플릿에 product와 reviews 둘 다 전달
    return templates.TemplateResponse("product_detail.html", {
        "request": request,
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