import pandas as pd
import pymysql
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# DB 접속 정보
host = "team-db.cf4wuo0gsigf.ap-southeast-2.rds.amazonaws.com"
port = 3306
user = "admin"
password = "dnjsgmlwhgdk"
database = "aidetect"

# DB 연결
conn = pymysql.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    database=database,
    charset="utf8mb4"
)

# 구매 테이블에서 데이터 가져오기
query = "SELECT gender, age_group, product FROM purchaseTest;"
df = pd.read_sql(query, conn)

# 전처리
df["gender"] = df["gender"].map({"남성":0, "여성":1})
df["age_group"] = df["age_group"].map({"10대":1, "20대":2, "30대":3, "40대":4, "50대":5})

X = df[["gender", "age_group"]]
y = df["product"]

# 학습 데이터 분리
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 모델 학습
model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

# 새로운 사용자 입력 → 추천 (남성, 20대)
new_user = pd.DataFrame({"gender":[0], "age_group":[2]})
print("new_user:",new_user)

# 확률 기반 Top-10 추천
proba = model.predict_proba(new_user)[0]
product_labels = model.classes_

top_indices = proba.argsort()[::-1][:10]
top_products = [(product_labels[i], float(proba[i])) for i in top_indices]

print("추천 상품 Top-10:")
for rank, (prod, prob) in enumerate(top_products, start=1):
    print(f"{rank}. {prod} (확률: {prob:.2f})")

# --- 추천 결과 DB 저장 ---
cursor = conn.cursor()

# 1. 기존 데이터 모두 삭제
cursor.execute("DELETE FROM recommendation_results")

# 2. 새 추천 결과 삽입
for prod, prob in top_products:
    cursor.execute(
        "INSERT INTO recommendation_results (product, probability) VALUES (%s, %s)",
        (prod, prob)
    )

conn.commit()
cursor.close()
conn.close()