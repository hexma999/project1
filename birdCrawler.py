import time
import argparse
import logging
import json
from bs4 import BeautifulSoup
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import openpyxl
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal
# -----------------------------------------------------------
#  !!!!step6 : db 테이블 저장
# -----------------------------------------------------------
db = SessionLocal()

def create_products(db: Session, category_id: str, name: str, price: int, brand: str, 
                    initial_stock: str, stock: str, sales_count: str, detail: str, detail_img_url: str, image_url: str, 
                    expiration_days: str):
    try:
        
        db.execute(
            text("""
                INSERT INTO products (
                    category_id, name, price, brand, initial_stock, stock, sales_count,
                    image_url, detail, detail_img_url, expiration_days
                )
                VALUES (
                    :category_id, :name, :price, :brand, :initial_stock, :stock, :sales_count, 
                    :image_url, :detail, :detail_img_url, :expiration_days
                )
                 
            """),
            {
                "category_id": category_id,
                "name": name,
                "price": price,
                "brand": brand,
                "initial_stock": initial_stock,
                "stock": stock,
                "sales_count": sales_count,
                "detail": detail,
                "detail_img_url": detail_img_url,
                "image_url": image_url,
                "expiration_days": expiration_days,
            }
        )
        db.commit()
        print(f"  [DB저장] {name[:10]}... 완료")
    except Exception as e:
        print(f"  [DB에러] {e}")
        db.rollback()


# -----------------------------------------------------------
# !!!!! step1: 카테고리별 URL 순회/ 301~306 ID 부여
# -----------------------------------------------------------

TARGET_URLS = [
    # 301: bird_food 
    ("https://birdpalace.co.kr/product/list.html?cate_no=73", "301"), 
    # 302: snack 
    ("https://birdpalace.co.kr/product/list.html?cate_no=102", "302"), 
    # 303: bird_house
    ("https://birdpalace.co.kr/product/list.html?cate_no=44", "303"), 
    # 304: bird_item
    ("https://birdpalace.co.kr/product/list.html?cate_no=25", "304"), 
    # 305: bird_alpha 
    ("https://birdpalace.co.kr/product/list.html?cate_no=49", "305"), 
    # 306: etc 
    ("https://birdpalace.co.kr/product/list.html?cate_no=79", "306"), 
]

# -----------------------------------------------------------
# !!!!!step2: 크롤링 실행 이중 for문 
# -----------------------------------------------------------


driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 15)  # 최대 15초 기다림 (그 전에 뜨면 바로 진행)


for url, category_id in TARGET_URLS:
    

    print(f"\n>>> 카테고리 {category_id} 작업 시작: {url}")
    driver.get(url)

    try:
        # 팝업 닫기 시도
        close_button = driver.find_element(By.CSS_SELECTOR, "#wrap > div.rightQuick > div > div > div.toggle-click > div")
        close_button.click()
        time.sleep(1)
            
    except:
    
            pass
    

    
    # [수정] 상품 전체 개수를 먼저 파악
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.prdList > li")))
        item_count = len(driver.find_elements(By.CSS_SELECTOR, "ul.prdList > li"))
    except:
        continue

    # 10개 제한 테스트
    loop_limit = min(item_count, 16)
    j = 6

    for i in range(j , loop_limit):

        try:
            # [핵심] 매번 요소를 새로 찾아서 Stale 에러 방지
            items = driver.find_elements(By.CSS_SELECTOR, "ul.prdList > li")
            
            # li 내부의 실제 클릭 가능한 <a> 태그를 찾아서 클릭
            target_link = items[i].find_element(By.CSS_SELECTOR, "a")
            

        
# -----------------------------------------------------------
# !!!!step3: 크롤링 실행 이중 for문 
# -----------------------------------------------------------
        
            # !! step2: 팝업 닫기 기능 구현/ scrollIntoView로 안정적 클릭
            driver.execute_script("arguments[0].scrollIntoView(true);", target_link)
            time.sleep(1) 
            
            target_link.click()
            print(f"[{i}] 상세 페이지 진입 성공")

            # --- 여기서 상세 페이지 데이터 크롤링 logic 수행 ---
            time.sleep(2) 

# -----------------------------------------------------------
# !!!!!step4:  데이터 파싱 & 가공
# -----------------------------------------------------------


            # 1. 이름
            try:
                name = driver.find_element(By.CSS_SELECTOR, "div.name > span").text
            except:
                name = "이름 없음"
            # print(name)
            
            #2. 가격
            try:
                price = driver.find_element(By.CSS_SELECTOR, "#span_product_price_text").text.split("원")[0] 
                price_text =price.replace(",","")
                price_text = int(price_text)
            except:
                price_text = "이름 없음"
            # print(price_text)
           
            # 3 브랜드
            brand = None
            if 0 < price_text <5000:
                brand = '버펠'
            elif price_text <15000:
                brand = '각하'
            elif price_text <25000:
                brand = '원희좋아'
            elif price_text <35000:
                brand = '향유고래'
            elif price_text <45000:
                brand = '쿠로미'
            elif price_text <55000:
                brand = '와조스키'
            else:
                brand = '경수오빠못해조' 

            # 4. 입고
            initial_stock = 100
            # 5. 재고
            stock = 100
            # 6. 판매량
            sales_count = 0
            # 7. 상품 설명
            try:
                detail = driver.find_element(By.CSS_SELECTOR, "#contents > div.mall_width > div.xans-element-.xans-product.xans-product-detail > div.detailArea > div.infoArea > div > div.xans-element-.xans-product.xans-product-detaildesign.item_detail_info.display_hide.display_show > table > tbody > tr:nth-child(3) > td > span").text
                
            # #contents > div.mall_width > div.xans-element-.xans-product.xans-product-detail > div.detailArea > div.infoArea > div > div.xans-element-.xans-product.xans-product-detaildesign.item_detail_info.display_hide.display_show > table > tbody > tr:nth-child(3) > td > span

            # #contents > div.mall_width > div.xans-element-.xans-product.xans-product-detail > div.detailArea > div.infoArea > div > div.xans-element-.xans-product.xans-product-detaildesign.item_detail_info.display_hide.display_show > table > tbody > tr:nth-child(2) > td > span

           

            except:
                detail = "이름 없음"
            # print(detail)
            # 8. 상품 설명 이미지
            try:
                detail_img_element = driver.find_elements(By.CSS_SELECTOR, "#prdDetail > div > div > div > img")[-2]
                detail_img_url = detail_img_element.get_attribute("src")
            except:
                detail_img_url = "이름 없음"
            # print(detail_img_url)

            # 9. 이미지 썸네일
            try:
                image_url1= driver.find_element(By.CSS_SELECTOR, "#contents > div.mall_width > div.xans-element-.xans-product.xans-product-detail > div.detailArea > div.xans-element-.xans-product.xans-product-image.imgArea > div:nth-child(1) > div > img")
                image_url  = image_url1.get_attribute("src")
            except:
                image_url = "이름 없음"
            # print(image_url)

            # 10. 만료기한
            expiration_days = -1


# -----------------------------------------------------------
# !!!!!step5:  db 저장 함수 실행 
# -----------------------------------------------------------

            create_products(db, category_id, name, price_text, brand,initial_stock, stock, sales_count, detail, detail_img_url, image_url, expiration_days)


# #contents > div.mall_width > div.xans-element-.xans-product.xans-product-detail > div.detailArea > div.infoArea > div > div.item_name > div.xans-element-.xans-product.xans-product-detaildesign > div

# #contents > div.mall_width > div.xans-element-.xans-product.xans-product-detail > div.detailArea > div.infoArea > div > div.item_name > div.xans-element-.xans-product.xans-product-detaildesign > div > span


            
            # 뒤로 가기
            driver.back()
            
            # [핵심] 목록 페이지가 로드될 때까지 명시적 대기
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.prdList > li")))
            time.sleep(1)

        except Exception as e:
            print(f"  [에러 발생] {i}번째 상품 처리 중: {e}")
            # 에러 시 목록으로 돌아가기 시도
            driver.get(url) 
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.prdList > li")))
            continue



