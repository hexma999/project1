# pip install selenium
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium import webdriver #브라우저 직접조작
from selenium.webdriver.common.keys import Keys #키보드 입력
from selenium.webdriver.common.by import By #요소 찾기(html특정태그 지정)
from selenium.webdriver.chrome.service import Service #ChromeDriver 실행 환경 설정
from webdriver_manager.chrome import ChromeDriverManager #크롬드라이버 자동설치
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import requests #HTML 요청
import pymysql
# 옷 사료 간식 방석 집 자료 뽑아오기
driver = webdriver.Chrome()
list_url = 'https://birdpalace.co.kr/category/%EA%B1%B4%EC%A1%B0%EA%B3%BC%EC%9D%BC%EC%B1%84%EC%86%8C/493/'
driver.get(list_url)
time.sleep(2)  # 페이지 로딩 대기
#######################
# 101   dog   food
# 102   dog   snack
# 103   dog   toy
# 104   dog   house
# 105   dog   clothes
# 106   dog   etc
# 201   cat   food
# 202   cat   snack
# 203   cat   toy
# 204   cat   house
# 205   cat   clothes
# 206   cat   etc
# 301   bird   food
# 302   bird   snack
# 303   bird   toy
# 304   bird   house
# 305   bird   clothes
# 306   bird   etc
# 1.이름name 2.가격price 3.회사명brand, 4.세부설명detail,
# 5.세부설명이미지링크(detail_img_url), 6.image_url(이미지링크) 이 들어가있어야함
#301 음식
#302 스낵
def Snack_info():
    xpath = '/html/body/div[4]/div[1]/div/div/div[3]/div/ul/li'
    snack_all = driver.find_elements(By.XPATH, xpath)
    snack_infos = []
    wait = WebDriverWait(driver, 10)
    for item in snack_all:
        try: #
            #/html/body/div[4]/div[1]/div/div/div[3]/div/ul/li[5]/div/span/span/div/div[3]/a/span
            name_elem = item.find_element(By.XPATH, './div/span/span/div/div[3]/a/span')
            print(name_elem)
            price_elem = item.find_element(By.XPATH, './div/span/span/div/ul[2]/li[2]/span[2]')
            print(price_elem)
            # brand_elem = item.find_element(By.XPATH, './div/span/span/div/ul[2]/li[5]/span[2]')
            # print(brand_elem)
             #!일단 브랜드명 없어서 한줄평으로 크롤링해옴
            # /html/body/div[4]/div[1]/div/div/div[3]/div/ul/li[6]/div/span/span/div/ul[2]/li[5]/span[2]
            # /html/body/div[4]/div[1]/div/div/div[3]/div/ul/li[9]/div/span/span/div/ul[2]/li[5]/span[2]
            # /html/body/div[4]/div[1]/div/div/div[3]/div/ul/li[15]/div/span/span/div/ul[2]/li[5]/span[2]
            name = name_elem.text.strip()
            print(name)
            price = price_elem.text.strip()
            print(price)
            # brand = brand_elem.text.strip()
            # print(brand)
            # 목록 카드에서 대표 이미지 링크 추출 (페이지 구조에 맞게 수정 가능)
            img_elem = item.find_element(By.XPATH, './div/span/span/div/div[1]/a/img[1]')
            image_url = img_elem.get_attribute("src")
            # 상세 페이지 이동을 위한 a 태그(상품제목을 누르면 이동되는 주소 <a href="~">)
            link_elem = item.find_element(By.XPATH, './div/span/span/div/div[3]/a')
            detail_url = link_elem.get_attribute("href")
            detail_text, detail_img_url = fetch_detail_page(detail_url, wait)
            # 위에서 얻은 상세 페이지 URL을 fetch_detail_page 함수에 넘겨서
            # 실제 상세 페이지로 이동해(새 탭) 상세 설명 텍스트(detail_text)와
            # 상세 이미지 링크(detail_img_url)를 받아옵니다.
            # wait는 그 함수 안에서 요소가 로드될 때까지 기다리도록 쓰는 WebDriverWait 객체.
            print(name)
            print(price)
            # print(brand)
            print(image_url)
            snack_infos.append({
                'name':name,
                'price':price,
                #'brand':brand,
                'detail':detail_text,
                'detail_img_url':detail_img_url,
                'image_url':image_url
            })
        except Exception as e:
            print(f"에러가 발생했습니다: {e}")
    print(snack_infos)
    return snack_infos
def fetch_detail_page(url, wait):
    """
    상세 페이지에서 상세 설명과 상세 이미지 링크를 가져온다.
    동작 방식:
    1. 같은 탭에서 상세 페이지로 이동 (driver.get(url))
    2. 상세 설명 요소가 로드될 때까지 대기 후 텍스트 추출
    3. 상세 이미지 요소를 찾아 이미지 URL 추출
    4. 목록 페이지로 돌아가기 (driver.back())
    5. 목록 페이지가 다시 로드될 때까지 대기
    6. 추출한 상세 설명과 이미지 URL 반환
    """
    # 1단계: 같은 탭에서 상세 페이지로 이동
    driver.get(url)
    detail_text = ''
    detail_img_url = ''
    try:
        # 2단계: 상세 설명 요소가 로드될 때까지 대기 후 텍스트 추출
        detail_elem = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div#prdDetail')) #!상세설명요소랄게 텍스트없음(한줄평은있음)
        )
        detail_text = detail_elem.text.strip()
        # 3단계: 상세 이미지 요소를 찾아 이미지 URL 추출
        detail_img = driver.find_elements(By.CSS_SELECTOR, 'div#prdDetail img')
        if detail_img:
            detail_img_url = detail_img[0].get_attribute("src")
    except Exception as e:
        print(f"상세 페이지 파싱 오류: {e}")
    finally:
        # 4단계: 목록 페이지로 돌아가기
        driver.back()
        # 5단계: 목록 페이지가 다시 로드될 때까지 대기
        wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[1]/div/div/div[3]/div/ul/li')))
    # 6단계: 추출한 상세 설명과 이미지 URL 반환
    return detail_text, detail_img_url
print("크롤링 시작!")
result = Snack_info()
print(f"크롤링 완료! 총 {len(result)}개 상품 수집됨")



# /html/body/div[4]/div[1]/div[1]/div/div[3]/div[2]/div[2]/div/div[2]/div[2]/div[1]/p[1]/strong