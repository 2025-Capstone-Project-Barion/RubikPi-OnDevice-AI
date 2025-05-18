# arduino_run_once.py

import time
import serial
from serial.tools import list_ports

def find_arduino_port():
    ports = list_ports.comports()
    for p in ports:
        if "Arduino" in p.description or "ttyACM" in p.device:
            return p.device
    return None

try:
    port = find_arduino_port()
    if not port:
        raise Exception("❌ Arduino 포트를 찾을 수 없음")

    print(f"🔌 아두이노 연결됨: {port}")
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)  # 초기화 대기
    ser.write(b'RUN\n')
    print("✔ RUN 명령 전송 완료")

    # 리니어액추에이터 동작 시간 대기 (15 + 2 + 15)
    time.sleep(32)

    ser.close()
    print("🔒 시리얼 포트 닫힘")

except Exception as e:
    print(f"⚠️ 오류 발생: {e}")
