from fastapi import APIRouter
from pydantic import BaseModel
import requests
import os

import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 파일 위치
FAQ_PATH = os.path.join(BASE_DIR, "faq.json")

# FAQ 데이터 로드
with open(FAQ_PATH, "r", encoding="utf-8") as f:
    faq_data = json.load(f)

router = APIRouter(prefix="/chat", tags=["chat"])

# 환경 변수에서 가져오기
API_URL = os.getenv("API_URL") #OpenAI API
API_KEY = os.getenv("API_KEY")

class ChatRequest(BaseModel):
    message: str

def search_faq(user_msg: str, faq_data: list):
    for item in faq_data:
        if item["question"] in user_msg:  # 단순 매칭
            return item["answer"]
    return None    

@router.post("/")
async def chat(req: ChatRequest):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    #faq_answer = search_faq(req.message, faq_data)

    #system_prompt = "너는 특정사이트 고객센터 직원이다. FAQ와 정책을 기반으로 답변해라."
    #if faq_answer:
    #    system_prompt += f"\nFAQ 관련 답변: {faq_answer}"

    # FAQ 전체를 문자열로 변환
    faq_context = "\n".join([f"Q: {item['question']} A: {item['answer']}" for item in faq_data])

    system_prompt = (
        "너는 특정사이트 고객센터 직원이다. 반드시 아래 FAQ와 정책을 기반으로 답변해라.\n"
        f"{faq_context}"
    )        

    data = {
        "model": "gpt-4.1-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.message}
        ]
    }    

    response = requests.post(API_URL, headers=headers, json=data)
    print(response.status_code)
    print(response.json())  # 응답 전체 확인

    if "choices" in response.json():
        bot_reply = response.json()["choices"][0]["message"]["content"]
    else:
        bot_reply = response.json().get("error", {}).get("message", "API 호출 실패")

    return {"reply": bot_reply}
