import sys
import time
import serial
from serial.tools import list_ports

# ✅ 명령 인자 처리 (UP 또는 DOWN)
if len(sys.argv) < 2 or sys.argv[1] not in ("UP", "DOWN"):
    print("❌ Usage: python3 actuator_serial_runner.py [UP|DOWN]")
    sys.exit(1)
direction = sys.argv[1]

def find_arduino_port():
    for p in list_ports.comports():
        if "Arduino" in p.description or "ttyACM" in p.device:
            return p.device
    return None

try:
    port = find_arduino_port()
    if not port:
        raise RuntimeError("Arduino 포트를 찾을 수 없음")

    print(f"🔌 아두이노 연결됨: {port}")
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)  # 시리얼 초기화 대기

    # ✅ UP → EXTEND, DOWN → RETRACT 명령 전송
    cmd = f"{direction}\n".encode()
    ser.write(cmd)
    print(f"✔ 명령 전송 완료: {direction}")

    # ✅ 액추에이터 동작 시간만큼 대기 (약 15초)
    time.sleep(15)

    ser.close()
    print("🔒 시리얼 포트 닫힘")

except Exception as e:
    print(f"⚠️ 오류 발생: {e}")
