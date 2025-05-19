#!/bin/bash
echo "🔁 GStreamer & Weston & DSP 초기화 중..."

# GStreamer 관련 프로세스 강제 종료
sudo pkill -f gst
sudo pkill -f gst-launch-1.0
sudo pkill -f gst-ai-object-detection

# Weston 종료 및 소켓 정리
sudo pkill -f weston
sudo rm -rf /dev/socket/weston

# 잠시 대기
sleep 2

# Weston 재실행
weston --tty=2 --idle-time=0 --log=/tmp/weston.log --config=/etc/xdg/weston/weston.ini --continue-without-input &

echo "✅ 초기화 완료. 다시 실행하세요."
