import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

Gst.init(None)

def on_new_sample(sink, data):
    sample = sink.emit("pull-sample")
    if sample:
        buf = sample.get_buffer()
        result, mapinfo = buf.map(Gst.MapFlags.READ)
        if result:
            try:
                metadata = mapinfo.data.decode("utf-8").strip()
                if "ObjectDetection" in metadata:
                    has_chair = "label\\=\\(string\\)wheelchair" in metadata
                    has_person = "label\\=\\(string\\)person" in metadata
                    if has_chair and has_person:
                        print("🟢 의자+사람 동시에 감지됨!")
                        print(metadata)
            except Exception as e:
                print("❌ 디코딩 실패:", e)
        buf.unmap(mapinfo)
    return Gst.FlowReturn.OK

pipeline_str = """
qtiqmmfsrc camera=0 !
video/x-raw(memory:GBM),format=NV12,width=1280,height=720,framerate=30/1 !
qtivtransform !
qtimlvconverter !
qtimltflite delegate=external
external-delegate-path=libQnnTFLiteDelegate.so
external-delegate-options="QNNExternalDelegate,backend_type=htp;"
model=/opt/RUBIKPi_models/YOLOv8-Detection-Quantized.tflite !
qtimlvdetection threshold=40.0 results=10 module=yolov8
labels=/opt/RUBIKPi_models/custom.labels
constants="YOLOv8,q-offsets=<21.0, 0.0, 0.0>,q-scales=<3.0935,0.00390625,1.0>;" !
text/x-raw,format=utf8 !
appsink name=meta_sink emit-signals=true
"""

def main():
    pipeline = Gst.parse_launch(pipeline_str)
    appsink = pipeline.get_by_name("meta_sink")
    appsink.connect("new-sample", on_new_sample, None)

    pipeline.set_state(Gst.State.PLAYING)
    print("📡 YOLO 메타데이터 수집 시작...")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("🛑 종료 요청")
        pipeline.set_state(Gst.State.NULL)

if __name__ == "__main__":
    main()