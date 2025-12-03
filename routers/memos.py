from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from dependencies import get_db
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/memos", tags=["memos"])
templates = Jinja2Templates(directory="templates")

@router.post("/")
async def create_memo(request: Request, memo: dict, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authorized")

    # 사용자 조회 (raw SQL)
    user = db.execute(text("SELECT * FROM users WHERE username = :username"), {"username": username}).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 메모 삽입 (raw SQL)
    db.execute(
        text("INSERT INTO memo (user_id, title, content) VALUES (:user_id, :title, :content)"),
        {"user_id": user.id, "title": memo["title"], "content": memo["content"]}
    )
    db.commit()
    return {"message": "Memo created successfully"}

@router.get("/")
async def list_memos(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authorized")

    user = db.execute(text("SELECT * FROM users WHERE username = :username"), {"username": username}).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    memos = db.execute(text("SELECT * FROM memo WHERE user_id = :user_id"), {"user_id": user.id}).fetchall()
    return templates.TemplateResponse("memos.html", {"request": request, "memos": memos, "username": username})

@router.put("/{memo_id}")
async def update_memo(request: Request, memo_id: int, memo: dict, db: Session = Depends(get_db)):
    username = request.session.get("username")
    user = db.execute(text("SELECT * FROM users WHERE username = :username"), {"username": username}).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = db.execute(
        text("UPDATE memo SET title = :title, content = :content WHERE id = :memo_id AND user_id = :user_id"),
        {"title": memo.get("title"), "content": memo.get("content"), "memo_id": memo_id, "user_id": user.id}
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Memo not found")
    return {"message": "Memo updated successfully"}

@router.delete("/{memo_id}")
async def delete_memo(request: Request, memo_id: int, db: Session = Depends(get_db)):
    username = request.session.get("username")
    user = db.execute(text("SELECT * FROM users WHERE username = :username"), {"username": username}).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = db.execute(
        text("DELETE FROM memo WHERE id = :memo_id AND user_id = :user_id"),
        {"memo_id": memo_id, "user_id": user.id}
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Memo not found")
    return {"message": "Memo deleted"}