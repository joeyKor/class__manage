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

from utils import resolve_image_paths, relativize_image_paths

class RichTextEdit(QTextEdit):
    def __init__(self, base_dir, parent=None):
        super().__init__(parent)
        self.base_dir = base_dir
        self.setAcceptRichText(True)
        self.setPlaceholderText("오늘의 수업 내용, 활동 사진, 학생 피드백 등을 자유롭게 기록하세요...\n(💡 캡처 도구로 캡처한 이미지를 Ctrl+V로 바로 붙여넣거나, 사진 파일을 드래그하여 넣을 수 있습니다)")

    def canInsertFromMimeData(self, source):
        if source.hasImage() or source.hasUrls():
            return True
        return super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        if source.hasImage():
            image = source.imageData()
            if isinstance(image, QImage) and not image.isNull():
                self.insert_qimage(image)
                return
            elif isinstance(image, QPixmap) and not image.isNull():
                self.insert_qimage(image.toImage())
                return
        elif source.hasUrls():
            for url in source.urls():
                local_path = url.toLocalFile()
                if local_path and local_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                    img = QImage(local_path)
                    if not img.isNull():
                        self.insert_qimage(img, orig_ext=os.path.splitext(local_path)[1])
                        return
        super().insertFromMimeData(source)

    def insert_qimage(self, image, orig_ext=".png"):
        img_dir = os.path.join(self.base_dir, 'log_images')
        os.makedirs(img_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        ext = orig_ext if orig_ext.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.webp'] else '.png'
        filename = f"log_img_{timestamp}{ext}"
        abs_saved_path = os.path.abspath(os.path.join(img_dir, filename)).replace('\\', '/')
        
        fmt = "PNG" if ext == ".png" else "JPEG"
        image.save(abs_saved_path, fmt)

        disp_width = min(image.width(), 680)
        cursor = self.textCursor()
        # 에디터 내부 실시간 표시용으로는 file:/// 절대 URL 사용
        cursor.insertHtml(f'<p><img src="file:///{abs_saved_path}" width="{disp_width}" style="max-width:100%; border-radius:8px; margin:6px 0;"></p><p></p>')
        self.ensureCursorVisible()

    def insert_image_from_file(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return
        img = QImage(file_path)
        if not img.isNull():
            ext = os.path.splitext(file_path)[1]
            self.insert_qimage(img, orig_ext=ext)

class LogWriteDialog(QDialog):
    def __init__(self, class_name, parent=None, initial_content=""):
        if isinstance(parent, str):
            actual_content = parent
            actual_parent = initial_content if isinstance(initial_content, QWidget) else None
        else:
            actual_parent = parent if isinstance(parent, QWidget) else None
            actual_content = initial_content if isinstance(initial_content, str) else ""

        super().__init__(actual_parent)
        self.class_name = class_name
        self.initial_content = actual_content
        self.result_text = ""
        self.base_dir = getattr(actual_parent, "base_dir", os.path.dirname(os.path.abspath(__file__)))
        self.current_text_color = QColor("#1E293B")
        self.initUI()
        
    def initUI(self):
        is_edit_mode = bool(self.initial_content.strip())
        self.setWindowTitle(f'{self.class_name} 수업 일지 {"수정" if is_edit_mode else "작성"}')
        self.resize(850, 720)
        self.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        title_icon = QLabel("📝")
        title_icon.setFont(QFont('Segoe UI Emoji', 18))
        header_layout.addWidget(title_icon)
        
        title = QLabel(f'[{self.class_name}] 오늘 수업 기록 {"수정" if is_edit_mode else "작성"}')
        title.setFont(QFont('Malgun Gothic', 15, QFont.Bold))
        title.setStyleSheet("color: #1E293B;")
        header_layout.addWidget(title)
        
        date_badge = QLabel(datetime.now().strftime('%Y년 %m월 %d일'))
        date_badge.setFont(QFont('Malgun Gothic', 10, QFont.Bold))
        date_badge.setStyleSheet("color: #3B82F6; background-color: #EFF6FF; border: 1px solid #DBEAFE; border-radius: 6px; padding: 4px 10px;")
        header_layout.addWidget(date_badge, alignment=Qt.AlignRight)
        layout.addLayout(header_layout)
        
        # Toolbar Container
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(6, 6, 6, 6)
        toolbar_layout.setSpacing(6)
        
        btn_style = """
            QPushButton {
                background-color: #F1F5F9;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 5px;
                font-family: 'Malgun Gothic';
                font-size: 12px;
                font-weight: bold;
                padding: 4px 8px;
                min-height: 26px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
                border-color: #94A3B8;
            }
            QPushButton:checked {
                background-color: #3B82F6;
                color: white;
                border-color: #2563EB;
            }
        """
        
        # Bold, Italic, Underline, Strikeout
        self.btn_bold = QPushButton("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setFixedWidth(32)
        self.btn_bold.setFont(QFont('Arial', 12, QFont.Bold))
        self.btn_bold.setStyleSheet(btn_style)
        self.btn_bold.setToolTip("굵게 (Ctrl+B)")
        self.btn_bold.clicked.connect(self.toggle_bold)
        toolbar_layout.addWidget(self.btn_bold)
        
        self.btn_italic = QPushButton("I")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setFixedWidth(32)
        self.btn_italic.setFont(QFont('Arial', 12, QFont.Normal, True))
        self.btn_italic.setStyleSheet(btn_style)
        self.btn_italic.setToolTip("기울임 (Ctrl+I)")
        self.btn_italic.clicked.connect(self.toggle_italic)
        toolbar_layout.addWidget(self.btn_italic)
        
        self.btn_underline = QPushButton("U")
        self.btn_underline.setCheckable(True)
        self.btn_underline.setFixedWidth(32)
        f_u = QFont('Arial', 11)
        f_u.setUnderline(True)
        self.btn_underline.setFont(f_u)
        self.btn_underline.setStyleSheet(btn_style)
        self.btn_underline.setToolTip("밑줄 (Ctrl+U)")
        self.btn_underline.clicked.connect(self.toggle_underline)
        toolbar_layout.addWidget(self.btn_underline)
        
        self.btn_strike = QPushButton("S")
        self.btn_strike.setCheckable(True)
        self.btn_strike.setFixedWidth(32)
        f_s = QFont('Arial', 11)
        f_s.setStrikeOut(True)
        self.btn_strike.setFont(f_s)
        self.btn_strike.setStyleSheet(btn_style)
        self.btn_strike.setToolTip("취소선")
        self.btn_strike.clicked.connect(self.toggle_strike)
        toolbar_layout.addWidget(self.btn_strike)
        
        # Separator line
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setStyleSheet("color: #E2E8F0;")
        toolbar_layout.addWidget(sep1)
        
        # Font size combo
        self.size_combo = QComboBox()
        self.size_combo.addItems(["10pt", "12pt", "13pt", "15pt", "18pt", "22pt", "26pt"])
        self.size_combo.setCurrentText("13pt")
        self.size_combo.setFixedHeight(30)
        self.size_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #CBD5E1;
                border-radius: 5px;
                padding: 2px 8px;
                background-color: #F8FAFC;
                font-family: 'Malgun Gothic';
                font-size: 11px;
                font-weight: bold;
                color: #334155;
            }
        """)
        self.size_combo.currentTextChanged.connect(self.change_font_size)
        toolbar_layout.addWidget(self.size_combo)
        
        # Color picker button
        self.btn_color = QPushButton("🎨 글자색")
        self.btn_color.setStyleSheet(btn_style)
        self.btn_color.setToolTip("글자 색상 선택")
        self.btn_color.clicked.connect(self.choose_text_color)
        toolbar_layout.addWidget(self.btn_color)
        
        # Separator line
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet("color: #E2E8F0;")
        toolbar_layout.addWidget(sep2)
        
        # Alignment buttons
        self.btn_align_left = QPushButton("좌측")
        self.btn_align_left.setStyleSheet(btn_style)
        self.btn_align_left.clicked.connect(lambda: self.text_edit.setAlignment(Qt.AlignLeft))
        toolbar_layout.addWidget(self.btn_align_left)
        
        self.btn_align_center = QPushButton("중앙")
        self.btn_align_center.setStyleSheet(btn_style)
        self.btn_align_center.clicked.connect(lambda: self.text_edit.setAlignment(Qt.AlignCenter))
        toolbar_layout.addWidget(self.btn_align_center)
        
        self.btn_align_right = QPushButton("우측")
        self.btn_align_right.setStyleSheet(btn_style)
        self.btn_align_right.clicked.connect(lambda: self.text_edit.setAlignment(Qt.AlignRight))
        toolbar_layout.addWidget(self.btn_align_right)
        
        # List & Divider
        self.btn_bullet = QPushButton("• 목록")
        self.btn_bullet.setStyleSheet(btn_style)
        self.btn_bullet.setToolTip("글머리 기호 목록 삽입")
        self.btn_bullet.clicked.connect(self.insert_bullet_list)
        toolbar_layout.addWidget(self.btn_bullet)
        
        self.btn_hr = QPushButton("― 선")
        self.btn_hr.setStyleSheet(btn_style)
        self.btn_hr.setToolTip("구분선 삽입")
        self.btn_hr.clicked.connect(self.insert_hr)
        toolbar_layout.addWidget(self.btn_hr)
        
        toolbar_layout.addStretch()
        
        # Image Insertion Button
        self.btn_image = QPushButton("🖼️ 이미지 첨부")
        self.btn_image.setFont(QFont('Malgun Gothic', 11, QFont.Bold))
        self.btn_image.setFixedHeight(30)
        self.btn_image.setCursor(Qt.PointingHandCursor)
        self.btn_image.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        self.btn_image.setToolTip("이미지 파일 추가 (캡처 후 Ctrl+V로 붙여넣기도 가능)")
        self.btn_image.clicked.connect(self.choose_image)
        toolbar_layout.addWidget(self.btn_image)
        
        layout.addWidget(toolbar_frame)
        
        # Text Editor
        self.text_edit = RichTextEdit(self.base_dir)
        self.text_edit.setFont(QFont('Malgun Gothic', 13))
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1.5px solid #CBD5E1;
                border-radius: 10px;
                padding: 14px;
                font-size: 13pt;
                color: #1E293B;
                line-height: 1.6;
            }
            QTextEdit:focus {
                border: 2px solid #3B82F6;
            }
        """)
        self.text_edit.cursorPositionChanged.connect(self.on_cursor_position_changed)
        layout.addWidget(self.text_edit)
        
        # Load initial content if provided
        if self.initial_content:
            raw = self.initial_content.strip()
            if "<html" in raw or "<p" in raw or "<div" in raw or "<img" in raw or "<br" in raw:
                # 과거/상대 경로 이미지를 현재 환경에 맞춰 올바르게 로드
                resolved = resolve_image_paths(raw, self.base_dir)
                self.text_edit.setHtml(resolved)
            else:
                self.text_edit.setPlainText(raw)
                
        # Status / Guide Label
        guide_label = QLabel("💡 TIP: 캡처 도구로 복사한 이미지를 <b>Ctrl+V</b>로 바로 붙여넣거나 사진 파일을 에디터로 드래그할 수 있습니다.")
        guide_label.setFont(QFont('Malgun Gothic', 9))
        guide_label.setStyleSheet("color: #64748B; padding-left: 4px;")
        layout.addWidget(guide_label)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton('취소')
        save_btn = QPushButton('💾 일지 저장' if not is_edit_mode else '💾 변경사항 저장')
        for btn in (cancel_btn, save_btn):
            btn.setFont(QFont('Malgun Gothic', 12, QFont.Bold))
            btn.setFixedHeight(48)
            btn.setCursor(Qt.PointingHandCursor)
        
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0;
                color: #475569;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #CBD5E1;
            }
        """)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.save)
        
        btn_layout.addWidget(cancel_btn, 1)
        btn_layout.addWidget(save_btn, 2)
        layout.addLayout(btn_layout)
        
    def toggle_bold(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold if self.btn_bold.isChecked() else QFont.Normal)
        self.text_edit.mergeCurrentCharFormat(fmt)
        
    def toggle_italic(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.btn_italic.isChecked())
        self.text_edit.mergeCurrentCharFormat(fmt)
        
    def toggle_underline(self):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.btn_underline.isChecked())
        self.text_edit.mergeCurrentCharFormat(fmt)
        
    def toggle_strike(self):
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(self.btn_strike.isChecked())
        self.text_edit.mergeCurrentCharFormat(fmt)
        
    def change_font_size(self, size_str):
        try:
            pt = int(size_str.replace('pt', '').strip())
            fmt = QTextCharFormat()
            fmt.setFontPointSize(pt)
            self.text_edit.mergeCurrentCharFormat(fmt)
        except Exception:
            pass
            
    def choose_text_color(self):
        color = QColorDialog.getColor(self.current_text_color, self, "글자 색상 선택")
        if color.isValid():
            self.current_text_color = color
            fmt = QTextCharFormat()
            fmt.setForeground(QBrush(color))
            self.text_edit.mergeCurrentCharFormat(fmt)
            self.btn_color.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color.name()};
                    color: {'white' if color.lightness() < 128 else 'black'};
                    border: 1px solid #CBD5E1;
                    border-radius: 5px;
                    font-family: 'Malgun Gothic';
                    font-size: 12px;
                    font-weight: bold;
                    padding: 4px 8px;
                    min-height: 26px;
                }}
            """)
            
    def insert_bullet_list(self):
        cursor = self.text_edit.textCursor()
        cursor.insertList(QTextListFormat.ListDisc)
        
    def insert_hr(self):
        cursor = self.text_edit.textCursor()
        cursor.insertHtml('<hr style="border: 0; height: 1px; background: #CBD5E1; margin: 10px 0;"><p></p>')
        
    def choose_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "일지 첨부 이미지 선택", "", "이미지 파일 (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;모든 파일 (*.*)"
        )
        if file_path:
            self.text_edit.insert_image_from_file(file_path)
            
    def on_cursor_position_changed(self):
        fmt = self.text_edit.currentCharFormat()
        self.btn_bold.blockSignals(True)
        self.btn_bold.setChecked(fmt.fontWeight() == QFont.Bold)
        self.btn_bold.blockSignals(False)
        
        self.btn_italic.blockSignals(True)
        self.btn_italic.setChecked(fmt.fontItalic())
        self.btn_italic.blockSignals(False)
        
        self.btn_underline.blockSignals(True)
        self.btn_underline.setChecked(fmt.fontUnderline())
        self.btn_underline.blockSignals(False)
        
        self.btn_strike.blockSignals(True)
        self.btn_strike.setChecked(fmt.fontStrikeOut())
        self.btn_strike.blockSignals(False)
        
        pt = int(fmt.fontPointSize())
        if pt > 0:
            target_str = f"{pt}pt"
            idx = self.size_combo.findText(target_str)
            if idx >= 0 and self.size_combo.currentIndex() != idx:
                self.size_combo.blockSignals(True)
                self.size_combo.setCurrentIndex(idx)
                self.size_combo.blockSignals(False)
                
    def save(self):
        raw_text = self.text_edit.toPlainText().strip()
        html_text = self.text_edit.toHtml()
        if not raw_text and '<img' not in html_text:
            QMessageBox.warning(self, '경고', '수업 내용 또는 이미지를 입력하세요.')
            return
        # 저장 시 경로를 상대 경로('log_images/파일명')로 변환하여 저장
        self.result_text = relativize_image_paths(html_text, self.base_dir)
        self.accept()


class ImageViewerDialog(QDialog):
    """
    수업 일지 및 스크린샷 이미지를 원본 해상도로 선명하게 볼 수 있는 고화질 전용 뷰어 모달
    """
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path.replace('file:///', '')
        self.orig_pixmap = QPixmap(self.image_path)
        self.scale_factor = 1.0
        self.is_dragging = False
        self.drag_start = QPoint()
        self.drag_start_h = 0
        self.drag_start_v = 0
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("🖼️ 수업 이미지 원본 고해상도 뷰어")
        self.resize(1180, 840)
        self.setStyleSheet("background-color: #0F172A;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)
        
        # 상단 툴바
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        
        title_icon = QLabel("🖼️")
        title_icon.setFont(QFont('Segoe UI Emoji', 14))
        top_bar.addWidget(title_icon)
        
        title_lbl = QLabel("수업 사진 원본 뷰어")
        title_lbl.setFont(QFont('Malgun Gothic', 13, QFont.Bold))
        title_lbl.setStyleSheet("color: white;")
        top_bar.addWidget(title_lbl)
        
        if not self.orig_pixmap.isNull():
            w, h = self.orig_pixmap.width(), self.orig_pixmap.height()
            res_badge = QLabel(f"📐 {w} × {h} px (원본 고해상도)")
            res_badge.setFont(QFont('Malgun Gothic', 10, QFont.Bold))
            res_badge.setStyleSheet("color: #38BDF8; background-color: #0369A1; padding: 4px 12px; border-radius: 6px;")
            top_bar.addWidget(res_badge)
            
        self.zoom_lbl = QLabel("100%")
        self.zoom_lbl.setFont(QFont('Malgun Gothic', 10, QFont.Bold))
        self.zoom_lbl.setStyleSheet("color: #94A3B8; background-color: #1E293B; padding: 4px 12px; border-radius: 6px;")
        top_bar.addWidget(self.zoom_lbl)
        
        top_bar.addStretch()
        
        btn_style = """
            QPushButton {
                background-color: #1E293B;
                color: #E2E8F0;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 14px;
                font-family: 'Malgun Gothic';
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #334155;
                color: white;
                border: 1px solid #64748B;
            }
        """
        
        btn_in = QPushButton("🔍+ 확대")
        btn_in.setStyleSheet(btn_style)
        btn_in.setCursor(Qt.PointingHandCursor)
        btn_in.clicked.connect(lambda: self.adjust_zoom(1.2))
        top_bar.addWidget(btn_in)
        
        btn_out = QPushButton("🔍- 축소")
        btn_out.setStyleSheet(btn_style)
        btn_out.setCursor(Qt.PointingHandCursor)
        btn_out.clicked.connect(lambda: self.adjust_zoom(0.8))
        top_bar.addWidget(btn_out)
        
        btn_fit = QPushButton("🖥️ 화면 맞춤")
        btn_fit.setStyleSheet(btn_style)
        btn_fit.setCursor(Qt.PointingHandCursor)
        btn_fit.clicked.connect(self.fit_to_window)
        top_bar.addWidget(btn_fit)
        
        btn_actual = QPushButton("1:1 원본 크기")
        btn_actual.setStyleSheet(btn_style)
        btn_actual.setCursor(Qt.PointingHandCursor)
        btn_actual.clicked.connect(self.reset_to_actual)
        top_bar.addWidget(btn_actual)
        
        btn_save = QPushButton("💾 파일 저장...")
        btn_save.setStyleSheet(btn_style)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.save_as)
        top_bar.addWidget(btn_save)
        
        btn_close = QPushButton("✕ 닫기 (Esc)")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border-radius: 6px;
                padding: 6px 16px;
                font-family: 'Malgun Gothic';
                font-size: 11px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        top_bar.addWidget(btn_close)
        
        main_layout.addLayout(top_bar)
        
        # 이미지 스크롤 뷰포트
        self.scroll = QScrollArea()
        self.scroll.setStyleSheet("""
            QScrollArea {
                background-color: #020617;
                border: 1px solid #1E293B;
                border-radius: 10px;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #0F172A;
                border: none;
                margin: 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #334155;
                border-radius: 4px;
                min-height: 25px;
                min-width: 25px;
            }
            QScrollBar::handle:hover {
                background: #475569;
            }
        """)
        self.scroll.setAlignment(Qt.AlignCenter)
        self.scroll.viewport().installEventFilter(self)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        self.scroll.setWidget(self.image_label)
        
        main_layout.addWidget(self.scroll, 1)
        
        # 하단 단축키 가이드
        footer = QLabel("💡 마우스 휠: 확대/축소 | 좌클릭 드래그: 화면 이동 | 더블 클릭: 1:1/화면맞춤 전환 | Esc: 닫기")
        footer.setFont(QFont('Malgun Gothic', 9))
        footer.setStyleSheet("color: #64748B; padding: 2px 4px;")
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)
        
        self.update_image_display()
        QTimer.singleShot(60, self.fit_to_window)

    def update_image_display(self):
        if self.orig_pixmap.isNull():
            self.image_label.setText("⚠️ 이미지를 불러올 수 없습니다.")
            self.image_label.setStyleSheet("color: #EF4444; font-size: 14pt;")
            return
        target_size = self.orig_pixmap.size() * self.scale_factor
        scaled = self.orig_pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self.image_label.resize(scaled.size())
        self.zoom_lbl.setText(f"{int(self.scale_factor * 100)}%")

    def adjust_zoom(self, factor):
        self.scale_factor = max(0.1, min(6.0, self.scale_factor * factor))
        self.update_image_display()

    def fit_to_window(self):
        if self.orig_pixmap.isNull():
            return
        vw = max(100, self.scroll.viewport().width() - 30)
        vh = max(100, self.scroll.viewport().height() - 30)
        factor_w = vw / self.orig_pixmap.width()
        factor_h = vh / self.orig_pixmap.height()
        self.scale_factor = min(factor_w, factor_h, 1.0)
        self.update_image_display()

    def reset_to_actual(self):
        self.scale_factor = 1.0
        self.update_image_display()

    def save_as(self):
        if not os.path.exists(self.image_path):
            QMessageBox.warning(self, "경고", "원본 이미지 파일을 찾을 수 없습니다.")
            return
        default_name = os.path.basename(self.image_path)
        dest, _ = QFileDialog.getSaveFileName(self, "이미지 저장", default_name, "이미지 파일 (*.png *.jpg *.jpeg *.bmp)")
        if dest:
            try:
                shutil.copyfile(self.image_path, dest)
                QMessageBox.information(self, "성공", f"이미지가 성공적으로 저장되었습니다:\n{dest}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"저장 중 오류 발생: {e}")

    def eventFilter(self, obj, event):
        if obj == self.scroll.viewport():
            if event.type() == QEvent.Wheel:
                delta = event.angleDelta().y()
                if delta > 0:
                    self.adjust_zoom(1.15)
                elif delta < 0:
                    self.adjust_zoom(0.85)
                return True
            elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.is_dragging = True
                self.drag_start = event.pos()
                self.drag_start_h = self.scroll.horizontalScrollBar().value()
                self.drag_start_v = self.scroll.verticalScrollBar().value()
                self.scroll.viewport().setCursor(Qt.ClosedHandCursor)
                return True
            elif event.type() == QEvent.MouseMove and self.is_dragging:
                delta = event.pos() - self.drag_start
                self.scroll.horizontalScrollBar().setValue(self.drag_start_h - delta.x())
                self.scroll.verticalScrollBar().setValue(self.drag_start_v - delta.y())
                return True
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self.is_dragging = False
                self.scroll.viewport().setCursor(Qt.ArrowCursor)
                return True
            elif event.type() == QEvent.MouseButtonDblClick and event.button() == Qt.LeftButton:
                if abs(self.scale_factor - 1.0) < 0.05:
                    self.fit_to_window()
                else:
                    self.reset_to_actual()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.accept()
        elif key in (Qt.Key_Plus, Qt.Key_Equal):
            self.adjust_zoom(1.2)
        elif key in (Qt.Key_Minus, Qt.Key_Underscore):
            self.adjust_zoom(0.8)
        elif key == Qt.Key_0:
            self.reset_to_actual()
        elif key == Qt.Key_F:
            self.fit_to_window()
        else:
            super().keyPressEvent(event)


class ClickableImageCard(QFrame):
    """
    일지 카드 내부에서 이미지를 Qt.SmoothTransformation 고품질로 선명하게 표시하고,
    클릭 시 원본 고해상도 팝업 뷰어를 띄우는 인터랙티브 위젯
    """
    def __init__(self, abs_path, on_click=None, parent=None):
        super().__init__(parent)
        self.abs_path = abs_path
        self.on_click = on_click
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            ClickableImageCard {
                background-color: #F8FAFC;
                border: 1.5px solid #E2E8F0;
                border-radius: 12px;
                padding: 10px;
                margin: 6px 0px;
            }
            ClickableImageCard:hover {
                background-color: #F0FDF4;
                border: 1.5px solid #10B981;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        pix = QPixmap(abs_path)
        img_lbl = QLabel()
        img_lbl.setAlignment(Qt.AlignCenter)
        img_lbl.setStyleSheet("border: none; background: transparent;")
        
        if not pix.isNull():
            orig_w, orig_h = pix.width(), pix.height()
            # 카드 너비에 맞춰 부드럽게 축소 (최대 760px)
            disp_w = min(760, orig_w)
            scaled = pix.scaledToWidth(disp_w, Qt.SmoothTransformation)
            img_lbl.setPixmap(scaled)
            layout.addWidget(img_lbl)
            
            bar = QHBoxLayout()
            bar.setContentsMargins(4, 0, 4, 0)
            
            res_lbl = QLabel(f"📐 원본 해상도: {orig_w} × {orig_h} px")
            res_lbl.setFont(QFont('Malgun Gothic', 9))
            res_lbl.setStyleSheet("color: #64748B; border: none;")
            bar.addWidget(res_lbl)
            
            bar.addStretch()
            
            hint_lbl = QLabel("🔍 클릭하여 원본 고화질 확대 (줌 / 1:1 지원)")
            hint_lbl.setFont(QFont('Malgun Gothic', 9, QFont.Bold))
            hint_lbl.setStyleSheet("color: #059669; border: none;")
            bar.addWidget(hint_lbl)
            
            layout.addLayout(bar)
        else:
            img_lbl.setText("⚠️ 이미지를 불러올 수 없습니다.")
            img_lbl.setStyleSheet("color: #EF4444; padding: 15px;")
            layout.addWidget(img_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.on_click:
                self.on_click(self.abs_path)
            event.accept()
        else:
            super().mousePressEvent(event)


class LogHistoryDialog(QDialog):
    def __init__(self, class_name, logs, parent=None):
        super().__init__(parent)
        self.class_name = class_name
        self.logs = logs
        self.parent_app = parent
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(f'{self.class_name} 전체 수업 기록')
        self.resize(860, 820)
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

    def open_image_viewer(self, path):
        dlg = ImageViewerDialog(path, self)
        dlg.exec_()

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
            
            raw_content = log.get('content', '')
            is_rich = any(tag in raw_content for tag in ['<!DOCTYPE', '<html', '<body', '<p', '<div', '<img', '<span', '<br'])
            if is_rich:
                base_d = getattr(self.parent_app, 'base_dir', os.path.dirname(os.path.abspath(__file__)))
                content_html = resolve_image_paths(raw_content, base_d)
                if '<body' in content_html and '</body>' in content_html:
                    try:
                        content_html = content_html.split('<body', 1)[1].split('>', 1)[1].rsplit('</body>', 1)[0].strip()
                    except Exception:
                        pass
                
                # 이미지가 포함된 경우: 텍스트와 이미지를 분리하여 이미지는 고화질 렌더링 카드(SmoothTransformation)로 표시
                if '<img' in content_html:
                    img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', re.IGNORECASE)
                    tokens = img_pattern.split(content_html)
                    # tokens: [text0, src0, text1, src1, text2, ...]
                    for idx_tok, tok in enumerate(tokens):
                        if idx_tok % 2 == 1:
                            # 이미지 경로
                            img_src = tok.replace('file:///', '')
                            if not os.path.exists(img_src):
                                fname = os.path.basename(img_src)
                                cand = os.path.join(base_d, 'log_images', fname)
                                if os.path.exists(cand):
                                    img_src = cand
                            img_card = ClickableImageCard(img_src, on_click=self.open_image_viewer, parent=self)
                            card_layout.addWidget(img_card)
                        else:
                            # 텍스트 HTML 부분
                            plain = re.sub(r'<[^>]+>', '', tok).strip()
                            if plain or '<hr' in tok:
                                lbl = QLabel(tok)
                                lbl.setTextFormat(Qt.RichText)
                                lbl.setFont(QFont('Malgun Gothic', 12))
                                lbl.setStyleSheet("color: #2C3E50; border: none; margin-top: 3px; margin-bottom: 3px;")
                                lbl.setWordWrap(True)
                                card_layout.addWidget(lbl)
                else:
                    content_label = QLabel(content_html)
                    content_label.setTextFormat(Qt.RichText)
                    content_label.setFont(QFont('Malgun Gothic', 12))
                    content_label.setStyleSheet("color: #2C3E50; border: none; margin-top: 5px;")
                    content_label.setWordWrap(True)
                    content_label.setOpenExternalLinks(False)
                    card_layout.addWidget(content_label)
            else:
                content_html = html.escape(raw_content).replace('\n', '<br>')
                content_label = QLabel(content_html)
                content_label.setTextFormat(Qt.RichText)
                content_label.setFont(QFont('Malgun Gothic', 12))
                content_label.setStyleSheet("color: #2C3E50; border: none; margin-top: 5px;")
                content_label.setWordWrap(True)
                content_label.setOpenExternalLinks(False)
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
        old_content = self.logs[idx].get('content', '')
        dlg = LogWriteDialog(self.class_name, initial_content=old_content, parent=self.parent_app or self)
        if dlg.exec_() == QDialog.Accepted:
            self.logs[idx]['content'] = dlg.result_text
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


