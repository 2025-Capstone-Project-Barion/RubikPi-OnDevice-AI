import cv2
import subprocess
import sys

# 사용 가능한 카메라 장치 확인
def check_camera_devices():
    try:
        result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        print("사용 가능한 카메라 장치:")
        print(result.stdout)
        return True
    except Exception as e:
        print(f"카메라 장치 확인 중 오류: {e}")
        return False

# GStreamer 버전 확인
def check_gstreamer():
    try:
        result = subprocess.run(['gst-inspect-1.0', '--version'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        print("GStreamer 버전 정보:")
        print(result.stdout)
        return True
    except Exception as e:
        print(f"GStreamer 확인 중 오류: {e}")
        return False

# 기본 진단 실행
check_camera_devices()
check_gstreamer()

# 다양한 GStreamer 파이프라인 시도
pipelines = [
    # 원래 파이프라인
    "qtiqmmfsrc camera=0 ! video/x-raw(memory:GBM),format=NV12,width=640,height=480,framerate=30/1 ! videoconvert ! video/x-raw,format=BGR ! appsink",
    
    # GBM 메모리 형식 없이 시도
    "qtiqmmfsrc camera=0 ! video/x-raw,format=NV12,width=640,height=480,framerate=30/1 ! videoconvert ! video/x-raw,format=BGR ! appsink",
    
    # 카메라 1로 시도
    "qtiqmmfsrc camera=1 ! video/x-raw(memory:GBM),format=NV12,width=640,height=480,framerate=30/1 ! videoconvert ! video/x-raw,format=BGR ! appsink",
    
    # 더 간단한 파이프라인
    "qtiqmmfsrc camera=0 ! videoconvert ! appsink"
]

# 각 파이프라인 시도
success = False
for i, pipeline in enumerate(pipelines):
    print(f"\n파이프라인 {i+1} 시도: {pipeline}")
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    
    if cap.isOpened():
        print("카메라가 성공적으로 열렸습니다!")
        success = True
        
        # 테스트 프레임 캡처
        ret, frame = cap.read()
        if ret:
            print(f"프레임 크기: {frame.shape}")
            # 테스트 이미지 저장
            cv2.imwrite('test_frame.jpg', frame)
            print("테스트 프레임이 'test_frame.jpg'로 저장되었습니다.")
        else:
            print("프레임을 읽을 수 없습니다.")
            
        cap.release()
        break
    else:
        print("이 파이프라인으로는 카메라를 열 수 없습니다.")
        cap.release()

if not success:
    print("\n모든 파이프라인이 실패했습니다. 다른 접근 방식이 필요합니다.")
    sys.exit(1)

print("\n성공한 파이프라인으로 계속 진행합니다...")

# 성공한 파이프라인으로 실제 처리 수행
cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임을 읽을 수 없습니다.")
            break

        # 이미지 표시 (SSH X11 포워딩이 설정된 경우) 
        cv2.imshow('Camera', frame)
        
        # 'q' 키를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("사용자에 의해 중단되었습니다.")
finally:
    cap.release()
    cv2.destroyAllWindows()