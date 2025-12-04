from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from dependencies import get_db
from fastapi.templating import Jinja2Templates
from typing import Optional
# 데이터 레이어 임포트
from data import memos as memo_data
from data import auth as auth_data # 사용자 확인용

router = APIRouter(prefix="/memos", tags=["memos"])
templates = Jinja2Templates(directory="templates")

@router.post("/")
async def create_memo(request: Request, memo: dict, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authorized")

    user = auth_data.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 메모 생성 (Data 레이어 호출)
    memo_data.create_memo(db, user.id, memo["title"], memo["content"])
    
    return {"message": "Memo created successfully"}

@router.get("/")
async def list_memos(
    request: Request, 
    keyword: Optional[str] = None, 
    search_type: Optional[str] = "title", 
    show_mine: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    username = request.session.get("username")
    if not username:
        # 로그인 안 된 경우 로그인 페이지로 리다이렉트하거나 401
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    current_user = auth_data.get_user_by_username(db, username)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 메모 목록 조회 (Data 레이어 호출 - 필터링 로직 포함)
    memos = memo_data.get_memos_with_filters(
        db, keyword, search_type, show_mine, current_user.id
    )

    return templates.TemplateResponse(
        "memos.html", 
        {
            "request": request, 
            "memos": memos, 
            "username": username,
            "current_user_id": current_user.id,
            "keyword": keyword if keyword else "",
            "search_type": search_type,
            "show_mine": show_mine
        }
    )

@router.put("/{memo_id}")
async def update_memo(request: Request, memo_id: int, memo: dict, db: Session = Depends(get_db)):
    username = request.session.get("username")
    user = auth_data.get_user_by_username(db, username)
    
    # 메모 업데이트 (Data 레이어 호출 - rowcount로 성공 여부 판단)
    updated_count = memo_data.update_memo(
        db, memo_id, user.id, memo.get("title"), memo.get("content")
    )
    
    if updated_count == 0:
        raise HTTPException(status_code=403, detail="권한이 없거나 게시글이 없습니다.")
    return {"message": "Memo updated successfully"}

@router.delete("/{memo_id}")
async def delete_memo(request: Request, memo_id: int, db: Session = Depends(get_db)):
    username = request.session.get("username")
    user = auth_data.get_user_by_username(db, username)

    # 메모 삭제 (Data 레이어 호출)
    deleted_count = memo_data.delete_memo(db, memo_id, user.id)
    
    if deleted_count == 0:
        raise HTTPException(status_code=403, detail="권한이 없거나 게시글이 없습니다.")
    return {"message": "Memo deleted"}