### 1. `main_rubikpi.py`

- **역할**: 전체 흐름을 제어하는 **메인 컨트롤러**
- **실행 방식**: **한 번만 실행** 후, 전시 5시간 내내 **계속 실행 유지**
- **동작**:
  - MQTT 메시지 수신 (START / CLOSE / DETECTED / PAY)
  - 메시지에 따라 **서브프로세스를 실행하거나 종료**
- 📌 **절대 중단되면 안 됨**

------

### 2. `camera_yolo_runner.py`

- **역할**: YOLO 모델을 사용한 **카메라 실시간 감지** (사람 + 휠체어)
- **실행 방식**:
  - `main_rubikpi.py`에 의해 **START 신호 받을 때마다 subprocess로 실행됨**
  - 감지 종료 시(CLOSE 메시지) → **subprocess 종료됨**
- 📌 YOLO는 리소스를 많이 쓰므로 **필요할 때만 켜고 끔**

------

### 3. `actuator_serial_runner.py`

- **역할**: 아두이노에 시리얼 명령(UP / DOWN)을 **단발성으로 전달**
- **실행 방식**:
  - `main_rubikpi.py`가 `run_actuator("UP")` 또는 `"DOWN"`을 호출할 때마다
  - `subprocess.call(["python3", "actuator_serial_runner.py", "UP"])` 같은 식으로
  - **1회 실행되고 자동 종료됨**
- 📌 **항상 짧게 실행되는 단발성 도우미 스크립트**

------

### 전체 구조 요약

| 파일명                      | 실행 방식           | 실행 시기                            | 종료 시기            |
| --------------------------- | ------------------- | ------------------------------------ | -------------------- |
| `main_rubikpi.py`           | 1회 실행, 계속 유지 | 전시 시작 시                         | 수동 종료 (Ctrl+C)   |
| `camera_yolo_runner.py`     | 필요 시 실행        | START 수신 시                        | CLOSE 수신 시        |
| `actuator_serial_runner.py` | 단발성 실행         | 감지 성공(→DOWN) 또는 결제 완료(→UP) | 약 15초 후 자동 종료 |