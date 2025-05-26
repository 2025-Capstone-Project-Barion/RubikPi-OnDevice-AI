# actuator_extend.py
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
        raise Exception(" Arduino 포트를 찾을 수 없음")

    print(f"아두이노 연결됨: {port}")
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)  # 시리얼 초기화 대기

    ser.write(b'UP\n')
    print("'UP' 명령 전송 완료 (최대 길이로 늘리기)")

    time.sleep(15)  # 동작 시간 대기 + 1 (15초 동작 + 1초 여유)
    ser.close()
    print(" 시리얼 포트 닫힘")

except Exception as e:
    print(f" 오류 발생: {e}")
