# 이거 먼저 실행해서 카메라 테스팅
`
export XDG_RUNTIME_DIR=/dev/socket/weston  
export WAYLAND_DISPLAY=wayland-1  
setprop persist.overlay.use_c2d_blit 2  
gst-launch-1.0 -e qtiqmmfsrc camera=0 name=camsrc ! video/x-raw\(memory:GBM\),format=NV12,width=1920,height=1080,framerate=30/1,compression=ubwc ! queue ! waylandsink fullscreen=true async=true
`

# QIM으로 카메라 스트리밍 출력 & YOLOv8-Detection-Quantized.tflite기반 탐지
`
 gst-ai-object-detection -t 2 -f 2 -m /opt/RUBIKPi_models/YOLOv8-Detection-Quantized.tflite -l /opt/RUBIKPi_models/yolov8.labels -c "YOLOv8,q-offsets=<21.0, 0.0, 0.0>,q-scales=<3.093529462814331, 0.00390625, 1.0>;"
`

# 콘솔에 메타데이터 출력은되나, 해당 객체탐지시에만 출력이아닌 매 시간마다 출력되어 더러움
```
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
                if metadata:
                    print("📦 탐지 메타데이터:", metadata)
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
qtimlvdetection threshold=50.0 results=10 module=yolov8
labels=/opt/RUBIKPi_models/yolov8.labels
constants="YOLOv8,q-offsets=<21.0, 0.0, 0.0>,q-scales=<3.0935,0.00390625,1.0>;" !
text/x-raw,format=utf8 !
appsink name=meta_sink emit-signals=true
"""

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
```


# 위 코드에서 객체탐지시에만 콘솔에 메타데이터 출력하도록하는 개선된 코드
```
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
                if metadata:
                    #print("🔎 전체 메타데이터:", metadata)
                    if "ObjectDetection" in metadata:
                        print("🟢 객체 탐지 메타데이터:", metadata)
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
qtimlvdetection threshold=50.0 results=10 module=yolov8
labels=/opt/RUBIKPi_models/yolov8.labels
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
```