# 🎓 SmartAttendance (Class Manage)

> **스마트 학급 출결 관리 및 인터랙티브 수업 지원 데스크톱 애플리케이션**  
> PyQt5 기반의 모던 UI와 다양한 수업 참여 유도 기능을 제공하는 올인원 학급 관리 솔루션입니다.

---

## 📌 주요 기능 (Key Features)

### 1. 📋 스마트 출결 관리 (Attendance System)
- **실시간 출석 확인**: 학생 목록 카드 UI를 통해 한눈에 상태 확인 및 빠른 출결 체크
- **수동 출결 수정**: 지각, 조퇴, 결석 등 상태를 간편하게 변경할 수 있는 수동 출결 다이얼로그
- **결석 사유 기록**: 결석 사유를 입력 및 누적 관리 (`absence_reasons.csv`, `attendance_logs.csv`)
- **전체 출결 통계**: 일자별/학생별 출결 현황을 분석하고 시각화된 통계 확인

### 2. ⏱️ 수업 타이머 & 플로팅 위젯 (Class Timer & Floating Widget)
- **수업 시간 관리**: 수업 시작/종료 시간 설정 및 세션 기록 자동 저장 (`class_logs.json`)
- **미니 플로팅 타이머 (`MiniTimerWindow`)**:
  - 화면 최상단(Always-on-top)에 떠 있는 미니멀 플로팅 타이머 제공
  - 다른 프로그램을 띄워두고 수업을 진행할 때도 남은 수업 시간 확인 가능

### 3. 🎯 인터랙티브 발표자 추첨 (Presenter Selection)
수업 몰입도와 참여도를 극대화하는 3가지 추첨 모드 지원:
- **룰렛 돌리기 (Roulette Wheel)**: 부드러운 회전 애니메이션과 사운드가 적용된 룰렛 추첨
- **사다리 타기 (Ladder Game)**: 시각적인 캔버스 애니메이션 기반 사다리 타기
- **제비뽑기 / 복권 모드 (Lottery Cards)**: 카드를 긁거나 뒤집어 발표자를 선발하는 긴장감 넘치는 모드
- **발표자 축하 팡파레**: 선정 시 축하 효과와 함께 안내

### 4. 🌟 오늘의 MVP 시스템 (MVP Recognition)
- **MVP 투표 및 추첨**: 학생들의 투표 또는 룰렛을 통한 오늘의 MVP 선발
- **축하 사운드 & 비주얼 연출**: 팡파레 효과음(`mvp_sound.mp3`) 및 축하 팝업 표출
- **MVP 통계 관리**: 역대 MVP 선정 횟수 및 랭킹 누적 관리 (`mvp_logs.csv`)

### 5. 😊 학생 감정 기록 & 상담 일지 (Emotion & Counseling Logs)
- **9가지 감정 이모티콘**: 학생의 그날 기분 및 상태를 직관적인 이모티콘으로 기록 (`emojis/`)
- **상담/학습 일지 작성**: 학생별 특이사항, 수업 피드백, 상담 내용을 기록하고 히스토리 조회

### 6. 🔊 TTS 음성 안내 (Text-To-Speech)
- `pyttsx3` 음성 엔진을 통한 주요 안내 멘트 음성 출력

---

## 🛠️ 기술 스택 (Tech Stack)

| 구분 | 기술 / 라이브러리 |
| :--- | :--- |
| **Language** | Python 3.8+ |
| **GUI Framework** | PyQt5 (Modern Frameless & Card UI, Animation) |
| **Audio & TTS** | PyQt5.QtMultimedia, pyttsx3, pythoncom (pywin32) |
| **Packaging** | PyInstaller |
| **Data Storage** | CSV, JSON 기반 로컬 파일 관리 |

---

## 📂 프로젝트 구조 (Directory Structure)

```plaintext
member_lookup_app/
├── emojis/                     # 감정 상태 이모티콘 이미지
├── photos/                     # 학생 프로필 사진 저장소
├── main.py                     # 애플리케이션 메인 소스 코드
├── SmartAttendance.spec        # PyInstaller 빌드 명세서
├── members.csv                 # 학생 명단 기본 데이터
├── attendance_logs.csv         # 출결 기록 로그
├── absence_reasons.csv         # 결석 사유 로그
├── class_logs.json             # 수업 시간 설정 및 로그
├── mvp_logs.csv                # MVP 선정 기록 로그
├── mvp_sound.mp3               # MVP 축하 사운드 파일
├── requirements.txt            # 프로젝트 의존성 목록
└── README.md                   # 프로젝트 안내 문서
```

---

## 🚀 시작하기 (Getting Started)

### 1. 저장소 클론
```bash
git clone https://github.com/joeyKor/class__manage.git
cd class__manage
```

### 2. 가상환경 설정 및 패키지 설치
```bash
# 가상환경 생성 (선택 사항)
python -m venv venv
venv\Scripts\activate

# 필수 패키지 설치
pip install -r requirements.txt
```

### 3. 애플리케이션 실행
```bash
python main.py
```

---

## 📦 단일 실행 파일 빌드 (PyInstaller Build)

PyInstaller를 사용하여 단일 실행 파일(`.exe`)로 패키징할 수 있습니다.

```bash
pyinstaller SmartAttendance.spec
```
빌드가 완료되면 `dist/SmartAttendance.exe` 파일이 생성됩니다.

---

## 📄 라이선스 (License)

This project is licensed under the MIT License.
