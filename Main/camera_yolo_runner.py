import gi
import paho.mqtt.client as mqtt
from gi.repository import Gst, GLib

# ✅ GStreamer 및 MQTT 초기화
gi.require_version('Gst', '1.0')
Gst.init(None)

MQTT_BROKER     = "61.74.20.97"
TOPIC_DETECTED  = "chair-person-detected"

client = mqtt.Client()
client.connect(MQTT_BROKER, 1883, 60)
client.loop_start()

def on_new_sample(sink, data):
    sample = sink.emit("pull-sample")
    if sample:
        buf = sample.get_buffer()
        ok, info = buf.map(Gst.MapFlags.READ)
        if ok:
            try:
                meta = info.data.decode('utf-8').strip()
                if "ObjectDetection" in meta:
                    has_chair  = "label\\=\\(string\\)chair" in meta
                    has_person = "label\\=\\(string\\)person" in meta
                    if has_chair and has_person:
                        print("🟢 의자+사람 동시 감지! → MQTT 발행")
                        client.publish(TOPIC_DETECTED, "true")
            except Exception as e:
                print("❌ 메타데이터 처리 실패:", e)
        buf.unmap(info)
    return Gst.FlowReturn.OK

pipeline_str = """
qtiqmmfsrc camera=0 !
video/x-raw(memory:GBM),format=NV12,width=1280,height=720,framerate=30/1 !
qtivtransform !
qtimlvconverter !
qtimltflite delegate=external external-delegate-path=libQnnTFLiteDelegate.so external-delegate-options="QNNExternalDelegate,backend_type=htp;" !
model=/opt/RUBIKPi_models/YOLOv8-Detection-Quantized.tflite !
qtimlvdetection threshold=70.0 results=10 module=yolov8 labels=/opt/RUBIKPi_models/yolov8.labels constants="YOLOv8,q-offsets=<21.0, 0.0, 0.0>,q-scales=<3.0935,0.00390625,1.0>;" !
text/x-raw,format=utf8 !
appsink name=meta_sink emit-signals=true
"""


def main():
    pipeline = Gst.parse_launch(pipeline_str)
    sink = pipeline.get_by_name("meta_sink")
    sink.connect("new-sample", on_new_sample, None)

    pipeline.set_state(Gst.State.PLAYING)
    print("📡 YOLO 메타데이터 수집 시작...")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("🛑 감지 서브프로그램 종료 요청")
    finally:
        pipeline.set_state(Gst.State.NULL)
        client.loop_stop()

if __name__ == "__main__":
    main()
