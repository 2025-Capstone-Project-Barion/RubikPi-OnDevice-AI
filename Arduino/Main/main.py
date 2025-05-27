# 노트북에서 실행예정
import time
import serial
from serial.tools import list_ports
import paho.mqtt.client as mqtt

# ✅ MQTT 브로커 정보 설정
BROKER_ADDRESS = "192.168.137.229"  # 라즈베리파이(Mosquitto 브로커 IP)
PORT = 1883

# ✅ 사용하는 MQTT 토픽
TOPIC_DETECTED = "chair-person-detected"  # 카메라 감지 성공 시 RubikPi가 발행
TOPIC_PAY = "payment-done"                # 결제 완료 시 라즈베리파이가 발행

# ✅ 전역 시리얼 객체 및 상태 플래그
ser = None
has_retracted = False  # 휠체어 감지 후 DOWN 명령을 보낸 상태 추적

def find_arduino_port():
    """
    🔍 연결된 Arduino 포트를 자동 탐지한다.
    """
    ports = list_ports.comports()
    for p in ports:
        if "Arduino" in p.description or "ttyACM" in p.device:
            return p.device
    return None

def init_serial():
    """
    🔌 Arduino 시리얼 포트를 초기화한다.
    """
    global ser
    port = find_arduino_port()
    if not port:
        raise Exception("❌ Arduino 포트를 찾을 수 없음")
    print(f"🔌 Arduino 연결됨: {port}")
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)  # 시리얼 초기화 대기

def send_command(cmd: str):
    """
    📤 Arduino로 명령을 전송한다 ("UP" 또는 "DOWN")
    """
    if ser is None or not ser.is_open:
        print("❗ 시리얼 포트가 닫혀있음")
        return
    ser.write(f"{cmd}\n".encode())  # 반드시 개행 포함
    print(f"📤 Arduino로 명령 전송됨: {cmd}")

def on_message(client, userdata, msg):
    """
    📩 MQTT 메시지를 수신했을 때 호출된다.
    """
    global has_retracted
    topic = msg.topic
    payload = msg.payload.decode().strip()  # 공백 제거
    print(f"[MQTT RX] {repr(topic)} → {repr(payload)}")

    if topic == TOPIC_DETECTED and payload == "true":
        if not has_retracted:
            send_command("DOWN")
            has_retracted = True
        else:
            print("⚠️ 이미 DOWN 상태입니다. 중복 무시")

    elif topic == TOPIC_PAY and payload == "complete":
        if has_retracted:
            send_command("UP")
            has_retracted = False
        else:
            print("ℹ️ 휠체어 감지되지 않아 UP 명령 생략됨")

    else:
        print(f"ℹ️ 무시된 토픽 또는 페이로드: topic={topic}, payload={payload}")

def on_connect(client, userdata, flags, rc):
    """
    🔌 MQTT 브로커에 연결되었을 때 호출된다.
    """
    if rc == 0:
        print("✅ MQTT 브로커 연결 성공")
        client.subscribe(TOPIC_DETECTED)
        client.subscribe(TOPIC_PAY)
    else:
        print(f"❌ MQTT 연결 실패: 코드 {rc}")

# ✅ 메인 실행부
try:
    init_serial()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🔌 MQTT 브로커({BROKER_ADDRESS}:{PORT}) 연결 시도...")
    client.connect(BROKER_ADDRESS, PORT, 60)
    client.loop_start()

    print("▶ actuator_mqtt_listener 실행 중. Ctrl+C로 종료")
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("🛑 종료 요청")
except Exception as e:
    print(f"❗ 예외 발생: {e}")
finally:
    if ser and ser.is_open:
        ser.close()
        print("🔒 시리얼 포트 닫힘")
    client.loop_stop()
    client.disconnect()
    print("🔌 MQTT 연결 종료 완료")
