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


class PresenterModeSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_mode = None
        self.initUI()
        
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1100, 440)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setAlignment(Qt.AlignCenter)
        
        card = QFrame()
        card.setFixedSize(1070, 410)
        card.setStyleSheet("""
            QFrame#ModeSelectCard {
                background-color: #0F172A;
                border: 3px solid #6366F1;
                border-radius: 24px;
            }
        """)
        card.setObjectName("ModeSelectCard")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 28, 30, 28)
        layout.setSpacing(20)
        
        # Header with Title and Close X
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("🎤 발표자 추첨 방식 선택")
        title_lbl.setFont(QFont('Malgun Gothic', 20, QFont.Bold))
        title_lbl.setStyleSheet("color: white; border: none; background: transparent;")
        
        sub_lbl = QLabel("원하시는 발표자 추첨 방식을 선택해주세요.")
        sub_lbl.setFont(QFont('Malgun Gothic', 12))
        sub_lbl.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header.addLayout(title_box)
        header.addStretch()
        
        close_x = QPushButton("✖")
        close_x.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        close_x.setFixedSize(36, 36)
        close_x.setCursor(Qt.PointingHandCursor)
        close_x.setStyleSheet("""
            QPushButton { background-color: #1E293B; color: #94A3B8; border-radius: 10px; border: none; }
            QPushButton:hover { background-color: #EF4444; color: white; }
        """)
        close_x.clicked.connect(self.reject)
        header.addWidget(close_x)
        layout.addLayout(header)
        
        # Options row (3 cards)
        options_layout = QHBoxLayout()
        options_layout.setSpacing(18)
        
        # 1. 룰렛 버튼
        btn_roulette = QPushButton()
        btn_roulette.setCursor(Qt.PointingHandCursor)
        btn_roulette.setFixedHeight(190)
        btn_roulette.setStyleSheet("""
            QPushButton {
                background-color: #1E1B4B;
                border: 2px solid #6366F1;
                border-radius: 18px;
                padding: 16px;
            }
            QPushButton:hover {
                background-color: #312E81;
                border: 2px solid #A5B4FC;
            }
        """)
        r_box = QVBoxLayout(btn_roulette)
        r_box.setSpacing(8)
        r_box.setAlignment(Qt.AlignCenter)
        r_icon = QLabel("🎡")
        r_icon.setFont(QFont('Segoe UI Emoji', 36))
        r_icon.setAlignment(Qt.AlignCenter)
        r_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        r_icon.setStyleSheet("border: none; background: transparent;")
        r_title = QLabel("원판 룰렛")
        r_title.setFont(QFont('Malgun Gothic', 16, QFont.Bold))
        r_title.setStyleSheet("color: #C7D2FE; border: none; background: transparent;")
        r_title.setAlignment(Qt.AlignCenter)
        r_title.setAttribute(Qt.WA_TransparentForMouseEvents)
        r_desc = QLabel("빙글빙글 원판 돌리기!\n박진감 넘치는 룰렛 추첨")
        r_desc.setFont(QFont('Malgun Gothic', 11))
        r_desc.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
        r_desc.setAlignment(Qt.AlignCenter)
        r_desc.setAttribute(Qt.WA_TransparentForMouseEvents)
        r_box.addWidget(r_icon)
        r_box.addWidget(r_title)
        r_box.addWidget(r_desc)
        btn_roulette.clicked.connect(lambda: self.select_and_accept('roulette'))
        options_layout.addWidget(btn_roulette)
        
        # 2. 사다리 버튼
        btn_ladder = QPushButton()
        btn_ladder.setCursor(Qt.PointingHandCursor)
        btn_ladder.setFixedHeight(190)
        btn_ladder.setStyleSheet("""
            QPushButton {
                background-color: #064E3B;
                border: 2px solid #10B981;
                border-radius: 18px;
                padding: 16px;
            }
            QPushButton:hover {
                background-color: #065F46;
                border: 2px solid #6EE7B7;
            }
        """)
        l_box = QVBoxLayout(btn_ladder)
        l_box.setSpacing(8)
        l_box.setAlignment(Qt.AlignCenter)
        l_icon = QLabel("🪜")
        l_icon.setFont(QFont('Segoe UI Emoji', 36))
        l_icon.setAlignment(Qt.AlignCenter)
        l_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        l_icon.setStyleSheet("border: none; background: transparent;")
        l_title = QLabel("사다리 타기")
        l_title.setFont(QFont('Malgun Gothic', 16, QFont.Bold))
        l_title.setStyleSheet("color: #A7F3D0; border: none; background: transparent;")
        l_title.setAlignment(Qt.AlignCenter)
        l_title.setAttribute(Qt.WA_TransparentForMouseEvents)
        l_desc = QLabel("두근두근 긴장감 최고!\n실시간 사다리 타기 애니")
        l_desc.setFont(QFont('Malgun Gothic', 11))
        l_desc.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
        l_desc.setAlignment(Qt.AlignCenter)
        l_desc.setAttribute(Qt.WA_TransparentForMouseEvents)
        l_box.addWidget(l_icon)
        l_box.addWidget(l_title)
        l_box.addWidget(l_desc)
        btn_ladder.clicked.connect(lambda: self.select_and_accept('ladder'))
        options_layout.addWidget(btn_ladder)
        
        # 3. 제비뽑기 버튼
        btn_lottery = QPushButton()
        btn_lottery.setCursor(Qt.PointingHandCursor)
        btn_lottery.setFixedHeight(190)
        btn_lottery.setStyleSheet("""
            QPushButton {
                background-color: #451A03;
                border: 2px solid #F59E0B;
                border-radius: 18px;
                padding: 16px;
            }
            QPushButton:hover {
                background-color: #78350F;
                border: 2px solid #FBBF24;
            }
        """)
        lot_box = QVBoxLayout(btn_lottery)
        lot_box.setSpacing(8)
        lot_box.setAlignment(Qt.AlignCenter)
        lot_icon = QLabel("🎁")
        lot_icon.setFont(QFont('Segoe UI Emoji', 36))
        lot_icon.setAlignment(Qt.AlignCenter)
        lot_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        lot_icon.setStyleSheet("border: none; background: transparent;")
        lot_title = QLabel("제비뽑기")
        lot_title.setFont(QFont('Malgun Gothic', 16, QFont.Bold))
        lot_title.setStyleSheet("color: #FDE68A; border: none; background: transparent;")
        lot_title.setAlignment(Qt.AlignCenter)
        lot_title.setAttribute(Qt.WA_TransparentForMouseEvents)
        lot_desc = QLabel("상자 속 제비 쏙 뽑기!\n직접 고르는 황금 제비")
        lot_desc.setFont(QFont('Malgun Gothic', 11))
        lot_desc.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
        lot_desc.setAlignment(Qt.AlignCenter)
        lot_desc.setAttribute(Qt.WA_TransparentForMouseEvents)
        lot_box.addWidget(lot_icon)
        lot_box.addWidget(lot_title)
        lot_box.addWidget(lot_desc)
        btn_lottery.clicked.connect(lambda: self.select_and_accept('lottery'))
        options_layout.addWidget(btn_lottery)
        
        # 4. 레이스 버튼
        btn_race = QPushButton()
        btn_race.setCursor(Qt.PointingHandCursor)
        btn_race.setFixedHeight(190)
        btn_race.setStyleSheet("""
            QPushButton {
                background-color: #4C0519;
                border: 2px solid #F43F5E;
                border-radius: 18px;
                padding: 16px;
            }
            QPushButton:hover {
                background-color: #881337;
                border: 2px solid #FB7185;
            }
        """)
        rc_box = QVBoxLayout(btn_race)
        rc_box.setSpacing(8)
        rc_box.setAlignment(Qt.AlignCenter)
        rc_icon = QLabel("🏃‍♂️")
        rc_icon.setFont(QFont('Segoe UI Emoji', 36))
        rc_icon.setAlignment(Qt.AlignCenter)
        rc_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        rc_icon.setStyleSheet("border: none; background: transparent;")
        rc_title = QLabel("레이스")
        rc_title.setFont(QFont('Malgun Gothic', 16, QFont.Bold))
        rc_title.setStyleSheet("color: #FECDD3; border: none; background: transparent;")
        rc_title.setAlignment(Qt.AlignCenter)
        rc_title.setAttribute(Qt.WA_TransparentForMouseEvents)
        rc_desc = QLabel("역전에 역전을 거듭하는!\n박진감 폭발 트랙 달리기")
        rc_desc.setFont(QFont('Malgun Gothic', 11))
        rc_desc.setStyleSheet("color: #94A3B8; border: none; background: transparent;")
        rc_desc.setAlignment(Qt.AlignCenter)
        rc_desc.setAttribute(Qt.WA_TransparentForMouseEvents)
        rc_box.addWidget(rc_icon)
        rc_box.addWidget(rc_title)
        rc_box.addWidget(rc_desc)
        btn_race.clicked.connect(lambda: self.select_and_accept('race'))
        options_layout.addWidget(btn_race)
        
        layout.addLayout(options_layout)
        
        # Cancel Button
        cancel_btn = QPushButton("닫기")
        cancel_btn.setFont(QFont('Malgun Gothic', 12))
        cancel_btn.setFixedHeight(42)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #94A3B8;
                border-radius: 10px;
                border: 1px solid #334155;
            }
            QPushButton:hover {
                background-color: #334155;
                color: white;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        main_layout.addWidget(card)
        
    def select_and_accept(self, mode):
        self.selected_mode = mode
        self.accept()


class RouletteWheelWidget(QWidget):
    def __init__(self, parent_dialog):
        super().__init__(parent_dialog)
        self.dlg = parent_dialog
        self.setMinimumSize(480, 480)
        self.setStyleSheet("background: transparent;")
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        candidates = self.dlg.pool
        N = len(candidates)
        if N == 0:
            return
            
        W = self.width()
        H = self.height()
        cx = W / 2.0
        cy = H / 2.0
        
        # radius of wheel
        r = min(cx, cy) - 35.0
        if r < 80:
            return
            
        delta = 360.0 / N
        colors = [
            '#4F46E5', '#EC4899', '#10B981', '#F59E0B', 
            '#3B82F6', '#8B5CF6', '#14B8A6', '#F97316', 
            '#06B6D4', '#E11D48', '#84CC16', '#6366F1'
        ]
        
        # 1. 원판 슬라이스 그리기
        for i in range(N):
            cand = candidates[i]
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(-90.0 + self.dlg.current_angle + i * delta)
            
            # Pie path
            path = QPainterPath()
            path.moveTo(0, 0)
            path.arcTo(QRectF(-r, -r, 2 * r, 2 * r), 0, -delta)
            path.closeSubpath()
            
            color_hex = colors[i % len(colors)]
            painter.setBrush(QBrush(QColor(color_hex)))
            painter.setPen(QPen(QColor('#0F172A'), 2))
            painter.drawPath(path)
            
            # 슬라이스 중앙 텍스트 (방사형 배치)
            painter.rotate(delta / 2.0)
            painter.setPen(QColor('#FFFFFF'))
            font_size = max(10, min(15, int(220 / max(N, 6))))
            painter.setFont(QFont('Malgun Gothic', font_size, QFont.Bold))
            text_rect = QRectF(r * 0.35, -20, r * 0.52, 40)
            painter.drawText(text_rect, Qt.AlignCenter, cand['name'])
            painter.restore()
            
        # 2. 바깥쪽 테두리 링 및 회전하는 LED 스터드 점
        painter.setPen(QPen(QColor('#312E81'), 16))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(cx - r - 8, cy - r - 8, (r + 8) * 2, (r + 8) * 2))
        
        painter.setPen(QPen(QColor('#F59E0B'), 3))
        painter.drawEllipse(QRectF(cx - r - 16, cy - r - 16, (r + 16) * 2, (r + 16) * 2))
        painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
        
        num_studs = max(N * 2, 24)
        stud_r = r + 8
        for si in range(num_studs):
            sang = math.radians(si * (360.0 / num_studs) + self.dlg.current_angle)
            sx = cx + stud_r * math.cos(sang)
            sy = cy + stud_r * math.sin(sang)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor('#FDE047') if si % 2 == 0 else QColor('#FFFFFF'))
            painter.drawEllipse(QRectF(sx - 3.5, sy - 3.5, 7, 7))
            
        # 3. 중앙 허브 (Center Cap)
        hub_r = max(38, int(r * 0.18))
        hub_rect = QRectF(cx - hub_r, cy - hub_r, hub_r * 2, hub_r * 2)
        painter.setPen(QPen(QColor('#F59E0B'), 4))
        painter.setBrush(QBrush(QColor('#0F172A')))
        painter.drawEllipse(hub_rect)
        
        inner_r = hub_r * 0.65
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor('#6366F1')))
        painter.drawEllipse(QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2))
        
        painter.setPen(QColor('#FFFFFF'))
        painter.setFont(QFont('Segoe UI Emoji', int(hub_r * 0.55)))
        painter.drawText(hub_rect, Qt.AlignCenter, "🎯")
        
        # 4. 상단 포인터 (Needle / Arrow)
        painter.save()
        painter.translate(cx, cy - r - 14)
        if hasattr(self.dlg, 'needle_wiggle'):
            painter.rotate(self.dlg.needle_wiggle)
            
        needle_path = QPainterPath()
        needle_path.moveTo(0, 32)
        needle_path.lineTo(-16, -4)
        needle_path.lineTo(16, -4)
        needle_path.closeSubpath()
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 120))
        painter.drawPath(needle_path.translated(2, 2))
        
        painter.setPen(QPen(QColor('#FEF08A'), 2.5))
        painter.setBrush(QBrush(QColor('#EF4444')))
        painter.drawPath(needle_path)
        
        painter.setPen(QPen(QColor('#FFFFFF'), 1.5))
        painter.setBrush(QBrush(QColor('#991B1B')))
        painter.drawEllipse(QRectF(-8, -10, 16, 16))
        painter.restore()


class PresenterRouletteDialog(QDialog):
    def __init__(self, candidates, parent_app=None, exclude_ids=None):
        super().__init__(parent_app)
        self.candidates = candidates
        self.parent_app = parent_app
        self.base_dir = getattr(parent_app, "base_dir", os.path.dirname(os.path.abspath(__file__)))
        self.exclude_ids = list(exclude_ids) if exclude_ids else []
        
        # 제외 대상 필터링 (다시 뽑기 시 활용)
        valid_candidates = [c for c in self.candidates if c['id'] not in self.exclude_ids]
        if not valid_candidates:
            valid_candidates = self.candidates
            self.exclude_ids = []
            
        self.pool = valid_candidates
        self.winner = random.choice(self.pool)
        
        self.current_angle = 0.0
        self.start_angle = 0.0
        self.total_spin_angle = 0.0
        self.step = 0
        self.total_steps = 150
        self.is_spinning = False
        self.is_finished = False
        self.last_idx = -1
        self.needle_wiggle = 0.0
        
        self.initUI()
        
    def get_current_index(self):
        if not self.pool:
            return 0
        N = len(self.pool)
        delta = 360.0 / N
        return int(((360.0 - (self.current_angle % 360.0)) % 360.0) / delta) % N
        
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 25, 40, 25)
        layout.setAlignment(Qt.AlignCenter)
        
        self.frame = QFrame()
        self.frame.setFixedSize(1000, 760)
        self.frame.setStyleSheet("""
            QFrame#RouletteMainFrame {
                background-color: #0F172A;
                border: 4px solid #6366F1;
                border-radius: 28px;
            }
        """)
        self.frame.setObjectName("RouletteMainFrame")
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(35, 25, 35, 25)
        frame_layout.setSpacing(15)
        
        # Header bar
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("🎡 오늘의 발표자 원판 룰렛 🎯")
        title_lbl.setFont(QFont('Malgun Gothic', 23, QFont.Bold))
        title_lbl.setStyleSheet("color: #818CF8; background: transparent; border: none;")
        
        sub_lbl = QLabel("빙글빙글 원판을 힘차게 돌려 오늘의 발표자를 뽑아보세요!")
        sub_lbl.setFont(QFont('Malgun Gothic', 13))
        sub_lbl.setStyleSheet("color: #94A3B8; background: transparent; border: none;")
        
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header.addLayout(title_box)
        header.addStretch()
        
        close_icon_btn = QPushButton("✖")
        close_icon_btn.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        close_icon_btn.setFixedSize(45, 45)
        close_icon_btn.setCursor(Qt.PointingHandCursor)
        close_icon_btn.setStyleSheet("""
            QPushButton { background-color: #334155; color: #CBD5E1; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #EF4444; color: white; }
        """)
        close_icon_btn.clicked.connect(self.reject)
        header.addWidget(close_icon_btn)
        frame_layout.addLayout(header)
        
        # Central content: Left (Wheel) + Right (Candidate Live Card)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        
        # 1. Wheel Canvas
        self.wheel_widget = RouletteWheelWidget(self)
        content_layout.addWidget(self.wheel_widget, stretch=3)
        
        # 2. Right Live Card
        self.right_card = QFrame()
        self.right_card.setFixedWidth(320)
        self.right_card.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 2px solid #334155;
                border-radius: 20px;
            }
        """)
        rc_layout = QVBoxLayout(self.right_card)
        rc_layout.setContentsMargins(20, 20, 20, 20)
        rc_layout.setSpacing(12)
        rc_layout.setAlignment(Qt.AlignCenter)
        
        self.status_badge = QLabel("🎯 현재 지목 학생")
        self.status_badge.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setStyleSheet("color: #A5B4FC; background: #312E81; padding: 6px 12px; border-radius: 10px; border: none;")
        rc_layout.addWidget(self.status_badge)
        
        self.photo_lbl = QLabel()
        self.photo_lbl.setFixedSize(200, 250)
        self.photo_lbl.setStyleSheet("background-color: white; border: 4px solid #6366F1; border-radius: 15px;")
        self.photo_lbl.setAlignment(Qt.AlignCenter)
        rc_layout.addWidget(self.photo_lbl, alignment=Qt.AlignCenter)
        
        self.name_lbl = QLabel("-")
        self.name_lbl.setFont(QFont('Malgun Gothic', 26, QFont.Bold))
        self.name_lbl.setAlignment(Qt.AlignCenter)
        self.name_lbl.setStyleSheet("color: #38BDF8; border: none;")
        rc_layout.addWidget(self.name_lbl)
        
        self.msg_lbl = QLabel("원판 돌리기 버튼을 눌러주세요!")
        self.msg_lbl.setFont(QFont('Malgun Gothic', 12))
        self.msg_lbl.setAlignment(Qt.AlignCenter)
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet("color: #94A3B8; border: none;")
        rc_layout.addWidget(self.msg_lbl)
        
        content_layout.addWidget(self.right_card, stretch=2)
        frame_layout.addLayout(content_layout)
        
        # Initial display
        init_idx = self.get_current_index()
        if self.pool:
            self.update_indicator_card(self.pool[init_idx])
            
        # Bottom Buttons
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(15)
        btn_bar.setAlignment(Qt.AlignCenter)
        
        self.spin_btn = QPushButton("🎡  원판 돌리기!")
        self.spin_btn.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        self.spin_btn.setFixedHeight(54)
        self.spin_btn.setFixedWidth(230)
        self.spin_btn.setCursor(Qt.PointingHandCursor)
        self.spin_btn.setStyleSheet("""
            QPushButton { background-color: #6366F1; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #4F46E5; }
            QPushButton:disabled { background-color: #475569; color: #94A3B8; }
        """)
        self.spin_btn.clicked.connect(self.start_spin)
        btn_bar.addWidget(self.spin_btn)
        
        self.skip_btn = QPushButton("⚡ 바로 결과 보기")
        self.skip_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.skip_btn.setFixedHeight(54)
        self.skip_btn.setFixedWidth(180)
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.setStyleSheet("""
            QPushButton { background-color: #334155; color: #CBD5E1; border-radius: 12px; border: 1px solid #475569; }
            QPushButton:hover { background-color: #475569; color: white; }
        """)
        self.skip_btn.clicked.connect(self.skip_spin)
        btn_bar.addWidget(self.skip_btn)
        
        self.restart_btn = QPushButton("🔄 다시 돌리기")
        self.restart_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.restart_btn.setFixedHeight(54)
        self.restart_btn.setFixedWidth(160)
        self.restart_btn.setCursor(Qt.PointingHandCursor)
        self.restart_btn.setStyleSheet("""
            QPushButton { background-color: #F59E0B; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #D97706; }
        """)
        self.restart_btn.clicked.connect(self.reset_spin)
        btn_bar.addWidget(self.restart_btn)
        
        self.close_btn = QPushButton("확인 (닫기)")
        self.close_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.close_btn.setFixedHeight(54)
        self.close_btn.setFixedWidth(140)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton { background-color: #10B981; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #059669; }
        """)
        self.close_btn.clicked.connect(self.accept)
        btn_bar.addWidget(self.close_btn)
        
        frame_layout.addLayout(btn_bar)
        layout.addWidget(self.frame)
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_spin)
        
    def play_fanfare(self):
        self.player = QMediaPlayer(None, QMediaPlayer.LowLatency)
        audio_path = os.path.join(self.base_dir, 'mvp_sound.mp3')
        if os.path.exists(audio_path):
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
            self.player.play()

    def closeEvent(self, event):
        if hasattr(self, 'player'):
            self.player.stop()
        super().closeEvent(event)

    def update_indicator_card(self, candidate):
        if not candidate:
            return
        if candidate.get('photo') and os.path.exists(candidate['photo']):
            self.photo_lbl.setPixmap(QPixmap(candidate['photo']).scaled(200, 250, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            self.photo_lbl.clear()
            self.photo_lbl.setText("👤")
            self.photo_lbl.setFont(QFont('Segoe UI Emoji', 45))
            self.photo_lbl.setStyleSheet("background-color: #334155; color: #94A3B8; border: 4px solid #6366F1; border-radius: 15px;")
        self.name_lbl.setText(f"{candidate['name']}")
        
    def start_spin(self):
        if len(self.pool) <= 1:
            self.winner = self.pool[0]
            self.update_indicator_card(self.winner)
            self.status_badge.setText("🎉 오늘의 발표자 당첨! 🎉")
            self.status_badge.setStyleSheet("color: white; background: #10B981; padding: 8px 14px; border-radius: 12px; font-weight: bold; border: none;")
            self.name_lbl.setText(f"✨ {self.winner['name']} 학생 ✨")
            self.name_lbl.setStyleSheet("color: #FBBF24; font-weight: bold; border: none;")
            self.msg_lbl.setText("멋진 발표와 활약을 기대합니다! 👏")
            self.msg_lbl.setStyleSheet("color: #6EE7B7; font-size: 14px; font-weight: bold; border: none;")
            self.photo_lbl.setStyleSheet("background-color: white; border: 5px solid #10B981; border-radius: 16px;")
            self.play_fanfare()
            if self.parent_app and hasattr(self.parent_app, 'play_tts'):
                self.parent_app.play_tts(f"{self.winner['name']} 학생, 오늘의 발표자로 당첨되었습니다! 멋진 발표 부탁드립니다.")
            return
        if self.is_spinning:
            return
            
        self.is_spinning = True
        self.is_finished = False
        self.step = 0
        self.total_steps = 150
        
        # Winner calculation
        self.winner = random.choice(self.pool)
        winner_idx = self.pool.index(self.winner)
        delta = 360.0 / len(self.pool)
        
        # 슬라이스 중앙에 바늘(12시)이 정확히 오도록 target_theta 계산
        jitter_deg = random.uniform(-0.20, 0.20) * delta
        target_theta = (360.0 - (winner_idx + 0.5) * delta - jitter_deg) % 360.0
        
        # 현재 각도에서 시작하여 시계 방향으로 5~7바퀴 돌고 target_theta에 정확히 멈춤
        full_turns = 360.0 * random.randint(5, 7)
        cur = self.current_angle
        diff = (target_theta - (cur % 360.0)) % 360.0
        self.start_angle = cur
        self.total_spin_angle = cur + full_turns + diff
        
        self.spin_btn.setEnabled(False)
        self.spin_btn.setText("원판 회전 중... 🎡")
        self.status_badge.setText("🎯 현재 지목 학생")
        self.status_badge.setStyleSheet("color: #A5B4FC; background: #312E81; padding: 6px 12px; border-radius: 10px; border: none;")
        self.msg_lbl.setText("과연 행운의 주인공은 누구일까요?")
        self.msg_lbl.setStyleSheet("color: #FBBF24; border: none;")
        self.photo_lbl.setStyleSheet("background-color: white; border: 4px solid #6366F1; border-radius: 15px;")
        self.timer.start(25)
        
    def update_spin(self):
        self.step += 1
        t = min(1.0, self.step / float(self.total_steps))
        
        # Quartic Out Easing for realistic roulette deceleration
        ease = 1.0 - math.pow(1.0 - t, 3.8)
        self.current_angle = self.start_angle + (self.total_spin_angle - self.start_angle) * ease
        
        # Needle spring bounce dampening
        self.needle_wiggle *= 0.70
        
        # Check slice change
        curr_idx = self.get_current_index()
        if curr_idx != self.last_idx:
            self.last_idx = curr_idx
            self.needle_wiggle = -14.0
            QApplication.beep()
            self.update_indicator_card(self.pool[curr_idx])
            
        self.wheel_widget.update()
        
        if self.step >= self.total_steps:
            self.timer.stop()
            self.is_spinning = False
            self.is_finished = True
            self.needle_wiggle = 0.0
            self.current_angle = self.total_spin_angle
            self.wheel_widget.update()
            
            # 물리적으로 12시 바늘이 가리키는 실제 인덱스로 당첨자 최종 확정
            final_idx = self.get_current_index()
            self.winner = self.pool[final_idx]
            self.update_indicator_card(self.winner)
            self.spin_btn.setEnabled(True)
            self.spin_btn.setText("🎡 다시 돌리기")
            
            self.status_badge.setText("🎉 오늘의 발표자 당첨! 🎉")
            self.status_badge.setStyleSheet("color: white; background: #10B981; padding: 8px 14px; border-radius: 12px; font-weight: bold; border: none;")
            self.name_lbl.setText(f"✨ {self.winner['name']} 학생 ✨")
            self.name_lbl.setStyleSheet("color: #FBBF24; font-weight: bold; border: none;")
            self.msg_lbl.setText("멋진 발표와 활약을 기대합니다! 👏")
            self.msg_lbl.setStyleSheet("color: #6EE7B7; font-size: 14px; font-weight: bold; border: none;")
            self.photo_lbl.setStyleSheet("background-color: white; border: 5px solid #10B981; border-radius: 16px;")
            
            self.play_fanfare()
            if self.parent_app and hasattr(self.parent_app, 'play_tts'):
                self.parent_app.play_tts(f"{self.winner['name']} 학생, 오늘의 발표자로 당첨되었습니다! 멋진 발표 부탁드립니다.")
            
    def skip_spin(self):
        self.timer.stop()
        self.is_spinning = False
        self.is_finished = True
        self.needle_wiggle = 0.0
        self.current_angle = self.total_spin_angle
        final_idx = self.get_current_index()
        self.winner = self.pool[final_idx]
        self.update_indicator_card(self.winner)
        self.spin_btn.setEnabled(True)
        self.spin_btn.setText("🎡 다시 돌리기")
        
        self.status_badge.setText("🎉 오늘의 발표자 당첨! 🎉")
        self.status_badge.setStyleSheet("color: white; background: #10B981; padding: 8px 14px; border-radius: 12px; font-weight: bold; border: none;")
        self.name_lbl.setText(f"✨ {self.winner['name']} 학생 ✨")
        self.name_lbl.setStyleSheet("color: #FBBF24; font-weight: bold; border: none;")
        self.msg_lbl.setText("멋진 발표와 활약을 기대합니다! 👏")
        self.msg_lbl.setStyleSheet("color: #6EE7B7; font-size: 14px; font-weight: bold; border: none;")
        self.photo_lbl.setStyleSheet("background-color: white; border: 5px solid #10B981; border-radius: 16px;")
        
        self.wheel_widget.update()
        self.play_fanfare()
        if self.parent_app and hasattr(self.parent_app, 'play_tts'):
            self.parent_app.play_tts(f"{self.winner['name']} 학생, 오늘의 발표자로 당첨되었습니다! 멋진 발표 부탁드립니다.")
        
    def reset_spin(self):
        self.timer.stop()
        if hasattr(self, 'player'):
            self.player.stop()
        self.is_spinning = False
        self.is_finished = False
        self.needle_wiggle = 0.0
        self.step = 0
        self.spin_btn.setEnabled(True)
        self.spin_btn.setText("🎡  원판 돌리기!")
        self.status_badge.setText("🎯 현재 지목 학생")
        self.status_badge.setStyleSheet("color: #A5B4FC; background: #312E81; padding: 6px 12px; border-radius: 10px; border: none;")
        self.msg_lbl.setText("원판 돌리기 버튼을 눌러주세요!")
        self.msg_lbl.setStyleSheet("color: #94A3B8; border: none;")
        self.photo_lbl.setStyleSheet("background-color: white; border: 4px solid #6366F1; border-radius: 15px;")
        self.wheel_widget.update()


class LadderCanvasWidget(QWidget):
    def __init__(self, parent_dialog):
        super().__init__(parent_dialog)
        self.dlg = parent_dialog
        self.setMinimumHeight(480)
        self.setStyleSheet("background: transparent;")
        
    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            num_cols = self.dlg.num_cols
            if num_cols < 2:
                return
                
            W = self.width()
            H = self.height()
            
            top_y = 100
            bot_y = H - 95
            ladder_h = bot_y - top_y
            
            col_w = W / (num_cols + 1)
            xs = [int(col_w * (i + 1)) for i in range(num_cols)]
            
            # 1. 기본 세로 기둥 선
            pen_col = QPen(QColor("#334155"), 4, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen_col)
            for x in xs:
                painter.drawLine(x, top_y, x, bot_y)
                
            # 2. 가로 다리(Bridge) 또는 시작 전 가운데 가림막
            if not self.dlg.is_blind:
                pen_bridge = QPen(QColor("#475569"), 4, Qt.SolidLine, Qt.RoundCap)
                painter.setPen(pen_bridge)
                for c, lvl in self.dlg.bridges:
                    if c < num_cols - 1:
                        y = int(top_y + (lvl / (self.dlg.num_levels + 1)) * ladder_h)
                        painter.drawLine(xs[c], y, xs[c + 1], y)
            else:
                # 시작 전 사다리 가운데 영역을 보이지 않게 가려주는 비밀 가림막 (Blind Curtain)
                blind_rect = QRectF(xs[0] - 30, top_y + 18, (xs[-1] - xs[0]) + 60, ladder_h - 36)
                
                # 그림자
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0, 130))
                painter.drawRoundedRect(blind_rect.translated(3, 4), 18, 18)
                
                # 가림막 메인 패널
                painter.setPen(QPen(QColor("#3B82F6"), 2, Qt.DashLine))
                painter.setBrush(QBrush(QColor("#1E293B")))
                painter.drawRoundedRect(blind_rect, 18, 18)
                
                # 가림막 내부 가로 장식 점선
                painter.setPen(QPen(QColor("#334155"), 1, Qt.DotLine))
                for py in range(int(blind_rect.top()) + 25, int(blind_rect.bottom()) - 10, 32):
                    painter.drawLine(int(blind_rect.left() + 20), py, int(blind_rect.right() - 20), py)
                
                # 중앙 락 아이콘 및 안내 문구
                mid_x = (xs[0] + xs[-1]) / 2.0
                mid_y = top_y + ladder_h / 2.0
                
                painter.setPen(QColor("#60A5FA"))
                painter.setFont(QFont('Segoe UI Emoji', 36))
                painter.drawText(QRectF(mid_x - 50, mid_y - 60, 100, 52), Qt.AlignCenter, "🔒")
                
                painter.setPen(QColor("#F8FAFC"))
                painter.setFont(QFont('Malgun Gothic', 16, QFont.Bold))
                painter.drawText(QRectF(mid_x - 250, mid_y - 4, 500, 32), Qt.AlignCenter, "사다리 경로 비공개 가림막")
                
                painter.setPen(QColor("#94A3B8"))
                painter.setFont(QFont('Malgun Gothic', 11))
                painter.drawText(QRectF(mid_x - 250, mid_y + 28, 500, 26), Qt.AlignCenter, "시작 버튼을 누르면 가림막이 열리고 사다리가 시작됩니다! 🚀")
                    
            # 3. 진행된 경로선(Trace) & 사다리를 타는 학생 사진 아바타
            has_progress = hasattr(self.dlg, 'progresses') and any(p > 0.0 for p in self.dlg.progresses)
            if has_progress:
                lead_k = -1
                max_prog = -1.0
                for k in range(num_cols):
                    if not self.dlg.finished_students[k] and self.dlg.progresses[k] > max_prog:
                        max_prog = self.dlg.progresses[k]
                        lead_k = k
                        
                markers_to_draw = []
                for k in range(num_cols):
                    prog = self.dlg.progresses[k]
                    if prog <= 0.0:
                        continue
                        
                    color = QColor(self.dlg.colors[k])
                    pen_trace = QPen(color, 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                    painter.setPen(pen_trace)
                    painter.setBrush(Qt.NoBrush)
                    
                    path = self.dlg.paths[k]
                    tot_d = self.dlg.path_lengths[k]
                    target_d = prog * tot_d
                    
                    accum = 0.0
                    last_pt = QPointF(xs[int(round(path[0][0]))], top_y)
                    
                    for i in range(len(path) - 1):
                        p1 = path[i]
                        p2 = path[i+1]
                        p1_px = QPointF(xs[int(round(p1[0]))], top_y + p1[1] * ladder_h)
                        p2_px = QPointF(xs[int(round(p2[0]))], top_y + p2[1] * ladder_h)
                        
                        seg_d = self.dlg.seg_dists[k][i]
                        if accum + seg_d <= target_d:
                            painter.drawLine(p1_px, p2_px)
                            accum += seg_d
                            last_pt = p2_px
                        else:
                            ratio = (target_d - accum) / seg_d if seg_d > 0 else 0
                            inter_px = QPointF(p1_px.x() + (p2_px.x() - p1_px.x()) * ratio,
                                               p1_px.y() + (p2_px.y() - p1_px.y()) * ratio)
                            painter.drawLine(p1_px, inter_px)
                            last_pt = inter_px
                            break
                            
                    is_leader = (k == lead_k and not self.dlg.finished_students[k] and num_cols > 2)
                    markers_to_draw.append((k, last_pt, color, is_leader))
                    
                # 사다리 선 위에 실시간으로 이동하는 학생 원형 사진 아바타 그리기
                avatar_r = min(22.0, max(14.0, col_w * 0.20))
                for k, pt, color, is_leader in markers_to_draw:
                    cand = self.dlg.pool[k]
                    p_path = cand.get('photo', '')
                    is_fin = self.dlg.finished_students[k]
                    
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(0, 0, 0, 110))
                    painter.drawEllipse(QPointF(pt.x() + 2, pt.y() + 2), avatar_r + 2, avatar_r + 2)
                    
                    border_color = QColor("#FBBF24") if is_leader else color
                    painter.setPen(QPen(border_color, 4 if is_leader else 3.5))
                    painter.setBrush(QBrush(QColor("#1E293B")))
                    painter.drawEllipse(pt, avatar_r, avatar_r)
                    
                    if p_path and os.path.exists(p_path):
                        pix = QPixmap(p_path).scaled(int((avatar_r - 2) * 2), int((avatar_r - 2) * 2), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                        path_clip = QPainterPath()
                        path_clip.addEllipse(pt, avatar_r - 2, avatar_r - 2)
                        painter.save()
                        painter.setClipPath(path_clip)
                        painter.drawPixmap(int(pt.x() - (avatar_r - 2)), int(pt.y() - (avatar_r - 2)), pix)
                        painter.restore()
                    else:
                        painter.setPen(QColor(color))
                        painter.setFont(QFont('Segoe UI Emoji', int(avatar_r * 0.9)))
                        painter.drawText(QRectF(pt.x() - avatar_r, pt.y() - avatar_r, avatar_r * 2, avatar_r * 2), Qt.AlignCenter, "👤")
                        
                    painter.setPen(QPen(border_color, 2.5))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(pt, avatar_r, avatar_r)
                    
                    tag_w = max(48.0, avatar_r * 2.6)
                    tag_h = 17.0
                    tag_rect = QRectF(pt.x() - tag_w / 2.0, pt.y() - avatar_r - tag_h - 3.0, tag_w, tag_h)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor(15, 23, 42, 220)))
                    painter.drawRoundedRect(tag_rect, 6, 6)
                    
                    painter.setPen(QColor("#FBBF24") if is_leader else QColor("#FFFFFF"))
                    painter.setFont(QFont('Malgun Gothic', 8, QFont.Bold))
                    
                    display_text = cand['name']
                    if is_fin:
                        display_text += " ✓"
                    elif is_leader:
                        display_text = "⚡ " + cand['name']
                    painter.drawText(tag_rect, Qt.AlignCenter, display_text)
                    
            # 4. 상단 학생 정보 카드
            for i, cand in enumerate(self.dlg.pool):
                cx = xs[i]
                photo_size = 46
                photo_rect = QRect(cx - photo_size // 2, 8, photo_size, photo_size)
                
                painter.setPen(QPen(QColor(self.dlg.colors[i]), 3))
                painter.setBrush(QBrush(QColor("#1E293B")))
                painter.drawEllipse(photo_rect)
                
                p_path = cand.get('photo', '')
                if p_path and os.path.exists(p_path):
                    pix = QPixmap(p_path).scaled(photo_size - 4, photo_size - 4, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    path_clip = QPainterPath()
                    path_clip.addEllipse(QRectF(cx - (photo_size - 4) / 2.0, 10.0, photo_size - 4.0, photo_size - 4.0))
                    painter.save()
                    painter.setClipPath(path_clip)
                    painter.drawPixmap(int(cx - (photo_size - 4) // 2), 10, pix)
                    painter.restore()
                else:
                    painter.setPen(QColor("#94A3B8"))
                    painter.setFont(QFont('Segoe UI Emoji', 16))
                    painter.drawText(photo_rect, Qt.AlignCenter, "👤")
                    
                name_rect = QRect(cx - 52, 60, 104, 26)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor("#1E293B")))
                painter.drawRoundedRect(name_rect, 13, 13)
                
                painter.setPen(QColor(self.dlg.colors[i]))
                painter.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
                painter.drawText(name_rect, Qt.AlignCenter, cand['name'])
                
            # 5. 하단 결과 슬롯 카드 (먼저 도착한 학생부터 실시간 오픈!)
            for i in range(num_cols):
                cx = xs[i]
                slot_rect = QRect(cx - 54, bot_y + 16, 108, 56)
                res = self.dlg.slot_results[i] if hasattr(self.dlg, 'slot_results') and i < len(self.dlg.slot_results) else None
                
                if res is None:
                    painter.setPen(QPen(QColor("#475569"), 2))
                    painter.setBrush(QBrush(QColor("#1E293B")))
                    painter.drawRoundedRect(slot_rect, 12, 12)
                    
                    painter.setPen(QColor("#F1C40F"))
                    painter.setFont(QFont('Segoe UI Emoji', 16))
                    painter.drawText(QRectF(slot_rect.left(), slot_rect.top() + 4, slot_rect.width(), 26), Qt.AlignCenter, "❓")
                    
                    painter.setPen(QColor("#64748B"))
                    painter.setFont(QFont('Malgun Gothic', 8, QFont.Bold))
                    painter.drawText(QRectF(slot_rect.left(), slot_rect.top() + 32, slot_rect.width(), 18), Qt.AlignCenter, "대기 중")
                else:
                    cand = res['cand']
                    if res['is_winner']:
                        painter.setPen(QPen(QColor("#F59E0B"), 3))
                        painter.setBrush(QBrush(QColor("#064E3B")))
                        painter.drawRoundedRect(slot_rect, 12, 12)
                        
                        painter.setPen(QColor("#FDE047"))
                        painter.setFont(QFont('Malgun Gothic', 10, QFont.Bold))
                        painter.drawText(QRectF(slot_rect.left(), slot_rect.top() + 6, slot_rect.width(), 20), Qt.AlignCenter, "🎯 발표자 당첨!")
                        
                        painter.setPen(QColor("#FFFFFF"))
                        painter.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
                        painter.drawText(QRectF(slot_rect.left(), slot_rect.top() + 28, slot_rect.width(), 22), Qt.AlignCenter, f"👑 {cand['name']}")
                    else:
                        painter.setPen(QPen(QColor("#3B82F6"), 1.5))
                        painter.setBrush(QBrush(QColor("#1E293B")))
                        painter.drawRoundedRect(slot_rect, 12, 12)
                        
                        painter.setPen(QColor("#38BDF8"))
                        painter.setFont(QFont('Malgun Gothic', 10, QFont.Bold))
                        painter.drawText(QRectF(slot_rect.left(), slot_rect.top() + 6, slot_rect.width(), 20), Qt.AlignCenter, "☕ 통과 (세이프)")
                        
                        painter.setPen(QColor("#E2E8F0"))
                        painter.setFont(QFont('Malgun Gothic', 10))
                        painter.drawText(QRectF(slot_rect.left(), slot_rect.top() + 28, slot_rect.width(), 22), Qt.AlignCenter, f"😄 {cand['name']}")
        except Exception as e:
            print("LadderCanvasWidget paint error:", e)


class PresenterLadderDialog(QDialog):
    def __init__(self, candidates, parent_app=None, exclude_ids=None):
        super().__init__(parent_app)
        self.candidates = candidates
        self.parent_app = parent_app
        self.base_dir = getattr(parent_app, "base_dir", os.path.dirname(os.path.abspath(__file__)))
        self.exclude_ids = list(exclude_ids) if exclude_ids else []
        
        valid_candidates = [c for c in self.candidates if c['id'] not in self.exclude_ids]
        if not valid_candidates:
            valid_candidates = self.candidates
            self.exclude_ids = []
            
        self.pool = valid_candidates
        self.winner = None
        self.is_running = False
        self.is_finished = False
        self.progress = 0.0
        self.is_blind = True
        
        self.init_ladder_data()
        self.initUI()
        
    def init_ladder_data(self):
        self.num_cols = len(self.pool)
        if self.num_cols <= 1:
            self.winner = self.pool[0] if self.pool else None
            self.progresses = [1.0]
            self.speeds = [0.0]
            self.finished_students = [True]
            self.slot_results = [{'cand': self.pool[0], 'is_winner': True}] if self.pool else [None]
            self.progress = 1.0
            return
            
        self.num_levels = max(9, min(14, self.num_cols * 2))
        
        self.bridges = []
        for lvl in range(1, self.num_levels + 1):
            cols_avail = list(range(self.num_cols - 1))
            random.shuffle(cols_avail)
            used = set()
            for c in cols_avail:
                if c - 1 not in used and c + 1 not in used and random.random() < 0.65:
                    self.bridges.append((c, lvl))
                    used.add(c)
                    
        if not self.bridges:
            for lvl in range(1, self.num_levels + 1):
                self.bridges.append((lvl % (self.num_cols - 1), lvl))
                
        self.paths = []
        for start_col in range(self.num_cols):
            curr_col = start_col
            pts = [(float(curr_col), 0.0)]
            for lvl in range(1, self.num_levels + 1):
                y_norm = lvl / (self.num_levels + 1)
                if (curr_col, lvl) in self.bridges:
                    pts.append((float(curr_col), y_norm))
                    curr_col += 1
                    pts.append((float(curr_col), y_norm))
                elif (curr_col - 1, lvl) in self.bridges:
                    pts.append((float(curr_col), y_norm))
                    curr_col -= 1
                    pts.append((float(curr_col), y_norm))
            pts.append((float(curr_col), 1.0))
            self.paths.append(pts)
            
        self.seg_dists = []
        self.path_lengths = []
        for path in self.paths:
            dists = []
            tot = 0.0
            for i in range(len(path) - 1):
                dx = (path[i+1][0] - path[i][0]) * 1.5
                dy = (path[i+1][1] - path[i][1]) * 1.0
                d = math.sqrt(dx*dx + dy*dy)
                dists.append(d)
                tot += d
            self.seg_dists.append(dists)
            self.path_lengths.append(tot)
            
        self.win_slot = random.randint(0, self.num_cols - 1)
        for idx, path in enumerate(self.paths):
            if int(round(path[-1][0])) == self.win_slot:
                self.winner = self.pool[idx]
                break
        else:
            self.winner = self.pool[0]
            
        palette = [
            "#38BDF8", "#34D399", "#FBBF24", "#F472B6", "#A78BFA", 
            "#2DD4BF", "#FB923C", "#A3E635", "#FB7185", "#818CF8",
            "#4ADE80", "#F43F5E", "#06B6D4", "#E879F9", "#FACC15"
        ]
        self.colors = [palette[i % len(palette)] for i in range(self.num_cols)]
        
        self.progresses = [0.0] * self.num_cols
        self.base_speeds = [random.uniform(0.0067, 0.0074) for _ in range(self.num_cols)]
        self.speeds = list(self.base_speeds)
        self.finished_students = [False] * self.num_cols
        self.slot_results = [None] * self.num_cols
        self.first_winner_revealed = False
        self.progress = 0.0
        self.last_beep_idx = -1
        
    def get_point_on_path(self, path, progress, k):
        if progress <= 0.0:
            return path[0]
        if progress >= 1.0:
            return path[-1]
            
        tot = self.path_lengths[k]
        if tot == 0:
            return path[0]
            
        target_d = progress * tot
        accum = 0.0
        dists = self.seg_dists[k]
        for i, d in enumerate(dists):
            if accum + d >= target_d:
                ratio = (target_d - accum) / d if d > 0 else 0
                cx = path[i][0] + (path[i+1][0] - path[i][0]) * ratio
                cy = path[i][1] + (path[i+1][1] - path[i][1]) * ratio
                return (cx, cy)
            accum += d
        return path[-1]
        
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setAlignment(Qt.AlignCenter)
        
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame#LadderMainFrame {
                background-color: #0F172A;
                border: 4px solid #10B981;
                border-radius: 25px;
            }
        """)
        self.frame.setObjectName("LadderMainFrame")
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(30, 25, 30, 25)
        frame_layout.setSpacing(15)
        
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("🪜 오늘의 발표자 사다리 타기 🎯")
        title_lbl.setFont(QFont('Malgun Gothic', 24, QFont.Bold))
        title_lbl.setStyleSheet("color: #34D399; background: transparent; border: none;")
        
        self.sub_lbl = QLabel("과연 사다리를 타고 내려와 발표자가 될 행운의 주인공은 누구일까요?")
        self.sub_lbl.setFont(QFont('Malgun Gothic', 13))
        self.sub_lbl.setStyleSheet("color: #94A3B8; background: transparent; border: none;")
        
        title_box.addWidget(title_lbl)
        title_box.addWidget(self.sub_lbl)
        header.addLayout(title_box)
        header.addStretch()
        
        close_icon_btn = QPushButton("✖")
        close_icon_btn.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        close_icon_btn.setFixedSize(45, 45)
        close_icon_btn.setCursor(Qt.PointingHandCursor)
        close_icon_btn.setStyleSheet("""
            QPushButton { background-color: #334155; color: #CBD5E1; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #EF4444; color: white; }
        """)
        close_icon_btn.clicked.connect(self.reject)
        header.addWidget(close_icon_btn)
        
        frame_layout.addLayout(header)
        
        if self.num_cols > 1:
            self.canvas = LadderCanvasWidget(self)
            frame_layout.addWidget(self.canvas, stretch=1)
        else:
            single_box = QLabel(f"후보 학생이 {self.winner['name']} 학생 1명뿐이어서 바로 발표자로 선정됩니다!")
            single_box.setFont(QFont('Malgun Gothic', 22, QFont.Bold))
            single_box.setStyleSheet("color: white; padding: 100px;")
            single_box.setAlignment(Qt.AlignCenter)
            frame_layout.addWidget(single_box, stretch=1)
        
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(15)
        btn_bar.setAlignment(Qt.AlignCenter)
        
        self.start_btn = QPushButton("▶️  사다리 타기 시작!")
        self.start_btn.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        self.start_btn.setFixedHeight(54)
        self.start_btn.setFixedWidth(240)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton { background-color: #10B981; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #059669; }
            QPushButton:disabled { background-color: #475569; color: #94A3B8; }
        """)
        self.start_btn.clicked.connect(self.start_ladder)
        btn_bar.addWidget(self.start_btn)
        
        self.skip_btn = QPushButton("⚡ 바로 결과 보기")
        self.skip_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.skip_btn.setFixedHeight(54)
        self.skip_btn.setFixedWidth(180)
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.setStyleSheet("""
            QPushButton { background-color: #334155; color: #CBD5E1; border-radius: 12px; border: 1px solid #475569; }
            QPushButton:hover { background-color: #475569; color: white; }
        """)
        self.skip_btn.clicked.connect(self.skip_ladder)
        btn_bar.addWidget(self.skip_btn)
        
        self.restart_btn = QPushButton("🔄 사다리 섞기")
        self.restart_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.restart_btn.setFixedHeight(54)
        self.restart_btn.setFixedWidth(160)
        self.restart_btn.setCursor(Qt.PointingHandCursor)
        self.restart_btn.setStyleSheet("""
            QPushButton { background-color: #F59E0B; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #D97706; }
        """)
        self.restart_btn.clicked.connect(self.reset_ladder)
        btn_bar.addWidget(self.restart_btn)
        
        self.blind_btn = QPushButton("👀 사다리 미리보기")
        self.blind_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.blind_btn.setFixedHeight(54)
        self.blind_btn.setFixedWidth(160)
        self.blind_btn.setCursor(Qt.PointingHandCursor)
        self.blind_btn.setStyleSheet("""
            QPushButton { background-color: #334155; color: #CBD5E1; border-radius: 12px; border: 1px solid #475569; }
            QPushButton:hover { background-color: #475569; color: white; }
        """)
        self.blind_btn.clicked.connect(self.toggle_blind)
        btn_bar.addWidget(self.blind_btn)
        
        self.close_btn = QPushButton("확인 (닫기)")
        self.close_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.close_btn.setFixedHeight(54)
        self.close_btn.setFixedWidth(140)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton { background-color: #10B981; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #059669; }
        """)
        self.close_btn.clicked.connect(self.accept)
        btn_bar.addWidget(self.close_btn)
        
        frame_layout.addLayout(btn_bar)
        layout.addWidget(self.frame)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        
    def toggle_blind(self):
        self.is_blind = not self.is_blind
        self.blind_btn.setText("🙈 사다리 가리기" if not self.is_blind else "👀 사다리 미리보기")
        if hasattr(self, 'canvas'):
            self.canvas.update()
        
    def play_fanfare(self):
        self.player = QMediaPlayer(None, QMediaPlayer.LowLatency)
        audio_path = os.path.join(self.base_dir, 'mvp_sound.mp3')
        if os.path.exists(audio_path):
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
            self.player.play()

    def closeEvent(self, event):
        if hasattr(self, 'player'):
            self.player.stop()
        super().closeEvent(event)

    def start_ladder(self):
        if self.num_cols <= 1:
            self.sub_lbl.setText(f"🎉 축하합니다! 오늘의 발표자는 [ {self.winner['name']} ] 학생입니다! 👏")
            self.sub_lbl.setStyleSheet("color: #34D399; font-size: 15px; font-weight: bold; background: transparent; border: none;")
            self.play_fanfare()
            if self.parent_app and hasattr(self.parent_app, 'play_tts'):
                self.parent_app.play_tts(f"{self.winner['name']} 학생, 사다리 발표자로 당첨되었습니다! 멋진 발표 부탁드립니다.")
            return
            
        if self.is_running:
            return
            
        self.is_running = True
        self.is_finished = False
        self.is_blind = False
        if hasattr(self, 'blind_btn'):
            self.blind_btn.setText("🙈 사다리 가리기")
            
        self.progresses = [0.0] * self.num_cols
        self.base_speeds = [random.uniform(0.0067, 0.0074) for _ in range(self.num_cols)]
        self.speeds = list(self.base_speeds)
        self.finished_students = [False] * self.num_cols
        self.slot_results = [None] * self.num_cols
        self.first_winner_revealed = False
        self.progress = 0.0
        self.last_beep_idx = -1
        
        self.start_btn.setEnabled(False)
        self.start_btn.setText("사다리 타는 중... 🪜")
        self.sub_lbl.setText("과연 누가 먼저 내려올까요? 먼저 내려온 친구부터 결과가 즉시 공개됩니다! 🏁")
        self.sub_lbl.setStyleSheet("color: #60A5FA; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        self.timer.start(30)
        
    def update_animation(self):
        any_finished_this_frame = False
        winner_just_arrived = False
        
        for k in range(self.num_cols):
            if not self.finished_students[k]:
                jitter = random.uniform(-0.00006, 0.00006)
                self.speeds[k] = max(0.0063, min(0.0076, self.speeds[k] + jitter))
                self.progresses[k] += self.speeds[k]
                
                if self.progresses[k] >= 1.0:
                    self.progresses[k] = 1.0
                    self.finished_students[k] = True
                    any_finished_this_frame = True
                    
                    dest_col = int(round(self.paths[k][-1][0]))
                    is_win = (dest_col == self.win_slot)
                    cand = self.pool[k]
                    self.slot_results[dest_col] = {
                        'cand': cand,
                        'is_winner': is_win,
                        'student_idx': k
                    }
                    
                    if is_win:
                        winner_just_arrived = True
                        self.first_winner_revealed = True
                        
        self.progress = max(self.progresses) if self.progresses else 0.0
        
        if any_finished_this_frame:
            QApplication.beep()
            
        if winner_just_arrived:
            self.sub_lbl.setText(f"🎯 [ {self.winner['name']} ] 학생이 발표자 슬롯에 도착했습니다!! 👑")
            self.sub_lbl.setStyleSheet("color: #FBBF24; font-size: 15px; font-weight: bold; background: transparent; border: none;")
            
        if all(self.finished_students):
            self.timer.stop()
            self.is_running = False
            self.is_finished = True
            self.start_btn.setEnabled(True)
            self.start_btn.setText("▶️ 다시 타기")
            self.sub_lbl.setText(f"🎉 축하합니다! 오늘의 발표자는 [ {self.winner['name']} ] 학생입니다! 멋진 발표 부탁드립니다. 👏")
            self.sub_lbl.setStyleSheet("color: #34D399; font-size: 15px; font-weight: bold; background: transparent; border: none;")
            if hasattr(self, 'canvas'):
                self.canvas.update()
            self.play_fanfare()
            if self.parent_app and hasattr(self.parent_app, 'play_tts'):
                self.parent_app.play_tts(f"{self.winner['name']} 학생, 사다리 발표자로 당첨되었습니다! 멋진 발표 부탁드립니다.")
            return
            
        if hasattr(self, 'canvas'):
            self.canvas.update()
            
    def skip_ladder(self):
        self.timer.stop()
        self.is_running = False
        self.is_finished = True
        self.is_blind = False
        if hasattr(self, 'blind_btn'):
            self.blind_btn.setText("🙈 사다리 가리기")
            
        for k in range(self.num_cols):
            self.progresses[k] = 1.0
            self.finished_students[k] = True
            dest_col = int(round(self.paths[k][-1][0]))
            self.slot_results[dest_col] = {
                'cand': self.pool[k],
                'is_winner': (dest_col == self.win_slot),
                'student_idx': k
            }
            
        self.progress = 1.0
        self.start_btn.setEnabled(True)
        self.start_btn.setText("▶️ 다시 타기")
        self.sub_lbl.setText(f"🎉 축하합니다! 오늘의 발표자는 [ {self.winner['name']} ] 학생입니다! 멋진 발표 부탁드립니다. 👏")
        self.sub_lbl.setStyleSheet("color: #34D399; font-size: 15px; font-weight: bold; background: transparent; border: none;")
        if hasattr(self, 'canvas'):
            self.canvas.update()
        self.play_fanfare()
        if self.parent_app and hasattr(self.parent_app, 'play_tts'):
            self.parent_app.play_tts(f"{self.winner['name']} 학생, 사다리 발표자로 당첨되었습니다! 멋진 발표 부탁드립니다.")
        
    def reset_ladder(self):
        self.timer.stop()
        if hasattr(self, 'player'):
            self.player.stop()
        self.is_running = False
        self.is_finished = False
        self.is_blind = True
        if hasattr(self, 'blind_btn'):
            self.blind_btn.setText("👀 사다리 미리보기")
        self.start_btn.setEnabled(True)
        self.start_btn.setText("▶️  사다리 타기 시작!")
        self.sub_lbl.setText("과연 사다리를 타고 내려와 발표자가 될 행운의 주인공은 누구일까요?")
        self.sub_lbl.setStyleSheet("color: #94A3B8; font-size: 13px; background: transparent; border: none;")
        self.init_ladder_data()
        if hasattr(self, 'canvas'):
            self.canvas.update()


class PresenterLotteryDialog(QDialog):
    def __init__(self, candidates, parent_app=None, exclude_ids=None):
        super().__init__(parent_app)
        self.candidates = candidates
        self.parent_app = parent_app
        self.base_dir = getattr(parent_app, "base_dir", os.path.dirname(os.path.abspath(__file__)))
        self.exclude_ids = list(exclude_ids) if exclude_ids else []
        
        valid_candidates = [c for c in self.candidates if c['id'] not in self.exclude_ids]
        if not valid_candidates:
            valid_candidates = self.candidates
            self.exclude_ids = []
            
        self.pool = valid_candidates
        self.shuffled_pool = list(self.pool)
        random.shuffle(self.shuffled_pool)
        
        self.winner = None
        self.winner_idx = -1
        self.is_running = False
        self.is_finished = False
        self.anim_step = 0
        self.total_anim_steps = 32
        self.highlight_idx = 0
        self.slip_buttons = []
        
        self.initUI()
        
    def play_fanfare(self):
        self.player = QMediaPlayer(None, QMediaPlayer.LowLatency)
        audio_path = os.path.join(self.base_dir, 'mvp_sound.mp3')
        if os.path.exists(audio_path):
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
            self.player.play()

    def closeEvent(self, event):
        if hasattr(self, 'player'):
            self.player.stop()
        super().closeEvent(event)
        
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 25, 40, 25)
        layout.setAlignment(Qt.AlignCenter)
        
        self.frame = QFrame()
        self.frame.setFixedSize(1040, 780)
        self.frame.setStyleSheet("""
            QFrame#LotteryMainFrame {
                background-color: #0F172A;
                border: 4px solid #F59E0B;
                border-radius: 28px;
            }
        """)
        self.frame.setObjectName("LotteryMainFrame")
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(35, 25, 35, 25)
        frame_layout.setSpacing(15)
        
        # 1. 헤더 바
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("🎁 오늘의 발표자 제비뽑기 🎯")
        title_lbl.setFont(QFont('Malgun Gothic', 23, QFont.Bold))
        title_lbl.setStyleSheet("color: #FBBF24; background: transparent; border: none;")
        
        self.sub_lbl = QLabel("원하는 제비를 직접 클릭하거나, [🎲 랜덤 제비 뽑기] 버튼을 눌러보세요!")
        self.sub_lbl.setFont(QFont('Malgun Gothic', 13))
        self.sub_lbl.setStyleSheet("color: #94A3B8; background: transparent; border: none;")
        
        title_box.addWidget(title_lbl)
        title_box.addWidget(self.sub_lbl)
        header.addLayout(title_box)
        header.addStretch()
        
        close_icon_btn = QPushButton("✖")
        close_icon_btn.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        close_icon_btn.setFixedSize(45, 45)
        close_icon_btn.setCursor(Qt.PointingHandCursor)
        close_icon_btn.setStyleSheet("""
            QPushButton { background-color: #334155; color: #CBD5E1; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #EF4444; color: white; }
        """)
        close_icon_btn.clicked.connect(self.reject)
        header.addWidget(close_icon_btn)
        frame_layout.addLayout(header)
        
        # 2. 상단 당첨 무대 (Lucky Stage)
        stage_box = QFrame()
        stage_box.setFixedHeight(240)
        stage_box.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 2px solid #334155;
                border-radius: 20px;
            }
        """)
        stage_layout = QHBoxLayout(stage_box)
        stage_layout.setContentsMargins(25, 15, 25, 15)
        stage_layout.setSpacing(25)
        stage_layout.setAlignment(Qt.AlignCenter)
        
        # Left: 상자 아이콘
        self.box_icon_lbl = QLabel("🎁")
        self.box_icon_lbl.setFont(QFont('Segoe UI Emoji', 60))
        self.box_icon_lbl.setAlignment(Qt.AlignCenter)
        self.box_icon_lbl.setFixedWidth(120)
        self.box_icon_lbl.setStyleSheet("border: none; background: transparent;")
        stage_layout.addWidget(self.box_icon_lbl)
        
        # Center: 학생 사진
        self.photo_lbl = QLabel()
        self.photo_lbl.setFixedSize(150, 190)
        self.photo_lbl.setStyleSheet("background-color: #0F172A; border: 4px dashed #F59E0B; border-radius: 14px;")
        self.photo_lbl.setAlignment(Qt.AlignCenter)
        self.photo_lbl.setText("❓")
        self.photo_lbl.setFont(QFont('Segoe UI Emoji', 38))
        stage_layout.addWidget(self.photo_lbl)
        
        # Right: 텍스트 정보
        info_vbox = QVBoxLayout()
        info_vbox.setAlignment(Qt.AlignVCenter)
        info_vbox.setSpacing(8)
        
        self.badge_lbl = QLabel("✨ 행운의 제비뽑기 대기 중")
        self.badge_lbl.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        self.badge_lbl.setStyleSheet("color: #FDE68A; background: #78350F; padding: 5px 12px; border-radius: 8px; border: none;")
        info_vbox.addWidget(self.badge_lbl, alignment=Qt.AlignLeft)
        
        self.name_lbl = QLabel("어떤 제비가 당첨될까요?")
        self.name_lbl.setFont(QFont('Malgun Gothic', 24, QFont.Bold))
        self.name_lbl.setStyleSheet("color: white; border: none;")
        info_vbox.addWidget(self.name_lbl)
        
        self.msg_lbl = QLabel("아래 번호 제비 중 하나를 고르거나 자동 추첨을 시작하세요.")
        self.msg_lbl.setFont(QFont('Malgun Gothic', 12))
        self.msg_lbl.setStyleSheet("color: #94A3B8; border: none;")
        info_vbox.addWidget(self.msg_lbl)
        
        stage_layout.addLayout(info_vbox)
        stage_layout.addStretch()
        frame_layout.addWidget(stage_box)
        
        # 3. 하단 제비 슬립 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #0B1120;
                border: 2px solid #1E293B;
                border-radius: 16px;
            }
            QScrollBar:vertical {
                background: #1E293B;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #475569;
                border-radius: 5px;
            }
        """)
        scroll_area.setWidgetResizable(True)
        
        self.slips_container = QWidget()
        self.slips_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.slips_container)
        self.grid_layout.setContentsMargins(15, 15, 15, 15)
        self.grid_layout.setSpacing(12)
        
        self.create_slip_buttons()
        scroll_area.setWidget(self.slips_container)
        frame_layout.addWidget(scroll_area, stretch=1)
        
        # 4. 하단 버튼 바
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(15)
        btn_bar.setAlignment(Qt.AlignCenter)
        
        self.draw_btn = QPushButton("🎲  랜덤 제비 뽑기!")
        self.draw_btn.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        self.draw_btn.setFixedHeight(54)
        self.draw_btn.setFixedWidth(220)
        self.draw_btn.setCursor(Qt.PointingHandCursor)
        self.draw_btn.setStyleSheet("""
            QPushButton { background-color: #F59E0B; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #D97706; }
            QPushButton:disabled { background-color: #475569; color: #94A3B8; }
        """)
        self.draw_btn.clicked.connect(self.start_random_draw)
        btn_bar.addWidget(self.draw_btn)
        
        self.skip_btn = QPushButton("⚡ 바로 결과 보기")
        self.skip_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.skip_btn.setFixedHeight(54)
        self.skip_btn.setFixedWidth(170)
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.setStyleSheet("""
            QPushButton { background-color: #334155; color: #CBD5E1; border-radius: 12px; border: 1px solid #475569; }
            QPushButton:hover { background-color: #475569; color: white; }
        """)
        self.skip_btn.clicked.connect(self.skip_draw)
        btn_bar.addWidget(self.skip_btn)
        
        self.restart_btn = QPushButton("🔄 다시 섞기")
        self.restart_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.restart_btn.setFixedHeight(54)
        self.restart_btn.setFixedWidth(140)
        self.restart_btn.setCursor(Qt.PointingHandCursor)
        self.restart_btn.setStyleSheet("""
            QPushButton { background-color: #3B82F6; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #2563EB; }
        """)
        self.restart_btn.clicked.connect(self.reset_slips)
        btn_bar.addWidget(self.restart_btn)
        
        self.close_btn = QPushButton("확인 (닫기)")
        self.close_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.close_btn.setFixedHeight(54)
        self.close_btn.setFixedWidth(140)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton { background-color: #10B981; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #059669; }
        """)
        self.close_btn.clicked.connect(self.accept)
        btn_bar.addWidget(self.close_btn)
        
        frame_layout.addLayout(btn_bar)
        layout.addWidget(self.frame)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_shuffle_animation)
        
    def create_slip_buttons(self):
        for btn in self.slip_buttons:
            btn.deleteLater()
        self.slip_buttons = []
        
        cols = 6 if len(self.shuffled_pool) >= 12 else max(4, len(self.shuffled_pool))
        for idx, student in enumerate(self.shuffled_pool):
            btn = QPushButton()
            btn.setFixedHeight(75)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1E293B;
                    color: #FBBF24;
                    font-size: 15px;
                    font-weight: bold;
                    border: 2px solid #F59E0B;
                    border-radius: 14px;
                }
                QPushButton:hover {
                    background-color: #334155;
                    border: 2px solid #FDE68A;
                    color: white;
                }
            """)
            btn.setText(f"📜  제비 {idx + 1}")
            btn.clicked.connect(lambda checked, i=idx: self.select_slip(i))
            self.slip_buttons.append(btn)
            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(btn, row, col)
            
    def select_slip(self, idx):
        if self.is_running:
            return
        if self.is_finished:
            student = self.shuffled_pool[idx]
            self.slip_buttons[idx].setText(f"☕ {student['name']}")
            self.slip_buttons[idx].setStyleSheet("""
                QPushButton {
                    background-color: #0F172A;
                    color: #94A3B8;
                    font-size: 13px;
                    border: 1px solid #334155;
                    border-radius: 14px;
                }
            """)
            return
            
        self.reveal_winner(idx)
        
    def reveal_winner(self, idx):
        self.winner_idx = idx
        self.winner = self.shuffled_pool[idx]
        self.is_finished = True
        
        for i, btn in enumerate(self.slip_buttons):
            if i == idx:
                btn.setText(f"👑 {self.winner['name']}!")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #065F46;
                        color: #FDE047;
                        font-size: 15px;
                        font-weight: bold;
                        border: 3px solid #34D399;
                        border-radius: 14px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1E293B;
                        color: #64748B;
                        font-size: 14px;
                        border: 1px solid #334155;
                        border-radius: 14px;
                    }
                """)
                
        self.box_icon_lbl.setText("🎉")
        if self.winner.get('photo') and os.path.exists(self.winner['photo']):
            self.photo_lbl.setPixmap(QPixmap(self.winner['photo']).scaled(150, 190, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.photo_lbl.setStyleSheet("background-color: white; border: 4px solid #10B981; border-radius: 14px;")
        else:
            self.photo_lbl.setText("👤")
            self.photo_lbl.setFont(QFont('Segoe UI Emoji', 45))
            self.photo_lbl.setStyleSheet("background-color: #334155; color: #94A3B8; border: 4px solid #10B981; border-radius: 14px;")
            
        self.badge_lbl.setText(f"🎉 제비 {idx + 1}번 당첨! 오늘의 발표자")
        self.badge_lbl.setStyleSheet("color: white; background: #10B981; padding: 6px 14px; border-radius: 10px; font-weight: bold; border: none;")
        self.name_lbl.setText(f"✨ {self.winner['name']} 학생 ✨")
        self.name_lbl.setStyleSheet("color: #FBBF24; font-size: 26px; font-weight: bold; border: none;")
        self.msg_lbl.setText("멋진 발표와 활약을 기대합니다! 👏")
        self.msg_lbl.setStyleSheet("color: #6EE7B7; font-size: 14px; font-weight: bold; border: none;")
        
        self.sub_lbl.setText(f"🎉 축하합니다! 오늘의 발표자는 [ {self.winner['name']} ] 학생입니다! 👏")
        self.sub_lbl.setStyleSheet("color: #34D399; font-size: 15px; font-weight: bold; background: transparent; border: none;")
        
        self.draw_btn.setEnabled(True)
        self.draw_btn.setText("🎲 다시 뽑기")
        
        self.play_fanfare()
        if self.parent_app and hasattr(self.parent_app, 'play_tts'):
            self.parent_app.play_tts(f"{self.winner['name']} 학생, 제비뽑기로 오늘의 발표자에 당첨되었습니다! 멋진 발표 부탁드립니다.")
            
    def start_random_draw(self):
        if self.is_running:
            return
            
        self.is_running = True
        self.is_finished = False
        self.anim_step = 0
        self.total_anim_steps = 30
        self.draw_btn.setEnabled(False)
        self.draw_btn.setText("제비 섞는 중... 🎲")
        
        self.box_icon_lbl.setText("📦")
        self.badge_lbl.setText("🎲 두근두근 제비 뽑는 중...")
        self.badge_lbl.setStyleSheet("color: #FDE68A; background: #78350F; padding: 6px 14px; border-radius: 10px; border: none;")
        self.name_lbl.setText("과연 누구의 제비가 나올까요?")
        self.photo_lbl.clear()
        self.photo_lbl.setText("❓")
        self.photo_lbl.setStyleSheet("background-color: #0F172A; border: 4px dashed #F59E0B; border-radius: 14px;")
        
        for idx, btn in enumerate(self.slip_buttons):
            btn.setText(f"📜  제비 {idx + 1}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1E293B;
                    color: #FBBF24;
                    font-size: 15px;
                    font-weight: bold;
                    border: 2px solid #F59E0B;
                    border-radius: 14px;
                }
            """)
            
        self.timer.start(50)
        
    def update_shuffle_animation(self):
        self.anim_step += 1
        
        old_btn = self.slip_buttons[self.highlight_idx]
        old_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #FBBF24;
                font-size: 15px;
                font-weight: bold;
                border: 2px solid #F59E0B;
                border-radius: 14px;
            }
        """)
        
        self.highlight_idx = random.randint(0, len(self.shuffled_pool) - 1)
        active_btn = self.slip_buttons[self.highlight_idx]
        active_btn.setStyleSheet("""
            QPushButton {
                background-color: #78350F;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: 3px solid #FDE047;
                border-radius: 14px;
            }
        """)
        
        QApplication.beep()
        
        if self.anim_step >= self.total_anim_steps:
            self.timer.stop()
            self.is_running = False
            self.reveal_winner(self.highlight_idx)
            
    def skip_draw(self):
        if self.timer.isActive():
            self.timer.stop()
        self.is_running = False
        target_idx = random.randint(0, len(self.shuffled_pool) - 1)
        self.reveal_winner(target_idx)
        
    def reset_slips(self):
        if self.timer.isActive():
            self.timer.stop()
        if hasattr(self, 'player'):
            self.player.stop()
            
        self.is_running = False
        self.is_finished = False
        self.winner = None
        self.winner_idx = -1
        
        random.shuffle(self.shuffled_pool)
        self.create_slip_buttons()
        
        self.box_icon_lbl.setText("🎁")
        self.photo_lbl.clear()
        self.photo_lbl.setText("❓")
        self.photo_lbl.setStyleSheet("background-color: #0F172A; border: 4px dashed #F59E0B; border-radius: 14px;")
        
        self.badge_lbl.setText("✨ 행운의 제비뽑기 대기 중")
        self.badge_lbl.setStyleSheet("color: #FDE68A; background: #78350F; padding: 6px 14px; border-radius: 10px; border: none;")
        self.name_lbl.setText("어떤 제비가 당첨될까요?")
        self.name_lbl.setStyleSheet("color: white; border: none;")
        self.msg_lbl.setText("아래 번호 제비 중 하나를 고르거나 자동 추첨을 시작하세요.")
        self.msg_lbl.setStyleSheet("color: #94A3B8; border: none;")
        
        self.sub_lbl.setText("원하는 제비를 직접 클릭하거나, [🎲 랜덤 제비 뽑기] 버튼을 눌러보세요!")
        self.sub_lbl.setStyleSheet("color: #94A3B8; font-size: 13px; background: transparent; border: none;")
        
        self.draw_btn.setEnabled(True)
        self.draw_btn.setText("🎲  랜덤 제비 뽑기!")


class RaceTrackWidget(QWidget):
    def __init__(self, parent_dialog):
        super().__init__(parent_dialog)
        self.dlg = parent_dialog
        self.update_min_height()
        self.setStyleSheet("background: transparent;")

    def update_min_height(self):
        N = len(self.dlg.pool)
        # 10명 이하일 때는 스크롤 없이 한 화면에 모든 레인이 꽉 차게 들어오도록 하고,
        # 11명 이상일 때만 레인당 최소 56px로 스크롤을 지원합니다.
        if N <= 10:
            self.setMinimumHeight(400)
        else:
            self.setMinimumHeight(N * 58 + 56)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        N = len(self.dlg.pool)
        if N == 0:
            return

        W = self.width()
        H = self.height()

        header_h = 34
        footer_h = 14
        track_top = header_h
        track_h = max(240, H - header_h - footer_h)
        lane_h = track_h / float(N)

        start_x = 185.0
        finish_x = W - 125.0
        run_dist = max(100.0, finish_x - start_x)

        # 1. 상단 거리 눈금 바 (Distance Markers)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#0F172A"))
        painter.drawRoundedRect(QRectF(10, 3, W - 20, header_h - 6), 8, 8)

        markers = [(0.0, "START"), (0.25, "25m"), (0.50, "50m"), (0.75, "75m"), (1.0, "FINISH 🏁")]
        for ratio, label in markers:
            mx = start_x + ratio * run_dist
            painter.setPen(QPen(QColor("#475569"), 1, Qt.DashLine))
            painter.drawLine(int(mx), int(track_top), int(mx), int(track_top + track_h))

            painter.setPen(QColor("#FBBF24") if ratio in (0.0, 1.0) else QColor("#94A3B8"))
            painter.setFont(QFont('Malgun Gothic', 9, QFont.Bold))
            painter.drawText(QRectF(mx - 45, 3, 90, header_h - 6), Qt.AlignCenter, label)

        # 2. 각 레인 배경 (초록색 잔디/트랙 위에 1등 레인은 강렬한 빨간 계열로 표시!)
        for i in range(N):
            ly = track_top + i * lane_h
            lane_rect = QRectF(12, ly, W - 24, lane_h)

            # 기본 초록색 교차 잔디/트랙 색상 (눈이 편안하고 선명한 스타디움 그린)
            if i % 2 == 0:
                bg_brush = QBrush(QColor("#14532D"))  # 짙은 포레스트 그린
            else:
                bg_brush = QBrush(QColor("#166534"))  # 선명한 에메랄드/잔디 그린

            # 1등으로 달리고 있거나 우승한 레인은 초록 트랙 위에서 보색 대비로 확 튀는 강렬한 레드/크림슨 그라데이션 적용!
            is_leader = (self.dlg.leader_idx == i and (self.dlg.is_running or self.dlg.is_finished))
            is_win_lane = (self.dlg.is_finished and self.dlg.winner_idx == i)

            if is_win_lane:
                l_grad = QLinearGradient(12, ly, W - 12, ly)
                l_grad.setColorAt(0.0, QColor("#991B1B"))
                l_grad.setColorAt(0.5, QColor("#DC2626"))
                l_grad.setColorAt(1.0, QColor("#F43F5E"))
                bg_brush = QBrush(l_grad)
            elif is_leader:
                l_grad = QLinearGradient(12, ly, W - 12, ly)
                l_grad.setColorAt(0.0, QColor("#881337"))
                l_grad.setColorAt(0.45, QColor("#DC2626"))
                l_grad.setColorAt(1.0, QColor("#FB7185"))
                bg_brush = QBrush(l_grad)

            painter.setPen(Qt.NoPen)
            painter.setBrush(bg_brush)
            painter.drawRect(lane_rect)

            # 1위 레인 전용 붉은 네온/골드 테두리 및 진행 게이지 하이라이트
            if is_leader or is_win_lane:
                prog_w = max(0.0, (start_x - 12) + self.dlg.positions[i] * run_dist)
                prog_rect = QRectF(12, ly + 1, prog_w, lane_h - 2)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(254, 202, 202, 70))
                painter.drawRect(prog_rect)

                glow_col = QColor("#FDE047") if is_win_lane else QColor("#FCA5A5")
                painter.setPen(QPen(glow_col, 3.0))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(lane_rect.adjusted(1.5, 1.5, -1.5, -1.5))
            else:
                # 일반 초록 트랙의 깔끔한 흰색 레인 구분선
                painter.setPen(QPen(QColor(255, 255, 255, 115), 1.5))
                painter.drawLine(12, int(ly + lane_h), W - 12, int(ly + lane_h))

            # 좌측 레인 번호 배지 & 미니 프로필 사진 & 학생 이름
            num_badge = QRectF(18, ly + (lane_h - 26) / 2.0, 26, 26)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#EF4444") if is_leader else QColor("#064E3B"))
            painter.drawRoundedRect(num_badge, 7, 7)

            painter.setPen(QColor("#FEF08A") if is_leader else QColor("#D1FAE5"))
            painter.setFont(QFont('Malgun Gothic', 10, QFont.Bold))
            painter.drawText(num_badge, Qt.AlignCenter, "👑" if is_leader else str(i + 1))

            # 좌측 출발선 옆 학생 미니 사진
            mini_sz = min(46.0, max(26.0, lane_h - 10.0))
            mini_rect = QRectF(50, ly + (lane_h - mini_sz) / 2.0, mini_sz, mini_sz)
            pix = self.dlg.avatar_pixmaps.get(i)
            if pix:
                painter.save()
                clip_p = QPainterPath()
                clip_p.addRoundedRect(mini_rect, 8, 8)
                painter.setClipPath(clip_p)
                painter.drawPixmap(mini_rect.toRect(), pix)
                painter.restore()
            else:
                painter.setBrush(QColor("#1E293B"))
                painter.drawRoundedRect(mini_rect, 8, 8)
                painter.setPen(QColor("#94A3B8"))
                painter.setFont(QFont('Malgun Gothic', 10, QFont.Bold))
                painter.drawText(mini_rect, Qt.AlignCenter, self.dlg.pool[i]['name'][:1])

            painter.setPen(QPen(QColor("#FDE047") if is_leader else QColor("#CBD5E1"), 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(mini_rect, 8, 8)

            cand_name = self.dlg.pool[i]['name']
            painter.setPen(QColor("#FEF08A") if is_leader else QColor("#FFFFFF"))
            painter.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
            painter.drawText(QRectF(50 + mini_sz + 8, ly, start_x - (50 + mini_sz + 12), lane_h), Qt.AlignVCenter | Qt.AlignLeft, cand_name)

        # 트랙 외곽 테두리
        painter.setPen(QPen(QColor("#10B981"), 2.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(12, track_top, W - 24, track_h), 6, 6)

        # 3. 출발선 (Start Line) & 결승선 체커보드 (Finish Line)
        painter.setPen(QPen(QColor("#FFFFFF"), 3))
        painter.drawLine(int(start_x), int(track_top), int(start_x), int(track_top + track_h))

        # 체커보드 결승선
        checker_w = 16
        checker_rows = max(14, int(track_h / 10))
        ch_h = track_h / float(checker_rows)
        for r in range(checker_rows):
            for c in range(2):
                is_white = ((r + c) % 2 == 0)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor("#FFFFFF") if is_white else QColor("#0F172A"))
                painter.drawRect(QRectF(finish_x + c * (checker_w / 2.0), track_top + r * ch_h, checker_w / 2.0, ch_h))

        # 4. 각 학생 러너 (큼직한 학생 얼굴 사진 아바타 + 이름표 + 부스트 이펙트)
        for i in range(N):
            ly = track_top + i * lane_h
            cy = ly + lane_h / 2.0
            prog = self.dlg.positions[i]
            rx = start_x + prog * run_dist

            state = self.dlg.states[i]  # 'normal', 'boost', 'super_boost', 'stumble', 'spurt'
            rank = self.dlg.ranks[i]

            # 달리는 상하 바운스 애니메이션 (레인을 벗어나지 않도록 정교하게 조절)
            bounce = 0.0
            if self.dlg.is_running and not self.dlg.finished_flags[i]:
                freq = 0.85 if state in ('boost', 'super_boost', 'spurt') else 0.55
                bounce = math.sin(self.dlg.tick_count * freq + i * 1.7) * min(4.0, lane_h * 0.06)

            ry = cy + bounce - 3.0  # 아래 이름표 공간 확보를 위해 살짝 위로 배치
            photo_h = min(72.0, max(38.0, lane_h - 14.0))
            photo_w = photo_h * 0.92

            # 부스트 불꽃 / 스피드 잔상 효과
            if self.dlg.is_running and not self.dlg.finished_flags[i]:
                if state in ('boost', 'super_boost', 'spurt'):
                    trail_len = 70.0 if state != 'super_boost' else 105.0
                    grad = QLinearGradient(rx - trail_len, ry, rx, ry)
                    if state == 'super_boost':
                        grad.setColorAt(0.0, QColor(56, 189, 248, 0))
                        grad.setColorAt(1.0, QColor(56, 189, 248, 210))
                    else:
                        grad.setColorAt(0.0, QColor(251, 191, 36, 0))
                        grad.setColorAt(1.0, QColor(244, 63, 94, 210))
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(grad))
                    painter.drawRoundedRect(QRectF(rx - trail_len, ry - photo_h * 0.42, trail_len, photo_h * 0.84), 10, 10)

                    # 먼지/불꽃 파티클
                    flame_txt = "⚡💨" if state == 'super_boost' else "🔥💨"
                    painter.setPen(QColor("#FFFFFF"))
                    painter.setFont(QFont('Segoe UI Emoji', max(11, int(photo_h * 0.32))))
                    painter.drawText(QRectF(rx - photo_w / 2.0 - 44, ry - 16, 42, 32), Qt.AlignCenter, flame_txt)
                elif state == 'stumble':
                    painter.setPen(QColor("#93C5FD"))
                    painter.setFont(QFont('Segoe UI Emoji', max(11, int(photo_h * 0.30))))
                    painter.drawText(QRectF(rx - photo_w / 2.0 - 34, ry - 16, 32, 32), Qt.AlignCenter, "💦")

            # 학생 사진 카드 테두리 색상
            border_col = QColor("#FFFFFF")
            border_w = 3.0
            if rank == 1 and (self.dlg.is_running or self.dlg.is_finished):
                border_col = QColor("#FDE047")
                border_w = 4.0
            elif state == 'super_boost':
                border_col = QColor("#38BDF8")
                border_w = 3.5
            elif state in ('boost', 'spurt'):
                border_col = QColor("#FB7185")
                border_w = 3.5

            avatar_rect = QRectF(rx - photo_w / 2.0, ry - photo_h / 2.0, photo_w, photo_h)

            # 1위 후광(Glow) 및 그림자
            if rank == 1 and (self.dlg.is_running or self.dlg.is_finished):
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(253, 224, 71, 75))
                painter.drawRoundedRect(avatar_rect.adjusted(-4, -4, 4, 4), 14, 14)

            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 130))
            painter.drawRoundedRect(avatar_rect.translated(3, 3), 12, 12)

            # 학생 사진 렌더링 (눈에 확 띄는 둥근 사각 포트레이트 카드)
            pix = self.dlg.avatar_pixmaps.get(i)
            if pix:
                painter.save()
                clip_path = QPainterPath()
                clip_path.addRoundedRect(avatar_rect, 12, 12)
                painter.setClipPath(clip_path)
                painter.drawPixmap(avatar_rect.toRect(), pix)
                painter.restore()
            else:
                # 사진이 없을 때도 학생 이름 첫 글자가 큼직하게 보이도록 표시
                painter.setBrush(QColor("#1E293B"))
                painter.drawRoundedRect(avatar_rect, 12, 12)
                painter.setPen(QColor("#F8FAFC"))
                painter.setFont(QFont('Malgun Gothic', max(11, int(photo_h * 0.32)), QFont.Bold))
                painter.drawText(avatar_rect, Qt.AlignCenter, self.dlg.pool[i]['name'][:2])

            # 사진 외곽선
            painter.setPen(QPen(border_col, border_w))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(avatar_rect, 12, 12)

            # 사진 바로 아래 일체형 학생 이름 캡슐 배지 (누군지 한눈에 식별 가능)
            name_badge_w = max(photo_w + 16.0, 64.0)
            name_badge_h = 19.0
            name_badge_rect = QRectF(rx - name_badge_w / 2.0, avatar_rect.bottom() - 8.0, name_badge_w, name_badge_h)
            painter.setPen(QPen(border_col, 1.5))
            painter.setBrush(QColor("#0F172A") if rank != 1 else QColor("#B91C1C"))
            painter.drawRoundedRect(name_badge_rect, 8, 8)

            painter.setPen(QColor("#FDE047") if rank == 1 else QColor("#FFFFFF"))
            painter.setFont(QFont('Malgun Gothic', 9, QFont.Bold))
            painter.drawText(name_badge_rect, Qt.AlignCenter, self.dlg.pool[i]['name'])

            # 1위 왕관 표시 (사진 우측 상단 모서리에 배치하여 1번 레인도 위쪽이 절대 잘리지 않게 함)
            if rank == 1 and (self.dlg.is_running or self.dlg.is_finished):
                painter.setPen(QColor("#FDE047"))
                painter.setFont(QFont('Segoe UI Emoji', max(11, int(photo_h * 0.30))))
                painter.drawText(QRectF(avatar_rect.right() - 14, avatar_rect.top() - 12, 28, 24), Qt.AlignCenter, "👑")

            # 러너 우측 상태 말풍선
            tag_x = avatar_rect.right() + 10
            status_tag = ""
            tag_col = QColor("#FFFFFF")
            if self.dlg.finished_flags[i]:
                if i == self.dlg.winner_idx:
                    status_tag = "🏆 1위 골인!!"
                    tag_col = QColor("#FDE047")
                else:
                    status_tag = f"{self.dlg.finish_order.index(i) + 1}위"
                    tag_col = QColor("#CBD5E1")
            elif self.dlg.is_running:
                if state == 'super_boost':
                    status_tag = "⚡초강력 역전!"
                    tag_col = QColor("#38BDF8")
                elif state == 'boost':
                    status_tag = "🔥스퍼트!"
                    tag_col = QColor("#FDA4AF")
                elif state == 'spurt':
                    status_tag = "🚀막판질주!"
                    tag_col = QColor("#FDE047")
                elif state == 'stumble':
                    status_tag = "헉!💦"
                    tag_col = QColor("#93C5FD")

            if status_tag:
                painter.setPen(tag_col)
                painter.setFont(QFont('Malgun Gothic', 10, QFont.Bold))
                painter.drawText(QRectF(tag_x, ry - 14, 130, 26), Qt.AlignVCenter | Qt.AlignLeft, status_tag)


class PresenterRaceDialog(QDialog):
    def __init__(self, candidates, parent_app=None, exclude_ids=None):
        super().__init__(parent_app)
        self.candidates = candidates
        self.parent_app = parent_app
        self.base_dir = getattr(parent_app, "base_dir", os.path.dirname(os.path.abspath(__file__)))
        self.exclude_ids = list(exclude_ids) if exclude_ids else []

        valid_candidates = [c for c in self.candidates if c['id'] not in self.exclude_ids]
        if not valid_candidates:
            valid_candidates = self.candidates
            self.exclude_ids = []

        self.pool = list(valid_candidates)
        random.shuffle(self.pool)

        self.num_runners = len(self.pool)
        self.positions = [0.0] * self.num_runners
        self.speeds = [0.0] * self.num_runners
        self.states = ['normal'] * self.num_runners
        self.state_timers = [0] * self.num_runners
        self.ranks = list(range(1, self.num_runners + 1))
        self.finished_flags = [False] * self.num_runners
        self.finish_order = []

        self.winner = None
        self.winner_idx = -1
        self.leader_idx = 0
        self.prev_leader_idx = -1
        self.overtake_count = 0
        self.tick_count = 0
        self.race_duration_sec = 7  # 기본 7초
        self.is_running = False
        self.is_finished = False

        # 아바타 이미지 고화질 캐싱
        self.avatar_pixmaps = {}
        for i, c in enumerate(self.pool):
            if c.get('photo') and os.path.exists(c['photo']):
                pix = QPixmap(c['photo'])
                if not pix.isNull():
                    self.avatar_pixmaps[i] = pix.scaled(120, 140, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        self.initUI()

    def play_fanfare(self):
        self.player = QMediaPlayer(None, QMediaPlayer.LowLatency)
        audio_path = os.path.join(self.base_dir, 'mvp_sound.mp3')
        if os.path.exists(audio_path):
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
            self.player.play()

    def closeEvent(self, event):
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        if hasattr(self, 'player'):
            self.player.stop()
        super().closeEvent(event)

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 14, 25, 14)
        layout.setAlignment(Qt.AlignCenter)

        self.frame = QFrame()
        self.frame.setMinimumSize(1160, 740)
        self.frame.setMaximumSize(1420, 960)
        self.frame.setStyleSheet("""
            QFrame#RaceMainFrame {
                background-color: #0F172A;
                border: 4px solid #F43F5E;
                border-radius: 28px;
            }
        """)
        self.frame.setObjectName("RaceMainFrame")

        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(26, 16, 26, 16)
        frame_layout.setSpacing(10)

        # 1. 컴팩트 상단 헤더 + 실시간 중계 한 줄 통합 바 (트랙 영역을 최대한 넓게 확보!)
        header = QHBoxLayout()
        header.setSpacing(14)

        title_lbl = QLabel("🏃‍♂️ 대역전 트랙 레이스 🏁")
        title_lbl.setFont(QFont('Malgun Gothic', 19, QFont.Bold))
        title_lbl.setStyleSheet("color: #FB7185; background: transparent; border: none;")
        header.addWidget(title_lbl)

        self.badge_lbl = QLabel("🎙️ 대기 중")
        self.badge_lbl.setFont(QFont('Malgun Gothic', 10, QFont.Bold))
        self.badge_lbl.setStyleSheet("color: #FECDD3; background: #881337; padding: 5px 10px; border-radius: 8px; border: none;")
        header.addWidget(self.badge_lbl)

        self.commentary_lbl = QLabel("출발선에서 신호총을 기다리고 있습니다! [🏁 레이스 출발!] 버튼을 눌러주세요!")
        self.commentary_lbl.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        self.commentary_lbl.setStyleSheet("color: #FDE047; background: #1E293B; padding: 6px 14px; border-radius: 10px; border: 1px solid #334155;")
        header.addWidget(self.commentary_lbl, stretch=1)

        self.rank_summary_lbl = QLabel("🔥 역전: 0회")
        self.rank_summary_lbl.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.rank_summary_lbl.setStyleSheet("color: #38BDF8; background: #1E293B; padding: 6px 12px; border-radius: 10px; border: 1px solid #334155;")
        header.addWidget(self.rank_summary_lbl)

        close_icon_btn = QPushButton("✖")
        close_icon_btn.setFont(QFont('Malgun Gothic', 14, QFont.Bold))
        close_icon_btn.setFixedSize(40, 40)
        close_icon_btn.setCursor(Qt.PointingHandCursor)
        close_icon_btn.setStyleSheet("""
            QPushButton { background-color: #334155; color: #CBD5E1; border-radius: 10px; border: none; }
            QPushButton:hover { background-color: #EF4444; color: white; }
        """)
        close_icon_btn.clicked.connect(self.reject)
        header.addWidget(close_icon_btn)
        frame_layout.addLayout(header)

        # 2. 중앙 육상 트랙 캔버스 (상단 전광판 박스를 제거하여 트랙이 위아래 잘림 없이 한눈에 꽉 차게 표시됨)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #0B1120;
                border: 2px solid #1E293B;
                border-radius: 18px;
            }
            QScrollBar:vertical {
                background: #1E293B;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #F43F5E;
                border-radius: 5px;
            }
        """)
        self.track_widget = RaceTrackWidget(self)
        self.scroll_area.setWidget(self.track_widget)
        frame_layout.addWidget(self.scroll_area, stretch=1)

        # 3. 하단 컨트롤 버튼 바 (레이스 시간 선택 + 출발/스킵/섞기/닫기)
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(12)
        btn_bar.setAlignment(Qt.AlignCenter)

        dur_lbl = QLabel("⏱️ 레이스 시간:")
        dur_lbl.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        dur_lbl.setStyleSheet("color: #CBD5E1; background: transparent; border: none;")
        btn_bar.addWidget(dur_lbl)

        self.duration_combo = QComboBox()
        self.duration_combo.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        self.duration_combo.setFixedHeight(48)
        self.duration_combo.setFixedWidth(185)
        self.duration_combo.setCursor(Qt.PointingHandCursor)
        self.duration_combo.addItem("⚡ 3초 (초고속)", 3)
        self.duration_combo.addItem("🏃 5초 (빠름)", 5)
        self.duration_combo.addItem("🔥 7초 (기본 추천)", 7)
        self.duration_combo.addItem("🎬 10초 (박진감)", 10)
        self.duration_combo.addItem("🐢 15초 (장거리 대역전)", 15)
        self.duration_combo.setCurrentIndex(2)  # 기본 7초
        self.duration_combo.setStyleSheet("""
            QComboBox {
                background-color: #1E293B;
                color: #FDE047;
                border: 2px solid #F43F5E;
                border-radius: 12px;
                padding: 4px 12px;
            }
            QComboBox:hover {
                border: 2px solid #FB7185;
                background-color: #334155;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #1E293B;
                color: white;
                selection-background-color: #F43F5E;
                selection-color: white;
                border: 1px solid #475569;
                border-radius: 8px;
            }
        """)
        btn_bar.addWidget(self.duration_combo)

        self.start_btn = QPushButton("🏁  레이스 출발! (탕!)")
        self.start_btn.setFont(QFont('Malgun Gothic', 14, QFont.Bold))
        self.start_btn.setFixedHeight(48)
        self.start_btn.setFixedWidth(230)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton { background-color: #F43F5E; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #E11D48; }
            QPushButton:disabled { background-color: #475569; color: #94A3B8; }
        """)
        self.start_btn.clicked.connect(self.start_race)
        btn_bar.addWidget(self.start_btn)

        self.skip_btn = QPushButton("⚡ 바로 결과 보기")
        self.skip_btn.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        self.skip_btn.setFixedHeight(48)
        self.skip_btn.setFixedWidth(170)
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.setStyleSheet("""
            QPushButton { background-color: #334155; color: #CBD5E1; border-radius: 12px; border: 1px solid #475569; }
            QPushButton:hover { background-color: #475569; color: white; }
        """)
        self.skip_btn.clicked.connect(self.skip_race)
        btn_bar.addWidget(self.skip_btn)

        self.restart_btn = QPushButton("🔄 레인 다시 섞기")
        self.restart_btn.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        self.restart_btn.setFixedHeight(48)
        self.restart_btn.setFixedWidth(160)
        self.restart_btn.setCursor(Qt.PointingHandCursor)
        self.restart_btn.setStyleSheet("""
            QPushButton { background-color: #F59E0B; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #D97706; }
        """)
        self.restart_btn.clicked.connect(self.reset_race)
        btn_bar.addWidget(self.restart_btn)

        self.close_btn = QPushButton("확인 (닫기)")
        self.close_btn.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        self.close_btn.setFixedHeight(48)
        self.close_btn.setFixedWidth(135)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton { background-color: #10B981; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #059669; }
        """)
        self.close_btn.clicked.connect(self.accept)
        btn_bar.addWidget(self.close_btn)

        frame_layout.addLayout(btn_bar)
        layout.addWidget(self.frame)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_race)

    def update_leader_card(self, idx, is_winner=False):
        if idx < 0 or idx >= self.num_runners:
            return
        cand = self.pool[idx]
        if is_winner:
            self.rank_summary_lbl.setText(f"🏆 우승: {cand['name']} (역전 {self.overtake_count}회)")
        else:
            self.rank_summary_lbl.setText(f"👑 1위: {cand['name']} (역전 {self.overtake_count}회)")

    def start_race(self):
        if self.num_runners <= 1:
            self.winner_idx = 0
            self.winner = self.pool[0]
            self.positions[0] = 1.0
            self.finished_flags[0] = True
            self.finish_order = [0]
            self.is_finished = True
            self.update_leader_card(0, is_winner=True)
            self.commentary_lbl.setText(f"🎉 단독 출전한 [ {self.winner['name']} ] 학생이 1위로 골인하여 발표자로 선정되었습니다!")
            self.track_widget.update()
            QTimer.singleShot(400, self.show_winner_popup)
            return

        if self.is_running:
            return

        # 이미 완주한 상태에서 다시 누르면 초기화 후 즉시 재출발
        if self.is_finished:
            self.positions = [0.0] * self.num_runners
            self.finished_flags = [False] * self.num_runners
            self.finish_order = []
            self.winner = None
            self.winner_idx = -1
            self.overtake_count = 0

        self.is_running = True
        self.is_finished = False
        self.tick_count = 0
        self.prev_leader_idx = -1

        # 사용자가 선택한 레이스 목표 시간(초) 반영 (기본 7초 기준 배율 계산)
        self.race_duration_sec = self.duration_combo.currentData() or 7
        self.speed_scale = 7.0 / float(self.race_duration_sec)

        # 초기 속도 세팅
        self.speeds = [random.uniform(0.0028, 0.0046) * self.speed_scale for _ in range(self.num_runners)]
        self.states = ['normal'] * self.num_runners
        self.state_timers = [random.randint(10, 22) for _ in range(self.num_runners)]

        self.duration_combo.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.start_btn.setText("레이스 진행 중... 🏃‍♂️💨")
        self.badge_lbl.setText(f"🔴 LIVE ({self.race_duration_sec}초)")
        self.badge_lbl.setStyleSheet("color: white; background: #E11D48; padding: 5px 10px; border-radius: 8px; border: none;")
        self.commentary_lbl.setText("💥 탕!! 출발 신호와 함께 모든 학생들이 힘차게 달려나갑니다!!")
        self.commentary_lbl.setStyleSheet("color: #FDE047; background: #1E293B; padding: 6px 14px; border-radius: 10px; border: 1px solid #334155;")

        QApplication.beep()
        self.timer.start(30)

    def update_race(self):
        self.tick_count += 1
        scale = getattr(self, 'speed_scale', 1.0)

        max_pos = max(self.positions) if self.positions else 0.0
        min_pos = min(self.positions) if self.positions else 0.0

        # 각 주자별 역전 드라마 물리 업데이트
        for i in range(self.num_runners):
            if self.finished_flags[i]:
                continue

            self.state_timers[i] -= 1
            pos = self.positions[i]
            gap_from_leader = max_pos - pos

            # 상태 타이머 만료 시 새로운 드라마틱 이벤트 결정 (고무줄 추격 + 막판 대역전 알고리즘)
            if self.state_timers[i] <= 0:
                r = random.random()
                # 결승선 직전 (72% ~ 95%) 구간에서는 대역전 막판 스퍼트 확률 대폭 상승!
                if 0.70 <= max_pos < 0.96:
                    if gap_from_leader > 0.06 and r < 0.58:
                        self.states[i] = 'super_boost'
                        self.speeds[i] = random.uniform(0.0068, 0.0088) * scale
                        self.state_timers[i] = max(6, int(random.randint(12, 22) / math.sqrt(scale)))
                        if random.random() < 0.45:
                            self.commentary_lbl.setText(f"⚡ 대역전극 시작?! [{self.pool[i]['name']}] 학생이 폭발적인 막판 초강력 스퍼트를 터뜨립니다!!")
                    elif pos >= max_pos - 0.015 and r < 0.42:
                        # 선두 주자가 결승선 앞에서 살짝 긴장하며 주춤!
                        self.states[i] = 'stumble'
                        self.speeds[i] = random.uniform(0.0014, 0.0024) * scale
                        self.state_timers[i] = max(5, int(random.randint(9, 16) / math.sqrt(scale)))
                        self.commentary_lbl.setText(f"헉! 선두를 달리던 [{self.pool[i]['name']}] 학생이 결승선을 앞두고 살짝 지쳤습니다! 추격조의 기회!")
                    else:
                        self.states[i] = 'spurt'
                        self.speeds[i] = random.uniform(0.0046, 0.0064) * scale
                        self.state_timers[i] = max(6, int(random.randint(10, 18) / math.sqrt(scale)))
                else:
                    # 일반 구간에서도 뒤처진 학생에게 부스트, 선두에게 주춤 이벤트를 주어 엎치락뒤치락 연출
                    if gap_from_leader > 0.11 and r < 0.62:
                        self.states[i] = 'super_boost'
                        self.speeds[i] = random.uniform(0.0062, 0.0078) * scale
                        self.state_timers[i] = max(6, int(random.randint(13, 22) / math.sqrt(scale)))
                    elif gap_from_leader > 0.05 and r < 0.48:
                        self.states[i] = 'boost'
                        self.speeds[i] = random.uniform(0.0050, 0.0065) * scale
                        self.state_timers[i] = max(6, int(random.randint(12, 20) / math.sqrt(scale)))
                    elif pos >= max_pos - 0.01 and (max_pos - min_pos) > 0.07 and r < 0.45:
                        self.states[i] = 'stumble'
                        self.speeds[i] = random.uniform(0.0016, 0.0026) * scale
                        self.state_timers[i] = max(5, int(random.randint(9, 16) / math.sqrt(scale)))
                    else:
                        self.states[i] = 'normal'
                        self.speeds[i] = random.uniform(0.0030, 0.0048) * scale
                        self.state_timers[i] = max(6, int(random.randint(10, 20) / math.sqrt(scale)))

            # 미세 호흡 가감속
            jitter = random.uniform(-0.00025, 0.00025) * scale
            self.speeds[i] = max(0.0010 * scale, min(0.0095 * scale, self.speeds[i] + jitter))
            self.positions[i] += self.speeds[i]

            # 결승선 통과 체크!
            if self.positions[i] >= 1.0:
                self.positions[i] = 1.0
                self.finished_flags[i] = True
                self.finish_order.append(i)

                # 가장 먼저 도착한 첫 번째 학생이 최종 발표자(Winner)로 확정!
                if self.winner is None:
                    self.winner_idx = i
                    self.winner = self.pool[i]
                    self.finish_race_with_winner(i)
                    return

        # 실시간 순위 계산
        sorted_indices = sorted(range(self.num_runners), key=lambda k: self.positions[k], reverse=True)
        for r_pos, r_idx in enumerate(sorted_indices):
            self.ranks[r_idx] = r_pos + 1

        current_leader = sorted_indices[0]
        self.leader_idx = current_leader

        # 선두가 바뀌었을 때 (역전 발생!)
        if self.prev_leader_idx != -1 and current_leader != self.prev_leader_idx:
            self.overtake_count += 1
            old_name = self.pool[self.prev_leader_idx]['name']
            new_name = self.pool[current_leader]['name']
            if max_pos > 0.72:
                self.commentary_lbl.setText(f"🔥 대역전!! [{new_name}] 학생이 [{old_name}] 학생을 제치고 결승선 코앞에서 1위로 치고 나갑니다!!")
            else:
                self.commentary_lbl.setText(f"💨 역전 성공! {current_leader + 1}번 레인 [{new_name}] 학생이 선두를 탈환합니다! (역전 {self.overtake_count}회)")
            if self.tick_count % 3 == 0:
                QApplication.beep()

        self.prev_leader_idx = current_leader
        self.update_leader_card(current_leader, is_winner=False)

        # 선두 주자가 스크롤 영역에 잘 보이도록 자동 팔로우
        self.track_widget.update()

    def finish_race_with_winner(self, win_idx):
        self.timer.stop()
        self.is_running = False
        self.is_finished = True
        self.winner_idx = win_idx
        self.winner = self.pool[win_idx]
        self.leader_idx = win_idx

        # 순위 정렬 업데이트
        sorted_indices = sorted(range(self.num_runners), key=lambda k: self.positions[k], reverse=True)
        for r_pos, r_idx in enumerate(sorted_indices):
            self.ranks[r_idx] = r_pos + 1

        self.update_leader_card(win_idx, is_winner=True)
        self.badge_lbl.setText("🏆 레이스 종료")
        self.badge_lbl.setStyleSheet("color: white; background: #10B981; padding: 5px 12px; border-radius: 8px; font-weight: bold; border: none;")

        self.commentary_lbl.setText(f"🎉 [{self.winner['name']}] 학생이 가장 먼저 결승선을 통과하여 오늘의 발표자가 되었습니다! 👏")
        self.commentary_lbl.setStyleSheet("color: #34D399; background: #1E293B; padding: 6px 14px; border-radius: 10px; border: 1px solid #10B981; font-weight: bold;")

        self.duration_combo.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🏁 다시 레이스 달리기!")
        self.track_widget.update()

        # 우승자가 잘 보이도록 해당 레인으로 스크롤 이동 (11명 이상일 때만)
        if self.num_runners > 10:
            lane_y = int((win_idx / float(self.num_runners)) * self.track_widget.height())
            self.scroll_area.verticalScrollBar().setValue(max(0, lane_y - 150))

        # 결승선 골인 장면을 잠시 보여준 뒤 축하 팝업 창 띄우기
        QTimer.singleShot(550, self.show_winner_popup)

    def show_winner_popup(self):
        if not self.winner or not self.isVisible():
            return
        celeb_dlg = PresenterCelebrationDialog(
            self.winner,
            self.candidates,
            self.exclude_ids,
            mode='race',
            parent_app=self.parent_app,
            race_dialog=self
        )
        celeb_dlg.exec_()

    def skip_race(self):
        if self.timer.isActive():
            self.timer.stop()
        win_idx = random.randint(0, self.num_runners - 1)
        for i in range(self.num_runners):
            if i == win_idx:
                self.positions[i] = 1.0
                self.finished_flags[i] = True
            else:
                self.positions[i] = random.uniform(0.78, 0.97)
                self.finished_flags[i] = False
        self.finish_order = [win_idx]
        self.overtake_count = random.randint(4, 9)
        self.finish_race_with_winner(win_idx)

    def reset_race(self):
        if self.timer.isActive():
            self.timer.stop()
        if hasattr(self, 'player'):
            self.player.stop()

        random.shuffle(self.pool)
        self.avatar_pixmaps.clear()
        for i, c in enumerate(self.pool):
            if c.get('photo') and os.path.exists(c['photo']):
                pix = QPixmap(c['photo'])
                if not pix.isNull():
                    self.avatar_pixmaps[i] = pix.scaled(120, 140, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        self.positions = [0.0] * self.num_runners
        self.speeds = [0.0] * self.num_runners
        self.states = ['normal'] * self.num_runners
        self.ranks = list(range(1, self.num_runners + 1))
        self.finished_flags = [False] * self.num_runners
        self.finish_order = []
        self.winner = None
        self.winner_idx = -1
        self.leader_idx = 0
        self.prev_leader_idx = -1
        self.overtake_count = 0
        self.is_running = False
        self.is_finished = False

        self.badge_lbl.setText("🎙️ 대기 중")
        self.badge_lbl.setStyleSheet("color: #FECDD3; background: #881337; padding: 5px 10px; border-radius: 8px; border: none;")
        self.commentary_lbl.setText("레인이 새롭게 배정되었습니다! [🏁 레이스 출발!] 버튼을 눌러 경기를 시작하세요!")
        self.commentary_lbl.setStyleSheet("color: #FDE047; background: #1E293B; padding: 6px 14px; border-radius: 10px; border: 1px solid #334155;")
        self.rank_summary_lbl.setText("🔥 역전: 0회")

        self.duration_combo.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🏁  레이스 출발! (탕!)")
        self.track_widget.update_min_height()
        self.track_widget.update()


class PresenterCelebrationDialog(QDialog):
    def __init__(self, winner, all_candidates, exclude_ids, mode='ladder', parent_app=None, race_dialog=None):
        super().__init__(race_dialog or parent_app)
        self.winner = winner
        self.all_candidates = all_candidates
        self.exclude_ids = list(exclude_ids)
        self.exclude_ids.append(winner['id'])
        self.mode = mode
        self.parent_app = parent_app
        self.race_dialog = race_dialog
        self.base_dir = getattr(parent_app, "base_dir", os.path.dirname(os.path.abspath(__file__)))
        self.initUI()
        self.play_sound()
        
        if self.parent_app and hasattr(self.parent_app, 'play_tts'):
            if self.mode == 'race':
                self.parent_app.play_tts(f"{self.winner['name']} 학생, 치열한 레이스 끝에 1위로 도착하여 오늘의 발표자로 선정되었습니다! 멋진 발표 부탁드립니다.")
            else:
                self.parent_app.play_tts(f"{self.winner['name']} 학생, 오늘의 발표자로 당첨되었습니다! 멋진 발표 부탁드립니다.")
            
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.bg_frame = QFrame()
        self.bg_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.96);
                border-radius: 25px;
                border: 4px solid #10B981;
            }
        """)
        self.bg_frame.setFixedSize(800, 750)
        
        bg_layout = QVBoxLayout(self.bg_frame)
        bg_layout.setAlignment(Qt.AlignCenter)
        bg_layout.setSpacing(20)
        
        title_text = "🏆 레이스 1위! 오늘의 발표자! 🏆" if self.mode == 'race' else "🎯 오늘의 발표자 당첨! 🎯"
        self.title = QLabel(title_text)
        self.title.setFont(QFont('Malgun Gothic', 40 if self.mode == 'race' else 42, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("color: #10B981;")
        bg_layout.addWidget(self.title)
        
        photo = QLabel()
        photo.setFixedSize(300, 380)
        photo.setAlignment(Qt.AlignCenter)
        photo.setStyleSheet("background-color: white; border: 8px solid #10B981; border-radius: 18px;")
        if self.winner.get('photo') and os.path.exists(self.winner['photo']):
            photo.setPixmap(QPixmap(self.winner['photo']).scaled(300, 380, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            photo.setText("사진 없음")
            photo.setFont(QFont('Malgun Gothic', 20))
            photo.setStyleSheet("background-color: #ECEFF1; color: #BDC3C7; border: 8px solid #10B981; border-radius: 18px;")
        bg_layout.addWidget(photo, alignment=Qt.AlignCenter)
        
        name_lbl = QLabel(f"✨ {self.winner['name']} 학생 ✨")
        name_lbl.setFont(QFont('Malgun Gothic', 38, QFont.Bold))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet("color: white;")
        bg_layout.addWidget(name_lbl)
        
        msg_lbl = QLabel("멋진 발표와 활약을 기대합니다! 👏")
        msg_lbl.setFont(QFont('Malgun Gothic', 22, QFont.Bold))
        msg_lbl.setAlignment(Qt.AlignCenter)
        msg_lbl.setStyleSheet("color: #6EE7B7;")
        bg_layout.addWidget(msg_lbl)
        
        # 버튼 영역 (다시 뽑기 / 닫기)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.setAlignment(Qt.AlignCenter)
        
        retry_btn = QPushButton("🔄 다시 뽑기")
        retry_btn.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        retry_btn.setFixedSize(180, 52)
        retry_btn.setCursor(Qt.PointingHandCursor)
        retry_btn.setStyleSheet("""
            QPushButton { background-color: #F59E0B; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #D97706; }
        """)
        retry_btn.clicked.connect(self.retry_pick)
        btn_layout.addWidget(retry_btn)
        
        close_btn = QPushButton("확인 (닫기)")
        close_btn.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        close_btn.setFixedSize(180, 52)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton { background-color: #10B981; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #059669; }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        bg_layout.addLayout(btn_layout)
        layout.addWidget(self.bg_frame)
        
        # 깜빡이 색상 타이머
        self.color_timer = QTimer(self)
        self.colors = ["#10B981", "#3B82F6", "#F59E0B", "#EC4899", "#8B5CF6"]
        self.color_idx = 0
        self.color_timer.timeout.connect(self.update_color)
        self.color_timer.start(250)
        
        # 페이드인 애니메이션
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(800)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()
        
    def play_sound(self):
        self.player = QMediaPlayer(None, QMediaPlayer.LowLatency)
        audio_path = os.path.join(self.base_dir, 'mvp_sound.mp3')
        if os.path.exists(audio_path):
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
            self.player.play()
            
    def update_color(self):
        self.color_idx = (self.color_idx + 1) % len(self.colors)
        self.title.setStyleSheet(f"color: {self.colors[self.color_idx]};")
        
    def retry_pick(self):
        if hasattr(self, 'player'):
            self.player.stop()
        self.accept()
        if self.mode == 'race' and self.race_dialog is not None:
            self.race_dialog.exclude_ids = list(self.exclude_ids)
            valid_cands = [c for c in self.all_candidates if c['id'] not in self.exclude_ids]
            if not valid_cands:
                valid_cands = list(self.all_candidates)
                self.race_dialog.exclude_ids = []
            self.race_dialog.pool = list(valid_cands)
            self.race_dialog.num_runners = len(self.race_dialog.pool)
            self.race_dialog.track_widget.update_min_height()
            self.race_dialog.reset_race()
            return
        if self.mode == 'roulette':
            dlg = PresenterRouletteDialog(self.all_candidates, self.parent_app, exclude_ids=self.exclude_ids)
        elif self.mode == 'race':
            dlg = PresenterRaceDialog(self.all_candidates, self.parent_app, exclude_ids=self.exclude_ids)
        else:
            dlg = PresenterLadderDialog(self.all_candidates, self.parent_app, exclude_ids=self.exclude_ids)
        dlg.exec_()
        
    def closeEvent(self, event):
        if hasattr(self, 'player'):
            self.player.stop()
        super().closeEvent(event)


