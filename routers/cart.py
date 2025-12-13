from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from dependencies import get_db
from data import cart as cart_data
from data import auth as auth_data
from data import orders as order_data

router = APIRouter(prefix="/cart", tags=["cart"])
templates = Jinja2Templates(directory="templates")

class CartRequest(BaseModel):
    product_id: int
    quantity: int

# 장바구니 담기 (API)
@router.post("/add")
async def add_to_cart(request: Request, item: CartRequest, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        return {"result": "fail", "message": "로그인이 필요합니다."}
    
    user = auth_data.get_user_by_username(db, username)
    cart_data.add_to_cart(db, user.id, item.product_id, item.quantity)
    
    # 갱신된 개수 반환
    count = cart_data.get_cart_count(db, user.id)
    return {"result": "success", "message": "장바구니에 담겼습니다.", "count": count}

# 장바구니 개수 조회 (API - 배지용)
@router.get("/count")
async def get_cart_count(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        return {"count": 0}
    
    user = auth_data.get_user_by_username(db, username)
    count = cart_data.get_cart_count(db, user.id)
    return {"count": count}

# 장바구니 페이지 조회
@router.get("/")
async def view_cart(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    
    user = auth_data.get_user_by_username(db, username)
    cart_items = cart_data.get_cart_items(db, user.id)
    
    # 총 결제 예상 금액
    total_price = sum(item.sub_total for item in cart_items)

    return templates.TemplateResponse("cart.html", {
        "request": request,
        "username": username,
        "cart_items": cart_items,
        "total_price": total_price
    })

# 장바구니 아이템 삭제
@router.delete("/remove/{item_id}")
async def remove_item(item_id: int, db: Session = Depends(get_db)):
    cart_data.remove_cart_item(db, item_id)
    return {"result": "success"}

# 장바구니 결제 (전체 구매)
@router.post("/checkout")
async def checkout_cart(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        return {"result": "fail", "message": "로그인이 필요합니다."}
    
    user = auth_data.get_user_by_username(db, username)
    cart_items = cart_data.get_cart_items(db, user.id)
    
    if not cart_items:
        return {"result": "fail", "message": "장바구니가 비어있습니다."}

    try:
        # 주문 생성 포맷으로 변환
        order_list = []
        for item in cart_items:
            order_list.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price
            })
        
        # 주문 생성
        order_data.create_order(db, user.id, order_list)
        
        # 장바구니 비우기
        cart_data.clear_cart(db, user.id)
        
        return {"result": "success", "message": "주문이 완료되었습니다!"}
    except Exception as e:
        print(e)
        return {"result": "fail", "message": "주문 처리 중 오류가 발생했습니다."}