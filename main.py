import sys
import csv
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QFrame, QGraphicsDropShadowEffect,
                             QListWidget, QListWidgetItem, QPushButton, QComboBox, QDialog, QTextEdit, QMessageBox, QScrollArea, QMenu, QInputDialog, QGridLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtGui import QPixmap, QFont, QColor, QKeyEvent, QCursor, QPainter, QPen, QBrush, QPainterPath
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QUrl, QPropertyAnimation, QEasingCurve, QRect, QRectF, QSize, QEvent, QPointF
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from collections import Counter
import json
import random
import html
import math

class TTSThread(QThread):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text

    def run(self):
        try:
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass
            import pyttsx3
            engine = pyttsx3.init()
            try:
                engine.stop()
            except Exception:
                pass
            engine.setProperty('rate', 180) 
            engine.say(self.text)
            engine.runAndWait()
        except Exception as e:
            print("TTS Error:", e)
        finally:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class MiniTimerWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(None)  # Top-level window, no parent widget to avoid clipping
        self.parent_app = parent
        self.initUI()
        
    def initUI(self):
        # Frameless, Stays on top, and Tool (to hide from taskbar)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.frame = QFrame()
        self.frame.setObjectName("MiniFrame")
        self.frame.setStyleSheet("""
            QFrame#MiniFrame {
                background-color: rgba(30, 41, 59, 0.9);
                border: 2px solid #3B82F6;
                border-radius: 15px;
            }
        """)
        
        frame_layout = QHBoxLayout(self.frame)
        frame_layout.setContentsMargins(15, 10, 15, 10)
        
        self.time_label = QLabel("수업 시간 조회 중...")
        self.time_label.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.time_label.setStyleSheet("color: #F8FAFC; border: none;")
        self.time_label.setAlignment(Qt.AlignCenter)
        
        frame_layout.addWidget(self.time_label)
        layout.addWidget(self.frame)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.frame.setGraphicsEffect(shadow)
        
        self.setCursor(Qt.PointingHandCursor)
        self.adjustSize()
        self.reposition()
        
    def reposition(self):
        if getattr(self, 'user_moved', False):
            return
        screen_geo = QApplication.primaryScreen().geometry()
        self.adjustSize()
        w = self.width()
        h = self.height()
        margin = 20
        # Position at top right
        self.move(screen_geo.width() - w - margin, margin)
        
    def update_time_display(self, current_period, remaining_minutes):
        if current_period:
            if remaining_minutes == 0:
                text = f"🕒 {current_period} (곧 종료)"
            else:
                text = f"🕒 {current_period} ({remaining_minutes}분 남음)"
            
            if remaining_minutes <= 5:
                self.frame.setStyleSheet("""
                    QFrame#MiniFrame {
                        background-color: rgba(239, 68, 68, 0.95);
                        border: 2px solid #F8FAFC;
                        border-radius: 15px;
                    }
                """)
            else:
                self.frame.setStyleSheet("""
                    QFrame#MiniFrame {
                        background-color: rgba(16, 185, 129, 0.95);
                        border: 2px solid #F8FAFC;
                        border-radius: 15px;
                    }
                """)
        else:
            text = "🕒 쉬는 시간"
            self.frame.setStyleSheet("""
                QFrame#MiniFrame {
                    background-color: rgba(71, 85, 105, 0.9);
                    border: 2px solid #E2E8F0;
                    border-radius: 15px;
                }
            """)
            
        self.time_label.setText(text)
        self.adjustSize()
        self.reposition()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.press_pos = event.globalPos()
            self.is_dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            if hasattr(self, 'press_pos') and (event.globalPos() - self.press_pos).manhattanLength() > 5:
                self.is_dragging = True
                self.user_moved = True
                self.move(event.globalPos() - self.drag_position)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not getattr(self, 'is_dragging', False):
                self.restore_parent()
            self.is_dragging = False
        super().mouseReleaseEvent(event)
        
    def restore_parent(self):
        self.hide()
        if self.parent_app:
            self.parent_app.showFullScreen()
            self.parent_app.activateWindow()
            self.parent_app.raise_()
            self.parent_app.id_input.setFocus()

class LogWriteDialog(QDialog):
    def __init__(self, class_name, parent=None):
        super().__init__(parent)
        self.class_name = class_name
        self.result_text = ""
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(f'{self.class_name} 수업 일지 작성')
        self.resize(500, 400)
        self.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(self)
        
        title = QLabel(f'[{self.class_name}] 오늘 수업 내용')
        title.setFont(QFont('Malgun Gothic', 14, QFont.Bold))
        layout.addWidget(title)
        
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont('Malgun Gothic', 12))
        self.text_edit.setStyleSheet("border: 2px solid #E2E8F0; border-radius: 8px; padding: 10px;")
        layout.addWidget(self.text_edit)
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton('취소')
        save_btn = QPushButton('저장')
        for btn in (cancel_btn, save_btn):
            btn.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
            btn.setFixedHeight(45)
            btn.setCursor(Qt.PointingHandCursor)
        
        cancel_btn.setStyleSheet("background-color: #E74C3C; color: white; border-radius: 5px;")
        save_btn.setStyleSheet("background-color: #2ECC71; color: white; border-radius: 5px;")
        
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.save)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
    def save(self):
        self.result_text = self.text_edit.toPlainText().strip()
        if not self.result_text:
            QMessageBox.warning(self, '경고', '수업 내용을 입력하세요.')
            return
        self.accept()

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

class LogHistoryDialog(QDialog):
    def __init__(self, class_name, logs, parent=None):
        super().__init__(parent)
        self.class_name = class_name
        self.logs = logs
        self.parent_app = parent
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(f'{self.class_name} 전체 수업 기록')
        self.resize(550, 650)
        self.setStyleSheet("background-color: #F8FAFC;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        title = QLabel(f'📚 [{self.class_name}] 지난 수업 기록 모아보기')
        title.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        title.setStyleSheet("color: #2C3E50;")
        header_layout.addWidget(title)
        
        self.count_label = QLabel(f'총 {len(self.logs)}건')
        self.count_label.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        self.count_label.setStyleSheet("color: #3498DB; background-color: #EBF5FB; padding: 5px 15px; border-radius: 8px;")
        header_layout.addWidget(self.count_label, alignment=Qt.AlignRight)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical {
                border: none;
                background: #F1F5F9;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }
        """)
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 15, 0)
        self.scroll_layout.setSpacing(15)
        
        self.draw_logs()
        
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)
        
        layout.addSpacing(10)
        close_btn = QPushButton('닫기')
        close_btn.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        close_btn.setFixedHeight(45)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495E; 
                color: white; 
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2C3E50;
            }
        """)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def draw_logs(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        self.count_label.setText(f'총 {len(self.logs)}건')
                
        for i, log in reversed(list(enumerate(self.logs))):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: white; 
                    border: 1px solid #E2E8F0; 
                    border-radius: 12px;
                }
                QFrame:hover {
                    border: 1px solid #3498DB;
                }
            """)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(0, 0, 0, 10))
            shadow.setOffset(0, 4)
            card.setGraphicsEffect(shadow)
            
            card.setContextMenuPolicy(Qt.CustomContextMenu)
            card.customContextMenuRequested.connect(lambda pos, idx=i, c=card: self.show_context_menu(pos, idx, c))
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 15, 20, 20)
            
            date_layout = QHBoxLayout()
            date_label = QLabel(f"🕒 {log['date']}")
            date_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
            date_label.setStyleSheet("color: #95A5A6; border: none;")
            date_layout.addWidget(date_label)
            
            hint_label = QLabel("💬 우클릭하여 수정/삭제")
            hint_label.setFont(QFont('Malgun Gothic', 9))
            hint_label.setStyleSheet("color: #BDC3C7; border: none;")
            date_layout.addWidget(hint_label, alignment=Qt.AlignRight)
            card_layout.addLayout(date_layout)
            
            content_label = QLabel(log['content'])
            content_label.setFont(QFont('Malgun Gothic', 13))
            content_label.setStyleSheet("color: #2C3E50; border: none; margin-top: 5px;")
            content_label.setWordWrap(True)
            card_layout.addWidget(content_label)
            
            self.scroll_layout.addWidget(card)
            
        self.scroll_layout.addStretch()

    def show_context_menu(self, pos, idx, card):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: white; border: 1px solid #BDC3C7; border-radius: 5px; padding: 5px; }
            QMenu::item { padding: 8px 20px; font-family: 'Malgun Gothic'; font-size: 14px; border-radius: 4px; }
            QMenu::item:selected { background-color: #3498DB; color: white; }
        """)
        edit_action = menu.addAction("✏️ 수정하기")
        delete_action = menu.addAction("🗑️ 삭제하기")
        
        global_pos = card.mapToGlobal(pos)
        action = menu.exec_(global_pos)
        
        if action == edit_action:
            self.edit_log(idx)
        elif action == delete_action:
            self.delete_log(idx)
            
    def edit_log(self, idx):
        old_content = self.logs[idx]['content']
        text, ok = QInputDialog.getMultiLineText(self, '수업 기록 수정', '내용을 수정하세요:', old_content)
        if ok and text.strip():
            self.logs[idx]['content'] = text.strip()
            self.save_and_redraw()

    def delete_log(self, idx):
        reply = QMessageBox.question(self, '기록 삭제', '정말로 이 수업 기록을 삭제하시겠습니까?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.logs[idx]
            self.save_and_redraw()
            
    def save_and_redraw(self):
        self.draw_logs()
        if self.parent_app:
            with open(self.parent_app.class_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.parent_app.class_logs, f, ensure_ascii=False, indent=4)
            self.parent_app.update_log_display(self.class_name)


class MVPVoteDialog(QDialog):
    def __init__(self, active_students, students_data, parent_app):
        super().__init__(parent_app)
        self.active_students = active_students
        self.students_data = students_data
        self.parent_app = parent_app
        self.base_dir = getattr(self.parent_app, "base_dir", os.path.dirname(os.path.abspath(__file__)))
        
        self.student_list = list(self.active_students.keys())
        if len(self.student_list) > 9:
            self.student_list = self.student_list[:9]
            
        self.votes = {s_id: 0 for s_id in self.student_list}
        self.total_votes = 0
        self.cards = {}
        self.is_voting_blocked = False
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('투표: 오늘의 MVP 뽑기')
        self.setFixedSize(1200, 850)
        self.setStyleSheet("background-color: #F8FAFC;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel("🌟 오늘의 MVP 투표 🌟")
        header.setFont(QFont('Malgun Gothic', 25, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2C3E50;")
        layout.addWidget(header)
        
        self.vote_status_lbl = QLabel("현재 누적 투표수: 0표 (익명 투표)")
        self.vote_status_lbl.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        self.vote_status_lbl.setAlignment(Qt.AlignCenter)
        self.vote_status_lbl.setStyleSheet("color: #E67E22; margin-bottom: 20px;")
        layout.addWidget(self.vote_status_lbl)
        
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # 학생 수에 따라 열 개수 결정 (7명 이상일 때 3줄이 되지 않도록 5열로 배치)
        n_students = len(self.student_list)
        if n_students <= 4:
            cols = 2
        elif n_students <= 6:
            cols = 3
        else:
            cols = 5
        
        for idx, s_id in enumerate(self.student_list):
            row = idx // cols
            col = idx % cols
            card = self.create_student_card(s_id, idx + 1)
            grid.addWidget(card, row, col)
            
        layout.addLayout(grid)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("취소")
        cancel_btn.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        cancel_btn.setFixedSize(150, 60)
        cancel_btn.setStyleSheet("QPushButton { background-color: #95A5A6; color: white; border-radius: 10px; }")
        cancel_btn.clicked.connect(self.reject)
        
        finish_btn = QPushButton("🎉 결과 발표 🎉")
        finish_btn.setFont(QFont('Malgun Gothic', 18, QFont.Bold))
        finish_btn.setFixedSize(300, 70)
        finish_btn.setStyleSheet("QPushButton { background-color: #F1C40F; color: #2C3E50; border-radius: 10px; border: 2px solid #E67E22; }")
        finish_btn.clicked.connect(self.finish_voting)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addSpacing(20)
        btn_layout.addWidget(finish_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
    def create_student_card(self, s_id, number):
        card = QFrame()
        card_style = "QFrame { background-color: white; border-radius: 15px; border: 3px solid #BDC3C7; }"
        card.setStyleSheet(card_style)
        
        class ClickableCard(QFrame):
            clicked = pyqtSignal(int)
            def __init__(self, num, parent=None):
                super().__init__(parent)
                self.num = num
            def mousePressEvent(self, event):
                if event.button() == Qt.LeftButton:
                    self.clicked.emit(self.num)
                super().mousePressEvent(event)
                
        card_widget = ClickableCard(number)
        
        # 학생 수에 따라 카드 및 사진 크기 조절 (공간 확보)
        n_students = len(self.student_list)
        if n_students <= 6:
            card_w, card_h = 250, 300
            photo_w, photo_h = 140, 180
            name_font_size = 18
            num_font_size = 24
        else:
            card_w, card_h = 210, 270
            photo_w, photo_h = 120, 150
            name_font_size = 15
            num_font_size = 20

        card_widget.setFixedSize(card_w, card_h)
        card_widget.setCursor(Qt.PointingHandCursor)
        card_widget.setStyleSheet(card_style)
        card_widget.clicked.connect(self.process_vote)
        
        c_layout = QVBoxLayout(card_widget)
        c_layout.setAlignment(Qt.AlignCenter)
        c_layout.setSpacing(5)
        
        s_info = self.students_data.get(s_id, {})
        pic_key = next((k for k in s_info.keys() if '사진' in k), None)
        pic_filename = s_info.get(pic_key, '') if pic_key else ''
        photo_path = os.path.join(self.base_dir, 'photos', pic_filename) if pic_filename else ''
        
        photo = QLabel()
        photo.setFixedSize(photo_w, photo_h)
        photo.setAlignment(Qt.AlignCenter)
        if os.path.exists(photo_path):
            photo.setPixmap(QPixmap(photo_path).scaled(photo_w, photo_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            photo.setText("no pic")
            photo.setStyleSheet("background-color: #EEEEEE; border-radius: 10px;")
            
        name = self.active_students[s_id]['name']
        name_lbl = QLabel(name)
        name_lbl.setFont(QFont('Malgun Gothic', name_font_size, QFont.Bold))
        name_lbl.setStyleSheet("color: #2C3E50; border: none;")
        
        num_lbl = QLabel(f"[{number}]")
        num_lbl.setFont(QFont('Arial', num_font_size, QFont.Bold))
        num_lbl.setStyleSheet("color: #E74C3C; border: none;")
        
        c_layout.addWidget(photo, alignment=Qt.AlignCenter)
        c_layout.addWidget(name_lbl, alignment=Qt.AlignCenter)
        c_layout.addWidget(num_lbl, alignment=Qt.AlignCenter)
        
        self.cards[number] = card_widget
        return card_widget

    def keyPressEvent(self, event):
        key = event.key()
        if Qt.Key_1 <= key <= Qt.Key_9:
            num = key - Qt.Key_0
            self.process_vote(num)
        elif key == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def process_vote(self, number):
        if self.is_voting_blocked:
            return

        if number <= len(self.student_list):
            self.is_voting_blocked = True
            s_id = self.student_list[number - 1]
            self.votes[s_id] += 1
            self.total_votes += 1
            self.vote_status_lbl.setText(f"현재 누적 투표수: {self.total_votes}표 (익명 투표)")
            QApplication.beep()
            
            self.show_vote_success_msg()
            
    def show_vote_success_msg(self):
        msg_box = QDialog(self)
        msg_box.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        msg_box.setAttribute(Qt.WA_TranslucentBackground)
        msg_box.setFixedSize(500, 200)
        
        layout = QVBoxLayout(msg_box)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel("투표하였습니다! 🗳️")
        lbl.setFont(QFont('Malgun Gothic', 30, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("background-color: rgba(44, 62, 80, 0.95); color: #2ECC71; border-radius: 20px; border: 4px solid #F1C40F; padding: 30px;")
        layout.addWidget(lbl)
        
        QTimer.singleShot(2000, lambda: self.close_vote_success_msg(msg_box))
        msg_box.exec_()
        
    def close_vote_success_msg(self, msg_box):
        msg_box.accept()
        self.is_voting_blocked = False

    def finish_voting(self):
        if self.total_votes == 0:
            QMessageBox.warning(self, "안내", "아직 투표가 진행되지 않았습니다!")
            return
            
        # 1. 무작위 선정 (동점자 처리)
        max_votes = max(self.votes.values())
        potential_winners = [s_id for s_id, v in self.votes.items() if v == max_votes]
        winner_id = random.choice(potential_winners)
        vote_count = self.votes[winner_id]
        winner_name = self.active_students[winner_id]['name']
        
        # 2. 결과 저장
        self.parent_app.save_mvp_log(winner_id, winner_name)
        
        # 3. 드라마틱한 애니메이션 다이얼로그 호출
        candidates = []
        for s_id in self.student_list:
            s_info = self.students_data.get(s_id, {})
            pic_key = next((k for k in s_info.keys() if '사진' in k), None)
            pic_filename = s_info.get(pic_key, '') if pic_key else ''
            photo_path = os.path.join(self.base_dir, 'photos', pic_filename) if pic_filename else ''
            candidates.append({'id': s_id, 'name': self.active_students[s_id]['name'], 'photo': photo_path})
            
        self.accept()
        roulette = MVPRouletteDialog(candidates, winner_id, vote_count, self.parent_app)
        roulette.exec_()


class MVPRouletteDialog(QDialog):
    def __init__(self, candidates, winner_id, vote_count, parent_app):
        super().__init__(parent_app)
        self.candidates = candidates
        self.winner_id = winner_id
        self.vote_count = vote_count
        self.parent_app = parent_app
        self.base_dir = getattr(parent_app, "base_dir", os.path.dirname(os.path.abspath(__file__)))
        self.count = 0
        self.total_steps = 30 # 애니메이션 단계 (일정한 속도)
        self.initUI()
        
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.frame = QFrame()
        self.frame.setFixedSize(700, 600)
        self.frame.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 5px solid #F1C40F;
                border-radius: 30px;
            }
        """)
        f_layout = QVBoxLayout(self.frame)
        f_layout.setAlignment(Qt.AlignCenter)
        
        self.msg_lbl = QLabel("누가 MVP가 될까요? 🤔")
        self.msg_lbl.setFont(QFont('Malgun Gothic', 35, QFont.Bold))
        self.msg_lbl.setStyleSheet("color: white; margin-bottom: 20px;")
        self.msg_lbl.setAlignment(Qt.AlignCenter)
        f_layout.addWidget(self.msg_lbl)
        
        self.photo_lbl = QLabel()
        self.photo_lbl.setFixedSize(250, 320)
        self.photo_lbl.setStyleSheet("background-color: white; border-radius: 15px; border: 4px solid white;")
        self.photo_lbl.setAlignment(Qt.AlignCenter)
        f_layout.addWidget(self.photo_lbl, alignment=Qt.AlignCenter)
        
        self.name_lbl = QLabel("")
        self.name_lbl.setFont(QFont('Malgun Gothic', 40, QFont.Bold))
        self.name_lbl.setStyleSheet("color: #F1C40F;")
        self.name_lbl.setAlignment(Qt.AlignCenter)
        f_layout.addWidget(self.name_lbl)
        
        layout.addWidget(self.frame)
        
        # 타이머 설정 (애니메이션)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_shuffle)
        self.current_interval = 50 # 처음 속도
        self.timer.start(self.current_interval)

    def update_shuffle(self):
        self.count += 1
        
        # 무작위 후보 선택 및 표시
        candidate = random.choice(self.candidates)
        if os.path.exists(candidate['photo']):
            self.photo_lbl.setPixmap(QPixmap(candidate['photo']).scaled(250, 320, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            self.photo_lbl.setText("?")
            
        self.name_lbl.setText(candidate['name'])
        QApplication.beep() # 긴장감 비프음
        
        # 단계가 끝나면 정지
        if self.count > self.total_steps:
            self.timer.stop()
            QTimer.singleShot(500, self.show_final_winner)

    def show_final_winner(self):
        winner_info = next(c for c in self.candidates if c['id'] == self.winner_id)
        dlg = MVPCelebrationDialog(self.winner_id, winner_info['name'], winner_info['photo'], self.vote_count, self.parent_app)
        self.accept()
        dlg.exec_()


class MVPCelebrationDialog(QDialog):
    def __init__(self, s_id, s_name, photo_path, vote_count, parent=None):
        super().__init__(parent)
        self.s_id = s_id
        self.s_name = s_name
        self.photo_path = photo_path
        self.vote_count = vote_count
        self.base_dir = getattr(self.parent(), "base_dir", os.path.dirname(os.path.abspath(__file__)))
        self.initUI()
        self.play_sound()
        
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.bg_frame = QFrame()
        self.bg_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 40, 50, 0.95);
                border-radius: 20px;
                border: 4px solid #F1C40F;
            }
        """)
        self.bg_frame.setFixedSize(800, 750)
        
        bg_layout = QVBoxLayout(self.bg_frame)
        bg_layout.setAlignment(Qt.AlignCenter)
        bg_layout.setSpacing(20)
        
        self.title = QLabel("🌟 오늘의 MVP 🌟")
        self.title.setFont(QFont('Malgun Gothic', 45, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("color: #F1C40F;")
        bg_layout.addWidget(self.title)
        
        photo = QLabel()
        photo.setFixedSize(300, 380)
        photo.setAlignment(Qt.AlignCenter)
        photo.setStyleSheet("background-color: white; border: 8px solid #F1C40F; border-radius: 15px;")
        if os.path.exists(self.photo_path):
            photo.setPixmap(QPixmap(self.photo_path).scaled(300, 380, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            photo.setText("사진 없음")
            photo.setFont(QFont('Malgun Gothic', 20))
            photo.setStyleSheet("background-color: #ECEFF1; color: #BDC3C7; border: 8px solid #F1C40F; border-radius: 15px;")
        bg_layout.addWidget(photo, alignment=Qt.AlignCenter)
        
        name_lbl = QLabel(f"{self.s_name} 학생")
        name_lbl.setFont(QFont('Malgun Gothic', 38, QFont.Bold))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet("color: white;")
        bg_layout.addWidget(name_lbl)
        
        msg_lbl = QLabel(f"🎉 총 {self.vote_count}표를 획득하여 MVP로 선정!! 🎉")
        msg_lbl.setFont(QFont('Malgun Gothic', 22, QFont.Bold))
        msg_lbl.setAlignment(Qt.AlignCenter)
        msg_lbl.setStyleSheet("color: #2ECC71;")
        bg_layout.addWidget(msg_lbl)
        
        close_btn = QPushButton("닫기")
        close_btn.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        close_btn.setFixedSize(200, 50)
        close_btn.setStyleSheet("""
            QPushButton { background-color: #E74C3C; color: white; border-radius: 10px; } 
            QPushButton:hover { background-color: #C0392B; }
        """)
        close_btn.clicked.connect(self.accept)
        close_btn.setCursor(Qt.PointingHandCursor)
        bg_layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        layout.addWidget(self.bg_frame)
        
        # 깜빡이 애니메이션 효과 타이머
        self.color_timer = QTimer(self)
        self.colors = ["#F1C40F", "#E74C3C", "#9B59B6", "#3498DB", "#2ECC71"]
        self.color_idx = 0
        self.color_timer.timeout.connect(self.update_color)
        self.color_timer.start(250)
        
        # 서서히 나타나는 페이드인(Fade-in) 효과 (중앙 정렬 유지)
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(1200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.InQuad)
        self.anim.start()

    def play_sound(self):
        self.player = QMediaPlayer(None, QMediaPlayer.LowLatency)
        audio_path = os.path.join(self.base_dir, 'mvp_sound.mp3')
        if os.path.exists(audio_path):
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
            self.player.play()
        else:
            print(f"[{audio_path}] 사운드 파일이 없습니다.")
            
    def update_color(self):
        self.color_idx = (self.color_idx + 1) % len(self.colors)
        self.title.setStyleSheet(f"color: {self.colors[self.color_idx]};")
        
    def closeEvent(self, event):
        if hasattr(self, 'player'):
            self.player.stop()
        super().closeEvent(event)


class PresenterModeSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_mode = None
        self.initUI()
        
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(920, 440)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setAlignment(Qt.AlignCenter)
        
        card = QFrame()
        card.setFixedSize(890, 410)
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
        
        # target theta to align center of winner slice under top needle
        jitter = random.uniform(-0.25, 0.25) * delta
        target_theta = (360.0 - (winner_idx + 0.5 + jitter) * delta) % 360.0
        
        # 5 to 7 full revolutions
        full_turns = 360.0 * random.randint(5, 7)
        self.total_spin_angle = full_turns + target_theta
        self.start_angle = self.current_angle % 360.0
        
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
            self.wheel_widget.update()
            
            # Ensure final winner is selected and shown directly on roulette screen
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
        if not hasattr(self, 'winner') or not self.winner:
            self.winner = random.choice(self.pool)
        self.current_angle = self.total_spin_angle
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
                
            # 2. 가로 다리(Bridge)
            pen_bridge = QPen(QColor("#475569"), 4, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen_bridge)
            for c, lvl in self.dlg.bridges:
                if c < num_cols - 1:
                    y = int(top_y + (lvl / (self.dlg.num_levels + 1)) * ladder_h)
                    painter.drawLine(xs[c], y, xs[c + 1], y)
                    
            # 3. 진행된 경로선(Trace) & 이동 구슬
            if self.dlg.progress > 0.0:
                for k in range(num_cols):
                    color = QColor(self.dlg.colors[k])
                    pen_trace = QPen(color, 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                    painter.setPen(pen_trace)
                    painter.setBrush(Qt.NoBrush)
                    
                    path = self.dlg.paths[k]
                    tot_d = self.dlg.path_lengths[k]
                    target_d = self.dlg.progress * tot_d
                    
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
                            
                    # 빛나는 마커 구슬 (선 끝점에 정확히 일치)
                    painter.setPen(QPen(Qt.white, 3))
                    painter.setBrush(QBrush(color))
                    painter.drawEllipse(last_pt, 9, 9)
                    
            # 4. 상단 학생 정보
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
        except Exception as e:
            print("LadderCanvasWidget paint error:", e)
            
        # 5. 하단 결과 슬롯 카드
        for i in range(num_cols):
            cx = xs[i]
            slot_rect = QRect(cx - 52, bot_y + 18, 104, 52)
            
            if not self.dlg.is_finished:
                painter.setPen(QPen(QColor("#475569"), 2))
                painter.setBrush(QBrush(QColor("#1E293B")))
                painter.drawRoundedRect(slot_rect, 12, 12)
                
                painter.setPen(QColor("#F1C40F"))
                painter.setFont(QFont('Malgun Gothic', 18, QFont.Bold))
                painter.drawText(slot_rect, Qt.AlignCenter, "❓")
            else:
                if i == self.dlg.win_slot:
                    painter.setPen(QPen(QColor("#34D399"), 3))
                    painter.setBrush(QBrush(QColor("#065F46")))
                    painter.drawRoundedRect(slot_rect, 12, 12)
                    
                    painter.setPen(QColor("#FBBF24"))
                    painter.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
                    painter.drawText(slot_rect, Qt.AlignCenter, "🎯 발표자!")
                else:
                    painter.setPen(QPen(QColor("#334155"), 1))
                    painter.setBrush(QBrush(QColor("#0F172A")))
                    painter.drawRoundedRect(slot_rect, 12, 12)
                    
                    painter.setPen(QColor("#94A3B8"))
                    painter.setFont(QFont('Malgun Gothic', 11))
                    painter.drawText(slot_rect, Qt.AlignCenter, "☕ 통과")


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
        
        self.init_ladder_data()
        self.initUI()
        
    def init_ladder_data(self):
        self.num_cols = len(self.pool)
        if self.num_cols <= 1:
            self.winner = self.pool[0] if self.pool else None
            return
            
        self.num_levels = max(9, min(14, self.num_cols * 2))
        
        # 가로 다리 생성
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
                
        # 각 학생 경로 계산
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
            
        # 경로 누적 거리 계산
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
            
        # 당첨 슬롯 지정 및 당첨자 추출
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
        
        # 메인 카드 프레임
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
        
        # 헤더 바
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
        
        # 중앙 사다리 캔버스
        if self.num_cols > 1:
            self.canvas = LadderCanvasWidget(self)
            frame_layout.addWidget(self.canvas, stretch=1)
        else:
            single_box = QLabel(f"후보 학생이 {self.winner['name']} 학생 1명뿐이어서 바로 발표자로 선정됩니다!")
            single_box.setFont(QFont('Malgun Gothic', 22, QFont.Bold))
            single_box.setStyleSheet("color: white; padding: 100px;")
            single_box.setAlignment(Qt.AlignCenter)
            frame_layout.addWidget(single_box, stretch=1)
        
        # 하단 조작 버튼 바
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
        
        # 애니메이션 타이머
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        
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
        self.progress = 0.0
        self.start_btn.setEnabled(False)
        self.start_btn.setText("사다리 타는 중... 🪜")
        self.sub_lbl.setText("과연 사다리를 타고 내려와 발표자가 될 행운의 주인공은 누구일까요?")
        self.sub_lbl.setStyleSheet("color: #94A3B8; font-size: 13px; background: transparent; border: none;")
        self.timer.start(30)
        
    def update_animation(self):
        self.progress += 0.007
        
        # 사다리 타는 동안 긴장감 비프음
        step_idx = int(self.progress * 15)
        if step_idx > self.last_beep_idx:
            self.last_beep_idx = step_idx
            QApplication.beep()
            
        if self.progress >= 1.0:
            self.progress = 1.0
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
        self.progress = 0.0
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


class PresenterCelebrationDialog(QDialog):
    def __init__(self, winner, all_candidates, exclude_ids, mode='ladder', parent_app=None):
        super().__init__(parent_app)
        self.winner = winner
        self.all_candidates = all_candidates
        self.exclude_ids = list(exclude_ids)
        self.exclude_ids.append(winner['id'])
        self.mode = mode
        self.parent_app = parent_app
        self.base_dir = getattr(parent_app, "base_dir", os.path.dirname(os.path.abspath(__file__)))
        self.initUI()
        self.play_sound()
        
        if self.parent_app and hasattr(self.parent_app, 'play_tts'):
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
        
        self.title = QLabel("🎯 오늘의 발표자 당첨! 🎯")
        self.title.setFont(QFont('Malgun Gothic', 42, QFont.Bold))
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
        if self.mode == 'roulette':
            dlg = PresenterRouletteDialog(self.all_candidates, self.parent_app, exclude_ids=self.exclude_ids)
        else:
            dlg = PresenterLadderDialog(self.all_candidates, self.parent_app, exclude_ids=self.exclude_ids)
        dlg.exec_()
        
    def closeEvent(self, event):
        if hasattr(self, 'player'):
            self.player.stop()
        super().closeEvent(event)


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



class MVPStatsDialog(QDialog):
    def __init__(self, mvp_file, log_file, parent=None):
        super().__init__(parent)
        self.mvp_file = mvp_file
        self.log_file = log_file
        self.initUI()
        self.load_data()
        
    def initUI(self):
        self.setWindowTitle('MVP 전체 랭킹 통계')
        self.resize(500, 600)
        self.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel('🏆 누적 MVP 랭킹 및 현황 🏆')
        title.setFont(QFont('Malgun Gothic', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2C3E50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont('Malgun Gothic', 13))
        self.list_widget.setStyleSheet("""
            QListWidget { border: 2px solid #E2E8F0; border-radius: 8px; padding: 5px; }
            QListWidget::item { padding: 10px; margin-bottom: 5px; border-radius: 5px; background-color: #F8FAFC; color: #2C3E50;}
            QListWidget::item:hover { background-color: #EBF5FB; }
        """)
        layout.addWidget(self.list_widget)
        
        close_btn = QPushButton("닫기")
        close_btn.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        close_btn.setFixedSize(120, 40)
        close_btn.setStyleSheet("background-color: #34495E; color: white; border-radius: 8px;")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
    def load_data(self):
        if not os.path.exists(self.mvp_file):
            self.list_widget.addItem("MVP 기록이 아직 없습니다.")
            return
            
        # 0. 학생별 반 정보 매핑 (미리 수행)
        student_to_class = {}
        students_data = {}
        if self.parent() and hasattr(self.parent(), 'students_data'):
            students_data = self.parent().students_data
            # 반 리스트 가져오기
            classes = self.parent().get_class_list() if hasattr(self.parent(), 'get_class_list') else []
            
            for s_id, s_info in students_data.items():
                info_str = " ".join(str(v) for v in s_info.values())
                for c in classes:
                    if c in info_str:
                        student_to_class[s_id] = c
                        break

        # 1. 반별 총 수업 일수(세션) 계산
        # 특정 반의 학생 중 한 명이라도 기록이 있는 날을 그 반의 '수업일'로 간주
        class_sessions = {} # {class_name: set(dates)}
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) >= 4:
                        date = row[0].split(' ')[0]
                        s_id = row[1]
                        c_name = student_to_class.get(s_id)
                        if c_name:
                            if c_name not in class_sessions:
                                class_sessions[c_name] = set()
                            class_sessions[c_name].add(date)

        # 2. 학생별 MVP 수상 횟수 계산
        mvp_counts = Counter()
        names = {}
        with open(self.mvp_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 3:
                    s_id = row[1]
                    name = row[2]
                    mvp_counts[s_id] += 1
                    names[s_id] = name
                    
        # 3. 승률(Win Rate) 계산 및 정렬
        # 승률 = (MVP 수상 횟수 / 해당 학생이 속한 반의 총 수업 일수) * 100
        stats = []
        for s_id, wins in mvp_counts.items():
            c_name = student_to_class.get(s_id)
            total_sessions = len(class_sessions.get(c_name, set()))
            
            # 수업 기록이 전혀 없을 경우(예외 상황) 최소 1로 설정하여 에러 방지
            if total_sessions == 0: total_sessions = wins
            
            win_rate = (wins / total_sessions) * 100
            stats.append({
                's_id': s_id,
                'name': names.get(s_id, '이름없음'),
                'class': c_name or "소속미정",
                'wins': wins,
                'total_sessions': total_sessions,
                'win_rate': win_rate
            })
            
        # 정렬 기준: 승률(내림차순), 수상 횟수(내림차순)
        stats.sort(key=lambda x: (x['win_rate'], x['wins']), reverse=True)
        
        if not stats:
            self.list_widget.addItem("MVP 기록이 아직 없습니다.")
            return
            
        current_rank = 0
        prev_rate = -1.0
        
        for i, s in enumerate(stats):
            if s['win_rate'] != prev_rate:
                current_rank = i + 1
                prev_rate = s['win_rate']
            
            info_text = f" ({s['class']})"
            item_text = f"{current_rank}위. {s['name']}{info_text}"
            
            item = QListWidgetItem(item_text)
            
            if current_rank == 1:
                item.setForeground(QColor("#D4AF37"))
                f = item.font(); f.setBold(True); item.setFont(f)
                item.setText("🥇 " + item_text)
            elif current_rank == 2:
                item.setForeground(QColor("#7F8C8D"))
                f = item.font(); f.setBold(True); item.setFont(f)
                item.setText("🥈 " + item_text)
            elif current_rank == 3:
                item.setForeground(QColor("#CD7F32"))
                f = item.font(); f.setBold(True); item.setFont(f)
                item.setText("🥉 " + item_text)
                
            self.list_widget.addItem(item)

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
            class_val = ""
            for k, v in s.items():
                if '학년' in k or '반' in k or '정보' in k:
                    class_val = str(v).split('\n')[0].strip()
                    break
            if class_val:
                m = re.search(r'(\d+학년\s*\d+반)', class_val)
                if m:
                    class_set.add(m.group(1))
                else:
                    val = re.sub(r'\s*\d+번.*$', '', class_val)
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
        # 만약 기존 members.csv만 있고 students.csv가 없다면 (이전 테스트용 환경 고려)
        members_path = os.path.join(self.base_dir, 'members.csv')
        if not os.path.exists(self.csv_path) and os.path.exists(members_path):
            self.csv_path = members_path
            
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
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)
        
        # ==========================================
        # 1. 왼쪽 패널 (사이드바)
        # ==========================================
        left_panel = QFrame()
        left_panel.setFixedWidth(340)
        left_panel.setStyleSheet("""
            QFrame { background-color: white; border-radius: 20px; }
        """)
        shadow_left = QGraphicsDropShadowEffect()
        shadow_left.setBlurRadius(20)
        shadow_left.setColor(QColor(0, 0, 0, 15))
        shadow_left.setOffset(0, 5)
        left_panel.setGraphicsEffect(shadow_left)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(25, 30, 25, 30)
        left_layout.setSpacing(20)
        
        t_label = QLabel('Smart Attendance')
        t_label.setFont(QFont('Segoe UI', 20, QFont.Bold))
        t_label.setAlignment(Qt.AlignCenter)
        t_label.setStyleSheet("color: #3B82F6; border: none; margin-bottom: 20px;")
        
        # class_label 제거됨

        
        # Hidden QComboBox for backend compatibility
        self.class_combo = QComboBox(self)
        self.class_combo.hide()
        sorted_classes = self.get_class_list()
        self.class_combo.addItems(["수업명 입력/선택"] + sorted_classes)
        
        # Sleek class selection button replacing the combo box and change button
        self.class_btn = QPushButton('🏫 수업반을 선택하세요')
        self.class_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.class_btn.setFixedHeight(55)
        self.class_btn.setCursor(Qt.PointingHandCursor)
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
        self.class_btn.clicked.connect(self.show_start_class_selector)
        
        # list_title 제거됨

        
        self.access_list = QListWidget()
        self.access_list.setFont(QFont('Malgun Gothic', 14, QFont.Bold))
        self.access_list.setSpacing(5)
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
        self.end_class_btn.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        self.end_class_btn.setFixedHeight(55)
        self.end_class_btn.setCursor(Qt.PointingHandCursor)
        self.end_class_btn.setStyleSheet("""
            QPushButton { background-color: #EF4444; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #DC2626; }
        """)
        self.end_class_btn.clicked.connect(self.end_all_class)
        
        left_layout.addWidget(t_label)
        # left_layout.addWidget(class_label) # 제거됨

        
        left_layout.addWidget(self.class_btn)
        # left_layout.addWidget(list_title) # 제거됨
        left_layout.addWidget(self.access_list)
        left_layout.addWidget(self.end_class_btn)
        
        # ==========================================
        # 2. 우측 메인 영역
        # ==========================================
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 0, 0, 0)
        right_layout.setSpacing(25)
        
        # 상단 정보표시 표시바 (시계, 교시)
        header_bar = QHBoxLayout()
        self.period_label = QLabel()
        self.period_label.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        self.period_label.setStyleSheet("color: #059669; background-color: #D1FAE5; padding: 10px 25px; border-radius: 15px;")
        self.period_label.hide() 
        
        header_bar.addWidget(self.period_label)
        header_bar.addStretch()
        
        self.time_label = QLabel()
        self.time_label.setFont(QFont('Malgun Gothic', 14, QFont.Bold))
        self.time_label.setStyleSheet("color: #64748B; background-color: white; padding: 10px 25px; border-radius: 15px;")
        
        self.minimize_btn = QPushButton('➖ 최소화')
        self.minimize_btn.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        self.minimize_btn.setFixedHeight(45)
        self.minimize_btn.setCursor(Qt.PointingHandCursor)
        self.minimize_btn.setStyleSheet("""
            QPushButton { 
                background-color: #E0F2FE; 
                color: #0284C7; 
                border-radius: 12px; 
                padding: 0 20px;
                margin-left: 10px;
                border: none;
            }
            QPushButton:hover { 
                background-color: #BAE6FD; 
            }
        """)
        self.minimize_btn.clicked.connect(self.minimize_app)
        
        self.exit_btn = QPushButton('✖ 종료 (ESC)')
        self.exit_btn.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
        self.exit_btn.setFixedHeight(45)
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.setStyleSheet("""
            QPushButton { 
                background-color: #FEE2E2; 
                color: #DC2626; 
                border-radius: 12px; 
                padding: 0 20px;
                margin-left: 10px;
                border: none;
            }
            QPushButton:hover { 
                background-color: #FECACA; 
            }
        """)
        self.exit_btn.clicked.connect(self.close)

        header_bar.addWidget(self.time_label)
        header_bar.addWidget(self.minimize_btn)
        header_bar.addWidget(self.exit_btn)

        
        self.update_time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        # 중앙 메인 정보 카드
        center_card = QFrame()
        center_card.setStyleSheet("QFrame { background-color: white; border-radius: 20px; border: 1px solid #E2E8F0; }")
        shadow_center = QGraphicsDropShadowEffect()
        shadow_center.setBlurRadius(30)
        shadow_center.setColor(QColor(0, 0, 0, 15))
        shadow_center.setOffset(0, 10)
        center_card.setGraphicsEffect(shadow_center)
        
        cc_layout = QVBoxLayout(center_card)
        cc_layout.setContentsMargins(30, 30, 30, 30) # 여백 감소 (50 -> 30)
        cc_layout.setSpacing(10) # 간격 감소 (20 -> 10)
        
        # 상단 정보 영역 (이모티콘이 나타나도 밀리지 않게 공간을 미리 확보)
        self.top_info_container = QWidget()
        top_hbox = QHBoxLayout(self.top_info_container)
        top_hbox.setContentsMargins(0, 0, 0, 0)
        top_hbox.setSpacing(15)
        
        self.status = QLabel('학생 번호를 누르세요')
        self.status.setFont(QFont('Malgun Gothic', 26, QFont.Bold))
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: #0F172A; border: none;")
        
        # 큰 감정 아이콘 표시용 레이블
        self.emotion_icon_label = QLabel()
        self.emotion_icon_label.setFixedSize(120, 120)
        self.emotion_icon_label.setAlignment(Qt.AlignCenter)
        self.emotion_icon_label.setStyleSheet("border: none; background: transparent;")
        self.emotion_icon_label.hide()
        
        top_hbox.addStretch()
        top_hbox.addWidget(self.status, alignment=Qt.AlignCenter)
        top_hbox.addWidget(self.emotion_icon_label, alignment=Qt.AlignCenter)
        top_hbox.addStretch()
        
        cc_layout.addWidget(self.top_info_container)
        cc_layout.addStretch()
        
        # 프로필 영역
        profile_layout = QHBoxLayout()
        profile_layout.setSpacing(30)
        
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(220, 280)
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet("background-color: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 20px; color: #94A3B8; font-size: 18px;")
        
        info_vbox = QVBoxLayout()
        info_vbox.setSpacing(15)
        
        self.detail = QTextEdit('학생 정보를 기다리는 중입니다')
        self.detail.setReadOnly(True)
        self.detail.setFont(QFont('Malgun Gothic', 16))
        self.detail.setStyleSheet("color: #64748B; background: transparent; border: none;")
        self.detail.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.history = QLabel('')
        self.history.setFont(QFont('Malgun Gothic', 15))
        self.history.setStyleSheet("color: #475569; border: none; padding-top: 15px;")
        self.history.hide()
        
        info_vbox.addWidget(self.detail, stretch=1)
        info_vbox.addWidget(self.history)
        
        profile_layout.addWidget(self.photo_label)
        profile_layout.addLayout(info_vbox, stretch=1)
        
        cc_layout.addLayout(profile_layout, stretch=1)
        cc_layout.addStretch()
        
        # 하단 바코드 입력창
        id_input_layout = QVBoxLayout()
        lbl = QLabel('STUDENT ID ENTRY')
        lbl.setFont(QFont('Segoe UI', 13, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #94A3B8; border: none;")
        
        self.id_input = QLineEdit()
        self.id_input.setEchoMode(QLineEdit.Password)
        self.id_input.setFont(QFont('Arial', 45, QFont.Bold))
        self.id_input.setMaxLength(6)
        self.id_input.setAlignment(Qt.AlignCenter)
        self.id_input.setFixedSize(450, 90) # 크기 확대
        self.id_input.setStyleSheet("""
            QLineEdit { 
                background-color: white; 
                border: 3px solid #94A3B8; 
                border-radius: 20px; 
                color: #0F172A; 
            }
            QLineEdit:focus { 
                border: 3px solid #3B82F6; 
                background-color: #EFF6FF; 
            }
        """)
        self.id_input.returnPressed.connect(self.process_enter)
        
        self.clear_btn = QPushButton("지우기") # "취소"보다 명확한 "지우기"로 변경 제안 (또는 사용자 요청대로 "취소")
        self.clear_btn.setText("취소") # 사용자 요청대로 "취소" 유지
        self.clear_btn.setFont(QFont('Malgun Gothic', 16, QFont.Bold))
        self.clear_btn.setFixedSize(100, 90)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet("""
            QPushButton { 
                background-color: #F1F5F9; 
                color: #475569; 
                border-radius: 20px; 
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
        input_hbox.addSpacing(15)
        input_hbox.addWidget(self.clear_btn)

        id_input_layout.addLayout(input_hbox) # lbl 추가 부분 제거
        cc_layout.addLayout(id_input_layout)
        
        # 하단 액션 바 (6개 버튼 균등 배치)
        action_bar = QHBoxLayout()
        action_bar.setSpacing(12)
        
        self.prev_log_btn = QPushButton('📋 지난 수업 기록')
        self.prev_log_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.prev_log_btn.setFixedHeight(65)
        self.prev_log_btn.setMinimumWidth(120)
        self.prev_log_btn.setCursor(Qt.PointingHandCursor)
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
        self.prev_log_btn.clicked.connect(self.show_class_log_history)
        
        self.write_log_btn = QPushButton('📝 일지 작성')
        self.write_log_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.write_log_btn.setFixedHeight(65)
        self.write_log_btn.setMinimumWidth(120)
        self.write_log_btn.setCursor(Qt.PointingHandCursor)
        self.write_log_btn.setStyleSheet("""
            QPushButton { background-color: #8B5CF6; color: white; border-radius: 15px; border: none; }
            QPushButton:hover { background-color: #7C3AED; }
        """)
        self.write_log_btn.clicked.connect(self.open_log_dialog)
        
        self.presenter_btn = QPushButton('🎤 발표자 뽑기')
        self.presenter_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.presenter_btn.setFixedHeight(65)
        self.presenter_btn.setMinimumWidth(120)
        self.presenter_btn.setCursor(Qt.PointingHandCursor)
        self.presenter_btn.setStyleSheet("""
            QPushButton { background-color: #10B981; color: white; border-radius: 15px; border: none; }
            QPushButton:hover { background-color: #059669; }
        """)
        self.presenter_btn.clicked.connect(self.open_presenter_dialog)
        
        self.mvp_btn = QPushButton('🌟 오늘의 MVP')
        self.mvp_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.mvp_btn.setFixedHeight(65)
        self.mvp_btn.setMinimumWidth(120)
        self.mvp_btn.setCursor(Qt.PointingHandCursor)
        self.mvp_btn.setStyleSheet("""
            QPushButton { background-color: #F59E0B; color: white; border-radius: 15px; border: none; }
            QPushButton:hover { background-color: #D97706; }
        """)
        self.mvp_btn.clicked.connect(self.open_mvp_dialog)
        
        self.overall_btn = QPushButton('🗓️ 출석 현황')
        self.overall_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.overall_btn.setFixedHeight(65)
        self.overall_btn.setMinimumWidth(120)
        self.overall_btn.setCursor(Qt.PointingHandCursor)
        self.overall_btn.setStyleSheet("""
            QPushButton { background-color: #3B82F6; color: white; border-radius: 15px; border: none; }
            QPushButton:hover { background-color: #2563EB; }
        """)
        self.overall_btn.clicked.connect(self.show_overall_attendance)
        
        self.mvp_stats_btn = QPushButton('📊 전체 통계')
        self.mvp_stats_btn.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        self.mvp_stats_btn.setFixedHeight(65)
        self.mvp_stats_btn.setMinimumWidth(120)
        self.mvp_stats_btn.setCursor(Qt.PointingHandCursor)
        self.mvp_stats_btn.setStyleSheet("""
            QPushButton { background-color: white; color: #334155; border-radius: 15px; border: 2px solid #E2E8F0; }
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

        # 룰렛 vs 사다리 vs 제비뽑기 모드 선택
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
        action_change = reply_menu.addAction("🔄 출결 상태 변경")
        action_cancel = reply_menu.addAction("❌ 출결 기록 취소")
        
        pos = QCursor.pos()
        selected = reply_menu.exec_(pos)
        
        if selected == action_change:
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
        
        self.current_id = s_id
        s = self.students_data.get(s_id, {})
        
        # 키 호환성 지원 (학생정보, 상세정보, 특이사항, 학년반 등)
        info_key = next((k for k in s.keys() if '정보' in k or '상세' in k or '특이' in k or '학년' in k or '반' in k), None)
        details = s.get(info_key, '') if info_key else ''
        
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
            
        detail_text = f"학번: {s_id}\n이름: {s_name}\n상태: {status_type}"
        if details:
            detail_text += f"\n학생 정보: {details}"
        self.detail.setText(detail_text)
        self.detail.setStyleSheet("color: #2C3E50; font-size: 16pt; font-weight: bold; background: transparent; border: none;")
        
        # 학생 사진 출력
        pic_key = next((k for k in s.keys() if '사진' in k), None)
        pic_filename = s.get(pic_key, '') if pic_key else ''
        p = os.path.join(self.base_dir, 'photos', pic_filename) if pic_filename else ''
        if p and os.path.exists(p) and os.path.isfile(p):
            self.photo_label.setPixmap(QPixmap(p).scaled(self.photo_label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.photo_label.setStyleSheet("border-radius: 20px; border: 2px solid #E2E8F0;")
        else:
            self.photo_label.clear()
            self.photo_label.setText('사진 없음')
            self.photo_label.setStyleSheet("background-color: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 20px; color: #94A3B8; font-size: 18px;")

        # 최근 출결 기록 출력
        h = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8-sig') as f:
                r = csv.reader(f)
                for row in r:
                    if len(row) >= 4 and row[1] == s_id and row[3] not in ('하교', '취소'):
                        h.append(row[0] + " [" + row[3] + "]")
        htxt = "🕒 최근 출결 기록\n" + "\n".join([f"- {t}" for t in reversed(h[-5:])])
        self.history.setStyleSheet("background-color: #F8F9FA; padding: 10px; border-radius:10px;")
        self.history.setText(htxt.strip())
        self.history.show()

        self.photo_label.show()
        self.status.show()

        # 학생 정보 표시 5초 뒤 원래(수업) 화면으로 복귀
        self.revert_timer.start(5000)

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
        
        if s_id in self.active_students:
            self.status.setText(f"{name} 학생")
            self.status.setStyleSheet("color: #2980B9;")
            self.play_tts(f"{name} 학생은 이미 출석 확인되었습니다.")
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
        
        self.detail.setText(f"학생 정보:\n{details}")
        self.detail.setStyleSheet("color: #2C3E50; font-size: 16pt; font-weight: bold; background: transparent; border: none;")
        
        h = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8-sig') as f:
                r = csv.reader(f)
                for row in r:
                    if len(row) >= 4 and row[1] == s_id and row[3] not in ('하교', '취소'): h.append(row[0] + " [" + row[3] + "]")
        htxt = "🕒 최근 출결 기록\n" + "\n".join([f"- {t}" for t in reversed(h[-5:])])
        self.history.setStyleSheet("background-color: #F8F9FA; padding: 10px; border-radius:10px;")
        self.history.setText(htxt.strip())
        self.history.show()

        pic_key = next((k for k in s.keys() if '사진' in k), None)
        pic_filename = s.get(pic_key, '') if pic_key else ''
        p = os.path.join(self.base_dir, 'photos', pic_filename) if pic_filename else ''
        if p and os.path.exists(p) and os.path.isfile(p):
            self.photo_label.setPixmap(QPixmap(p).scaled(self.photo_label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            self.photo_label.clear()
            self.photo_label.setText('사진 없음')
            self.photo_label.setStyleSheet("background-color: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 20px; color: #94A3B8; font-size: 18px;")

        # 학생증 정보 표시 5초 뒤 원래(수업) 화면으로 복귀
        self.revert_timer.start(5000)

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
                
                # 줄 단위 파싱 및 카드형 항목 렌더링
                raw_lines = content.split('\n')
                items_html = ""
                for l in raw_lines:
                    text_l = l.strip()
                    if not text_l:
                        items_html += '<div style="height: 10px;"></div>'
                        continue
                    items_html += f"""
                    <div style="margin-bottom: 12px; padding: 12px 18px; background-color: #F8FAFC; border-left: 6px solid #3B82F6; border-radius: 8px;">
                        <span style="font-size: 21pt; font-weight: bold; color: #1E293B;">{html.escape(text_l)}</span>
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
                <div style="font-family: 'Malgun Gothic', sans-serif; text-align: center; padding-top: 50px;">
                    <div style="font-size: 38pt; margin-bottom: 15px;">📝</div>
                    <div style="font-size: 22pt; font-weight: bold; color: #475569; margin-bottom: 12px;">
                        [{html.escape(class_name)}] 등록된 수업 일지가 없습니다.
                    </div>
                    <div style="font-size: 16pt; color: #94A3B8;">
                        하단의 <b>[📝 일지 작성]</b> 버튼을 눌러 지난 수업 내용이나 오늘 진도를 기록해 보세요.
                    </div>
                </div>
                """
                self.detail.setHtml(empty_html)
                self.detail.setStyleSheet("""
                    QTextEdit {
                        background-color: #F8FAFC;
                        border: 2px dashed #CBD5E1;
                        border-radius: 20px;
                        padding: 30px;
                    }
                """)
                
            self.history.hide()
            self.photo_label.hide()
            if hasattr(self, 'emotion_icon_label'):
                self.emotion_icon_label.clear()
                self.emotion_icon_label.hide()
        else:
            self.reset_screen()

if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    ex = StudentAttendanceApp()
    sys.exit(app.exec_())
