# [routers/orders.py] 새로 생성
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from dependencies import get_db
from pydantic import BaseModel
# 데이터 파일들 가져오기
from data import auth as auth_data
from data import products as product_data
from data import orders as order_data

router = APIRouter(prefix="/orders", tags=["orders"])

# 주문 요청 데이터 검증용
class OrderRequest(BaseModel):
    quantity: int

@router.post("/buy/{product_id}")
async def buy_product(request: Request, product_id: int, order_req: OrderRequest, db: Session = Depends(get_db)):
    # 1. 로그인 체크
    username = request.session.get("username")
    if not username:
        return {"result": "fail", "message": "로그인이 필요한 서비스입니다."}
    
    user = auth_data.get_user_by_username(db, username)
    
    # 2. 상품 정보 & 재고 확인
    product = product_data.get_product_by_id(db, product_id)
    if not product:
        return {"result": "fail", "message": "상품을 찾을 수 없습니다."}
    
    if product.stock < order_req.quantity:
        return {"result": "fail", "message": f"재고가 부족합니다. (남은 수량: {product.stock}개)"}

    # 3. 구매 처리 (DB 작업)
    try:
        # A. 주문 내역 저장 (스냅샷 포함)
        order_data.create_order(
            db, user.id, product.id, 
            product.name, product.category, product.sub_category, 
            product.price, order_req.quantity
        )
        
        # B. 재고 감소 및 판매량 증가
        product_data.update_stock_and_sales(db, product.id, order_req.quantity)
        
        return {"result": "success", "message": "구매가 완료되었습니다!"}
        
    except Exception as e:
        print(f"구매 에러: {e}")
        return {"result": "fail", "message": "서버 오류로 구매에 실패했습니다."}