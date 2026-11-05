import sys
import csv
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QFrame, QGraphicsDropShadowEffect,
                             QListWidget, QListWidgetItem, QPushButton, QComboBox, QDialog, QTextEdit, QTextBrowser, QMessageBox, QScrollArea, QMenu, QInputDialog, QGridLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QColorDialog, QToolButton, QTabWidget, QSplitter)
from PyQt5.QtGui import (QPixmap, QFont, QColor, QKeyEvent, QCursor, QPainter, QPen, QBrush, QPainterPath,
                         QImage, QTextCursor, QTextCharFormat, QTextBlockFormat, QTextListFormat, QIcon, QLinearGradient)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QUrl, QPropertyAnimation, QEasingCurve, QRect, QRectF, QSize, QEvent, QPoint, QPointF
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from collections import Counter
import json
import random
import html
import math
import shutil
import re


class EmotionSelectDialog(QDialog):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.emotion = ""
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('감정 선택')
        self.resize(1230, 380)
        self.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(self)
        
        lbl = QLabel(f"{self.name} 학생, today 기분이 어때요?")
        lbl.setText(f"{self.name} 학생, 오늘 기분이 어때요?")
        lbl.setFont(QFont('Malgun Gothic', 22, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #2C3E50;")
        layout.addWidget(lbl)
        
        layout.addSpacing(20)
        
        btn_layout = QHBoxLayout()
        emotions = [
            ("좋아요", "1_good.png", "#E8F8F5", "#1ABC9C"),
            ("신나요", "2_excited.png", "#FEF9E7", "#F1C40F"),
            ("괜찮아요", "3_okay.png", "#EAF2F8", "#3498DB"),
            ("안좋아요", "8_bad.png", "#FDF2E9", "#E67E22"),
            ("졸려요", "4_sleepy.png", "#F4F6F6", "#95A5A6"),
            ("슬퍼요", "5_sad.png", "#EAECEE", "#7F8C8D"),
            ("화나요", "6_angry.png", "#FDEDEC", "#E74C3C"),
            ("무서워요", "7_scared.png", "#F5EEF8", "#9B59B6"),
            ("짜증나요", "9_annoyed.png", "#FFF1F2", "#E11D48")
        ]
        
        base_dir = getattr(self.parent(), "base_dir", os.path.dirname(os.path.abspath(__file__)))
        
        for idx, (text, img, bg_color, border_color) in enumerate(emotions, 1):
            btn = QPushButton()
            btn.setFixedSize(120, 170)
            btn.setCursor(Qt.PointingHandCursor)
            
            e_layout = QVBoxLayout(btn)
            e_layout.setContentsMargins(5, 10, 5, 5)
            e_layout.setAlignment(Qt.AlignCenter)
            
            icon_lbl = QLabel()
            img_path = os.path.join(base_dir, 'emojis', img)
            if os.path.exists(img_path):
                pix = QPixmap(img_path).scaled(84, 84, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_lbl.setPixmap(pix)
            else:
                icon_lbl.setText("?")
            icon_lbl.setAlignment(Qt.AlignCenter)
            
            txt_lbl = QLabel(f"{idx}. {text}")
            txt_lbl.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
            txt_lbl.setAlignment(Qt.AlignCenter)
            txt_lbl.setStyleSheet(f"color: {border_color}; border: none;")
            
            e_layout.addWidget(icon_lbl)
            e_layout.addWidget(txt_lbl)
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    border: 2px solid {border_color};
                    border-radius: 15px;
                }}
                QPushButton:hover {{
                    background-color: white;
                    border: 3px solid {border_color};
                }}
            """)
            btn.clicked.connect(lambda _, t=text: self.select_emotion(t))
            btn_layout.addWidget(btn)
            
        layout.addLayout(btn_layout)
        
        layout.addSpacing(20)
        cancel_btn = QPushButton("취소 (Escape)")
        cancel_btn.setFont(QFont('Malgun Gothic', 14, QFont.Bold))
        cancel_btn.setFixedHeight(50)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #94A3B8;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #64748B;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
    def select_emotion(self, text):
        self.emotion = text
        self.accept()

    def keyPressEvent(self, event):
        key = event.key()
        if Qt.Key_1 <= key <= Qt.Key_9:
            emotions_list = ["좋아요", "신나요", "괜찮아요", "안좋아요", "졸려요", "슬퍼요", "화나요", "무서워요", "짜증나요"]
            index = key - Qt.Key_1
            self.select_emotion(emotions_list[index])
        elif key == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


class OverallAttendanceDialog(QDialog):
    def __init__(self, students_data, log_file, absence_file, classes, initial_class="", parent=None):
        super().__init__(parent)
        self.students_data = students_data
        self.log_file = log_file
        self.absence_file = absence_file
        self.classes = classes
        self.initial_class = initial_class
        self.attendance_history = {} # {date: {s_id: status}}
        self.absence_reasons = {} # {date: {s_id: reason}}
        self.all_dates = []
        self.class_students_mapping = [] # 현재 표시 중인 학생 리스트 (row 인덱스 매핑용)
        
        self.initUI()
        self.load_attendance_history()
        
        # 초기 반 설정
        if self.initial_class in self.classes:
            self.class_selector.setCurrentText(self.initial_class)
        elif self.classes:
            self.class_selector.setCurrentIndex(0)
            
        self.update_table()
        
    def initUI(self):
        self.setWindowTitle('출석 현황판')
        self.resize(1200, 800)
        self.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 상단 헤더 및 반 선택
        top_layout = QHBoxLayout()
        title = QLabel('📅 출석 현황')
        title.setFont(QFont('Malgun Gothic', 22, QFont.Bold))
        title.setStyleSheet("color: #1E293B;")
        top_layout.addWidget(title)
        
        top_layout.addStretch()
        
        sel_label = QLabel('조회할 반 선택:')
        sel_label.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        sel_label.setStyleSheet("color: #64748B;")
        top_layout.addWidget(sel_label)
        
        self.class_selector = QComboBox()
        self.class_selector.addItems(self.classes)
        self.class_selector.setFixedSize(200, 45)
        self.class_selector.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        self.class_selector.setStyleSheet("""
            QComboBox { 
                border: 2px solid #E2E8F0; 
                border-radius: 10px; 
                padding: 5px 15px; 
                background-color: #F8FAFC; 
            }
        """)
        self.class_selector.currentTextChanged.connect(self.update_table)
        top_layout.addWidget(self.class_selector)
        
        layout.addLayout(top_layout)
        layout.addSpacing(20)
        
        # 테이블
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                gridline-color: #F1F5F9;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                font-weight: bold;
                color: #475569;
            }
        """)
        layout.addWidget(self.table)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
        # 하단 버튼
        btn_layout = QHBoxLayout()
        hint = QLabel('💡 ✔️: 출석 완료 / 🏫: 학교 결석 / 📖: 수업 결석 / 빈칸: 미출석')
        hint.setFont(QFont('Malgun Gothic', 11))
        hint.setStyleSheet("color: #94A3B8;")
        btn_layout.addWidget(hint)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("닫기")
        close_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        close_btn.setFixedSize(150, 50)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton { background-color: #1E293B; color: white; border-radius: 10px; }
            QPushButton:hover { background-color: #334155; }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)

    def load_attendance_history(self):
        self.attendance_history = {}
        self.absence_reasons = {}
        dates_set = set()
        
        # 1. 출석 로그 로드
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) < 4: continue
                    dt_str, s_id, status = row[0], row[1], row[3]
                    date = dt_str.split(' ')[0]
                    if date not in self.attendance_history:
                        self.attendance_history[date] = {}
                    if status in ['출석', '학교 결석', '수업 결석']:
                        self.attendance_history[date][s_id] = status
                    elif status == '취소' and s_id in self.attendance_history[date]:
                        del self.attendance_history[date][s_id]
                    dates_set.add(date)
        
        # 2. 결석 사유 로드
        if os.path.exists(self.absence_file):
            with open(self.absence_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) < 3: continue
                    date, s_id, reason = row[0], row[1], row[2]
                    if date not in self.absence_reasons:
                        self.absence_reasons[date] = {}
                    self.absence_reasons[date][s_id] = reason
                    dates_set.add(date)
        
        self.all_dates = sorted(list(dates_set), reverse=True)

    def on_cell_double_clicked(self, row, col):
        active_dates = getattr(self, 'current_active_dates', self.all_dates)
        if row >= len(self.class_students_mapping) or col >= len(active_dates):
            return
            
        s_id, s_name = self.class_students_mapping[row]
        date = active_dates[col]
        
        # 이미 출석한 경우
        if self.attendance_history.get(date, {}).get(s_id, False):
            QMessageBox.information(self, "안내", f"{s_name} 학생은 해당 일에 출석하였습니다.")
            return
            
        # 결석 사유 입력
        old_reason = self.absence_reasons.get(date, {}).get(s_id, "")
        reason, ok = QInputDialog.getText(self, "결석 사유 입력", 
                                        f"[{date}] {s_name} 학생의 결석 사유를 입력하세요:",
                                        QLineEdit.Normal, old_reason)
        
        if ok:
            self.save_absence_reason(date, s_id, reason)
            self.load_attendance_history()
            self.update_table()

    def save_absence_reason(self, date, s_id, reason):
        reasons = []
        found = False
        
        # 기존 파일 읽기
        if os.path.exists(self.absence_file):
            with open(self.absence_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if len(row) >= 3 and row[0] == date and row[1] == s_id:
                        if reason.strip(): # 내용이 있으면 업데이트
                            reasons.append([date, s_id, reason])
                        found = True # 내용이 없으면 (삭제) 그냥 추가 안 함
                    else:
                        reasons.append(row)
        
        if not found and reason.strip():
            reasons.append([date, s_id, reason])
            
        # 파일 저장
        with open(self.absence_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['날짜', '학번', '사유'])
            writer.writerows(reasons)

    def update_table(self):
        class_name = self.class_selector.currentText()
        if not class_name: return
        
        # 1. 해당 반 학생 필터링
        class_students = []
        for s_id, s_info in self.students_data.items():
            info_str = " ".join(str(v) for v in s_info.values())
            if class_name in info_str:
                class_students.append((s_id, s_info.get('이름', '이름 없음')))
        
        class_students.sort(key=lambda x: x[0]) # 학번순 정렬
        self.class_students_mapping = class_students
        
        # 2. 해당 반에 기록(출석 혹은 결석사유)이 있는 날짜만 필터링
        active_dates = []
        for date in self.all_dates:
            has_record = False
            for s_id, _ in class_students:
                if self.attendance_history.get(date, {}).get(s_id) or \
                   self.absence_reasons.get(date, {}).get(s_id):
                    has_record = True
                    break
            if has_record:
                active_dates.append(date)
        
        self.current_active_dates = active_dates
        
        # 3. 테이블 설정
        self.table.setRowCount(len(class_students))
        self.table.setColumnCount(len(active_dates))
        
        # 헤더 설정
        self.table.setVerticalHeaderLabels([name for _, name in class_students])
        self.table.setHorizontalHeaderLabels([d.split('-')[1]+'/'+d.split('-')[2] for d in active_dates]) # MM/DD 형식
        
        # 셀 데이터 채우기
        for row, (s_id, _) in enumerate(class_students):
            for col, date in enumerate(active_dates):
                st_val = self.attendance_history.get(date, {}).get(s_id, False)
                reason = self.absence_reasons.get(date, {}).get(s_id, "")
                
                if st_val == '출석' or st_val is True:
                    item = QTableWidgetItem("✔️ 출석")
                    item.setForeground(QColor("#10B981"))
                elif st_val == '학교 결석':
                    item = QTableWidgetItem("🏫 학교결석")
                    item.setForeground(QColor("#D97706"))
                elif st_val == '수업 결석':
                    item = QTableWidgetItem("📖 수업결석")
                    item.setForeground(QColor("#DB2777"))
                elif reason:
                    item = QTableWidgetItem(f"📌 {reason}")
                    item.setForeground(QColor("#F59E0B")) # 주황색 (사유 있음)
                    item.setFont(QFont('Malgun Gothic', 9))
                else:
                    item = QTableWidgetItem("")
                
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
        
        # 열 너비 자동 조절
        self.table.horizontalHeader().setDefaultSectionSize(80)
        if len(class_students) > 0:
            self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
            self.table.verticalHeader().setDefaultSectionSize(45)




class StartClassSelectDialog(QDialog):
    def __init__(self, classes, parent=None):
        super().__init__(parent)
        self.classes = classes
        self.selected_class = ""
        
        # 학년별로 반 그룹화
        self.grade_groups = {}
        import re
        for c in self.classes:
            m = re.match(r'(\d+학년)', c)
            grade = m.group(1) if m else "기타"
            if grade not in self.grade_groups:
                self.grade_groups[grade] = []
            self.grade_groups[grade].append(c)
        
        # 학년 순서 정렬 (숫자 추출하여 정렬, '기타'는 맨 뒤로)
        self.sorted_grades = sorted([g for g in self.grade_groups.keys() if g != "기타"], 
                                     key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 999)
        if "기타" in self.grade_groups:
            self.sorted_grades.append("기타")
            
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('오늘의 수업(반) 선택')
        self.setFixedSize(850, 800)
        self.setStyleSheet("background-color: white; border-radius: 20px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        title_lbl = QLabel("🏫 반 선택")
        title_lbl.setFont(QFont('Malgun Gothic', 28, QFont.Bold))
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("color: #3B82F6;")
        layout.addWidget(title_lbl)
        
        sub_lbl = QLabel("")
        sub_lbl.setFont(QFont('Malgun Gothic', 13))
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet("color: #64748B; margin-bottom: 10px;")
        layout.addWidget(sub_lbl)
        
        # 스크롤 영역 추가
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        container_layout = QVBoxLayout(scroll_content)
        container_layout.setSpacing(35)
        
        for grade in self.sorted_grades:
            grade_vbox = QVBoxLayout()
            grade_vbox.setSpacing(10)
            
            grade_lbl = QLabel(f"📍 {grade}")
            grade_lbl.setFont(QFont('Malgun Gothic', 16, QFont.Bold))
            grade_lbl.setStyleSheet("color: #1E293B; padding-bottom: 5px; border-bottom: 2px solid #F1F5F9;")
            grade_vbox.addWidget(grade_lbl)
            
            # 그리드 레이아웃으로 반 버튼 배치
            classes_grid = QGridLayout()
            classes_grid.setSpacing(12)
            classes_grid.setAlignment(Qt.AlignLeft)
            
            for idx, c_name in enumerate(sorted(self.grade_groups[grade])):
                btn = QPushButton(c_name)
                btn.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
                btn.setFixedSize(170, 65)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #F8FAFC;
                        border: 2px solid #E2E8F0;
                        border-radius: 12px;
                        color: #334155;
                    }
                    QPushButton:hover {
                        background-color: #3B82F6;
                        color: white;
                        border: 2px solid #3B82F6;
                    }
                """)
                btn.clicked.connect(lambda _, n=c_name: self.select_class(n))
                classes_grid.addWidget(btn, idx // 4, idx % 4)
            
            grade_vbox.addLayout(classes_grid)
            container_layout.addLayout(grade_vbox)
        
        container_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        layout.addSpacing(10)
        cancel_btn = QPushButton("닫기")
        cancel_btn.setFont(QFont('Malgun Gothic', 14, QFont.Bold))
        cancel_btn.setFixedHeight(50)
        cancel_btn.setFixedWidth(150)
        cancel_btn.setStyleSheet("background-color: #94A3B8; color: white; border-radius: 10px; border: none;")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)

    def select_class(self, class_name):
        self.selected_class = class_name
        self.accept()


class ManualAttendanceDialog(QDialog):
    def __init__(self, s_name, photo_path=None, parent=None):
        super().__init__(parent)
        self.s_name = s_name
        self.photo_path = photo_path
        self.selected_action = None # '출석', '학교 결석', '수업 결석'
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('수동 출결 선택')
        self.setFixedSize(400, 410)
        self.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(10)
        
        # 학생 사진 표시
        if self.photo_path and os.path.exists(self.photo_path):
            photo_lbl = QLabel()
            photo_lbl.setFixedSize(64, 64)
            pix = QPixmap(self.photo_path).scaled(64, 64, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            photo_lbl.setPixmap(pix)
            photo_lbl.setStyleSheet("border-radius: 32px; border: 2px solid #CBD5E1;")
            photo_lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(photo_lbl, alignment=Qt.AlignCenter)
        
        title_lbl = QLabel(f"📋 {self.s_name} 학생 출결 처리")
        title_lbl.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("color: #1E293B;")
        layout.addWidget(title_lbl)
        
        sub_lbl = QLabel("원하는 출결 상태를 선택하세요:")
        sub_lbl.setFont(QFont('Malgun Gothic', 11))
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet("color: #64748B;")
        layout.addWidget(sub_lbl)
        
        layout.addSpacing(5)
        
        btn_attend = QPushButton("🟢  출석 (기분 선택)")
        btn_attend.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        btn_attend.setFixedHeight(48)
        btn_attend.setCursor(Qt.PointingHandCursor)
        btn_attend.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        btn_attend.clicked.connect(lambda: self.choose('출석'))
        layout.addWidget(btn_attend)
        
        btn_school_absent = QPushButton("🏫  학교 결석")
        btn_school_absent.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        btn_school_absent.setFixedHeight(48)
        btn_school_absent.setCursor(Qt.PointingHandCursor)
        btn_school_absent.setStyleSheet("""
            QPushButton {
                background-color: #F59E0B;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #D97706;
            }
        """)
        btn_school_absent.clicked.connect(lambda: self.choose('학교 결석'))
        layout.addWidget(btn_school_absent)
        
        btn_class_absent = QPushButton("📖  수업 결석")
        btn_class_absent.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        btn_class_absent.setFixedHeight(48)
        btn_class_absent.setCursor(Qt.PointingHandCursor)
        btn_class_absent.setStyleSheet("""
            QPushButton {
                background-color: #EC4899;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #DB2777;
            }
        """)
        btn_class_absent.clicked.connect(lambda: self.choose('수업 결석'))
        layout.addWidget(btn_class_absent)
        
        layout.addSpacing(5)
        
        cancel_btn = QPushButton("닫기 / 취소")
        cancel_btn.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        cancel_btn.setFixedHeight(38)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #94A3B8;
                color: white;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #64748B;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
    def choose(self, status):
        self.selected_action = status
        self.accept()


class StudentItemWidget(QWidget):
    def __init__(self, s_id, name, time_s, emotion, photo_path, is_attended, status_type="출석", parent=None):
        super().__init__(parent)
        self.setFixedHeight(68) # 85 -> 68 (적당히 축소)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(3, 2, 3, 2) # 여백 축소
        main_layout.setSpacing(0)
        
        # 카드 프레임
        self.card = QFrame()
        self.card.setObjectName("StudentCard")
        
        # 출석 여부 및 상태에 따른 카드 스타일
        if is_attended:
            if status_type == "학교 결석":
                border_color = "#F59E0B"
                bg_color = "#FFFBEB"
                status_text = f"🏫 학교 결석 ({time_s})"
                status_color = "#D97706"
            elif status_type == "수업 결석":
                border_color = "#EC4899"
                bg_color = "#FDF2F8"
                status_text = f"📖 수업 결석 ({time_s})"
                status_color = "#DB2777"
            else:
                border_color = "#3B82F6"
                bg_color = "white"
                status_text = f"🕒 {time_s}"
                status_color = "#3B82F6"
        else:
            border_color = "#E2E8F0"
            bg_color = "#F8FAFC"
            status_text = "미출석"
            status_color = "#94A3B8"
            
        self.card.setStyleSheet(f"""
            QFrame#StudentCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-left: 4px solid {border_color};
                border-radius: 10px;
            }}
        """)
        
        if is_attended:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setColor(QColor(0, 0, 0, 12))
            shadow.setOffset(0, 2)
            self.card.setGraphicsEffect(shadow)
            
        card_layout = QHBoxLayout(self.card)
        card_layout.setContentsMargins(12, 5, 12, 5) # 상하 여백 대폭 축소
        card_layout.setSpacing(12)
        
        # 프로필 이미지 (크기 축소 50->38)
        self.photo_lbl = QLabel()
        self.photo_lbl.setFixedSize(38, 38)
        if is_attended and os.path.exists(photo_path):
            pix = QPixmap(photo_path).scaled(38, 38, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.photo_lbl.setPixmap(pix)
            self.photo_lbl.setStyleSheet("border-radius: 19px; border: 1.5px solid white;")
        else:
            if not is_attended:
                icon_str = "😶"
            elif status_type == "학교 결석":
                icon_str = "🏫"
            elif status_type == "수업 결석":
                icon_str = "📖"
            else:
                icon_str = "👤"
            self.photo_lbl.setText(icon_str)
            self.photo_lbl.setAlignment(Qt.AlignCenter)
            self.photo_lbl.setStyleSheet("background-color: #F1F5F9; border-radius: 19px; color: #94A3B8; font-size: 16px;")
            
        card_layout.addWidget(self.photo_lbl)
        
        # 정보 영역
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)
        info_layout.setAlignment(Qt.AlignVCenter)
        
        name_lbl = QLabel(name)
        name_lbl.setFont(QFont('Malgun Gothic', 12, QFont.Bold)) # 13 -> 12
        name_lbl.setStyleSheet(f"color: {'#1E293B' if is_attended else '#64748B'}; border: none;")
        
        status_lbl = QLabel(status_text)
        status_lbl.setFont(QFont('Malgun Gothic', 9)) # 10 -> 9
        status_lbl.setStyleSheet(f"color: {status_color}; border: none;")
        
        info_layout.addWidget(name_lbl)
        info_layout.addWidget(status_lbl)
        
        card_layout.addLayout(info_layout, stretch=1)
        
        # 감정 태그 또는 결석 상태 태그
        if is_attended:
            tag_text = None
            bg, fg = None, None
            if emotion:
                colors = {
                    "좋아요": ("#D1FAE5", "#065F46"), "신나요": ("#FEF3C7", "#92400E"), "괜찮아요": ("#DBEAFE", "#1E40AF"), "안좋아요": ("#FFEDD5", "#C2410C"),
                    "졸려요": ("#F1F5F9", "#475569"), "슬퍼요": ("#E0F2FE", "#075985"), "화나요": ("#FEE2E2", "#991B1B"), "무서워요": ("#F3E8FF", "#6B21A8"),
                    "짜증나요": ("#FFE4E6", "#9F1239")
                }
                bg, fg = colors.get(emotion, ("#DBEAFE", "#1E40AF"))
                tag_text = emotion
            elif status_type == "학교 결석":
                bg, fg = "#FEF3C7", "#D97706"
                tag_text = "학교 결석"
            elif status_type == "수업 결석":
                bg, fg = "#FCE7F3", "#DB2777"
                tag_text = "수업 결석"
                
            if tag_text:
                emo_lbl = QLabel(tag_text)
                emo_lbl.setFont(QFont('Malgun Gothic', 8, QFont.Bold)) # 9 -> 8
                emo_lbl.setStyleSheet(f"""
                    color: {fg}; 
                    background-color: {bg}; 
                    border-radius: 10px; 
                    padding: 3px 10px;
                    border: none;
                """)
                card_layout.addWidget(emo_lbl)
            
        main_layout.addWidget(self.card)
        self.setStyleSheet("background: transparent;")



