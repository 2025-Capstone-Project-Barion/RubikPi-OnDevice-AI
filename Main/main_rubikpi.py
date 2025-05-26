import paho.mqtt.client as mqtt
import serial
import time
import threading
from serial.tools import list_ports
import subprocess

# ✅ MQTT 브로커 연결 설정을 정의한다.
broker_address = "192.168.137.229"  # 라즈베리파이 Mosquitto 브로커 IP
port = 1883                         # 기본 MQTT TCP 포트(1883)

# ✅ 사용하는 MQTT 토픽명을 정의한다.
TOPIC_START    = "kiosk-start"               # 키오스크 시작(웨이크워드)
TOPIC_CLOSE    = "kiosk-close"               # 메뉴 진입 시 감지 종료
TOPIC_PAY      = "payment-done"              # 결제 완료 시
TOPIC_DETECTED = "chair-person-detected"     # 카메라 서브의 탐지 메시지

# ✅ 카메라 활성 상태 플래그와 락, 프로세스 핸들을 정의한다.
is_camera_active = False
camera_lock      = threading.Lock()
camera_proc      = None

# ✅ 휠체어 감지 후 리니어 수축 여부를 추적하는 플래그
has_retracted = False

# ✅ 전역 시리얼 객체 (메인에서 한 번만 연다)
ser = None

def find_arduino_port():
    """
    🔍 연결된 Arduino의 시리얼 포트를 자동 탐지한다.
    """
    ports = list_ports.comports()
    for p in ports:
        if "Arduino" in p.description or "ttyACM" in p.device:
            return p.device
    return None

def init_serial():
    """
    🔌 Arduino 시리얼 포트를 한 번만 열어두고 유지한다.
    """
    global ser
    port = find_arduino_port()
    if not port:
        raise RuntimeError("❌ Arduino 포트를 찾을 수 없습니다.")
    print(f"🔌 아두이노 연결됨: {port}")
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)  # 시리얼 초기화 대기  

def send_command(cmd: str):
    """
    📤 한 번 열린 시리얼 포트로 UP/DOWN 명령을 전송한다.
    """
    if ser is None or not ser.is_open:
        print("❗ 시리얼 포트가 열려있지 않습니다.")
        return
    ser.write(f"{cmd}\n".encode())  # ✅ 개행문자 반드시 포함
    print(f"📤 Arduino로 '{cmd}' 명령 전송됨")

def start_camera_yolo():
    """
    🎬 카메라+YOLO 서브프로그램을 백그라운드로 실행한다.
    """
    global is_camera_active, camera_proc
    with camera_lock:
        if is_camera_active:
            print("⚠️ 카메라 감지가 이미 실행 중입니다. 무시합니다.")
            return
        print("▶ YOLO 카메라 감지 서브 시작")
        camera_proc = subprocess.Popen(["python3", "camera_yolo_runner.py"])
        is_camera_active = True

def stop_camera_yolo():
    """
    📴 실행 중인 카메라+YOLO 서브프로그램을 안전히 종료한다.
    """
    global is_camera_active, camera_proc
    with camera_lock:
        if not is_camera_active:
            print("⚠️ 카메라 감지가 이미 종료되었습니다. 무시합니다.")
            return
        print("▶ YOLO 카메라 감지 서브 종료 요청")
        camera_proc.terminate()
        camera_proc.wait()
        camera_proc = None
        is_camera_active = False

def on_message(client, userdata, msg):
    """
    📩 MQTT 메시지 수신 콜백.
    각 토픽에 맞춰 카메라/액추에이터 제어를 실행한다.
    """
    global has_retracted
    topic   = msg.topic
    payload = msg.payload.decode()
    print(f"[MQTT RX] {topic} → {payload}")

    if topic == TOPIC_START and payload == "activate":
        # 키오스크 시작 → 카메라+YOLO 감지 서브 실행
        start_camera_yolo()

    elif topic == TOPIC_CLOSE and payload == "close":
        # 메뉴 진입 → 카메라+YOLO 감지 서브 종료
        stop_camera_yolo()

    elif topic == TOPIC_DETECTED and payload == "true":
        # 카메라 탐지 성공 → 리니어 수축(DOWN)
        send_command("DOWN")
        has_retracted = True  # 수축 완료 플래그 설정

    elif topic == TOPIC_PAY and payload == "complete":
        # 결제 완료 → 수축된 상태에서만 복귀(UP)
        if has_retracted:
            send_command("UP")
            has_retracted = False  # 플래그 리셋
        else:
            print("ℹ️ 휠체어 미탑승: UP 명령 무시")

def on_connect(client, userdata, flags, rc):
    """
    🔌 MQTT 브로커 연결 콜백.
    연결 시 네 개의 토픽을 모두 구독한다.
    """
    if rc == 0:
        print("✅ MQTT 브로커 연결 성공")
        client.subscribe(TOPIC_START)
        client.subscribe(TOPIC_CLOSE)
        client.subscribe(TOPIC_DETECTED)
        client.subscribe(TOPIC_PAY)
    else:
        print(f"❌ MQTT 브로커 연결 실패 (코드 {rc})")

if __name__ == "__main__":
    try:
        # 1) 아두이노 시리얼 초기화 (한 번만)
        init_serial()

        # 2) MQTT 클라이언트 생성 및 콜백 등록
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        # 3) MQTT 연결 및 루프 시작
        print(f"🔌 MQTT 브로커({broker_address}:{port}) 연결 시도...")
        client.connect(broker_address, port, 60)
        client.loop_start()

        print("▶ RubikPi 메인 서비스 실행 중 (Ctrl+C로 종료) ")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 서비스 종료 요청 받음")
        stop_camera_yolo()

    finally:
        # 종료 처리
        client.loop_stop()
        client.disconnect()
        if ser and ser.is_open:
            ser.close()
        print("🔒 모든 연결 종료, 서비스 종료")
