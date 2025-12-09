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
import pandas as pd
import openpyxl

from sqlalchemy.orm import Session
from sqlalchemy import text

# 크롬으로 창 열기
driver = webdriver.Chrome()
driver.get('https://www.dogpang.com/shop/goods/goods_list.php?category=002001')


time.sleep(2)   


boxes = driver.find_elements(By.CLASS_NAME, 'flex-root')

# 수집한 데이터를 저장할 리스트
data = []


for i, box in enumerate(boxes):
    if i < 20:
        continue
    try:
        print(f"{i+1}번째 클릭 중…")
        box = driver.find_elements(By.CLASS_NAME, 'flex-root')[i]
        box.click()
        time.sleep(1)  # 클릭 후 잠깐 대기

        # 1.이름
        name = driver.find_elements(By.ID, 'viewName')[0].text
        print(name)

        # 2.가격
        price = driver.find_elements(By.ID, 'cart_total_price_pc')[0].text
        print(price)

        # 3.이미지
        image_element = driver.find_element(By.ID, 'photo_detail')
        # 'src' 속성 값 가져오기
        image_url = image_element.get_attribute('src')
        print(image_url)

        # 4.상세정보 가져오기
        description_elements = driver.find_elements(By.CSS_SELECTOR, 'dl.add-info dt' + ' + dd')
        print("저장 중…1")
        # 리스트를 반복하면서 각 요소의 텍스트를 추출하고 리스트에 추가합니다.
        description_texts = []
        for element in description_elements:
            txt = element.text
            description_texts.append(txt)
            print(txt)
        description_text = ' | '.join(description_texts)
            

        # 5. 디테일 img
        detail_image_element = driver.find_element(By.ID, 'goods_desc_img')
        # 'src' 속성 값 가져오기
        detail_image_url = detail_image_element.get_attribute('src')
        print(detail_image_url)

        # 6. 카테고리
        # id='location' 내부의 첫번째 <a> 텍스트를 안전하게 가져오기
        try:
            location_elem = driver.find_element(By.ID, 'location')
            a_elems = location_elem.find_elements(By.TAG_NAME, 'a')
            category = a_elems[0].text if a_elems else ''
        except Exception:
            category = ''
        if category == "사료":
            category = "food"
        print(category)

        # 수집한 항목을 리스트에 추가
        data.append({
            'category': category,
            'name': name,
            'price': price,
            'image_url': image_url,
            'detail_image_url': detail_image_url,
            'description': description_text,
        })
        




        # DB에 저장
#        def create_user(db: Session, category: str, sub_category: str, name: str, price: str, detail: str, image_url: str, detail_img: str):
#            db.execute(
#                text("""
#                    INSERT INTO pet_item (category, sub_category, name, price, detail, image_url, detail_img) 
#                    VALUES (:category, :sub_category, :name, :price, :detail, :image_url, detail_img)
#                """),
#                {
#                    "category": "dog", 
#                    "sub_category": category, 
#                    "name": name,
#                    "price": price,
#                    "detail": description_text,
#                    "image_url": image_element,
#                    "detail_img": detail_image_url,
#
#                }
#            )
#            db.commit()



        time.sleep(1)  # 클릭 후 잠깐 대기



        # 뒤로 가기 (클릭 후 다른 페이지로 이동하면 돌아와야 함)
        driver.back()
        time.sleep(2)

        # 페이지 돌아오면 요소들이 초기화되므로 다시 찾기
        boxes = driver.find_elements(By.CLASS_NAME, 'flex-root')

    except Exception as e:
        print("에러:", e)


# 수집 결과를 엑셀로 저장
if data:
    df = pd.DataFrame(data)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = f"data/dog_products_{timestamp}.xlsx"
    df.to_excel(out_path, index=False)
    print(f"Saved {len(data)} rows to {out_path}")
else:
    print("수집된 데이터가 없습니다.")

# 드라이버 종료
try:
    driver.quit()
except Exception:
    pass



