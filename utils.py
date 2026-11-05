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

def resolve_image_paths(html_content, base_dir):
    """
    HTML 내의 <img src="..."> 경로가 과거 절대 경로이거나 상대 경로일 경우,
    현재 실행 디렉토리의 log_images 폴더를 기준으로 올바른 로컬 URL(file:///)로 자동 변환합니다.
    """
    if not html_content or '<img' not in html_content:
        return html_content

    log_img_dir = os.path.join(base_dir, 'log_images')

    def replace_src(match):
        orig_src = match.group(1)
        # 이미 유효한 file:/// URL이거나 파일이 직접 존재하는지 확인
        cleaned_path = orig_src.replace('file:///', '')
        if os.path.exists(cleaned_path):
            abs_path = os.path.abspath(cleaned_path).replace('\\', '/')
            return f'src="file:///{abs_path}"'

        # 파일명만 추출하여 현재 log_images 폴더에서 탐색
        filename = os.path.basename(orig_src.replace('\\', '/'))
        candidate_path = os.path.join(log_img_dir, filename)
        if os.path.exists(candidate_path):
            abs_path = os.path.abspath(candidate_path).replace('\\', '/')
            return f'src="file:///{abs_path}"'

        # 그대로 유지
        return f'src="{orig_src}"'

    return re.sub(r'src=["\']([^"\']+)["\']', replace_src, html_content)

def relativize_image_paths(html_content, base_dir):
    """
    HTML 저장 시 절대 경로를 'log_images/파일명' 상대 경로로 정규화하여
    폴더 위치나 드라이브가 바뀌어도 일지가 손상되지 않도록 합니다.
    """
    if not html_content or '<img' not in html_content:
        return html_content

    def replace_to_relative(match):
        orig_src = match.group(1)
        filename = os.path.basename(orig_src.replace('\\', '/').replace('file:///', ''))
        return f'src="log_images/{filename}"'

    return re.sub(r'src=["\']([^"\']+)["\']', replace_to_relative, html_content)

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

