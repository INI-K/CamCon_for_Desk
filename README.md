# 범용 카메라 관리자 (Universal Camera Manager)

니콘 카메라의 0x935a 인증을 자동으로 처리하고 python-gphoto2를 활용한 범용 카메라 관리 툴입니다.

## 프로젝트 구조

```
pacTest/
├── src/                        # 소스 코드
│   ├── nikon_ptp_client.py    # 니콘 PTP/IP 클라이언트 (핵심 인증 로직)
│   ├── nikon_authenticator.py # 니콘 인증 전용 스크립트
│   ├── camera_manager.py      # CLI 카메라 관리자
│   └── camera_gui.py          # GUI 카메라 관리자
├── logs/                       # 로그 파일 저장소
├── downloads/                  # 다운로드 파일 저장소
├── python-gphoto2/            # python-gphoto2 라이브러리 참조
└── README.md                  # 프로젝트 문서
```

## 주요 기능

### 1. 니콘 카메라 자동 인증

- 0x935a 승인 요청 자동 처리
- Phase 1: 초기 연결 및 승인 요청
- Phase 2: 인증된 연결 설정 및 유지
- 원본 패킷 분석 기반 정확한 구현

### 2. 범용 카메라 지원

- 니콘: 자동 인증 후 python-gphoto2 사용
- 캐논/소니/기타: 직접 python-gphoto2 사용
- 자동 카메라 감지 및 적절한 처리 방식 선택

### 3. 다양한 사용 방식

- **GUI**: 직관적인 그래픽 인터페이스
- **CLI**: 명령줄 인터페이스
- **라이브러리**: 다른 프로젝트에서 임포트 가능

## 사용 방법

### GUI 모드 (권장)

```bash
cd src
python3 camera_gui.py
```

### CLI 모드

```bash
cd src
# 카메라 감지
python3 camera_manager.py detect 192.168.147.75

# 사진 촬영
python3 camera_manager.py capture 192.168.147.75

# 파일 목록
python3 camera_manager.py list 192.168.147.75

# 직접 gphoto2 명령
python3 camera_manager.py gphoto2 192.168.147.75 --list-config
```

### 니콘 인증만

```bash
cd src
python3 nikon_authenticator.py 192.168.147.75
```

## 지원 카메라

### 니콘 (0x935a 인증 필요)

- Z 시리즈 (Z8, Z9 등)
- D 시리즈 DSLR
- 기타 Wi-Fi 지원 니콘 카메라

### 기타 브랜드 (직접 지원)

- 캐논 (EOS 시리즈)
- 소니 (α 시리즈)
- 기타 gphoto2 지원 카메라

## 주요 개선사항

### 로그 관리

- 모든 로그 파일을 `logs/` 디렉토리에 자동 저장
- 타임스탬프 포함 자동 파일명 생성
- GUI와 CLI 모두 통합 로그 시스템

### 연결 유지

- 니콘 인증 후 연결 상태 유지
- gphoto2 사용 시에만 일시적 해제
- 자동 재인증 기능

### 사용성 개선

- 직관적인 GUI 인터페이스
- 실시간 작업 로그 표시
- 자동 카메라 감지
- 에러 처리 및 복구

## 의존성

### Python 라이브러리

```bash
pip install gphoto2  # python-gphoto2
```

### 시스템 요구사항

- Python 3.8+
- gphoto2 (시스템 패키지)
- libgphoto2-dev
- tkinter (GUI용)

### macOS 설치

```bash
brew install gphoto2
pip install gphoto2
```

### Ubuntu/Debian 설치

```bash
sudo apt-get install gphoto2 libgphoto2-dev
pip install gphoto2
```

## 개발 참고사항

### 니콘 PTP/IP 프로토콜

- Frame 1~47: 초기 연결 및 0x935a 승인
- Frame 68~: 새로운 인증된 연결
- 0x952b → 0x935a → 재연결 순서 중요

### python-gphoto2 활용

- python-gphoto2/examples/ 참조
- 카메라별 특성 고려한 구현
- 에러 처리 및 예외 상황 대응

## 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

## 기여

버그 리포트, 기능 요청, 코드 기여 환영합니다.