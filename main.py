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


from utils import (
    resolve_image_paths,
    relativize_image_paths,
    TTSThread,
    ClickableLabel,
    MiniTimerWindow,
)
from log_dialogs import (
    RichTextEdit,
    LogWriteDialog,
    ImageViewerDialog,
    ClickableImageCard,
    LogHistoryDialog,
)
from presenter_dialogs import (
    PresenterModeSelectDialog,
    RouletteWheelWidget,
    PresenterRouletteDialog,
    LadderCanvasWidget,
    PresenterLadderDialog,
    PresenterLotteryDialog,
    RaceTrackWidget,
    PresenterRaceDialog,
    PresenterCelebrationDialog,
)
from mvp_dialogs import (
    MVPVoteDialog,
    MVPRouletteDialog,
    MVPCelebrationDialog,
    MVPStatsDialog,
)
from attendance_dialogs import (
    EmotionSelectDialog,
    OverallAttendanceDialog,
    StartClassSelectDialog,
    ManualAttendanceDialog,
    StudentItemWidget,
)
from student_manager import (
    StudentEditDialog,
    StudentManagementDialog,
)

class StudentAttendanceApp(QWidget):
    def __init__(self):
        super().__init__()
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.students_data = {}
        self.active_students = {} 
        self.current_id = None
        self.csv_path = os.path.join(self.base_dir, 'students.csv')
        self.log_file = os.path.join(self.base_dir, 'attendance_logs.csv')
        self.class_log_file = os.path.join(self.base_dir, 'class_logs.json')
        self.absence_file = os.path.join(self.base_dir, 'absence_reasons.csv')
        self.mvp_file = os.path.join(self.base_dir, 'mvp_logs.csv')
        self.class_logs = {}
        self.load_data()
        self.mini_timer = MiniTimerWindow(self)
        self.initUI()
        self.load_today_attendance()
        # 앱 시작 시 반 선택 다이얼로그 띄우기
        QTimer.singleShot(100, self.show_start_class_selector)

    def get_class_list(self):
        import re
        class_set = set()
        for s in self.students_data.values():
            # 1. '학생정보' 또는 '학년반' 컬럼을 우선적으로 읽음 ('학년반번호' 컬럼이 오인되는 것 방지)
            class_val = s.get('학생정보', '') or s.get('학년반', '')
            if not class_val:
                for k, v in s.items():
                    if ('학년' in k or '반' in k or '정보' in k) and ('번호' not in k and '학번' not in k):
                        class_val = str(v).split('\n')[0].strip()
                        break
            else:
                class_val = str(class_val).split('\n')[0].strip()

            if class_val:
                m = re.search(r'(\d+학년\s*\d+반)', class_val)
                if m:
                    class_set.add(m.group(1))
                elif not class_val.isdigit():
                    val = re.sub(r'\s*\d+번.*$', '', class_val).strip()
                    if val:
                        class_set.add(val)
        return sorted(list(class_set))

    def show_start_class_selector(self):
        classes = self.get_class_list()
        if classes:
            dlg = StartClassSelectDialog(classes, self)
            if dlg.exec_() == QDialog.Accepted:
                self.class_combo.setCurrentText(dlg.selected_class)
                # update_log_display가 호출되면서 combo가 비활성화됨
                self.update_log_display(dlg.selected_class)


    def load_data(self):
        # students.csv를 기본/우선으로 사용, 없을 경우 members.csv 호환
        students_path = os.path.join(self.base_dir, 'students.csv')
        members_path = os.path.join(self.base_dir, 'members.csv')
        if os.path.exists(students_path):
            self.csv_path = students_path
        elif os.path.exists(members_path):
            self.csv_path = members_path
        else:
            self.csv_path = students_path
            
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['학년반번호', '이름', '학생정보', '사진파일명'])
                writer.writerow(['10101', '홍길동', '1학년 1반 1번\n동아리: 밴드부', '10101.jpg'])
                writer.writerow(['20202', '이순신', '2학년 2반 2번\n동아리: 방송부', '20202.jpg'])
            os.makedirs(os.path.join(self.base_dir, 'photos'), exist_ok=True)
            
        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 유연하게 학번이나 입력번호 키 모두 인식
                id_key = next((k for k in row.keys() if '번호' in k or '학번' in k), None)
                if id_key and row[id_key]:
                    self.students_data[row[id_key]] = row

        if os.path.exists(self.class_log_file):
            try:
                with open(self.class_log_file, 'r', encoding='utf-8') as f:
                    self.class_logs = json.load(f)
            except Exception as e:
                print("Failed to load class_logs.json:", e)

    def initUI(self):
        self.setWindowTitle('스마트 학생 출결 관리')
        self.setStyleSheet("""
            QWidget {
                background-color: #F8FAFC;
            }
            QToolTip {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 2px solid #F59E0B;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 14px;
                font-family: 'Malgun Gothic';
            }
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(18, 12, 18, 12)
        main_layout.setSpacing(16)
        
        # ==========================================
        # 1. 왼쪽 패널 (사이드바)
        # ==========================================
        left_panel = QFrame()
        left_panel.setFixedWidth(310)
        left_panel.setStyleSheet("""
            QFrame { background-color: white; border-radius: 16px; }
        """)
        shadow_left = QGraphicsDropShadowEffect()
        shadow_left.setBlurRadius(15)
        shadow_left.setColor(QColor(0, 0, 0, 15))
        shadow_left.setOffset(0, 4)
        left_panel.setGraphicsEffect(shadow_left)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)
        
        t_label = QLabel('Smart Attendance')
        t_label.setFont(QFont('Segoe UI', 18, QFont.Bold))
        t_label.setAlignment(Qt.AlignCenter)
        t_label.setStyleSheet("color: #3B82F6; border: none; margin-bottom: 6px;")
        
        # Hidden QComboBox for backend compatibility
        self.class_combo = QComboBox(self)
        self.class_combo.hide()
        sorted_classes = self.get_class_list()
        self.class_combo.addItems(["수업명 입력/선택"] + sorted_classes)
        
        # Sleek class selection button replacing the combo box and change button
        self.class_btn = QPushButton('🏫 수업반을 선택하세요')
        self.class_btn.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        self.class_btn.setFixedHeight(46)
        self.class_btn.setCursor(Qt.PointingHandCursor)
        self.class_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #475569;
                border: 2px dashed #CBD5E1;
                border-radius: 12px;
                padding: 4px 12px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #EFF6FF;
                color: #2563EB;
                border: 2px solid #3B82F6;
            }
        """)
        self.class_btn.clicked.connect(self.show_start_class_selector)
        
        self.access_list = QListWidget()
        self.access_list.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.access_list.setSpacing(4)
        self.access_list.setStyleSheet("""
            QListWidget { 
                border: none; 
                background-color: transparent; 
            }
            QListWidget::item { 
                border: none; 
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #F1F5F9;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 3px;
            }
        """)
        self.access_list.itemClicked.connect(self.cancel_attendance)
        
        self.end_class_btn = QPushButton('수업 전체 종료')
        self.end_class_btn.setFont(QFont('Malgun Gothic', 14, QFont.Bold))
        self.end_class_btn.setFixedHeight(48)
        self.end_class_btn.setCursor(Qt.PointingHandCursor)
        self.end_class_btn.setStyleSheet("""
            QPushButton { background-color: #EF4444; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #DC2626; }
        """)
        self.end_class_btn.clicked.connect(self.end_all_class)
        
        left_layout.addWidget(t_label)
        left_layout.addWidget(self.class_btn)
        left_layout.addWidget(self.access_list)
        left_layout.addWidget(self.end_class_btn)
        
        # ==========================================
        # 2. 우측 메인 영역
        # ==========================================
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # 상단 정보표시 표시바 (시계, 교시, 학생관리, 최소화, 종료)
        header_bar = QHBoxLayout()
        self.period_label = QLabel()
        self.period_label.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.period_label.setStyleSheet("color: #059669; background-color: #D1FAE5; padding: 6px 18px; border-radius: 12px;")
        self.period_label.hide() 
        
        header_bar.addWidget(self.period_label)
        header_bar.addStretch()
        
        self.student_mgr_btn = QPushButton('👥 학생 관리')
        self.student_mgr_btn.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.student_mgr_btn.setFixedHeight(38)
        self.student_mgr_btn.setCursor(Qt.PointingHandCursor)
        self.student_mgr_btn.setStyleSheet("""
            QPushButton { 
                background-color: #EEF2FF; 
                color: #4F46E5; 
                border-radius: 10px; 
                padding: 0 16px;
                margin-right: 6px;
                border: 1.5px solid #C7D2FE;
            }
            QPushButton:hover { 
                background-color: #E0E7FF; 
            }
        """)
        self.student_mgr_btn.clicked.connect(self.open_student_manager)

        self.time_label = QLabel()
        self.time_label.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        self.time_label.setStyleSheet("color: #64748B; background-color: white; padding: 6px 18px; border-radius: 12px;")
        
        self.minimize_btn = QPushButton('➖ 최소화')
        self.minimize_btn.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.minimize_btn.setFixedHeight(38)
        self.minimize_btn.setCursor(Qt.PointingHandCursor)
        self.minimize_btn.setStyleSheet("""
            QPushButton { 
                background-color: #E0F2FE; 
                color: #0284C7; 
                border-radius: 10px; 
                padding: 0 16px;
                margin-left: 6px;
                border: none;
            }
            QPushButton:hover { 
                background-color: #BAE6FD; 
            }
        """)
        self.minimize_btn.clicked.connect(self.minimize_app)
        
        self.exit_btn = QPushButton('✖ 종료 (ESC)')
        self.exit_btn.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.exit_btn.setFixedHeight(38)
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.setStyleSheet("""
            QPushButton { 
                background-color: #FEE2E2; 
                color: #DC2626; 
                border-radius: 10px; 
                padding: 0 16px;
                margin-left: 6px;
                border: none;
            }
            QPushButton:hover { 
                background-color: #FECACA; 
            }
        """)
        self.exit_btn.clicked.connect(self.close)

        header_bar.addWidget(self.student_mgr_btn)
        header_bar.addWidget(self.time_label)
        header_bar.addWidget(self.minimize_btn)
        header_bar.addWidget(self.exit_btn)
        
        self.update_time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        # 중앙 메인 정보 카드
        center_card = QFrame()
        center_card.setStyleSheet("QFrame { background-color: white; border-radius: 18px; border: 1px solid #E2E8F0; }")
        shadow_center = QGraphicsDropShadowEffect()
        shadow_center.setBlurRadius(20)
        shadow_center.setColor(QColor(0, 0, 0, 15))
        shadow_center.setOffset(0, 6)
        center_card.setGraphicsEffect(shadow_center)
        
        cc_layout = QVBoxLayout(center_card)
        cc_layout.setContentsMargins(20, 14, 20, 14)
        cc_layout.setSpacing(8)
        
        # 상단 정보 영역
        self.top_info_container = QWidget()
        top_hbox = QHBoxLayout(self.top_info_container)
        top_hbox.setContentsMargins(0, 0, 0, 0)
        top_hbox.setSpacing(12)
        
        self.status = QLabel('학생 번호를 누르세요')
        self.status.setFont(QFont('Malgun Gothic', 22, QFont.Bold))
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: #0F172A; border: none;")
        
        # 큰 감정 아이콘 표시용 레이블
        self.emotion_icon_label = QLabel()
        self.emotion_icon_label.setFixedSize(90, 90)
        self.emotion_icon_label.setAlignment(Qt.AlignCenter)
        self.emotion_icon_label.setStyleSheet("border: none; background: transparent;")
        self.emotion_icon_label.hide()
        
        top_hbox.addStretch()
        top_hbox.addWidget(self.status, alignment=Qt.AlignCenter)
        top_hbox.addWidget(self.emotion_icon_label, alignment=Qt.AlignCenter)
        top_hbox.addStretch()
        
        cc_layout.addWidget(self.top_info_container)
        
        # 프로필 영역
        profile_layout = QHBoxLayout()
        profile_layout.setSpacing(20)
        
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(190, 250)
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet("background-color: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 18px; color: #94A3B8; font-size: 16px;")
        
        info_vbox = QVBoxLayout()
        info_vbox.setSpacing(10)
        
        self.detail = QTextBrowser()
        self.detail.setOpenLinks(False)
        self.detail.anchorClicked.connect(self.on_detail_anchor_clicked)
        self.detail.setReadOnly(True)
        self.detail.setFont(QFont('Malgun Gothic', 15))
        self.detail.setStyleSheet("color: #64748B; background: transparent; border: none;")
        self.detail.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.history = QLabel('')
        self.history.setFont(QFont('Malgun Gothic', 13))
        self.history.setStyleSheet("color: #475569; border: none; padding-top: 8px;")
        self.history.hide()
        
        info_vbox.addWidget(self.detail, stretch=1)
        info_vbox.addWidget(self.history)
        
        profile_layout.addWidget(self.photo_label, alignment=Qt.AlignTop)
        profile_layout.addLayout(info_vbox, stretch=1)
        
        cc_layout.addLayout(profile_layout, stretch=1)
        
        # 하단 바코드 입력창
        id_input_layout = QVBoxLayout()
        
        self.id_input = QLineEdit()
        self.id_input.setEchoMode(QLineEdit.Password)
        self.id_input.setFont(QFont('Arial', 32, QFont.Bold))
        self.id_input.setMaxLength(6)
        self.id_input.setAlignment(Qt.AlignCenter)
        self.id_input.setFixedSize(380, 68)
        self.id_input.setStyleSheet("""
            QLineEdit { 
                background-color: white; 
                border: 2.5px solid #94A3B8; 
                border-radius: 16px; 
                color: #0F172A; 
            }
            QLineEdit:focus { 
                border: 2.5px solid #3B82F6; 
                background-color: #EFF6FF; 
            }
        """)
        self.id_input.returnPressed.connect(self.process_enter)
        
        self.clear_btn = QPushButton("취소")
        self.clear_btn.setFont(QFont('Malgun Gothic', 14, QFont.Bold))
        self.clear_btn.setFixedSize(85, 68)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet("""
            QPushButton { 
                background-color: #F1F5F9; 
                color: #475569; 
                border-radius: 16px; 
                border: 2px solid #CBD5E1;
            }
            QPushButton:hover { 
                background-color: #E2E8F0; 
                color: #1E293B;
                border: 2px solid #94A3B8;
            }
        """)
        self.clear_btn.clicked.connect(lambda: self.id_input.clear() or self.id_input.setFocus())
        
        input_hbox = QHBoxLayout()
        input_hbox.setContentsMargins(0, 0, 0, 0)
        input_hbox.setAlignment(Qt.AlignCenter)
        input_hbox.addWidget(self.id_input)
        input_hbox.addSpacing(12)
        input_hbox.addWidget(self.clear_btn)

        id_input_layout.addLayout(input_hbox)
        cc_layout.addLayout(id_input_layout)
        
        # 하단 액션 바 (6개 버튼 균등 배치)
        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)
        
        self.prev_log_btn = QPushButton('📋 지난 수업 기록')
        self.prev_log_btn.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.prev_log_btn.setFixedHeight(50)
        self.prev_log_btn.setMinimumWidth(100)
        self.prev_log_btn.setCursor(Qt.PointingHandCursor)
        self.prev_log_btn.setToolTip("반을 선택하면 이전 수업 기록을 확인하실 수 있습니다.")
        self.prev_log_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #64748B;
                border: 2px dashed #CBD5E1;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                color: #334155;
            }
        """)
        self.prev_log_btn.clicked.connect(self.show_class_log_history)
        
        self.write_log_btn = QPushButton('📝 일지 작성')
        self.write_log_btn.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.write_log_btn.setFixedHeight(50)
        self.write_log_btn.setMinimumWidth(100)
        self.write_log_btn.setCursor(Qt.PointingHandCursor)
        self.write_log_btn.setStyleSheet("""
            QPushButton { background-color: #8B5CF6; color: white; border-radius: 12px; border: none; font-size: 12px; }
            QPushButton:hover { background-color: #7C3AED; }
        """)
        self.write_log_btn.clicked.connect(self.open_log_dialog)
        
        self.presenter_btn = QPushButton('🎤 발표자 뽑기')
        self.presenter_btn.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.presenter_btn.setFixedHeight(50)
        self.presenter_btn.setMinimumWidth(100)
        self.presenter_btn.setCursor(Qt.PointingHandCursor)
        self.presenter_btn.setStyleSheet("""
            QPushButton { background-color: #10B981; color: white; border-radius: 12px; border: none; font-size: 12px; }
            QPushButton:hover { background-color: #059669; }
        """)
        self.presenter_btn.clicked.connect(self.open_presenter_dialog)
        
        self.mvp_btn = QPushButton('🌟 오늘의 MVP')
        self.mvp_btn.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.mvp_btn.setFixedHeight(50)
        self.mvp_btn.setMinimumWidth(100)
        self.mvp_btn.setCursor(Qt.PointingHandCursor)
        self.mvp_btn.setStyleSheet("""
            QPushButton { background-color: #F59E0B; color: white; border-radius: 12px; border: none; font-size: 12px; }
            QPushButton:hover { background-color: #D97706; }
        """)
        self.mvp_btn.clicked.connect(self.open_mvp_dialog)
        
        self.overall_btn = QPushButton('🗓️ 출석 현황')
        self.overall_btn.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.overall_btn.setFixedHeight(50)
        self.overall_btn.setMinimumWidth(100)
        self.overall_btn.setCursor(Qt.PointingHandCursor)
        self.overall_btn.setStyleSheet("""
            QPushButton { background-color: #3B82F6; color: white; border-radius: 12px; border: none; font-size: 12px; }
            QPushButton:hover { background-color: #2563EB; }
        """)
        self.overall_btn.clicked.connect(self.show_overall_attendance)
        
        self.mvp_stats_btn = QPushButton('📊 전체 통계')
        self.mvp_stats_btn.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.mvp_stats_btn.setFixedHeight(50)
        self.mvp_stats_btn.setMinimumWidth(100)
        self.mvp_stats_btn.setCursor(Qt.PointingHandCursor)
        self.mvp_stats_btn.setStyleSheet("""
            QPushButton { background-color: white; color: #334155; border-radius: 12px; border: 1.5px solid #E2E8F0; font-size: 12px; }
            QPushButton:hover { background-color: #F8FAFC; }
        """)
        self.mvp_stats_btn.clicked.connect(self.show_mvp_stats)
        
        action_bar.addWidget(self.prev_log_btn, 1)
        action_bar.addWidget(self.write_log_btn, 1)
        action_bar.addWidget(self.presenter_btn, 1)
        action_bar.addWidget(self.mvp_btn, 1)
        action_bar.addWidget(self.overall_btn, 1)
        action_bar.addWidget(self.mvp_stats_btn, 1)
        
        right_layout.addLayout(header_bar)
        right_layout.addWidget(center_card, stretch=1)
        right_layout.addLayout(action_bar)
        
        main_layout.addWidget(left_panel)
        main_layout.addLayout(right_layout, stretch=1)
        
        self.class_combo.activated.connect(lambda: self.id_input.setFocus())
        self.class_combo.currentTextChanged.connect(self.update_log_display)
        if self.class_combo.lineEdit():
            self.class_combo.lineEdit().returnPressed.connect(lambda: self.id_input.setFocus())

        self.revert_timer = QTimer(self)
        self.revert_timer.setSingleShot(True)
        self.revert_timer.timeout.connect(self.show_default_class_log)

        self.showFullScreen()
        self.id_input.setFocus()
        self.reset_screen(reset_class=True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_F4:
            self.open_presenter_dialog()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.minimize_app()
        super().changeEvent(event)

    def minimize_app(self):
        self.hide()
        self.update_time()
        self.mini_timer.show()

    def show_class_log_history(self):
        class_name = self.class_combo.currentText()
        if class_name == "수업명 입력/선택" or not class_name.strip():
            QMessageBox.information(self, "안내", "수업반을 먼저 선택해 주세요.")
            return
        if class_name in self.class_logs and self.class_logs[class_name]:
            dlg = LogHistoryDialog(class_name, self.class_logs[class_name], self)
            dlg.exec_()
        else:
            QMessageBox.information(self, "안내", f"[{class_name}] 에 등록된 이전 수업 기록이 없습니다.")

    def update_log_display(self, class_name):
        # 반이 선택되면 확정(잠금) 처리 및 시각적 표시
        if class_name != "수업명 입력/선택" and class_name.strip():
            self.class_combo.setEnabled(False)
            self.class_combo.setStyleSheet("""
                QComboBox, QComboBox:disabled {
                    border: 2px solid #10B981; border-radius: 10px; padding: 5px 15px; background-color: #ECFDF5; color: #047857; font-weight: bold;
                }
            """)
            self.class_btn.setText(f"🏫 {class_name}")
            self.class_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ECFDF5;
                    color: #047857;
                    border: 2px solid #10B981;
                    border-radius: 15px;
                    padding: 5px 15px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #D1FAE5;
                    color: #065F46;
                    border: 2px solid #059669;
                }
            """)
            self.refresh_list()
        else:
            self.class_btn.setText("🏫 수업반을 선택하세요")
            self.class_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9;
                    color: #475569;
                    border: 2px dashed #CBD5E1;
                    border-radius: 15px;
                    padding: 5px 15px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #EFF6FF;
                    color: #2563EB;
                    border: 2px solid #3B82F6;
                }
            """)
            
        if class_name in self.class_logs and self.class_logs[class_name]:
            last_log = self.class_logs[class_name][-1]
            date_short = last_log['date'][:10]
            self.prev_log_btn.setText(f"📋 지난 수업 기록\n({date_short})")
            self.prev_log_btn.setToolTip(f"📅 최근 기록 일시: {last_log['date']}\n\n📝 내용:\n{last_log['content']}\n\n💡 클릭하면 전체 수업 기록을 확인 및 관리할 수 있습니다.")
            self.prev_log_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FEF3C7;
                    color: #92400E;
                    border: 2px solid #F59E0B;
                    border-radius: 15px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #FDE68A;
                }
            """)
        else:
            self.prev_log_btn.setText('📋 지난 수업 기록\n(기록 없음)')
            self.prev_log_btn.setToolTip("이전 수업 기록이 없습니다.\n클릭하여 확인할 수 있습니다.")
            self.prev_log_btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #94A3B8;
                    border: 2px dashed #CBD5E1;
                    border-radius: 15px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F8FAFC;
                    color: #64748B;
                }
            """)
            
        self.show_default_class_log()
        self.id_input.setFocus()

    def open_log_dialog(self):
        class_name = self.class_combo.currentText()
        if class_name == "수업명 입력/선택" or not class_name.strip():
            QMessageBox.warning(self, "안내", "수업 일지를 작성할 '현재 진행 수업(반)'을 먼저 선택해 주세요.")
            return
            
        dlg = LogWriteDialog(class_name, self)
        if dlg.exec_() == QDialog.Accepted:
            new_log = {
                "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
                "content": dlg.result_text
            }
            if class_name not in self.class_logs:
                self.class_logs[class_name] = []
            self.class_logs[class_name].append(new_log)
            
            with open(self.class_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.class_logs, f, ensure_ascii=False, indent=4)
                
            self.update_log_display(class_name)
            
    def open_presenter_dialog(self):
        current_class = self.class_combo.currentText()
        has_class = (current_class != "수업명 입력/선택" and current_class.strip())
        
        candidates = []
        for s_id, info in self.active_students.items():
            # 결석(학교 결석, 수업 결석) 제외하고 실제 '출석' 상태인 학생만 대상
            if info.get('status') == '출석':
                s = self.students_data.get(s_id, {})
                if has_class:
                    info_str = " ".join(str(v) for v in s.values())
                    if current_class not in info_str:
                        continue
                name = s.get('이름', info.get('name', '이름 없음'))
                pic_key = next((k for k in s.keys() if '사진' in k), None)
                pic_filename = s.get(pic_key, '') if pic_key else ''
                photo_path = os.path.join(self.base_dir, 'photos', pic_filename) if pic_filename else ''
                candidates.append({'id': s_id, 'name': name, 'photo': photo_path})
                
        if not candidates:
            if has_class:
                QMessageBox.warning(self, "안내", f"[{current_class}] 에 오늘 출석한 학생이 없습니다.\n(결석자는 발표자 추첨에서 제외됩니다)")
            else:
                QMessageBox.warning(self, "안내", "현재 출석한 학생이 없어 발표자를 추첨할 수 없습니다.")
            return

        if len(candidates) == 1:
            dlg = PresenterRouletteDialog(candidates, self)
            dlg.exec_()
            return

        # 룰렛 vs 사다리 vs 제비뽑기 vs 레이스 모드 선택
        mode_dlg = PresenterModeSelectDialog(self)
        if mode_dlg.exec_() == QDialog.Accepted and mode_dlg.selected_mode:
            if mode_dlg.selected_mode == 'roulette':
                dlg = PresenterRouletteDialog(candidates, self)
                dlg.exec_()
            elif mode_dlg.selected_mode == 'ladder':
                dlg = PresenterLadderDialog(candidates, self)
                dlg.exec_()
            elif mode_dlg.selected_mode == 'lottery':
                dlg = PresenterLotteryDialog(candidates, self)
                dlg.exec_()
            elif mode_dlg.selected_mode == 'race':
                dlg = PresenterRaceDialog(candidates, self)
                dlg.exec_()

    def open_mvp_dialog(self):
        if not self.active_students:
            QMessageBox.warning(self, "안내", "현재 출석한 학생이 없어 투표를 진행할 수 없습니다.")
            return
            
        dlg = MVPVoteDialog(self.active_students, self.students_data, self)
        dlg.exec_()

    def save_mvp_log(self, s_id, name):
        new = not os.path.exists(self.mvp_file)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.mvp_file, 'a', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            if new: w.writerow(['날짜', '학번', '이름'])
            w.writerow([now, s_id, name])
            
    def show_mvp_stats(self):
        dlg = MVPStatsDialog(self.mvp_file, self.log_file, self)
        dlg.exec_()

    def show_overall_attendance(self):
        classes = self.get_class_list()
        if not classes:
            QMessageBox.warning(self, "안내", "등록된 반 정보가 없습니다.")
            return
            
        current_class = self.class_combo.currentText()
        if current_class == "수업명 입력/선택":
            current_class = ""
            
        dlg = OverallAttendanceDialog(self.students_data, self.log_file, self.absence_file, classes, current_class, self)
        dlg.exec_()

    def update_time(self):
        now = datetime.now()
        weekdays = ['월', '화', '수', '목', '금', '토', '일']
        time_str = now.strftime(f'%Y년 %m월 %d일 ({weekdays[now.weekday()]}) %p %I:%M:%S').replace('AM', '오전').replace('PM', '오후')
        self.time_label.setText(time_str)
        
        # 교시 별 일정
        current_time_minutes = now.hour * 60 + now.minute
        current_period = None
        remaining_minutes = 0
        
        schedule = [
            ("1교시", 9*60+0, 9*60+40),
            ("2교시", 9*60+45, 10*60+25),
            ("3교시", 10*60+30, 11*60+10),
            ("4교시", 11*60+15, 11*60+55),
            ("5교시", 12*60+0, 12*60+40),
            ("6교시", 13*60+35, 14*60+15),
            ("7교시", 14*60+25, 15*60+5),
            ("8교시", 15*60+10, 15*60+50)
        ]
        
        for name, start_m, end_m in schedule:
            if start_m <= current_time_minutes <= end_m:
                current_period = name
                remaining_minutes = end_m - current_time_minutes
                break
                
        if current_period:
            if remaining_minutes == 0:
                self.period_label.setText(f"🕒 {current_period} (곧 종료)")
            else:
                self.period_label.setText(f"🕒 {current_period} ({remaining_minutes}분 남음)")
            
            # 종료 5분 이하 경고색 표시
            if remaining_minutes <= 5:
                self.period_label.setStyleSheet("color: #DC2626; background-color: #FEE2E2; padding: 10px 25px; border-radius: 15px;")
            else:
                self.period_label.setStyleSheet("color: #059669; background-color: #D1FAE5; padding: 10px 25px; border-radius: 15px;")
            
            self.period_label.show()
        else:
            self.period_label.hide()

        if hasattr(self, 'mini_timer'):
            self.mini_timer.update_time_display(current_period, remaining_minutes)

    def refresh_list(self):
        self.access_list.clear()
        
        class_name = self.class_combo.currentText()
        if class_name != "수업명 입력/선택" and class_name.strip() and not self.class_combo.isEnabled():
            class_students = []
            for s_id, s_info in self.students_data.items():
                info_str = " ".join(str(v) for v in s_info.values())
                if class_name in info_str:
                    class_students.append(s_id)
            
            class_students.sort()
            
            # 1. 반 헤더 아이템 제거됨 (공간 확보)

            
            # 2. 반 학생 목록
            for s_id in class_students:
                s_info = self.students_data[s_id]
                s_name = s_info.get('이름', '이름 없음')
                
                is_attended = s_id in self.active_students
                time_s = self.active_students[s_id]['time'] if is_attended else ""
                emo = self.active_students[s_id].get('emotion', '') if is_attended else ""
                st_type = self.active_students[s_id].get('status', '출석') if is_attended else "미출석"
                
                # 사진 경로
                pic_key = next((k for k in s_info.keys() if '사진' in k), None)
                pic_filename = s_info.get(pic_key, '') if pic_key else ''
                photo_path = os.path.join(self.base_dir, 'photos', pic_filename)
                
                # 커스텀 위젯 생성 및 추가
                item = QListWidgetItem()
                item.setData(Qt.UserRole, s_id)
                widget = StudentItemWidget(s_id, s_name, time_s, emo, photo_path, is_attended, st_type)
                item.setSizeHint(widget.sizeHint())
                self.access_list.addItem(item)
                self.access_list.setItemWidget(item, widget)
                
            # 3. 타반 출석 헤더 제거됨
            other_students = [s_id for s_id in self.active_students if s_id not in class_students]
            if other_students:

                
                for s_id in other_students:
                    s_info = self.students_data.get(s_id, {})
                    s_name = self.active_students[s_id]['name']
                    time_s = self.active_students[s_id]['time']
                    emo = self.active_students[s_id].get('emotion', '')
                    st_type = self.active_students[s_id].get('status', '출석')
                    
                    pic_key = next((k for k in s_info.keys() if '사진' in k), None)
                    pic_filename = s_info.get(pic_key, '') if pic_key else ''
                    photo_path = os.path.join(self.base_dir, 'photos', pic_filename)
                    
                    item = QListWidgetItem()
                    item.setData(Qt.UserRole, s_id)
                    widget = StudentItemWidget(s_id, s_name, time_s, emo, photo_path, True, st_type)
                    item.setSizeHint(widget.sizeHint())
                    self.access_list.addItem(item)
                    self.access_list.setItemWidget(item, widget)
        else:
            # 반 선택 전 기본 목록 표시
            for s_id, info in reversed(list(self.active_students.items())):
                s_info = self.students_data.get(s_id, {})
                emo = info.get('emotion', '')
                st_type = info.get('status', '출석')
                
                pic_key = next((k for k in s_info.keys() if '사진' in k), None)
                pic_filename = s_info.get(pic_key, '') if pic_key else ''
                photo_path = os.path.join(self.base_dir, 'photos', pic_filename)
                
                item = QListWidgetItem()
                item.setData(Qt.UserRole, s_id)
                widget = StudentItemWidget(s_id, info['name'], info['time'], emo, photo_path, True, st_type)
                item.setSizeHint(widget.sizeHint())
                self.access_list.addItem(item)
                self.access_list.setItemWidget(item, widget)
            
    def cancel_attendance(self, item):
        s_id = item.data(Qt.UserRole)
        if not s_id: 
            return
            
        info = self.active_students.get(s_id)
        s_info = self.students_data.get(s_id, {})
        s_name = s_info.get('이름', info['name'] if info else '이름 없음')
        
        pic_key = next((k for k in s_info.keys() if '사진' in k), None)
        pic_filename = s_info.get(pic_key, '') if pic_key else ''
        photo_path = os.path.join(self.base_dir, 'photos', pic_filename) if pic_filename else None
        
        if not info:
            dlg = ManualAttendanceDialog(s_name, photo_path=photo_path, parent=self)
            if dlg.exec_() == QDialog.Accepted and dlg.selected_action:
                action = dlg.selected_action
                if action == '출석':
                    self.lookup(s_id)
                elif action in ['학교 결석', '수업 결석']:
                    self.record_manual_absence(s_id, s_name, action)
            return
            
        reply_menu = QMenu(self)
        action_view = reply_menu.addAction("👤 학생 정보 및 출결·감정 보기")
        action_change = reply_menu.addAction("🔄 출결 상태 변경")
        action_cancel = reply_menu.addAction("❌ 출결 기록 취소")
        
        pos = QCursor.pos()
        selected = reply_menu.exec_(pos)
        
        if selected == action_view:
            self.display_student_profile(s_id, status_type=info.get('status', '출석'), emotion=info.get('emotion', ''))
        elif selected == action_change:
            dlg = ManualAttendanceDialog(s_name, photo_path=photo_path, parent=self)
            if dlg.exec_() == QDialog.Accepted and dlg.selected_action:
                action = dlg.selected_action
                if action == '출석':
                    self.lookup(s_id)
                elif action in ['학교 결석', '수업 결석']:
                    self.record_manual_absence(s_id, s_name, action)
        elif selected == action_cancel:
            self.log_entry(s_id, info['name'], '취소')
            if s_id in self.active_students:
                del self.active_students[s_id]
            self.refresh_list()
            self.id_input.setFocus()

    def build_student_dashboard_html(self, s_id, name, class_info, today_status, today_time, today_emotion, logs):
        emojis_dir = os.path.join(self.base_dir, "emojis").replace("\\", "/")
        
        EMOTION_META = {
            "좋아요": {
                "file": "1_good.png", "color": "#047857", "bg": "#ECFDF5", "border": "#10B981", 
                "badge": "😊", "guide": "차분하고 안정적으로 수업에 잘 참여하고 있습니다 ✨"
            },
            "신나요": {
                "file": "2_excited.png", "color": "#B45309", "bg": "#FFFBEB", "border": "#F59E0B", 
                "badge": "🎉", "guide": "학습 의욕과 긍정 에너지가 매우 높은 상태입니다 🚀"
            },
            "괜찮아요": {
                "file": "3_okay.png", "color": "#1D4ED8", "bg": "#EFF6FF", "border": "#3B82F6", 
                "badge": "🙂", "guide": "특별한 문제 없이 평온하게 수업에 참여하고 있습니다 🌿"
            },
            "졸려요": {
                "file": "4_sleepy.png", "color": "#475569", "bg": "#F8FAFC", "border": "#94A3B8", 
                "badge": "🥱", "guide": "피로감을 느끼는 상태이므로 가벼운 스트레칭을 권해보세요 ☕"
            },
            "슬퍼요": {
                "file": "5_sad.png", "color": "#4338CA", "bg": "#EEF2FF", "border": "#6366F1", 
                "badge": "😢", "guide": "마음이 다소 가라앉아 있어 따뜻한 격려와 관심이 필요합니다 💧"
            },
            "화나요": {
                "file": "6_angry.png", "color": "#B91C1C", "bg": "#FEF2F2", "border": "#EF4444", 
                "badge": "😡", "guide": "답답하거나 속상한 일이 있어 조용한 경청과 공감이 필요합니다 👂"
            },
            "무서워요": {
                "file": "7_scared.png", "color": "#6D28D9", "bg": "#F5F3FF", "border": "#8B5CF6", 
                "badge": "😨", "guide": "긴장되거나 불안한 상태이므로 안도감을 주는 격려를 해주세요 🛡️"
            },
            "안좋아요": {
                "file": "8_bad.png", "color": "#C2410C", "bg": "#FFF7ED", "border": "#EA580C", 
                "badge": "😕", "guide": "기운이 없거나 피곤할 수 있으니 따뜻하게 안부를 물어봐 주세요 💬"
            },
            "짜증나요": {
                "file": "9_annoyed.png", "color": "#BE123C", "bg": "#FFF1F2", "border": "#E11D48", 
                "badge": "😤", "guide": "마음이 다소 예민한 상태이므로 잠시 차분한 호흡이 도움 됩니다 🌿"
            }
        }
        
        # 1. 오늘의 기분 눈에 띄는 강조 카드 (Prominent Today's Mood Card)
        today_emo_card_html = ""
        if today_emotion and today_emotion in EMOTION_META:
            meta = EMOTION_META[today_emotion]
            icon_url = "file:///" + emojis_dir + "/" + meta["file"]
            today_emo_card_html = f'''
            <div style="background-color: {meta['bg']}; border: 2.5px solid {meta['border']}; border-radius: 14px; padding: 12px 22px; text-align: left; display: inline-block;">
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td valign="middle" style="padding-right: 14px;">
                    <img src="{icon_url}" width="54" height="54" style="vertical-align: middle;" />
                  </td>
                  <td valign="middle">
                    <div style="font-size: 10pt; color: #64748B; font-weight: bold; margin-bottom: 2px;">🌟 오늘의 기분 (TODAY'S MOOD)</div>
                    <div style="font-size: 20pt; font-weight: bold; color: {meta['color']};">{today_emotion} {meta['badge']}</div>
                  </td>
                </tr>
              </table>
            </div>
            '''
        else:
            today_emo_card_html = '''
            <div style="background-color: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 14px; padding: 12px 20px; text-align: center; display: inline-block;">
              <div style="font-size: 10pt; color: #94A3B8; font-weight: bold; margin-bottom: 2px;">오늘의 기분</div>
              <span style="font-size: 12pt; color: #64748B; font-weight: bold;">등록된 기분 없음</span>
            </div>
            '''

        status_bg = "#ECFDF5" if "출석" in today_status else ("#FEF3C7" if "학교" in today_status else "#FEF2F2")
        status_color = "#047857" if "출석" in today_status else ("#D97706" if "학교" in today_status else "#B91C1C")
        status_border = "#A7F3D0" if "출석" in today_status else ("#FDE68A" if "학교" in today_status else "#FECACA")

        # 2. 통합 출결 및 감정 기록표 (Crisp Grid Table)
        rev_logs = list(reversed(logs))[:6]
        table_rows = ""
        if rev_logs:
            for idx, item in enumerate(rev_logs, 1):
                t_str = item.get("time", "")
                st = item.get("status", "출석")
                emo = item.get("emotion", "")

                st_color = "#047857" if "출석" in st else ("#D97706" if "학교" in st else "#B91C1C")
                st_bg = "#ECFDF5" if "출석" in st else ("#FEF3C7" if "학교" in st else "#FEF2F2")
                st_border = "#A7F3D0" if "출석" in st else ("#FDE68A" if "학교" in st else "#FECACA")

                emo_cell = ""
                if emo and emo in EMOTION_META:
                    m = EMOTION_META[emo]
                    emo_url = "file:///" + emojis_dir + "/" + m["file"]
                    emo_cell = f'''<span style="background-color: {m['bg']}; color: {m['color']}; border: 1.5px solid {m['border']}; padding: 4px 12px; border-radius: 6px; font-size: 11pt; font-weight: bold;"><img src="{emo_url}" width="16" height="16" style="vertical-align: middle;" /> {emo}</span>'''
                else:
                    emo_cell = '<span style="color: #94A3B8; font-size: 10.5pt;">기록 없음</span>'

                row_bg = "#FFFFFF" if idx % 2 == 1 else "#F8FAFC"
                table_rows += f'''
                <tr style="background-color: {row_bg};">
                  <td align="center" style="border-bottom: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; padding: 10px 6px; font-size: 11pt; color: #64748B; font-weight: bold;">
                    {idx}
                  </td>
                  <td style="border-bottom: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; padding: 10px 16px; font-size: 11pt; color: #1E293B; font-weight: bold;">
                    🕒 {t_str}
                  </td>
                  <td align="center" style="border-bottom: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; padding: 10px 8px;">
                    <span style="background-color: {st_bg}; color: {st_color}; border: 1px solid {st_border}; padding: 3px 14px; border-radius: 6px; font-size: 10.5pt; font-weight: bold;">{st}</span>
                  </td>
                  <td align="center" style="border-bottom: 1px solid #E2E8F0; padding: 10px 10px;">
                    {emo_cell}
                  </td>
                </tr>
                '''
        else:
            table_rows = '<tr><td colspan="4" align="center" style="padding: 35px; color: #94A3B8; font-size: 12pt;">출결 기록이 없습니다.</td></tr>'

        # 3. 하단 요약 통계 바 (Cumulative attendance, top emotion, recent timeline)
        all_emotions = [x["emotion"] for x in logs if x.get("emotion") and x["emotion"] in EMOTION_META]
        counts = Counter(all_emotions)

        ranking_parts = []
        medals = ["🥇", "🥈", "🥉"]
        for i, (emo_name, cnt) in enumerate(counts.most_common(2)):
            ranking_parts.append(f"{medals[i]} {emo_name} ({cnt}회)")
        ranking_summary = " · ".join(ranking_parts) if ranking_parts else "기록 없음"

        flow_chips = []
        for item in rev_logs[:5]:
            emo = item.get("emotion")
            date_short = item.get("time", "")[5:10].replace("-", "/")
            if emo and emo in EMOTION_META:
                m = EMOTION_META[emo]
                flow_chips.append(f"{m['badge']} {emo}({date_short})")
        flow_summary = " ➔ ".join(flow_chips) if flow_chips else "기록 없음"

        # 학년반 및 특이사항 태그
        class_lines = [cl.strip() for cl in class_info.split('\n') if cl.strip()]
        class_badge_txt = class_lines[0] if class_lines else "미배정"
        extra_note_html = ""
        if len(class_lines) > 1:
            extra_notes = " · ".join(class_lines[1:])
            extra_note_html = f'''<span style="background-color: #FEF3C7; color: #92400E; font-size: 10pt; font-weight: bold; padding: 4px 10px; border-radius: 6px; border: 1px solid #FDE68A; margin-left: 8px;">📌 {html.escape(extra_notes)}</span>'''

        html_out = f'''
        <div style="font-family: 'Malgun Gothic', sans-serif; padding: 2px;">
          <!-- 1. Header Card (일체형 프로필 + 강조된 오늘의 기분) -->
          <div style="background-color: #FFFFFF; border: 2px solid #E2E8F0; border-radius: 16px; padding: 16px 22px; margin-bottom: 14px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td valign="middle">
                  <div style="margin-bottom: 8px;">
                    <span style="font-size: 26pt; font-weight: bold; color: #0F172A; letter-spacing: -0.5px;">{html.escape(name)}</span>
                    <span style="background-color: #EEF2FF; color: #4F46E5; font-size: 12.5pt; font-weight: bold; padding: 5px 14px; border-radius: 8px; border: 1.5px solid #C7D2FE; margin-left: 12px;">🏫 {html.escape(class_badge_txt)}</span>
                    <span style="background-color: #F1F5F9; color: #475569; font-size: 12.5pt; font-weight: bold; padding: 5px 14px; border-radius: 8px; border: 1.5px solid #E2E8F0; margin-left: 8px;">학번: {html.escape(s_id)}</span>
                    {extra_note_html}
                  </div>
                  <div>
                    <span style="background-color: {status_bg}; color: {status_color}; border: 1.5px solid {status_border}; font-size: 12pt; font-weight: bold; padding: 6px 14px; border-radius: 8px;">
                      🟢 오늘 출석: {today_time} {today_status} 완료
                    </span>
                  </div>
                </td>
                <td align="right" valign="middle">
                  {today_emo_card_html}
                </td>
              </tr>
            </table>
          </div>

          <!-- 2. Clean Grid Table (반듯한 통합 격자 표) -->
          <div style="background-color: #FFFFFF; border: 2px solid #E2E8F0; border-radius: 16px; padding: 16px 20px; margin-bottom: 14px;">
            <div style="margin-bottom: 12px;">
              <span style="font-size: 13.5pt; font-weight: bold; color: #0F172A;">📋 최근 출결 및 감정 기록</span>
              <span style="color: #64748B; font-size: 10pt; margin-left: 8px;">(최근 {len(rev_logs)}회 기록)</span>
            </div>

            <table width="100%" cellpadding="8" cellspacing="0" style="border: 1.5px solid #CBD5E1; border-collapse: collapse; border-radius: 8px;">
              <thead>
                <tr style="background-color: #F1F5F9;">
                  <th width="10%" align="center" style="border-bottom: 2px solid #CBD5E1; border-right: 1px solid #CBD5E1; font-size: 11pt; color: #334155; padding: 10px 4px;">순번</th>
                  <th width="38%" align="left" style="border-bottom: 2px solid #CBD5E1; border-right: 1px solid #CBD5E1; font-size: 11pt; color: #334155; padding: 10px 16px;">출결 일시</th>
                  <th width="24%" align="center" style="border-bottom: 2px solid #CBD5E1; border-right: 1px solid #CBD5E1; font-size: 11pt; color: #334155; padding: 10px 6px;">출결 상태</th>
                  <th width="28%" align="center" style="border-bottom: 2px solid #CBD5E1; font-size: 11pt; color: #334155; padding: 10px 6px;">당일 감정</th>
                </tr>
              </thead>
              <tbody>
                {table_rows}
              </tbody>
            </table>
          </div>

          <!-- 3. Bottom Stats Summary Bar (깔끔한 3분할 요약) -->
          <div style="background-color: #FFFFFF; border: 2px solid #E2E8F0; border-radius: 14px; padding: 12px 20px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="30%" valign="middle" style="border-right: 1px solid #E2E8F0; padding-right: 14px;">
                  <span style="font-size: 10pt; color: #64748B; font-weight: bold;">📊 누적 출결:</span>
                  <span style="font-size: 11pt; color: #0F172A; font-weight: bold; margin-left: 6px;">총 {len(logs)}회 기록</span>
                </td>
                <td width="35%" valign="middle" style="border-right: 1px solid #E2E8F0; padding-left: 14px; padding-right: 14px;">
                  <span style="font-size: 10pt; color: #64748B; font-weight: bold;">💖 최다 기분:</span>
                  <span style="font-size: 11pt; color: #0F172A; font-weight: bold; margin-left: 6px;">{ranking_summary}</span>
                </td>
                <td width="35%" valign="middle" style="padding-left: 14px;">
                  <span style="font-size: 10pt; color: #64748B; font-weight: bold;">🌈 최근 기분 추이:</span>
                  <span style="font-size: 10.5pt; color: #334155; font-weight: bold; margin-left: 6px;">{flow_summary}</span>
                </td>
              </tr>
            </table>
          </div>
        </div>
        '''
        return html_out

    def display_student_profile(self, s_id, status_type='출석', emotion=''):
        self.current_id = s_id
        s = self.students_data.get(s_id, {})
        name = s.get('이름', '이름 없음')
        
        # 키 호환성 지원 (학생정보, 상세정보, 특이사항, 학년반 등)
        info_key = None
        for k in s.keys():
            if ('정보' in k or '상세' in k or '특이' in k or '학년' in k or '반' in k) and ('번호' not in k and '학번' not in k):
                info_key = k
                break
        class_info = s.get(info_key, '') if info_key else (s.get('학생정보', '') or s.get('학년반', ''))
        if not class_info:
            current_c = self.class_combo.currentText()
            class_info = current_c if current_c != "수업명 입력/선택" and current_c.strip() else "미배정"
            
        # 학생 사진 출력
        pic_key = next((k for k in s.keys() if '사진' in k), None)
        pic_filename = s.get(pic_key, '') if pic_key else ''
        p = os.path.join(self.base_dir, 'photos', pic_filename) if pic_filename else ''
        if p and os.path.exists(p) and os.path.isfile(p):
            self.photo_label.setPixmap(QPixmap(p).scaled(self.photo_label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.photo_label.setStyleSheet("border-radius: 18px; border: 2.5px solid #CBD5E1; background-color: white;")
        else:
            self.photo_label.clear()
            self.photo_label.setText("👤\n\n사진 없음")
            self.photo_label.setStyleSheet("background-color: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 18px; color: #94A3B8; font-size: 16px; font-weight: bold;")

        # 최근 출결 및 감정 기록 수집
        student_logs = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8-sig') as f:
                r = csv.reader(f)
                for row in r:
                    if len(row) >= 4 and row[1] == s_id and row[3] not in ('하교', '취소'):
                        student_logs.append({
                            'time': row[0],
                            'status': row[3],
                            'emotion': row[4] if len(row) >= 5 else ''
                        })

        today_time = datetime.now().strftime('%H:%M')
        if s_id in self.active_students:
            today_time = self.active_students[s_id].get('time', today_time)
            if not emotion:
                emotion = self.active_students[s_id].get('emotion', '')

        dashboard_html = self.build_student_dashboard_html(
            s_id=s_id,
            name=name,
            class_info=class_info,
            today_status=status_type,
            today_time=today_time,
            today_emotion=emotion,
            logs=student_logs
        )
        self.detail.setHtml(dashboard_html)
        self.detail.setStyleSheet("QTextBrowser { background: transparent; border: none; }")
        self.history.hide()
        self.photo_label.show()
        self.status.show()

        # 학생 정보 표시 7초 뒤 원래(수업) 화면으로 복귀
        self.revert_timer.start(7000)

    def record_manual_absence(self, s_id, s_name, status_type):
        time_s = datetime.now().strftime('%H:%M')
        self.log_entry(s_id, s_name, status_type, "")
        self.active_students[s_id] = {
            'name': s_name, 
            'time': time_s, 
            'emotion': '', 
            'status': status_type
        }
        self.refresh_list()
        
        if status_type == '학교 결석':
            self.status.setText(f"[학교 결석] {s_name} 학생")
            self.status.setStyleSheet("color: #D97706; font-size: 32pt;")
            self.emotion_icon_label.hide()
            self.play_tts(f"{s_name} 학생, 학교 결석 처리되었습니다.")
        elif status_type == '수업 결석':
            self.status.setText(f"[수업 결석] {s_name} 학생")
            self.status.setStyleSheet("color: #DB2777; font-size: 32pt;")
            self.emotion_icon_label.hide()
            self.play_tts(f"{s_name} 학생, 수업 결석 처리되었습니다.")
            
        self.display_student_profile(s_id, status_type=status_type, emotion='')

    def load_today_attendance(self):
        self.active_students.clear()
        if os.path.exists(self.log_file):
            t_str = datetime.now().strftime('%Y-%m-%d')
            with open(self.log_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader, None)
                for r in reader:
                    if len(r) >= 3 and r[0].startswith(t_str):
                        time_s, s_id, s_name = r[0], r[1], r[2]
                        st = r[3] if len(r) >= 4 else '출석'
                        emo = r[4] if len(r) >= 5 else ''
                        if st in ['출석', '학교 결석', '수업 결석']: 
                            self.active_students[s_id] = {'name': s_name, 'time': time_s.split(' ')[1][:5], 'emotion': emo, 'status': st}
                        elif (st == '하교' or st == '취소') and s_id in self.active_students: del self.active_students[s_id]
        self.refresh_list()

    def log_entry(self, s_id, name, st, emotion=""):
        new = not os.path.exists(self.log_file)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, 'a', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            if new: w.writerow(['시간', '학번', '이름', '상태', '감정'])
            w.writerow([now, s_id, name, st, emotion])

    def process_enter(self):
        txt = self.id_input.text()
        if txt:
            self.lookup(txt)
            self.id_input.clear()
            self.id_input.setFocus()

    def lookup(self, s_id):
        self.photo_label.show()
        self.status.show()
        s = self.students_data.get(s_id)
        if not s:
            self.status.setText("출결 오류")
            self.status.setStyleSheet("color: #E74C3C;")
            self.detail.setText("등록되지 않은 학번입니다.")
            self.photo_label.clear()
            self.photo_label.setText('접근 차단')
            self.history.hide()
            self.play_tts("등록되지 않은 학생입니다.")
            return

        self.current_id = s_id
        name = s.get('이름', '이름 없음')
        
        # 키 호환성 지원 (학생정보, 상세정보, 특이사항, 학년반 등)
        info_key = next((k for k in s.keys() if '정보' in k or '상세' in k or '특이' in k or '학년' in k or '반' in k), None)
        details = s.get(info_key, '') if info_key else ''
        
        today_emotion = ""
        today_status = '출석'
        if s_id in self.active_students:
            self.status.setText(f"{name} 학생")
            self.status.setStyleSheet("color: #2980B9;")
            self.play_tts(f"{name} 학생은 이미 출석 확인되었습니다.")
            today_entry = self.active_students[s_id]
            today_emotion = today_entry.get('emotion', '')
            today_status = today_entry.get('status', '출석')
        else:
            dlg = EmotionSelectDialog(name, self)
            if dlg.exec_() != QDialog.Accepted:
                self.id_input.clear()
                self.id_input.setFocus()
                current_class = self.class_combo.currentText()
                if current_class != "수업명 입력/선택" and current_class.strip():
                    self.show_default_class_log()
                else:
                    self.reset_screen(reset_class=False)
                return
                
            emotion = dlg.emotion if dlg.emotion else ""
            today_emotion = emotion
            
            self.log_entry(s_id, name, '출석', emotion)
            self.active_students[s_id] = {'name': name, 'time': datetime.now().strftime('%H:%M'), 'emotion': emotion, 'status': '출석'}
            self.refresh_list()
            
            self.play_tts(f"{name} 학생, 출석 완료되었습니다.")
            
            # 감정 아이콘 크게 표시
            emojis_map = {
                "좋아요": "1_good.png", "신나요": "2_excited.png", "괜찮아요": "3_okay.png", "안좋아요": "8_bad.png",
                "졸려요": "4_sleepy.png", "슬퍼요": "5_sad.png", "화나요": "6_angry.png", "무서워요": "7_scared.png",
                "짜증나요": "9_annoyed.png"
            }
            img_file = emojis_map.get(emotion)
            if img_file:
                img_path = os.path.join(self.base_dir, 'emojis', img_file)
                if os.path.exists(img_path):
                    self.emotion_icon_label.setPixmap(QPixmap(img_path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self.emotion_icon_label.show()
            else:
                self.emotion_icon_label.hide()
            
            emo_txt = f"[{emotion}] " if emotion else ""
            self.status.setText(f"{emo_txt}{name} 학생")
            self.status.setStyleSheet("color: #27AE60; font-size: 32pt;")
        
        self.display_student_profile(s_id, status_type=today_status, emotion=today_emotion)

    def play_tts(self, text):
        tts_thread = TTSThread(text, self)
        if not hasattr(self, 'tts_threads'):
            self.tts_threads = []
        self.tts_threads.append(tts_thread)
        tts_thread.finished.connect(lambda t=tts_thread: self.tts_threads.remove(t) if t in getattr(self, 'tts_threads', []) else None)
        tts_thread.start()

    def end_all_class(self):
        # 현재 접속 중인 모든 학생을 한 번에 하교 처리
        for s_id, info in list(self.active_students.items()):
            self.log_entry(s_id, info['name'], '하교')
        
        self.active_students.clear()
        self.refresh_list()
        self.reset_screen(reset_class=True)

    def reset_screen(self, reset_class=False):
        if hasattr(self, 'revert_timer') and self.revert_timer.isActive():
            self.revert_timer.stop()
            
        self.current_id = None
        self.status.show()
        self.status.setText('학생번호를 누르세요')
        self.status.setStyleSheet("color: #0F172A; border: none;")
        self.detail.setText('학생 정보를 기다리는 중입니다')
        self.detail.setStyleSheet("color: #64748B; background: transparent; border: none;")
        self.history.hide()
        self.photo_label.show()
        self.photo_label.clear()
        self.photo_label.setStyleSheet("background-color: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 20px; color: #94A3B8; font-size: 18px;")
        self.photo_label.setText('PHOTO \n (대기중)')
        if hasattr(self, 'emotion_icon_label'):
            self.emotion_icon_label.clear()
            self.emotion_icon_label.hide()
        self.id_input.clear()
        
        if reset_class:
            self.class_combo.setStyleSheet("""
                QComboBox { border: 2px solid #E2E8F0; border-radius: 10px; padding: 5px 15px; background-color: #F8FAFC; color: #334155; }
                QComboBox:focus { border: 2px solid #3B82F6; }
            """)
            self.class_combo.setCurrentIndex(0)
            if hasattr(self, 'prev_log_btn'):
                self.prev_log_btn.setText("📋 지난 수업 기록")
                self.prev_log_btn.setToolTip("반을 선택하면 이전 수업 기록을 확인하실 수 있습니다.")
                self.prev_log_btn.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        color: #64748B;
                        border: 2px dashed #CBD5E1;
                        border-radius: 15px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #F8FAFC;
                        color: #334155;
                    }
                """)
        self.refresh_list()
        self.id_input.setFocus()
        
    def show_default_class_log(self):
        class_name = self.class_combo.currentText()
        if class_name != "수업명 입력/선택" and class_name.strip():
            self.current_id = None
            self.status.hide()
            
            if class_name in self.class_logs and self.class_logs[class_name]:
                last_log = self.class_logs[class_name][-1]
                content = last_log.get('content', '')
                date_str = last_log.get('date', '')
                
                # 일지 내용 렌더링 (리치 텍스트 HTML 지원)
                is_rich = any(tag in content for tag in ['<!DOCTYPE', '<html', '<body', '<p', '<div', '<img', '<span', '<br'])
                if is_rich:
                    # 이미지 경로를 현재 실행 디렉토리 기준으로 자동 복원
                    resolved_content = resolve_image_paths(content, self.base_dir)
                    body_content = resolved_content
                    if '<body' in resolved_content and '</body>' in resolved_content:
                        try:
                            body_content = resolved_content.split('<body', 1)[1].split('>', 1)[1].rsplit('</body>', 1)[0].strip()
                        except Exception:
                            body_content = resolved_content

                    # 이미지 태그를 클릭 시 고화질 팝업 뷰어가 열리는 <a> 링크로 래핑하고, 화면에 맞게 확장 표시
                    def wrap_img_tag(m):
                        tag = m.group(0)
                        src_m = re.search(r'src=["\']([^"\']+)["\']', tag)
                        if not src_m:
                            return tag
                        img_src = src_m.group(1)
                        # 고정 460px 제한을 시원한 너비로 확장
                        cleaned_tag = re.sub(r'width=["\']\d+["\']', 'width="720"', tag)
                        if 'width=' not in cleaned_tag:
                            cleaned_tag = cleaned_tag.replace('<img ', '<img width="720" ')
                        return (f'<div style="text-align: center; margin: 14px 0;">'
                                f'<a href="{img_src}" title="클릭하여 원본 고화질로 확대 보기">{cleaned_tag}</a>'
                                f'<div style="font-size: 10pt; color: #10B981; font-weight: bold; margin-top: 6px;">'
                                f'🔍 사진을 클릭하면 원본 고해상도 확대 뷰어가 열립니다'
                                f'</div></div>')
                    
                    body_content = re.sub(r'<img[^>]+>', wrap_img_tag, body_content)
                    
                    items_html = f"""
                    <div style="margin-bottom: 12px; padding: 18px 22px; background-color: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; font-size: 14pt; color: #1E293B; line-height: 1.6;">
                        {body_content}
                    </div>
                    """
                else:
                    raw_lines = content.split('\n')
                    items_html = ""
                    for l in raw_lines:
                        text_l = l.strip()
                        if not text_l:
                            items_html += '<div style="height: 10px;"></div>'
                            continue
                        items_html += f"""
                        <div style="margin-bottom: 12px; padding: 12px 18px; background-color: #F8FAFC; border-left: 6px solid #3B82F6; border-radius: 8px;">
                            <span style="font-size: 18pt; font-weight: bold; color: #1E293B;">{html.escape(text_l)}</span>
                        </div>
                        """
                
                html_body = f"""
                <div style="font-family: 'Malgun Gothic', sans-serif; padding: 10px 15px;">
                    <div style="margin-bottom: 18px;">
                        <span style="background-color: #EEF2FF; color: #4F46E5; font-size: 19pt; font-weight: bold; padding: 6px 16px; border-radius: 10px; border: 1px solid #C7D2FE;">
                            🏫 {html.escape(class_name)}
                        </span>
                        <span style="color: #64748B; font-size: 15pt; font-weight: bold; margin-left: 15px;">
                            🕒 {html.escape(date_str)} 수업 일지
                        </span>
                    </div>
                    <hr style="border: none; border-top: 2px solid #E2E8F0; margin-bottom: 20px;">
                    {items_html}
                </div>
                """
                self.detail.setHtml(html_body)
                self.detail.setStyleSheet("""
                    QTextEdit {
                        background-color: #FFFFFF;
                        border: 2px solid #E2E8F0;
                        border-radius: 20px;
                        padding: 25px;
                    }
                """)
            else:
                empty_html = f"""
                <div style="font-family: 'Malgun Gothic', sans-serif; text-align: center; padding-top: 15px;">
                    <div style="font-size: 26pt; margin-bottom: 8px;">📝</div>
                    <div style="font-size: 16pt; font-weight: bold; color: #475569; margin-bottom: 8px;">
                        [{html.escape(class_name)}] 등록된 수업 일지가 없습니다.
                    </div>
                    <div style="font-size: 13pt; color: #94A3B8;">
                        하단의 <b>[📝 일지 작성]</b> 버튼을 눌러 지난 수업 내용이나 오늘 진도를 기록해 보세요.
                    </div>
                </div>
                """
                self.detail.setHtml(empty_html)
                self.detail.setStyleSheet("""
                    QTextEdit {
                        background-color: #F8FAFC;
                        border: 2px dashed #CBD5E1;
                        border-radius: 16px;
                        padding: 15px;
                    }
                """)
                
            self.history.hide()
            self.photo_label.hide()
            if hasattr(self, 'emotion_icon_label'):
                self.emotion_icon_label.clear()
                self.emotion_icon_label.hide()
        else:
            self.reset_screen()

    def on_detail_anchor_clicked(self, url):
        self.open_image_viewer(url)

    def open_image_viewer(self, path_or_url):
        if isinstance(path_or_url, QUrl):
            target = path_or_url.toLocalFile() or path_or_url.toString()
        else:
            target = str(path_or_url)
        target = target.replace('file:///', '')
        
        # 파일이 바로 존재하지 않는 경우 log_images 디렉토리에서 검색
        if not os.path.exists(target):
            cand = os.path.join(self.base_dir, 'log_images', os.path.basename(target))
            if os.path.exists(cand):
                target = cand
                
        if os.path.exists(target) and target.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
            dlg = ImageViewerDialog(target, self)
            dlg.exec_()

    def open_student_manager(self):
        dlg = StudentManagementDialog(self)
        dlg.exec_()

    def save_students_data(self):
        # Save back to self.csv_path
        if not self.students_data:
            return
        fieldnames = ['학년반번호', '이름', '학생정보', '사진파일명']
        try:
            with open(self.csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                for s_id, data in sorted(self.students_data.items()):
                    # 키 이름 일치화
                    row = {
                        '학년반번호': s_id,
                        '이름': data.get('이름', ''),
                        '학생정보': data.get('학생정보', data.get('학년반', '')),
                        '사진파일명': data.get('사진파일명', '')
                    }
                    writer.writerow(row)
        except Exception as e:
            print("Error saving students data:", e)

if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    ex = StudentAttendanceApp()
    sys.exit(app.exec_())
