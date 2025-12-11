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


# DB에 저장
db = SessionLocal() 
def create_products(db: Session, category_id: str, name: str, price: str, brand: str, initial_stock: str, detail: str, detail_img_url: str, image_url: str):
    db.execute(
        text("""
            INSERT INTO products (category_id, name, price, brand, initial_stock, image_url, detail, detail_img_url) 
            VALUES (:category_id, :name, :price, :brand, :initial_stock, :image_url, :detail, :detail_img_url)
        """),
        {
            "category_id": category_id, 
            "name": name,
            "price": price,
            "brand": brand,
            "initial_stock": initial_stock,
            "detail": detail,
            "detail_img_url": detail_img_url,
            "image_url": image_url,
        }
    )
    db.commit()

# 크롬으로 창 열기
driver = webdriver.Chrome()
driver.get('https://www.catpang.com/shop/goods/goods_list.php?category=001002')
wait = WebDriverWait(driver, 10)

time.sleep(1)   


boxes = driver.find_elements(By.CLASS_NAME, 'flex-root')

# 수집한 데이터를 저장할 리스트
data = []

def get_page_count(driver):
    pager = driver.find_element(By.CLASS_NAME, "pager")
    links = pager.find_elements(By.TAG_NAME, "a")
    return len(links)

# 사용 예시
count = get_page_count(driver)  # 🔥 결과: 8

for j in range(count):
    print(f"페이지 {j+1} 페이지 작업중...")

    # 페이지네이션 div 찾기
    pager = driver.find_element(By.CLASS_NAME, "pager")

    # div 안의 모든 a 태그 가져오기 (★★ 페이지마다 다시 읽어야 한다)
    pages = pager.find_elements(By.TAG_NAME, "a")

    # pages 길이 체크 (index error 방지)
    if j >= len(pages):
        print("페이지 인덱스가 페이지 수보다 큼 — 건너뜀")
        continue

    # 클릭 가능 상태까지 기다리기 (★★ 여기 추가!)
    try:
        element = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"(//div[@class='pager']//a)[{j+1}]"))
        )
        element.click()
        time.sleep(1)

        # 🔥🔥 [수정 1] 페이지 이동 후 boxes 다시 불러오기
        boxes = driver.find_elements(By.CLASS_NAME, 'flex-root')

    except Exception as e:
        print("페이지 클릭 오류:", e)
        continue

    ############################페이지 안 작업##########################

    for i, box in enumerate(boxes):

        if j == 0 and i < 20:
            continue

        try:
            box = driver.find_elements(By.CLASS_NAME, 'flex-root')[i]
            element = wait.until(EC.element_to_be_clickable(box))
            element.click()

            # 1.이름
            name = driver.find_elements(By.ID, 'viewName')[0].text

            # 2.가격
            price = driver.find_elements(By.ID, 'cart_total_price_pc')[0].text
            text_price = price.replace(',', '')
            if text_price == '0':
                text_price = "19900"

            # 3.이미지
            image_element = driver.find_element(By.ID, 'photo_detail')
            image_url = image_element.get_attribute('src')

            # 4.상세정보 가져오기
            detail_elements = driver.find_elements(By.CSS_SELECTOR, 'dl.add-info dt' + ' + dd')
            detail_texts = []
            for element in detail_elements:
                txt = element.text
                detail_texts.append(txt)
                
            detail_text = ' | '.join(detail_texts)

            # 5. 디테일 img
            try:
                detail_image_element = driver.find_element(By.ID, 'goods_desc_img')
                detail_img_url = detail_image_element.get_attribute('src')
            except:
                detail_img_url = ""
            if detail_img_url == "":
                break
           
            # 6. 카테고리
            try:
                location_elem = driver.find_element(By.ID, 'location')
                a_elems = location_elem.find_elements(By.TAG_NAME, 'a')
                category = a_elems[0].text if a_elems else ''
            except Exception:
                category = ''

            # 7. 브랜드 명
            brand = driver.find_element(
                By.XPATH,
                "/html/body/div[4]/div/div[2]/div/div[1]/div[2]/div[1]/a"
            ).text
             
            category_id=''
            if category == "사료":
                category_id = "201"
            elif category == "캔/간식":
                category_id = "202"
            elif category == "장난감":
                category_id = "203"
            elif category == "하우스/쿠션":
                category_id = "204"
            elif category == "스크래쳐/캣타워":
                category_id = "205"
            else:
                category_id = "206"

            initial_stock = "100"

            # 수집 리스트 추가
            data.append({
                'category_id': category_id,
                'name': name,
                'price': text_price,
                'brand' : brand,
                'initial_stock' : initial_stock,
                'detail': detail_text,
                'detail_img_url': detail_img_url,
                'image_url': image_url,
            })

            # DB 저장
            create_products(
                db,
                category_id,
                name,
                text_price,
                brand,
                initial_stock,
                detail_text,
                detail_img_url,
                image_url
            )

            time.sleep(0.1)

            # 뒤로 가기
            driver.back()
            time.sleep(1)

            # 🔥 boxes 재로드는 여기 유지 (문제 없음)
            boxes = driver.find_elements(By.CLASS_NAME, 'flex-root')

        except Exception as e:
            print("에러:", e)

######################페이지 안 작업########################


# 드라이버 종료
try:
    driver.quit()
except Exception:
    pass


