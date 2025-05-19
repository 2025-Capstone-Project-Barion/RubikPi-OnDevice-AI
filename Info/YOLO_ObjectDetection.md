# 카메라 스트리밍 전에 해당 명령어 필수입력
```sh
export XDG_RUNTIME_DIR=/dev/socket/weston  
export WAYLAND_DISPLAY=wayland-1  
setprop persist.overlay.use_c2d_blit 2  
```

# 카메라 스트리밍 작동 테스팅
```sh
export XDG_RUNTIME_DIR=/dev/socket/weston  
export WAYLAND_DISPLAY=wayland-1  
setprop persist.overlay.use_c2d_blit 2  
gst-launch-1.0 -e qtiqmmfsrc camera=0 name=camsrc ! video/x-raw\(memory:GBM\),format=NV12,width=1920,height=1080,framerate=30/1,compression=ubwc ! queue ! waylandsink fullscreen=true async=true
```

# QIM으로 카메라 스트리밍 출력 & YOLOv8-Detection-Quantized.tflite기반 탐지
```sh
 gst-ai-object-detection -t 2 -f 2 -m /opt/RUBIKPi_models/YOLOv8-Detection-Quantized.tflite -l /opt/RUBIKPi_models/yolov8.labels -c "YOLOv8,q-offsets=<21.0, 0.0, 0.0>,q-scales=<3.093529462814331, 0.00390625, 1.0>;"
```

# 콘솔에 메타데이터 출력은되나, 해당 객체탐지시에만 출력이아닌 매 시간마다 출력되어 더러움
```python
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
```python
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


# 의자랑 사람 동시에 객체탐지되었을 때만 콘솔에 출력하도록 개선된 코드
```python
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
                    has_chair = "label\\=\\(string\\)chair" in metadata
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

# 디스플레이에 스트리밍 출력 + 휠체어+사람 탐지시 콘솔에 출력(but, 출력 더러움) 
```python
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
                    has_person = "label\\=\\(string\\)person" in metadata
                    has_wheelchair = "label\\=\\(string\\)wheelchair" in metadata
                    if has_person and has_wheelchair:
                        print("🟢 휠체어+사람 동시에 감지됨!")
                        print(metadata)
            except Exception as e:
                print("❌ 메타데이터 디코딩 실패:", e)
        buf.unmap(mapinfo)
    return Gst.FlowReturn.OK

pipeline_str = (
    "qtiqmmfsrc camera=0 ! "
    "video/x-raw(memory:GBM), format=NV12, width=1280, height=720, framerate=30/1 ! "
    "qtivtransform ! tee name=t "

    "t. ! queue ! qtivtransform ! qtimetamux name=meta_mux ! "
    "qtioverlay ! waylandsink fullscreen=true "

    "t. ! queue ! qtivtransform ! qtimlvconverter ! "
    "qtimltflite delegate=external "
    "external-delegate-path=libQnnTFLiteDelegate.so "
    "external-delegate-options=QNNExternalDelegate,backend_type=htp; "
    "model=/opt/RUBIKPi_models/YOLOv8-Detection-Quantized.tflite ! "
    "qtimlvdetection threshold=50.0 results=10 module=yolov8 "
    "labels=/opt/RUBIKPi_models/custom.labels "
    "constants=YOLOv8,q-offsets=<21.0,0.0,0.0>,q-scales=<3.0935,0.00390625,1.0>; "

    "! tee name=detection_tee "

    "detection_tee. ! queue ! text/x-raw,format=utf8 ! appsink name=meta_sink emit-signals=true "

    "detection_tee. ! queue ! text/x-raw,format=utf8 ! meta_mux."
)


def main():
    pipeline = Gst.parse_launch(pipeline_str)
    appsink = pipeline.get_by_name("meta_sink")
    appsink.connect("new-sample", on_new_sample, None)

    pipeline.set_state(Gst.State.PLAYING)
    print("📡 YOLO 실시간 탐지 및 메타 수집 시작...")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("🛑 종료 요청")
        pipeline.set_state(Gst.State.NULL)

if __name__ == "__main__":
    main()
```