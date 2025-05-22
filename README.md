# RubikPi-OnDevice-AI

## 프로젝트 개요
본 시스템은 스마트 배리어프리 키오스크 플랫폼에서 On-Device AI 기반 객체탐지를 수행하는 RubikPi (Qualcomm QCS6490 기반 보드) 관련 레포지토리이다.  
RubikPi는 연결된 카메라로부터 실시간 영상을 수신하고, Qualcomm intelligent multimedia software development kit (QIM SDK)를 활용한 YOLOv8 기반 객체 탐지를 수행하여, 사람과 휠체어가 동시에 탐지되었을 때 시리얼 및 MQTT 신호를 송-수신한다.

<br>

## 시스템 구성 흐름

```
[카메라 입력]
     │  qtiqmmfsrc
     ▼
[포맷 변환 / 리사이징]
     │  qtivtransform
     ▼
[두 갈래로 분기] ← tee
 ┌────────────┐                  ┌──────────────────────────────────────┐
 │            ▼                  ▼                                      │
 │  [YOLO 추론 수행]         [메타데이터 오버레이]                      │
 │    qtimlvconverter         qtimetamux ← YOLO 결과 메타 합침         │
 │    qtimltflite             qtioverlay                                │
 │    qtimlvdetection         waylandsink ← 최종 화면 출력             │
 │            │                                                       │
 └──→ appsink  ← 텍스트 메타데이터만 따로 파이썬에서 받아오기 ←───────┘
```

<br>

## GStreamer 파이프라인

```bash
qtiqmmfsrc camera=0 !
video/x-raw(memory:GBM),format=NV12,width=1280,height=720,framerate=30/1 !
qtivtransform ! tee name=t

# 영상 출력 브랜치
t. ! queue ! qtivtransform ! qtimetamux name=meta_mux !
qtioverlay ! waylandsink fullscreen=true

# 추론 브랜치
t. ! queue ! qtivtransform ! qtimlvconverter !
qtimltflite delegate=external
external-delegate-path=libQnnTFLiteDelegate.so
external-delegate-options="QNNExternalDelegate,backend_type=htp;"
model=/opt/RUBIKPi_models/YOLOv8-Detection-Quantized.tflite !
qtimlvdetection threshold=50.0 results=10 module=yolov8
labels=/opt/RUBIKPi_models/custom.labels
constants="YOLOv8,q-offsets=<21.0,0.0,0.0>,q-scales=<3.0935,0.00390625,1.0>;" !
tee name=detection_tee

# 추론 결과 수신
detection_tee. ! queue ! text/x-raw,format=utf8 ! appsink name=meta_sink emit-signals=true

# 메타데이터를 overlay와 mux에 전달
detection_tee. ! queue ! text/x-raw,format=utf8 ! meta_mux.
```

<br>

## GStreamer 플러그인 설명 (QIM SDK 기반)

| 플러그인          | 설명                                        |
| ----------------- | ------------------------------------------- |
| `qtiqmmfsrc`      | 카메라 소스 입력 (Qualcomm 전용 MIPI)       |
| `qtivtransform`   | 프레임 포맷/크기 변환 및 전처리             |
| `tee`             | 추론 및 디스플레이 경로로 분기              |
| `qtimlvconverter` | ML 모델 입력 형식으로 변환                  |
| `qtimltflite`     | TFLite 양자화 모델 실행 (QNN Delegate 사용) |
| `qtimlvdetection` | YOLOv8 출력 후처리 및 메타 생성             |
| `qtimetamux`      | 메타데이터를 영상 프레임에 합성             |
| `qtioverlay`      | 탐지 결과를 화면에 시각화                   |
| `appsink`         | 파이썬에서 메타데이터를 수신 처리           |

<br>

## 주요 기능

- Qualcomm Ai Hub에서 Compile & Qunatized를 거친 Quantized YOLOv8 기반 실시간 객체 탐지  
- GStreamer 기반 영상 출력 및 메타데이터 추출  
- 휠체어 + 사람 동시 탐지 시 시리얼 통신 송신  
- 키오스크 제어를 담당하는 RaspberryPi에 MQTT 메시지 송신  
