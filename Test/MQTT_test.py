import paho.mqtt.client as mqtt
import time

# ✅ MQTT 브로커 연결 설정을 정의한다.
broker_address = "61.74.20.97"  # 라즈베리파이에서 실행 중인 Mosquitto 브로커의 IP 주소이다.
port = 1883  # 루빅파이에서는 기본 TCP 포트(1883)를 사용한다. WebSocket이 아님에 주의한다.

# ✅ 사용하는 MQTT 토픽명을 간결하게 재정의한다.
TOPIC_DETECTED = "chair-person-detected"  # 휠체어 + 사람 감지 시 RubikPi가 이 토픽에 "true"를 발행한다.
TOPIC_START = "kiosk-start"               # 키오스크 시작 (음성명령 시작 시)
TOPIC_CLOSE = "kiosk-close"               # 감지 종료 (메뉴 진입 시)
TOPIC_PAY = "payment-done"                # 결제 완료 → 액추에이터 복귀

# ✅ 하드웨어 또는 시뮬레이션용 함수들을 정의한다.
def camera_on():
    print("🎬 YOLO 감지 시작 (카메라 ON)")

def camera_off():
    print("📴 YOLO 감지 종료 (카메라 OFF)")

def actuator_up():
    print("⬆️ 리니어 액추에이터 상승 (기기 원위치)")

# ✅ MQTT 메시지를 수신했을 때 호출되는 콜백 함수이다.
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"📩 수신됨: {topic} → {payload}")
    if topic == TOPIC_START and payload == "activate":
        camera_on()
    elif topic == TOPIC_CLOSE and payload == "close":
        camera_off()
    elif topic == TOPIC_PAY and payload == "complete":
        actuator_up()

# ✅ MQTT 브로커에 연결되었을 때 호출되는 콜백 함수이다.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT 브로커 연결 성공")
        # 시작, 종료, 결제완료 토픽을 구독한다.
        client.subscribe(TOPIC_START)
        client.subscribe(TOPIC_CLOSE)
        client.subscribe(TOPIC_PAY)
    else:
        print(f"❌ 연결 실패, 코드: {rc}")

# ✅ MQTT 클라이언트를 생성한다.
# client_id는 생략하여 자동 생성되도록 한다.
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    print(f"🔌 MQTT 브로커({broker_address}:{port})에 연결 중...")
    client.connect(broker_address, port, 60)
    client.loop_start()

    # 사용자 테스트용 명령어 입력 UI를 표시한다.
    print("\n🧪 [명령어 입력 메뉴]")
    print("1 → 휠체어+사람 감지 메시지 발행")
    print("3 → 카메라 상태 확인")
    print("q → 종료")

    while True:
        cmd = input("입력: ")
        if cmd == '1':
            # 휠체어 + 사람 동시 감지 메시지를 발행한다.
            client.publish(TOPIC_DETECTED, "true")
            print(f"📤 발행됨: {TOPIC_DETECTED} → true")
        elif cmd == '3':
            print("📷 카메라 상태 확인 (시뮬레이션)")
        elif cmd.lower() == 'q':
            print("👋 프로그램 종료됨")
            break
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n👋 사용자에 의해 종료됨")
except Exception as e:
    print(f"❗ 오류 발생: {e}")
finally:
    client.loop_stop()
    client.disconnect()
    print("🔒 MQTT 연결 종료 완료")