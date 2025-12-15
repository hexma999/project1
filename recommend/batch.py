import time
import schedule
import subprocess

def run_recommendation():
    print("추천 로직 실행 중...")
    subprocess.run(["python", "recommend.py"])

# 매 1시간마다 실행
schedule.every(1).hours.do(run_recommendation)
#schedule.every(1).minutes.do(run_recommendation)
#schedule.every(5).seconds.do(run_recommendation)

while True:
    schedule.run_pending()
    time.sleep(1)