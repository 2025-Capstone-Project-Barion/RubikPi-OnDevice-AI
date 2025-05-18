import cv2
import numpy as np
from tflite_runtime.interpreter import Interpreter

# ========================
# 1. Quantized TFLite 모델 로드
# ========================
interpreter = Interpreter(model_path="wheelChair_YOLOv8-Detection-Quantized.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("📥 입력 텐서 정보:", input_details[0])
print("📤 출력 텐서 정보:", output_details[0])

# ========================
# 2. 이미지 전처리 함수 정의
# - 이미지 로드 및 리사이징
# - RGB 변환, 정규화 후 양자화 적용
# - 모델 입력 텐서로 변환
# ========================
def preprocess_image(image_path, input_shape=(640, 640)):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
    print(f"🖼️ 입력 이미지 크기: {image.shape}")

    image_resized = cv2.resize(image, input_shape)
    image_rgb = cv2.cvtColor(image_resized, cv2.COLOR_BGR2RGB)
    image_normalized = image_rgb.astype(np.float32) / 255.0

    scale, zero_point = input_details[0]['quantization']
    print(f"🧮 입력 quantization scale={scale}, zero_point={zero_point}")
    image_quantized = image_normalized / scale + zero_point
    image_quantized = np.clip(image_quantized, -128, 127).astype(np.int8)

    print("🔎 입력 텐서 min/max:", image_quantized.min(), image_quantized.max())
    input_tensor = np.expand_dims(np.transpose(image_quantized, (2, 0, 1)), axis=0)
    return image, input_tensor

# ========================
# 3. IoU (Intersection over Union) 계산 함수
# - 두 바운딩 박스의 겹치는 정도 계산
# ========================
def iou(box1, box2):
    x1, y1, x2, y2 = box1
    x1_p, y1_p, x2_p, y2_p = box2

    inter_x1 = max(x1, x1_p)
    inter_y1 = max(y1, y1_p)
    inter_x2 = min(x2, x2_p)
    inter_y2 = min(y2, y2_p)

    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    box1_area = (x2 - x1) * (y2 - y1)
    box2_area = (x2_p - x1_p) * (y2_p - y1_p)
    union = box1_area + box2_area - inter_area

    return inter_area / union if union != 0 else 0

# ========================
# 4. NMS (Non-Max Suppression) 적용 함수
# - 높은 confidence 값을 가진 박스만 남기고 중복 제거
# ========================
def nms(boxes, iou_thresh=0.5):
    boxes = sorted(boxes, key=lambda x: x[4], reverse=True)
    selected = []

    while boxes:
        current = boxes.pop(0)
        selected.append(current)
        boxes = [b for b in boxes if iou(current[:4], b[:4]) < iou_thresh]

    return selected

# ========================
# 5. 후처리 함수
# - 출력 텐서 디퀀타이즈
# - confidence 기반 필터링
# - bounding box 계산
# - NMS 적용 후 최종 박스 시각화
# ========================
def postprocess(output_data, image, conf_threshold=0.4):
    output = output_data[0]  # (1, 5, 8400)
    print("📤 출력 shape:", output.shape)
    scale, zero_point = output_details[0]['quantization']
    print(f"📐 출력 quantization scale={scale}, zero_point={zero_point}")

    output = (output.astype(np.float32) - zero_point) * scale
    output = np.transpose(output[0])  # (8400, 5)

    conf_values = output[:, 4]
    print(f"📊 confidence 값 통계: min={conf_values.min():.4f}, max={conf_values.max():.4f}, avg={conf_values.mean():.4f}")
    print("📋 상위 10개 confidence:", np.sort(conf_values)[-10:])

    h, w, _ = image.shape
    boxes = []

    for det in output:
        x_c, y_c, box_w, box_h, conf = det
        if conf < conf_threshold:
            continue

        x1 = int((x_c - box_w / 2) * w)
        y1 = int((y_c - box_h / 2) * h)
        x2 = int((x_c + box_w / 2) * w)
        y2 = int((y_c + box_h / 2) * h)
        boxes.append((x1, y1, x2, y2, conf))

    if not boxes:
        print("❌ 탐지 결과 없음")
        return image

    # NMS 적용
    boxes = nms(boxes, iou_thresh=0.5)
    print(f"✅ NMS 이후 최종 박스 개수: {len(boxes)}")

    for x1, y1, x2, y2, conf in boxes:
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"people_wheelchair {conf:.2f}"
        cv2.putText(image, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        print(f"🟢 탐지됨: people_wheelchair (신뢰도: {conf:.2f})")

    return image

# ========================
# 6. 메인 실행 코드
# - 이미지 불러오기 → 전처리 → 추론 → 후처리
# ========================
if __name__ == "__main__":
    image_path = "calib_images/1.jpg"
    orig_image, input_tensor = preprocess_image(image_path)

    interpreter.set_tensor(input_details[0]['index'], input_tensor)
    interpreter.invoke()
    output_data = [interpreter.get_tensor(out['index']) for out in output_details]

    output_image = postprocess(output_data, orig_image)
    cv2.imwrite("images/Output/output_tflite_detected.jpg", output_image)
    print("✅ 결과 저장됨: images/Output/output_tflite_detected.jpg")
