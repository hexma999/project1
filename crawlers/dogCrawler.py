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

# 크롬으로 창 열기
driver = webdriver.Chrome()
driver.get('https://www.dogpang.com/shop/goods/goods_list.php?category=002001')

time.sleep(2)


boxes = driver.find_elements(By.CLASS_NAME, 'flex-root')


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
        # find_elements를 사용하여 조건에 맞는 모든 <dd> 요소를 리스트로 가져옵니다.
        description_elements = driver.find_elements(By.CSS_SELECTOR, 'dl.add-info dt' + ' + dd')
        
        # 리스트를 반복하면서 각 요소의 텍스트를 추출하고 리스트에 추가합니다.
        for element in description_elements:
            description_text = element.text
            print(description_text)

        


        time.sleep(1)  # 클릭 후 잠깐 대기



        # 뒤로 가기 (클릭 후 다른 페이지로 이동하면 돌아와야 함)
        driver.back()
        time.sleep(2)

        # 페이지 돌아오면 요소들이 초기화되므로 다시 찾기
        boxes = driver.find_elements(By.CLASS_NAME, 'flex-root')

    except Exception as e:
        print("에러:", e)



