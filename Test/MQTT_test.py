import paho.mqtt.client as mqtt
import time
import threading

# MQTT 설정
broker_address = "61.74.20.97"  # Windows PC의 IP 주소
port = 9001  # WebSocket 포트 
client_id = f"rubikpi_test_{int(time.time())}"

# 키오스크 토픽
DETECTED_TOPIC = "barion/kiosk/detected"
START_TOPIC = "barion/kiosk/start"
CLOSE_TOPIC = "barion/kiosk/closeDetection"
PAYMENT_TOPIC = "barion/kiosk/paymentFinish"

# 실제 하드웨어 제어를 시뮬레이션하는 함수들
def simulate_camera_activation():
    print("🎬 YOLO 카메라 활성화 시뮬레이션 - 사용자/휠체어 감지 시작")
    # 실제로는 여기에 YOLO 관련 코드 연결

def simulate_camera_deactivation():
    print("📴 YOLO 카메라 비활성화 시뮬레이션 - 감지 종료")
    # 실제로는 여기에 YOLO 중지 코드 연결

def simulate_actuator_up():
    print("⬆️ 리니어 액추에이터 상승 시뮬레이션")
    # 실제로는 여기에 액추에이터 제어 코드 연결

# 자동 휠체어 감지 시뮬레이션 (데모용)
def wheelchair_detection_simulation(client):
    while True:
        time.sleep(30)  # 30초마다 자동 감지 (테스트용, 실제로는 YOLO에서 감지)
        simulate_wheelchair_detection(client)

def simulate_wheelchair_detection(client):
    print("\n🦽 [자동 감지] 휠체어 사용자 감지됨!")
    client.publish(DETECTED_TOPIC, "wheelchair")
    print(f"발행: {DETECTED_TOPIC} -> wheelchair")

# 메시지 수신 콜백 - 실제 동작 추가
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"📩 수신: {topic} -> {payload}")
    
    # 토픽별 처리
    if topic == START_TOPIC and payload == "activate":
        print("👂 음성 웨이크워드('헤이 베리온') 감지됨")
        simulate_camera_activation()
        
    elif topic == CLOSE_TOPIC and payload == "close":
        print("🚪 메뉴 페이지로 이동 - YOLO 감지 종료")
        simulate_camera_deactivation()
        
    elif topic == PAYMENT_TOPIC and payload == "complete":
        print("💰 결제 완료 - 리니어 액추에이터 상승 신호")
        simulate_actuator_up()

# 연결 콜백
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ 브로커 연결 성공: {broker_address}")
        # 키오스크가 보내는 메시지 수신을 위해 구독
        client.subscribe(START_TOPIC)
        print(f"✅ '{START_TOPIC}' 구독 완료")
        
        client.subscribe(CLOSE_TOPIC)
        print(f"✅ '{CLOSE_TOPIC}' 구독 완료")
        
        client.subscribe(PAYMENT_TOPIC)
        print(f"✅ '{PAYMENT_TOPIC}' 구독 완료")
    else:
        print(f"❌ 연결 실패, 코드: {rc}")

# MQTT 클라이언트 설정
client = mqtt.Client(client_id=client_id, transport="websockets")
client.on_connect = on_connect
client.on_message = on_message

try:
    # 브로커 연결
    print(f"🔄 MQTT 브로커 연결 중... {broker_address}:{port}")
    client.connect(broker_address, port, 60)
    
    # 메시지 처리 스레드 시작
    client.loop_start()
    
    # 자동 감지 시뮬레이션 시작 (테스트용, 필요 없으면 제거)
    # detection_thread = threading.Thread(target=wheelchair_detection_simulation, args=(client,))
    # detection_thread.daemon = True
    # detection_thread.start()
    
    print("\n=== 테스트 명령어 ===")
    print("1: 휠체어 감지 메시지 발행")
    print("2: 일반 사용자 감지 메시지 발행")
    print("3: 카메라 활성화 상태 확인")
    print("q: 종료")
    
    # 메인 루프
    while True:
        cmd = input("\n명령 입력: ")
        
        if cmd == '1':
            # 휠체어 감지 메시지
            client.publish(DETECTED_TOPIC, "wheelchair")
            print(f"📤 발행: {DETECTED_TOPIC} -> wheelchair")
            
        elif cmd == '2':
            # 일반 사용자 감지
            client.publish(DETECTED_TOPIC, "user")
            print(f"📤 발행: {DETECTED_TOPIC} -> user")
            
        elif cmd == '3':
            print("📷 카메라 상태 확인 (시뮬레이션)")
            
        elif cmd.lower() == 'q':
            print("👋 프로그램 종료")
            break
            
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print("\n👋 사용자에 의해 종료됨")
except Exception as e:
    print(f"❌ 오류 발생: {e}")
finally:
    # 연결 종료
    client.loop_stop()
    client.disconnect()