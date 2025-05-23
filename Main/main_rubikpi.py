import paho.mqtt.client as mqtt
import subprocess
import threading
import time

# MQTT 브로커 연결 설정을 정의한다.
broker_address = "192.168.137.229"  # 라즈베리파이에서 실행 중인 Mosquitto 브로커의 IP 주소이다.
port = 1883                    # RubikPi에서는 기본 MQTT TCP 포트(1883)를 사용한다.

# 사용하는 MQTT 토픽명을 정의한다.
TOPIC_START    = "kiosk-start"               # 키오스크 시작(음성 웨이크워드) 메시지
TOPIC_CLOSE    = "kiosk-close"               # 메뉴 진입 시 감지 종료 메시지
TOPIC_PAY      = "payment-done"              # 결제 완료 시 메시지
TOPIC_DETECTED = "chair-person-detected"     # 폴백: camera_yolo_runner.py가 발행하는 감지 메시지

# 카메라 활성 상태 플래그와 락, 프로세스 핸들을 정의한다.
is_camera_active = False
camera_lock      = threading.Lock()
camera_proc      = None
has_retracted    = False   # 현재 휠체어가 감지되어 리니어 액추에이터가 수축된 상태인지를 추적

def start_camera_yolo():
    """
    🎬 카메라+YOLO 서브프로그램을 백그라운드로 실행한다.
    이미 실행 중이면 무시한다.
    """
    global is_camera_active, camera_proc
    with camera_lock:
        if is_camera_active:
            print("⚠️ 카메라 감지가 이미 실행 중이다. 중복 실행을 무시한다.")
            return
        print("▶ YOLO 카메라 감지 서브프로그램 시작")
        camera_proc = subprocess.Popen(["python3", "camera_yolo_runner.py"])
        is_camera_active = True

def stop_camera_yolo():
    """
    📴 실행 중인 카메라+YOLO 서브프로그램을 종료한다.
    이미 종료된 상태면 무시한다.
    """
    global is_camera_active, camera_proc
    with camera_lock:
        if not is_camera_active:
            print("⚠️ 카메라 감지가 이미 종료되었다.")
            return
        print("▶ YOLO 카메라 감지 서브프로그램 종료 요청")
        camera_proc.terminate()
        camera_proc.wait()
        camera_proc = None
        is_camera_active = False

def run_actuator(direction):
    """
    ↕️ 아두이노 제어 서브프로그램을 실행한다.
    direction: "DOWN" or "UP"
    """
    print(f"▶ 액추에이터 제어 서브프로그램 시작 → {direction}")
    subprocess.call(["python3", "actuator_serial_runner.py", direction])

def on_message(client, userdata, msg):
    """
    📩 MQTT 메시지 수신 콜백.
    각 토픽과 페이로드(payload)에 맞춰 동작을 분기 처리한다.
    """
    topic   = msg.topic
    payload = msg.payload.decode()
    print(f"[MQTT RX] {topic} → {payload}")

    if topic == TOPIC_START and payload == "activate":
        start_camera_yolo()
    elif topic == TOPIC_CLOSE and payload == "close":
        stop_camera_yolo()
    elif topic == TOPIC_DETECTED and payload == "true":
        # 감지가 성공되면 즉시 최소 길이로 리트랙트
        run_actuator("DOWN")
        has_retracted = True      # DOWN 명령 보냈음을 표시
    elif topic == TOPIC_PAY and payload == "complete":
        # (+ 이전에 휠체어가 탐지되어 내려가있는 상태라면)결제 완료 후에는 최대 길이로 익스텐드
        if has_retracted:
            run_actuator("UP")
            has_retracted = False  # UP(리니어 최대상승)후 플래그 리셋
        else:
            print("ℹ️ 휠체어 미탑승 상태: UP 명령 무시")

def on_connect(client, userdata, flags, rc):
    """
    🔌 MQTT 브로커 연결 콜백.
    연결되면 필요한 토픽들을 모두 구독(subscribe)한다.
    """
    if rc == 0:
        print("✅ MQTT 브로커 연결 성공")
        client.subscribe(TOPIC_START)
        client.subscribe(TOPIC_CLOSE)
        client.subscribe(TOPIC_DETECTED)
        client.subscribe(TOPIC_PAY)
    else:
        print(f"❌ MQTT 브로커 연결 실패, 코드: {rc}")

# ✅ MQTT 클라이언트 생성 및 콜백 함수 등록
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

if __name__ == "__main__":
    try:
        print(f"🔌 MQTT 브로커({broker_address}:{port}) 연결 시도...")
        client.connect(broker_address, port, 60)
        client.loop_start()

        print("▶ RubikPi 메인 서비스 실행 중. Ctrl+C로 종료.")
        # 메인 스레드 대기
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 서비스 종료 요청 받음")
        stop_camera_yolo()

    finally:
        client.loop_stop()
        client.disconnect()
        print("🔒 MQTT 연결 종료, RubikPi 메인 서비스 종료")
