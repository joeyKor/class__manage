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


class StudentEditDialog(QDialog):
    def __init__(self, parent=None, student_data=None, class_list=None):
        super().__init__(parent)
        self.student_data = student_data or {}
        self.class_list = class_list or []
        self.selected_photo_path = ""
        self.base_dir = parent.base_dir if parent else os.path.dirname(os.path.abspath(__file__))
        self.initUI()

    def initUI(self):
        is_edit = bool(self.student_data)
        self.setWindowTitle("학생 정보 수정" if is_edit else "새 학생 등록")
        self.setFixedSize(460, 520)
        self.setStyleSheet("""
            QDialog { background-color: #F8FAFC; border-radius: 16px; }
            QLabel { font-family: 'Malgun Gothic'; color: #334155; font-size: 13px; font-weight: bold; }
            QLineEdit, QComboBox {
                background-color: white; border: 1.5px solid #CBD5E1; border-radius: 10px;
                padding: 10px 14px; font-size: 14px; font-family: 'Malgun Gothic';
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #3B82F6; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("✏️ 학생 정보 수정" if is_edit else "➕ 새 학생 등록")
        title.setFont(QFont('Malgun Gothic', 16, QFont.Bold))
        title.setStyleSheet("color: #0F172A; border: none;")
        layout.addWidget(title)

        # Photo section
        photo_row = QHBoxLayout()
        self.photo_preview = QLabel("사진 없음")
        self.photo_preview.setFixedSize(100, 120)
        self.photo_preview.setAlignment(Qt.AlignCenter)
        self.photo_preview.setStyleSheet("""
            QLabel { background-color: white; border: 2px dashed #94A3B8; border-radius: 12px; color: #94A3B8; font-size: 12px; }
        """)

        photo_btn_box = QVBoxLayout()
        photo_btn_box.setSpacing(8)
        photo_desc = QLabel("프로필 사진")
        photo_desc.setStyleSheet("color: #64748B; font-size: 12px;")

        self.select_photo_btn = QPushButton("📁 사진 선택...")
        self.select_photo_btn.setCursor(Qt.PointingHandCursor)
        self.select_photo_btn.setStyleSheet("""
            QPushButton { background-color: #EEF2FF; color: #4F46E5; font-weight: bold; border: 1.5px solid #C7D2FE; border-radius: 8px; padding: 8px 14px; }
            QPushButton:hover { background-color: #E0E7FF; }
        """)
        self.select_photo_btn.clicked.connect(self.choose_photo)

        self.remove_photo_btn = QPushButton("삭제")
        self.remove_photo_btn.setCursor(Qt.PointingHandCursor)
        self.remove_photo_btn.setStyleSheet("""
            QPushButton { background-color: #F1F5F9; color: #64748B; border: 1px solid #CBD5E1; border-radius: 8px; padding: 6px 12px; }
            QPushButton:hover { background-color: #E2E8F0; color: #DC2626; }
        """)
        self.remove_photo_btn.clicked.connect(self.clear_photo)

        photo_btn_box.addWidget(photo_desc)
        photo_btn_box.addWidget(self.select_photo_btn)
        photo_btn_box.addWidget(self.remove_photo_btn)
        photo_btn_box.addStretch()

        photo_row.addWidget(self.photo_preview)
        photo_row.addSpacing(16)
        photo_row.addLayout(photo_btn_box)
        photo_row.addStretch()
        layout.addLayout(photo_row)

        # Fields
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)

        lbl_id = QLabel("학번 / 번호 (입력키) *")
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("예: 10101, 932407 등")
        if is_edit:
            self.id_input.setEnabled(False)
            self.id_input.setStyleSheet("background-color: #F1F5F9; color: #64748B; border: 1.5px solid #E2E8F0;")
        form_layout.addWidget(lbl_id)
        form_layout.addWidget(self.id_input)

        lbl_name = QLabel("이름 *")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("학생 이름을 입력하세요")
        form_layout.addWidget(lbl_name)
        form_layout.addWidget(self.name_input)

        lbl_class = QLabel("학년 / 반 *")
        self.class_input = QComboBox()
        self.class_input.setEditable(True)
        self.class_input.addItems(self.class_list)
        self.class_input.lineEdit().setPlaceholderText("예: 1학년 3반")
        form_layout.addWidget(lbl_class)
        form_layout.addWidget(self.class_input)

        layout.addLayout(form_layout)
        layout.addStretch()

        # Bottom buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.setFixedHeight(44)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton { background-color: #E2E8F0; color: #475569; font-weight: bold; border-radius: 10px; border: none; font-size: 13px; }
            QPushButton:hover { background-color: #CBD5E1; }
        """)
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("저장 완료")
        self.save_btn.setFixedHeight(44)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton { background-color: #3B82F6; color: white; font-weight: bold; border-radius: 10px; border: none; font-size: 13px; }
            QPushButton:hover { background-color: #2563EB; }
        """)
        self.save_btn.clicked.connect(self.save)

        btn_row.addWidget(self.cancel_btn, 1)
        btn_row.addWidget(self.save_btn, 2)
        layout.addLayout(btn_row)

        # Load initial values
        if is_edit:
            s_id = self.student_data.get('id', '')
            self.id_input.setText(s_id)
            self.name_input.setText(self.student_data.get('name', ''))
            cls = self.student_data.get('class', '')
            idx = self.class_input.findText(cls)
            if idx >= 0:
                self.class_input.setCurrentIndex(idx)
            else:
                self.class_input.setEditText(cls)
            
            pic_fn = self.student_data.get('photo', '')
            if pic_fn:
                p_path = os.path.join(self.base_dir, 'photos', pic_fn)
                if os.path.exists(p_path):
                    self.set_preview_image(p_path)
                    self.selected_photo_path = p_path

    def choose_photo(self):
        fpath, _ = QFileDialog.getOpenFileName(self, "학생 사진 선택", "", "이미지 파일 (*.png *.jpg *.jpeg *.bmp)")
        if fpath:
            self.selected_photo_path = fpath
            self.set_preview_image(fpath)

    def clear_photo(self):
        self.selected_photo_path = ""
        self.photo_preview.clear()
        self.photo_preview.setText("사진 없음")

    def set_preview_image(self, path):
        pix = QPixmap(path)
        if not pix.isNull():
            self.photo_preview.setPixmap(pix.scaled(self.photo_preview.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.photo_preview.setStyleSheet("border-radius: 12px; border: 2px solid #3B82F6;")

    def save(self):
        s_id = self.id_input.text().strip()
        s_name = self.name_input.text().strip()
        s_class = self.class_input.currentText().strip()

        if not s_id:
            QMessageBox.warning(self, "경고", "학번(번호)을 입력해 주세요.")
            self.id_input.setFocus()
            return
        if not s_name:
            QMessageBox.warning(self, "경고", "학생 이름을 입력해 주세요.")
            self.name_input.setFocus()
            return
        if not s_class:
            QMessageBox.warning(self, "경고", "학년/반 정보를 입력해 주세요.")
            self.class_input.setFocus()
            return

        self.result_data = {
            'id': s_id,
            'name': s_name,
            'class': s_class,
            'photo_path': self.selected_photo_path
        }
        self.accept()


class StudentManagementDialog(QDialog):
    def __init__(self, main_app):
        super().__init__(main_app)
        self.main_app = main_app
        self.base_dir = main_app.base_dir
        self.current_student_id = None
        self.initUI()
        self.load_students_list()

    def initUI(self):
        self.setWindowTitle("👥 스마트 출결 - 학생 관리 시스템")
        self.resize(1080, 700)
        self.setMinimumSize(960, 620)
        self.setStyleSheet("""
            QDialog { background-color: #F8FAFC; }
            QLabel { font-family: 'Malgun Gothic'; color: #1E293B; }
            QLineEdit, QComboBox {
                background-color: white; border: 1.5px solid #CBD5E1; border-radius: 10px;
                padding: 8px 12px; font-size: 13px; font-family: 'Malgun Gothic';
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #3B82F6; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        title_lbl = QLabel("👥 학생 관리")
        title_lbl.setFont(QFont('Malgun Gothic', 16, QFont.Bold))
        title_lbl.setStyleSheet("color: #0F172A;")

        self.class_filter = QComboBox()
        self.class_filter.setFixedWidth(160)
        self.class_filter.addItem("전체 학급")
        for cls in self.main_app.get_class_list():
            self.class_filter.addItem(cls)
        self.class_filter.currentTextChanged.connect(self.filter_students)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 이름 또는 학번 검색...")
        self.search_input.setFixedWidth(220)
        self.search_input.textChanged.connect(self.filter_students)

        self.count_lbl = QLabel("총 0명")
        self.count_lbl.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.count_lbl.setStyleSheet("color: #64748B; padding: 4px 10px; background-color: #F1F5F9; border-radius: 8px;")

        self.add_student_btn = QPushButton("➕ 새 학생 등록")
        self.add_student_btn.setFixedHeight(38)
        self.add_student_btn.setCursor(Qt.PointingHandCursor)
        self.add_student_btn.setStyleSheet("""
            QPushButton { background-color: #3B82F6; color: white; font-weight: bold; border-radius: 9px; padding: 0 16px; font-size: 13px; border: none; }
            QPushButton:hover { background-color: #2563EB; }
        """)
        self.add_student_btn.clicked.connect(self.open_add_student_dialog)

        top_bar.addWidget(title_lbl)
        top_bar.addSpacing(10)
        top_bar.addWidget(self.class_filter)
        top_bar.addWidget(self.search_input)
        top_bar.addWidget(self.count_lbl)
        top_bar.addStretch()
        top_bar.addWidget(self.add_student_btn)
        layout.addLayout(top_bar)

        # Splitter Body
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle { background-color: #E2E8F0; width: 2px; }
        """)

        # Left Panel (Table)
        left_widget = QWidget()
        left_vbox = QVBoxLayout(left_widget)
        left_vbox.setContentsMargins(0, 0, 10, 0)
        left_vbox.setSpacing(8)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["학번", "이름", "학년/반", "MVP"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white; border: 1px solid #E2E8F0; border-radius: 12px;
                font-family: 'Malgun Gothic'; font-size: 13px; outline: none;
            }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #F1F5F9; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #1E40AF; font-weight: bold; }
            QHeaderView::section {
                background-color: #F8FAFC; color: #475569; font-weight: bold; border: none;
                border-bottom: 2px solid #E2E8F0; padding: 8px; font-size: 12px;
            }
        """)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self.on_student_selected)
        left_vbox.addWidget(self.table)

        # Right Panel (Details)
        right_widget = QWidget()
        right_vbox = QVBoxLayout(right_widget)
        right_vbox.setContentsMargins(10, 0, 0, 0)
        right_vbox.setSpacing(12)

        # Profile Card
        self.profile_card = QFrame()
        self.profile_card.setStyleSheet("""
            QFrame { background-color: white; border: 1px solid #E2E8F0; border-radius: 14px; }
        """)
        pcard_layout = QHBoxLayout(self.profile_card)
        pcard_layout.setContentsMargins(18, 14, 18, 14)
        pcard_layout.setSpacing(16)

        self.detail_photo = QLabel("사진")
        self.detail_photo.setFixedSize(85, 105)
        self.detail_photo.setAlignment(Qt.AlignCenter)
        self.detail_photo.setStyleSheet("background-color: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; color: #94A3B8;")

        info_box = QVBoxLayout()
        info_box.setSpacing(4)
        self.detail_name = QLabel("학생을 선택하세요")
        self.detail_name.setFont(QFont('Malgun Gothic', 16, QFont.Bold))
        self.detail_name.setStyleSheet("color: #0F172A; border: none;")

        self.detail_id = QLabel("학번: -")
        self.detail_id.setFont(QFont('Malgun Gothic', 12))
        self.detail_id.setStyleSheet("color: #64748B; border: none;")

        self.detail_class = QLabel("학급: -")
        self.detail_class.setFont(QFont('Malgun Gothic', 12))
        self.detail_class.setStyleSheet("color: #64748B; border: none;")

        info_box.addWidget(self.detail_name)
        info_box.addWidget(self.detail_id)
        info_box.addWidget(self.detail_class)
        info_box.addStretch()

        btn_box = QVBoxLayout()
        btn_box.setSpacing(8)
        self.edit_btn = QPushButton("✏️ 정보 수정")
        self.edit_btn.setFixedHeight(34)
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setStyleSheet("""
            QPushButton { background-color: #EEF2FF; color: #4F46E5; font-weight: bold; border-radius: 8px; border: 1px solid #C7D2FE; padding: 0 12px; font-size: 12px; }
            QPushButton:hover { background-color: #E0E7FF; }
        """)
        self.edit_btn.clicked.connect(self.edit_selected_student)

        self.delete_btn = QPushButton("🗑️ 삭제")
        self.delete_btn.setFixedHeight(34)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setStyleSheet("""
            QPushButton { background-color: #FEE2E2; color: #DC2626; font-weight: bold; border-radius: 8px; border: 1px solid #FECACA; padding: 0 12px; font-size: 12px; }
            QPushButton:hover { background-color: #FCA5A5; color: white; }
        """)
        self.delete_btn.clicked.connect(self.delete_selected_student)

        btn_box.addWidget(self.edit_btn)
        btn_box.addWidget(self.delete_btn)
        btn_box.addStretch()

        pcard_layout.addWidget(self.detail_photo)
        pcard_layout.addLayout(info_box, stretch=1)
        pcard_layout.addLayout(btn_box)

        right_vbox.addWidget(self.profile_card)

        # Tab Widget for Attendance / MVP
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E2E8F0; border-radius: 12px; background: white; }
            QTabBar::tab {
                background: #F1F5F9; color: #64748B; padding: 8px 18px; font-weight: bold;
                border-top-left-radius: 8px; border-top-right-radius: 8px; font-size: 12px;
            }
            QTabBar::tab:selected { background: white; color: #2563EB; border-bottom: 2px solid #2563EB; }
        """)

        # Tab 1: Attendance
        tab_att = QWidget()
        tab_att_layout = QVBoxLayout(tab_att)
        tab_att_layout.setContentsMargins(12, 12, 12, 12)
        tab_att_layout.setSpacing(8)

        self.att_summary_lbl = QLabel("출석 0회 | 학교 결석 0회 | 수업 결석 0회")
        self.att_summary_lbl.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.att_summary_lbl.setStyleSheet("color: #0369A1; background-color: #E0F2FE; border-radius: 8px; padding: 6px 12px;")
        tab_att_layout.addWidget(self.att_summary_lbl)

        self.att_table = QTableWidget()
        self.att_table.setColumnCount(4)
        self.att_table.setHorizontalHeaderLabels(["일시", "상태", "기분/감정", "사유/내용"])
        self.att_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.att_table.setShowGrid(False)
        self.att_table.verticalHeader().setVisible(False)
        self.att_table.setStyleSheet("""
            QTableWidget { border: none; font-size: 12px; font-family: 'Malgun Gothic'; }
            QTableWidget::item { padding: 6px; border-bottom: 1px solid #F1F5F9; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; border: none; padding: 6px; }
        """)
        self.att_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.att_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.att_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.att_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        tab_att_layout.addWidget(self.att_table)

        # Tab 2: MVP
        tab_mvp = QWidget()
        tab_mvp_layout = QVBoxLayout(tab_mvp)
        tab_mvp_layout.setContentsMargins(12, 12, 12, 12)
        tab_mvp_layout.setSpacing(8)

        self.mvp_summary_lbl = QLabel("🌟 총 0회 선정")
        self.mvp_summary_lbl.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.mvp_summary_lbl.setStyleSheet("color: #92400E; background-color: #FEF3C7; border-radius: 8px; padding: 6px 12px;")
        tab_mvp_layout.addWidget(self.mvp_summary_lbl)

        self.mvp_table = QTableWidget()
        self.mvp_table.setColumnCount(2)
        self.mvp_table.setHorizontalHeaderLabels(["선정 일시", "내용"])
        self.mvp_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.mvp_table.setShowGrid(False)
        self.mvp_table.verticalHeader().setVisible(False)
        self.mvp_table.setStyleSheet("""
            QTableWidget { border: none; font-size: 12px; font-family: 'Malgun Gothic'; }
            QTableWidget::item { padding: 6px; border-bottom: 1px solid #F1F5F9; }
            QHeaderView::section { background-color: #F8FAFC; color: #64748B; font-weight: bold; border: none; padding: 6px; }
        """)
        self.mvp_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.mvp_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        tab_mvp_layout.addWidget(self.mvp_table)

        self.tabs.addTab(tab_att, "🗓️ 출결 내역")
        self.tabs.addTab(tab_mvp, "🌟 MVP 기록")
        right_vbox.addWidget(self.tabs, stretch=1)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([420, 620])
        layout.addWidget(splitter, stretch=1)

    def load_mvp_counts(self):
        counts = {}
        if os.path.exists(self.main_app.mvp_file):
            try:
                with open(self.main_app.mvp_file, 'r', encoding='utf-8-sig') as f:
                    r = csv.reader(f)
                    next(r, None)
                    for row in r:
                        if len(row) >= 2:
                            s_id = row[1]
                            counts[s_id] = counts.get(s_id, 0) + 1
            except Exception:
                pass
        return counts

    def load_students_list(self):
        mvp_counts = self.load_mvp_counts()
        self.all_students = []
        for s_id, s_info in self.main_app.students_data.items():
            s_name = s_info.get('이름', '')
            cls_val = s_info.get('학생정보', '') or s_info.get('학년반', '')
            if not cls_val:
                for k, v in s_info.items():
                    if ('학년' in k or '반' in k or '정보' in k) and ('번호' not in k and '학번' not in k):
                        cls_val = str(v).split('\n')[0].strip()
                        break
            else:
                cls_val = str(cls_val).split('\n')[0].strip()
            pic_k = next((k for k in s_info.keys() if '사진' in k), None)
            photo_fn = s_info.get(pic_k, '') if pic_k else ''
            mvp_cnt = mvp_counts.get(s_id, 0)
            self.all_students.append({
                'id': s_id,
                'name': s_name,
                'class': cls_val,
                'photo': photo_fn,
                'mvp': mvp_cnt,
                'raw': s_info
            })

        self.all_students.sort(key=lambda x: (x['class'], x['id']))
        self.filter_students()

    def filter_students(self):
        selected_cls = self.class_filter.currentText()
        query = self.search_input.text().strip().lower()

        filtered = []
        for s in self.all_students:
            if selected_cls != "전체 학급" and selected_cls not in s['class']:
                continue
            if query and (query not in s['id'].lower() and query not in s['name'].lower()):
                continue
            filtered.append(s)

        self.count_lbl.setText(f"총 {len(filtered)}명")
        self.table.setRowCount(len(filtered))
        for row_idx, s in enumerate(filtered):
            item_id = QTableWidgetItem(s['id'])
            item_id.setTextAlignment(Qt.AlignCenter)
            item_name = QTableWidgetItem(s['name'])
            item_name.setTextAlignment(Qt.AlignCenter)
            item_cls = QTableWidgetItem(s['class'])
            item_mvp = QTableWidgetItem(f"⭐ {s['mvp']}" if s['mvp'] > 0 else "-")
            item_mvp.setTextAlignment(Qt.AlignCenter)

            item_id.setData(Qt.UserRole, s['id'])

            self.table.setItem(row_idx, 0, item_id)
            self.table.setItem(row_idx, 1, item_name)
            self.table.setItem(row_idx, 2, item_cls)
            self.table.setItem(row_idx, 3, item_mvp)

        if filtered:
            self.table.selectRow(0)
        else:
            self.clear_detail()

    def on_student_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        item_id = self.table.item(row, 0)
        if not item_id:
            return
        s_id = item_id.data(Qt.UserRole)
        self.display_student_detail(s_id)

    def display_student_detail(self, s_id):
        self.current_student_id = s_id
        student = next((s for s in self.all_students if s['id'] == s_id), None)
        if not student:
            return

        self.detail_name.setText(student['name'])
        self.detail_id.setText(f"학번: {student['id']}")
        self.detail_class.setText(f"학급: {student['class']}")

        pic_fn = student['photo']
        p_path = os.path.join(self.base_dir, 'photos', pic_fn) if pic_fn else ''
        if p_path and os.path.exists(p_path):
            pix = QPixmap(p_path)
            self.detail_photo.setPixmap(pix.scaled(self.detail_photo.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.detail_photo.setStyleSheet("border-radius: 10px; border: 1.5px solid #CBD5E1;")
        else:
            self.detail_photo.clear()
            self.detail_photo.setText("사진 없음")
            self.detail_photo.setStyleSheet("background-color: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; color: #94A3B8;")

        # Attendance data
        att_rows = []
        att_cnt = 0
        school_abs_cnt = 0
        class_abs_cnt = 0
        if os.path.exists(self.main_app.log_file):
            try:
                with open(self.main_app.log_file, 'r', encoding='utf-8-sig') as f:
                    r = csv.reader(f)
                    next(r, None)
                    for row in r:
                        if len(row) >= 4 and row[1] == s_id:
                            time_s = row[0]
                            st = row[3]
                            emo = row[4] if len(row) >= 5 else ''
                            if st == '출석':
                                att_cnt += 1
                            elif st == '학교 결석':
                                school_abs_cnt += 1
                            elif st == '수업 결석':
                                class_abs_cnt += 1
                            att_rows.append((time_s, st, emo, ""))
            except Exception:
                pass

        # Absences reasons
        if os.path.exists(self.main_app.absence_file):
            try:
                with open(self.main_app.absence_file, 'r', encoding='utf-8-sig') as f:
                    r = csv.reader(f)
                    next(r, None)
                    for row in r:
                        if len(row) >= 4 and row[1] == s_id:
                            date_s, abs_type, reason = row[0], row[2], row[3]
                            att_rows.append((date_s, abs_type, "", f"사유: {reason}"))
            except Exception:
                pass

        att_rows.sort(key=lambda x: x[0], reverse=True)
        self.att_summary_lbl.setText(f"출석 {att_cnt}회 | 학교 결석 {school_abs_cnt}회 | 수업 결석 {class_abs_cnt}회")
        self.att_table.setRowCount(len(att_rows))
        for idx, (dt, st, emo, note) in enumerate(att_rows):
            i_dt = QTableWidgetItem(dt)
            i_st = QTableWidgetItem(st)
            i_emo = QTableWidgetItem(emo)
            i_note = QTableWidgetItem(note)
            if '결석' in st:
                i_st.setForeground(QColor("#DC2626"))
            elif st == '출석':
                i_st.setForeground(QColor("#059669"))
            self.att_table.setItem(idx, 0, i_dt)
            self.att_table.setItem(idx, 1, i_st)
            self.att_table.setItem(idx, 2, i_emo)
            self.att_table.setItem(idx, 3, i_note)

        # MVP data
        mvp_rows = []
        if os.path.exists(self.main_app.mvp_file):
            try:
                with open(self.main_app.mvp_file, 'r', encoding='utf-8-sig') as f:
                    r = csv.reader(f)
                    next(r, None)
                    for row in r:
                        if len(row) >= 2 and row[1] == s_id:
                            dt = row[0]
                            reason = row[3] if len(row) >= 4 else "오늘의 MVP 선정"
                            mvp_rows.append((dt, reason))
            except Exception:
                pass

        mvp_rows.sort(key=lambda x: x[0], reverse=True)
        self.mvp_summary_lbl.setText(f"🌟 총 {len(mvp_rows)}회 선정")
        self.mvp_table.setRowCount(len(mvp_rows))
        for idx, (dt, reason) in enumerate(mvp_rows):
            i_dt = QTableWidgetItem(dt)
            i_rs = QTableWidgetItem(reason)
            self.mvp_table.setItem(idx, 0, i_dt)
            self.mvp_table.setItem(idx, 1, i_rs)

    def clear_detail(self):
        self.current_student_id = None
        self.detail_name.setText("학생을 선택하세요")
        self.detail_id.setText("학번: -")
        self.detail_class.setText("학급: -")
        self.detail_photo.clear()
        self.detail_photo.setText("사진 없음")
        self.att_table.setRowCount(0)
        self.mvp_table.setRowCount(0)
        self.att_summary_lbl.setText("출석 0회 | 학교 결석 0회 | 수업 결석 0회")
        self.mvp_summary_lbl.setText("🌟 총 0회 선정")

    def open_add_student_dialog(self):
        classes = self.main_app.get_class_list()
        dlg = StudentEditDialog(self, student_data=None, class_list=classes)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.result_data
            s_id = data['id']
            s_name = data['name']
            if s_id in self.main_app.students_data:
                QMessageBox.warning(self, "경고", f"이미 등록되어 있는 학번입니다 ({s_id}).")
                return

            pic_filename = ""
            if data['photo_path'] and os.path.exists(data['photo_path']):
                ext = os.path.splitext(data['photo_path'])[1].lower() or '.jpg'
                pic_filename = f"{s_name}{ext}"
                dest = os.path.join(self.base_dir, 'photos', pic_filename)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                try:
                    if os.path.abspath(data['photo_path']) != os.path.abspath(dest):
                        shutil.copy2(data['photo_path'], dest)
                except Exception as e:
                    print("Photo copy error:", e)

            # Add to main_app
            self.main_app.students_data[s_id] = {
                '학년반번호': s_id,
                '이름': s_name,
                '학생정보': data['class'],
                '사진파일명': pic_filename
            }
            self.main_app.save_students_data()
            self.load_students_list()
            self.main_app.refresh_list()
            QMessageBox.information(self, "완료", f"[{s_name}] 학생이 성공적으로 등록되었습니다.")

    def edit_selected_student(self):
        if not self.current_student_id:
            return
        student = next((s for s in self.all_students if s['id'] == self.current_student_id), None)
        if not student:
            return

        classes = self.main_app.get_class_list()
        dlg = StudentEditDialog(self, student_data=student, class_list=classes)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.result_data
            s_id = student['id']
            s_name = data['name']

            pic_filename = student['photo']
            if data['photo_path'] and os.path.exists(data['photo_path']) and data['photo_path'] != os.path.join(self.base_dir, 'photos', pic_filename):
                ext = os.path.splitext(data['photo_path'])[1].lower() or '.jpg'
                pic_filename = f"{s_name}{ext}"
                dest = os.path.join(self.base_dir, 'photos', pic_filename)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                try:
                    shutil.copy2(data['photo_path'], dest)
                except Exception as e:
                    print("Photo copy error:", e)
            elif not data['photo_path']:
                pic_filename = ""

            orig = self.main_app.students_data.get(s_id, {})
            orig['이름'] = s_name
            orig['학생정보'] = data['class']
            orig['사진파일명'] = pic_filename
            self.main_app.students_data[s_id] = orig
            self.main_app.save_students_data()
            self.load_students_list()
            self.main_app.refresh_list()
            QMessageBox.information(self, "완료", f"[{data['name']}] 학생 정보가 수정되었습니다.")

    def delete_selected_student(self):
        if not self.current_student_id:
            return
        student = next((s for s in self.all_students if s['id'] == self.current_student_id), None)
        if not student:
            return

        res = QMessageBox.question(self, "학생 삭제", f"정말로 [{student['name']}] 학생을 명단에서 삭제하시겠습니까?\n(기존 출결 및 MVP 로그는 보존됩니다.)", QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            s_id = student['id']
            if s_id in self.main_app.students_data:
                del self.main_app.students_data[s_id]
            if s_id in self.main_app.active_students:
                del self.main_app.active_students[s_id]
            self.main_app.save_students_data()
            self.load_students_list()
            self.main_app.refresh_list()
            QMessageBox.information(self, "완료", "학생이 삭제되었습니다.")


