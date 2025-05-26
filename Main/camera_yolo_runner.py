import gi
import paho.mqtt.client as mqtt
from gi.repository import Gst, GLib

# ✅ GStreamer 및 MQTT 초기화
gi.require_version('Gst', '1.0')
Gst.init(None)

MQTT_BROKER     = "192.168.137.229"
TOPIC_DETECTED  = "chair-person-detected"

client = mqtt.Client()
client.connect(MQTT_BROKER, 1883, 60)
client.loop_start()

# ✅ 감지 플래그 (중복 방지)
is_detected = False

def on_new_sample(sink, data):
    global is_detected
    sample = sink.emit("pull-sample")
    if sample:
        buf = sample.get_buffer()
        ok, info = buf.map(Gst.MapFlags.READ)
        if ok:
            try:
                meta = info.data.decode('utf-8').strip()
                if "ObjectDetection" in meta:
                    has_wheelchair = "label\\=\\(string\\)wheelchair" in meta
                    has_person     = "label\\=\\(string\\)person" in meta
                    if has_wheelchair and has_person:
                        if not is_detected:
                            print("🟢 wheelchair + person 감지됨 → MQTT 발행")
                            client.publish(TOPIC_DETECTED, "true")
                            is_detected = True
                        else:
                            print("⚠️ 이미 감지됨 → MQTT 중복 생략")
            except Exception as e:
                print("❌ 메타데이터 디코딩 오류:", e)
        buf.unmap(info)
    return Gst.FlowReturn.OK

# ✅ 최적화된 GStreamer 파이프라인 설정
pipeline_str = """
qtiqmmfsrc camera=0 !
video/x-raw(memory:GBM),format=NV12,width=640,height=480,framerate=15/1 !
qtivtransform !
qtimlvconverter !
qtimltflite delegate=external
external-delegate-path=libQnnTFLiteDelegate.so
external-delegate-options="QNNExternalDelegate,backend_type=htp;"
model=/opt/RUBIKPi_models/YOLOv8-Detection-Quantized.tflite !
qtimlvdetection threshold=70.0 results=10 module=yolov8
labels=/opt/RUBIKPi_models/custom.labels
constants="YOLOv8,q-offsets=<21.0, 0.0, 0.0>,q-scales=<3.0935,0.00390625,1.0>;" !
text/x-raw,format=utf8 !
appsink name=meta_sink emit-signals=true
"""

def main():
    print("🚀 파이프라인 생성 시도")
    pipeline = Gst.parse_launch(pipeline_str)

    sink = pipeline.get_by_name("meta_sink")
    sink.connect("new-sample", on_new_sample, None)

    pipeline.set_state(Gst.State.PLAYING)
    print("📡 YOLO 실시간 감지 및 메타 수집 시작...")

    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("🛑 감지 서브프로그램 종료 요청됨")
    finally:
        pipeline.set_state(Gst.State.NULL)
        client.loop_stop()
        print("🔒 리소스 정리 완료")

if __name__ == "__main__":
    main()
