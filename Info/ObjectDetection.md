# Barion YOLOv8 객체 탐지 시연 구성

## 목적
Barion은 On-Device AI 기반 배리어프리 키오스크 플랫폼이다.  
이 시스템은 휠체어 이용자의 접근을 실시간으로 감지하고 자동 응답하는 것을 목표로 한다.

## 배경 및 기준

시연에 사용하는 YOLOv8-Detection-Quantized.tflite 모델은 COCO 데이터셋 기반으로 학습돼 있다.  
기본적으로 `chair`, `bicycle`, `motorcycle`과 같은 클래스들을 감지할 수 있다.

하지만 실제 시연 환경에서는 단순한 휠체어 외에도 다양한 유형의 이동 보조기구가 등장한다:

- 전동 휠체어 (모터가 달린 형태)
- 수동 휠체어 (의자 구조)
- 전기자전거 형태의 개인형 이동장치

이처럼 외형은 다르지만 **기능적으로 동일한 탈것들**을 하나의 개념으로 인식하는 게 적절하다고 판단했다.  
따라서 이 프로젝트에서는 위 3가지 클래스를 **모두 `"wheelchair"`로 통합**해 시각화하고 처리한다.

## 적용 방식

### 모델
- 사용 모델: `YOLOv8-Detection-Quantized.tflite`
- 라벨 파일: `/opt/RUBIKPi_models/custom.labels`

### custom.labels 내용

```plaintext
(structure)"person,id=(guint)0x0,color=(guint)0x00FF00FF;"
(structure)"wheelchair,id=(guint)0x1,color=(guint)0x00FF00FF;"   # bicycle
(structure)"wheelchair,id=(guint)0x3,color=(guint)0x00FF00FF;"   # motorcycle
(structure)"wheelchair,id=(guint)0x38,color=(guint)0x00FF00FF;"  # chair
