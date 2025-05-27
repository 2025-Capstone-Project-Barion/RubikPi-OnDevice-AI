# RubikPi-OnDevice-AI

## 프로젝트 개요

본 프로젝트는 Qualcomm과의 산학협력으로 진행된 스마트 배리어프리 키오스크 플랫폼 내 On-Device AI 객체탐지 시스템 구현을 목적으로 합니다. Qualcomm QCS6490 칩셋 기반의 RubikPi 보드를 활용하여 YOLOv8 모델을 Qualcomm Intelligent Multimedia Software Development Kit(QIM SDK) 및 Neural Processing Unit(NPU)을 이용해 최적화하고, 휠체어와 사람을 실시간으로 탐지하여 시리얼 통신 및 MQTT 메시지 송신을 수행합니다.

------

## 시스템 구성 흐름

```plaintext
[카메라 입력]
     │  qtiqmmfsrc
     ▼
[포맷 변환 / 리사이징]
     │  qtivtransform
     ▼
[두 갈래로 분기] ← tee
 ┌───────────────┐                 ┌─────────────────────────────┐
 │               ▼                 ▼                             │
 │   [YOLOv8 객체 탐지]        [메타데이터 오버레이]              │
 │ qtimlvconverter          qtimetamux (YOLO 메타 병합)        │
 │ qtimltflite              qtioverlay                         │
 │ qtimlvdetection          waylandsink (화면 출력)            │
 │       │                                                      │
 └───→ appsink (메타데이터를 별도 Python 프로그램에서 처리) ←───┘
```

------

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
qtimltflite delegate=external \
external-delegate-path=libQnnTFLiteDelegate.so \
external-delegate-options="QNNExternalDelegate,backend_type=htp;" \
model=/opt/RUBIKPi_models/YOLOv8-Detection-Quantized.tflite !
qtimlvdetection threshold=50.0 results=10 module=yolov8 \
labels=/opt/RUBIKPi_models/custom.labels \
constants="YOLOv8,q-offsets=<21.0,0.0,0.0>,q-scales=<3.0935,0.00390625,1.0>;" !
tee name=detection_tee

# 추론 결과 수신
detection_tee. ! queue ! text/x-raw,format=utf8 ! appsink name=meta_sink emit-signals=true

# 메타데이터를 overlay와 mux에 전달
detection_tee. ! queue ! text/x-raw,format=utf8 ! meta_mux.
```

------

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

------

## 주요 기능

- Qualcomm AI Hub 기반의 양자화(Quantized) YOLOv8 모델 최적화
- QIM SDK를 활용한 GStreamer 기반 실시간 객체 탐지 및 메타데이터 처리
- 휠체어와 사람 동시 탐지 시, 시리얼 및 MQTT 기반 메시지 송수신
- RaspberryPi 기반 키오스크 시스템과의 안정적인 MQTT 메시지 교환

------

## AI 모델 성능 분석 및 비교 (Qualcomm AI Hub 프로파일링 결과)

본 프로젝트에서는 Qualcomm AI Hub를 통해 float32 기반과 INT8 양자화 모델을 프로파일링하고 성능 분석을 진행하였습니다.

| 항목               | Float32 모델  | INT8 양자화 모델 | 성능 개선         |
| ------------------ | ------------- | ---------------- | ----------------- |
| **최소 추론 시간** | 64.8 ms       | 4.6 ms           | 약 14배 성능 향상 |
| **평균 추론 시간** | 83.8 ms       | 7.0 ms           | 약 12배 성능 향상 |
| **메모리 사용량**  | 9~52 MB       | 0~29 MB          | 최대 44% 절감     |
| **주요 연산 장치** | GPU(455 중심) | NPU(278 중심)    | 전력 효율 개선    |

- 모델 입력 크기: `(1, 640, 640, 3)`
- 타겟 디바이스: `Qualcomm QCS6490 (RubikPi)`
- 프로파일링 도구: `Qualcomm AI Hub`

이러한 AI모델 최적화는 모델 성능과 전력 효율성을 크게 향상시키기에 RubikPi와 같은 On-Device Ai IOT디바이스에 매우 적합하고, 실시간 객체 탐지가 필수적인 스마트 배리어프리 키오스크 플랫폼에 매우 적합하다.

------

## 결론

본 시스템은 Qualcomm의 QCS6490 칩셋기반의 RubikPi IOT보드와 Qualcomm AI Hub를 활용한 YOLOv8 모델 최적화 기술을 적용하여,  
실시간으로 정확하고 효율적인 객체 탐지 시스템을 구축하였다.  
이는 앞으로 우리가 진행한 스마트 배리어프리 키오스크 플렛폼과 같은 사용자의 접근성과 사용자 경험의 개선이 요구되는 여러 분야에 크게 기여할 것으로 기대가 된다. 
