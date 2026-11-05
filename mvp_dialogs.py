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

