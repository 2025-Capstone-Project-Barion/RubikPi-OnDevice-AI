import paho.mqtt.client as mqtt
import subprocess
import threading
import time

broker_address = "192.168.137.229"
port = 1883

TOPIC_START    = "kiosk-start"
TOPIC_CLOSE    = "kiosk-close"

is_camera_active = False
camera_lock = threading.Lock()
camera_proc = None

def start_camera_yolo():
    global is_camera_active, camera_proc
    with camera_lock:
        if is_camera_active:
            print("⚠️ 카메라 이미 실행 중")
            return
        print("▶ YOLO 서브프로그램 실행")
        camera_proc = subprocess.Popen(["python3", "camera_yolo_runner.py"])
        is_camera_active = True

def stop_camera_yolo():
    global is_camera_active, camera_proc
    with camera_lock:
        if not is_camera_active:
            print("⚠️ 카메라 이미 종료됨")
            return
        print("🛑 YOLO 서브프로그램 종료")
        camera_proc.terminate()
        camera_proc.wait()
        camera_proc = None
        is_camera_active = False

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"[MQTT RX] {topic} → {payload}")
    
    if topic == TOPIC_START and payload == "activate":
        start_camera_yolo()
    elif topic == TOPIC_CLOSE and payload == "close":
        stop_camera_yolo()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT 연결 성공")
        client.subscribe(TOPIC_START)
        client.subscribe(TOPIC_CLOSE)
    else:
        print(f"❌ 연결 실패: 코드 {rc}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

if __name__ == "__main__":
    try:
        print(f"🔌 MQTT 브로커({broker_address}:{port}) 연결 시도...")
        client.connect(broker_address, port, 60)
        client.loop_start()
        print("▶ RubikPi 메인 서비스 실행 중")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 종료 요청")
        stop_camera_yolo()
    finally:
        client.loop_stop()
        client.disconnect()
        print("🔒 MQTT 종료")
