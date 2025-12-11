from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from dependencies import get_db
from pydantic import BaseModel
# 데이터 모듈 임포트
from data import auth as auth_data
from data import products as product_data
from data import orders as order_data
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/orders", tags=["orders"])

class OrderRequest(BaseModel):
    quantity: int

@router.post("/buy/{product_id}")
async def buy_product(request: Request, product_id: int, order_req: OrderRequest, db: Session = Depends(get_db)):
    # 1. 로그인 체크
    username = request.session.get("username")
    if not username:
        return {"result": "fail", "message": "로그인이 필요한 서비스입니다."}
    
    user = auth_data.get_user_by_username(db, username)
    if not user:
        return {"result": "fail", "message": "사용자 정보를 찾을 수 없습니다."}
    
    # 2. 상품 정보 조회 (가격 및 재고 확인용)
    product = product_data.get_product_by_id(db, product_id)
    if not product:
        return {"result": "fail", "message": "상품을 찾을 수 없습니다."}
    
    # 3. 재고 확인
    if product.stock < order_req.quantity:
        return {"result": "fail", "message": f"재고가 부족합니다. (남은 수량: {product.stock}개)"}

    # 4. 구매 처리 (리스트 형태로 변환하여 전달)
    # data/orders.py의 create_order는 리스트를 받도록 설계됨
    try:
        order_items = [{
            "product_id": product.id,
            "quantity": order_req.quantity,
            "price": product.price  # DB에 있는 현재 가격 사용
        }]
        
        # 주문 생성 호출
        order_data.create_order(db, user.id, order_items)
        
        return {"result": "success", "message": "구매가 완료되었습니다!"}
        
    except Exception as e:
        print(f"구매 에러: {e}")
        return {"result": "fail", "message": "서버 오류로 구매에 실패했습니다."}

@router.get("/detail/{order_id}")
async def order_detail(request: Request, order_id: int, db: Session = Depends(get_db)):
    # 1. 로그인 체크
    username = request.session.get("username")
    if not username:
        # 비로그인 시 로그인 페이지로 이동하거나 에러 처리
        return RedirectResponse(url="/login", status_code=302)
    
    # 2. 주문 정보 가져오기
    order = order_data.get_order_detail(db, order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="주문 정보를 찾을 수 없습니다.")
        
    # 3. 본인 주문인지 확인 (보안)
    user = auth_data.get_user_by_username(db, username)
    if order['user_id'] != user.id:
         raise HTTPException(status_code=403, detail="권한이 없습니다.")

    # 4. 영수증 페이지 렌더링 (receipt.html)
    return templates.TemplateResponse("receipt.html", {
        "request": request,
        "username": username,
        "order": order
    })