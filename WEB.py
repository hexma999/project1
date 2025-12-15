import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal

# -----------------------------------------------------------
# 1. DB 설정
# -----------------------------------------------------------
db = SessionLocal()

def create_products(db: Session, category_id: str, name: str, price: str, brand: str, 
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
# 2. 크롤링 타겟 설정
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
# 3. 크롤링 실행
# -----------------------------------------------------------
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 15)  # 최대 15초 기다림 (그 전에 뜨면 바로 진행)

for url, category_id in TARGET_URLS:
    print(f"\n>>> 카테고리 {category_id} 작업 시작: {url}")
    driver.get(url)
    
    # [1] 목록 페이지 로딩 대기: 상품 리스트(ul.prdList)가 나타날 때까지
    try:
        # #contents > div.xans-element-.xans-product.xans-product-normalpackage.item_normal_display > div > ul > li:nth-child()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.prdList > li")))
    except:
        print("상품 리스트 로딩 실패 (타임아웃)")
        continue

    # 상품 리스트 요소들 찾기
    try:
        items = driver.find_elements(By.CSS_SELECTOR, "ul.prdList > li")
        if not items:
             items = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
    except:
        print("상품 리스트를 찾을 수 없습니다.")
        continue

    print(f"  총 {len(items)}개의 상품 발견 (페이지 1)")

    # 리스트 루프
    for i in range(len(items)):
        if i >= 10: break # 테스트용 10개 제한 (실제 사용 시 제거/주석)

        try:
            # [2] Stale 방지: 목록 요소가 확실히 다시 로드될 때까지 기다렸다가 다시 찾음
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.prdList > li")))
            items = driver.find_elements(By.CSS_SELECTOR, "ul.prdList > li")
            
            if i >= len(items): break # 인덱스 에러 방지
            box = items[i]
            
            # 썸네일 클릭 (화면에 보일 때까지 대기 후 클릭)
            try:
                link = wait.until(EC.element_to_be_clickable(box.find_element(By.TAG_NAME, "a")))
                link.click()
            except Exception as e:
                print("  클릭 실패, 건너뜀")
                continue
            
            # [3] 상세 페이지 로딩 대기: 핵심 내용(.xans-product-detail)이 뜰 때까지
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".xans-product-detail")))
            except:
                print("  상세페이지 로딩 시간 초과")
                driver.back()
                continue

            # ==========================
            # 데이터 추출 시작
            # ==========================

            # 1. 이름
            try:
                name = driver.find_element(By.CSS_SELECTOR, ".headingArea h2").text
            except:
                name = "이름 없음"

            # 2. 가격
            try:
                price_text = driver.find_element(By.ID, "span_product_price_text").text
                price = re.sub(r"[^0-9]", "", price_text)
                if not price: price = "0"
            except:
                price = "0"

            # 3. 브랜드
            brand = "BirdPalace"
            try:
                table_rows = driver.find_elements(By.CSS_SELECTOR, ".xans-product-detaildesign tr")
                for row in table_rows:
                    th = row.find_element(By.TAG_NAME, "th").text
                    if "제조사" in th or "브랜드" in th:
                        brand = row.find_element(By.TAG_NAME, "td").text
                        break
            except:
                pass

            # 4, 5, 6. 재고 및 판매량 (고정값)
            initial_stock = "100"
            stock = "100"
            sales_count = "0"

            # 7. 상세 텍스트
            detail = ""
            try:
                detail_area = driver.find_element(By.ID, "prdDetail")
                detail = detail_area.text.replace("\n", " | ")
            except:
                detail = ""

            # 8. 상세 이미지
            detail_img_url = ""
            try:
                detail_area = driver.find_element(By.ID, "prdDetail")
                imgs = detail_area.find_elements(By.TAG_NAME, "img")
                if imgs:
                    detail_img_url = imgs[0].get_attribute("src")
            except:
                pass

            # 9. 대표 이미지
            try:
                image_url = driver.find_element(By.CSS_SELECTOR, ".keyImg img").get_attribute("src")
            except:
                image_url = ""
    
            # 10. 유통기한
            expiration_days = "-1"

            # 출력 확인
            print(f"[{category_id}] {name[:10]} | {price}원 | 브랜드: {brand} | 재고: {stock}")

            # DB 저장 (필요시 주석 해제)
            create_products(
               db, category_id, name, price, brand, initial_stock, stock, sales_count,
               detail, detail_img_url, image_url, expiration_days
            )

            # [4] 뒤로가기 실행
            driver.back()
            
            # [5] 목록 복귀 대기: 다시 상품 리스트가 보일 때까지 기다려야 다음 루프가 정상 작동
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.prdList > li")))
            except:
                print("  목록 복귀 실패 (타임아웃)")
                pass

        except Exception as e:
            # 에러 발생 시에도 안전하게 목록으로 복귀 시도
            try:
                driver.back()
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.prdList > li")))
            except:
                pass
            continue

# 종료
driver.quit()
