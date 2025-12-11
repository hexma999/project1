from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from dependencies import get_db
from fastapi.templating import Jinja2Templates
from typing import Optional
from pydantic import BaseModel

# 데이터 모듈
from data import memos as memo_data
from data import auth as auth_data

router = APIRouter(prefix="/memos", tags=["memos"])
templates = Jinja2Templates(directory="templates")

class MemoRequest(BaseModel):
    title: str
    content: str

@router.post("/")
async def create_memo(request: Request, memo: MemoRequest, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    user = auth_data.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 메모 생성
    memo_data.create_memo(db, user.id, memo.title, memo.content)
    
    return {"message": "메모가 등록되었습니다."}

@router.get("/")
async def list_memos(
    request: Request, 
    keyword: Optional[str] = None, 
    search_type: Optional[str] = "title", 
    show_mine: bool = False,
    db: Session = Depends(get_db)
):
    username = request.session.get("username")
    if not username:
         # 비로그인 상태에서 게시판 접근 시 로그인 페이지로 안내하거나 에러 처리
         # 여기서는 템플릿 렌더링을 위해 user_id만 None으로 처리
         current_user = None
         current_user_id = None
    else:
        current_user = auth_data.get_user_by_username(db, username)
        current_user_id = current_user.id if current_user else None

    # 메모 목록 조회
    memos = memo_data.get_memos_with_filters(
        db, keyword, search_type, show_mine, current_user_id
    )

    return templates.TemplateResponse(
        "memos.html", 
        {
            "request": request, 
            "memos": memos, 
            "username": username,
            "current_user_id": current_user_id,
            "keyword": keyword if keyword else "",
            "search_type": search_type,
            "show_mine": show_mine
        }
    )

@router.put("/{memo_id}")
async def update_memo(request: Request, memo_id: int, memo: MemoRequest, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        
    user = auth_data.get_user_by_username(db, username)
    
    # 업데이트 수행 (rowcount 확인)
    updated_count = memo_data.update_memo(db, memo_id, user.id, memo.title, memo.content)
    
    if updated_count == 0:
        raise HTTPException(status_code=403, detail="권한이 없거나 존재하지 않는 게시글입니다.")
        
    return {"message": "수정되었습니다."}

@router.delete("/{memo_id}")
async def delete_memo(request: Request, memo_id: int, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        
    user = auth_data.get_user_by_username(db, username)

    # 삭제 수행
    deleted_count = memo_data.delete_memo(db, memo_id, user.id)
    
    if deleted_count == 0:
        raise HTTPException(status_code=403, detail="권한이 없거나 존재하지 않는 게시글입니다.")
        
    return {"message": "삭제되었습니다."}