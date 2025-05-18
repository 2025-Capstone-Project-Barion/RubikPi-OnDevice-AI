# main_runner.py

import subprocess
import time

COOLDOWN_SECONDS = 32  # 아두이노 동작 시간

while True:
    key = input("▶ 리니어액추에이터를 작동하려면 'r' 입력 후 Enter: ")
    if key.lower() == 'r':
        print("🟡 리니어액추에이터 동작 시작 (약 32초 대기 중...)")
        subprocess.call(["python3", "arduino_run_once.py"])
        print("✅ 동작 완료. 다시 입력 가능.")
    else:
        print("ℹ️ 'r' 외 다른 키 입력됨. 무시합니다.")
