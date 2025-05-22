# 시연장 네트워크 구성도

# RubikPi Wi-Fi 연결 방법 (시연장 전용 요약)

RubikPi는 Linux 기반 장치로, 터미널에서 간단한 명령어로 주변 Wi-Fi를 스캔하고 원하는 SSID에 연결할 수 있다.

## ✅ 1. 주변 Wi-Fi 목록 확인
```bash
iw wlan0 scan | grep SSID
```

## 2. Wi-Fi `첫 연결`시 
```bash
wpa_passphrase "SSID명" "비밀번호" > /etc/wpa_supplicant.conf
systemctl restart wifi
```

> 위 명령으로 연결된 네트워크는 부팅 후 자동 재연결된다.

## ✅ 3. 이후 다른 Wi-Fi로 변경시(이걸 주로 쓰게된다-직접 수정)
```bash
vi /etc/wpa_supplicant.conf
```

`내용을 아래처럼 수정 후 저장:`
```conf
ctrl_interface=/var/run/wpa_supplicant
update_config=1
pmf=1
network={
    ssid="새로운SSID"
    psk="새로운비밀번호"
}
```

`이후 재연결:`
```bash
killall -9 wpa_supplicant
wpa_supplicant -Dnl80211 -iwlan0 -c/etc/wpa_supplicant.conf -B
```

## ✅ 현재 RubikPi가 연결된 Wi-Fi 확인
```bash
iw dev wlan0 link
```

> 출력 예시:
```
Connected to 0c:96:cd:dc:53:d5 (on wlan0)  
SSID: KT_GiGA_53D1  
signal: -68 dBm  
tx bitrate: 43.0 MBit/s  
```

## 🔁 연결 상태 확인
```bash
ip a              # wlan0에 IP가 할당되었는지 확인
ping google.com  # 외부 연결 확인
```

> 문제가 있을 경우 `dmesg` 또는 `/var/log/syslog` 확인

<br>

## 1. 전체 요약
- 라즈베리파이(wjpi)와 RubikPi는 서로 다른 방식으로 네트워크에 연결됨
- **호스트명 충돌 방지**를 위해 라즈베리파이의 호스트명을 반드시 `wjpi`로 변경해야 함
- RubikPi는 호스트명 변경이 불가능하므로 별도 네트워크 구성 필요

---

## 2. 구성 세부

### [A] 라즈베리파이 & 접속용 노트북
- **라즈베리파이**
  - 학교 Wi-Fi에 직접 연결
  - **호스트명: `wjpi`로 반드시 변경**
  - 변경 이유: 시연장에 동일한 `raspberrypi` 호스트명이 많은 경우 충돌 방지
- **접속용 노트북**
  - 동일하게 학교 Wi-Fi에 연결
- ✅ `ping wjpi.local`로 원격 접속 가능

#### ✅ 호스트명 변경 방법
1. 터미널에서 다음 명령어 입력:
   ```bash
   sudo raspi-config
   ```
2. 메뉴에서 `2. System Options` 선택
3. `S4 Hostname` 선택
4. 원하는 이름 입력: `wjpi`
5. `Finish` 선택 후 재부팅

---

### [B] RubikPi & 접속용 노트북
- **접속용 노트북**
  - 학교 Wi-Fi 연결 + **핫스팟 생성**
- **RubikPi**
  - 해당 노트북의 핫스팟에 연결
  - 호스트명: `rubikpi` (변경 불가)
- ✅ 둘만의 **로컬 네트워크 구성**으로 호스트명 충돌 방지

---

## 3. MQTT 통신 전략

### 기본 아이디어
- 라즈베리파이와 RubikPi는 **서로 다른 네트워크**에 있음
- MQTT 통신을 위해 몇 가지 고려 필요

### 시나리오 1: 브로커 = 라즈베리파이
- 라즈베리파이에 `mosquitto` 브로커 설치 및 백그라운드 실행
- RubikPi가 해당 IP에 접속 → 가능 여부는 네트워크 구조에 따라 달림

### 시나리오 2: 브로커 = RubikPi 연결된 노트북
- MQTT 브로커를 핫스팟 생성 노트북에 설치
- 라즈베리파이가 해당 노트북의 IP로 접속

### 주의 사항
- IP 접근 가능성 확인
- 학교 Wi-Fi 방화벽이 **1883 포트**를 막을 수 있음 → 대안 필요

---

## 4. 결론
- `wjpi`로 호스트명 반드시 변경해야 안정적 원격접속 가능
- RubikPi는 고정 이름이므로 **로컬 네트워크 구성 필수**
- MQTT 브로커는 환경에 따라 유동적으로 선택 가능
