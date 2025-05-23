#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QComboBox, QGridLayout, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor

# 回合数据类 - 用于储存各回合信息
class RoundData:
    def __init__(self, title, speaker, duration):
        self.title = title  # 回合标题
        self.speaker = speaker  # 发言方 (0=正方, 1=反方)
        self.duration = duration  # 时间(秒)

# 标准辩论赛回合配置
STANDARD_DEBATE_ROUNDS = [
    RoundData("正方一辩陈词", 0, 180),  # 3分钟
    RoundData("反方一辩陈词", 1, 180),  # 3分钟
    RoundData("正方二辩质询反方一辩", 0, 120),  # 2分钟
    RoundData("反方二辩质询正方一辩", 1, 120),  # 2分钟
    RoundData("正方三辩陈词", 0, 180),  # 3分钟
    RoundData("反方三辩陈词", 1, 180),  # 3分钟
    RoundData("反方四辩质询正方三辩", 1, 120),  # 2分钟
    RoundData("正方四辩质询反方三辩", 0, 120),  # 2分钟
    RoundData("反方四辩总结陈词", 1, 240),  # 4分钟
    RoundData("正方四辩总结陈词", 0, 240),  # 4分钟
    RoundData("自由辩论", 2, 300),  # 5分钟
]

# 控制回合的通信信号
class RoundControlSignals(QObject):
    # 回合控制信号
    set_round_signal = pyqtSignal(RoundData)  # 设置当前回合
    start_timer_signal = pyqtSignal()  # 开始计时
    pause_timer_signal = pyqtSignal()  # 暂停计时
    reset_timer_signal = pyqtSignal()  # 重置计时
    time_update_signal = pyqtSignal(int)  # 更新剩余时间
    round_finished_signal = pyqtSignal()  # 回合结束信号

# 回合控制器部件 - 用于控制台
class RoundController(QWidget):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        self.current_round_index = 0
        self.rounds = STANDARD_DEBATE_ROUNDS
        self.timer_active = False
        self.remaining_time = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        
        self.init_ui()
    
    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 回合选择区域
        round_select_group = QGroupBox("回合选择")
        round_select_layout = QHBoxLayout()
        
        self.round_combo = QComboBox()
        for round_data in self.rounds:
            self.round_combo.addItem(round_data.title)
        self.round_combo.currentIndexChanged.connect(self.change_round)
        
        round_select_layout.addWidget(self.round_combo)
        round_select_group.setLayout(round_select_layout)
        main_layout.addWidget(round_select_group)
        
        # 当前回合信息区域
        round_info_group = QGroupBox("当前回合信息")
        round_info_layout = QGridLayout()
        
        # 回合标题
        round_info_layout.addWidget(QLabel("当前回合:"), 0, 0)
        self.current_round_title = QLabel()
        self.current_round_title.setFont(QFont("微软雅黑", 12, QFont.Bold))
        round_info_layout.addWidget(self.current_round_title, 0, 1)
        
        # 发言方
        round_info_layout.addWidget(QLabel("发言方:"), 1, 0)
        self.current_speaker = QLabel()
        self.current_speaker.setFont(QFont("微软雅黑", 12))
        round_info_layout.addWidget(self.current_speaker, 1, 1)
        
        # 剩余时间
        round_info_layout.addWidget(QLabel("剩余时间:"), 2, 0)
        self.time_display = QLabel()
        self.time_display.setFont(QFont("Arial", 14, QFont.Bold))
        round_info_layout.addWidget(self.time_display, 2, 1)
        
        round_info_group.setLayout(round_info_layout)
        main_layout.addWidget(round_info_group)
        
        # 控制按钮区域
        controls_group = QGroupBox("计时控制")
        controls_layout = QHBoxLayout()
        
        # 开始/暂停按钮
        self.toggle_button = QPushButton("开始")
        self.toggle_button.clicked.connect(self.toggle_timer)
        controls_layout.addWidget(self.toggle_button)
        
        # 重置按钮
        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self.reset_timer)
        controls_layout.addWidget(self.reset_button)
        
        # 下一回合按钮
        self.next_button = QPushButton("下一回合")
        self.next_button.clicked.connect(self.next_round)
        controls_layout.addWidget(self.next_button)
        
        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group)
        
        # 初始化当前回合
        self.update_round_display()
    
    def update_round_display(self):
        """更新回合显示信息"""
        current_round = self.rounds[self.current_round_index]
        self.current_round_title.setText(current_round.title)
        
        # 设置发言方
        if current_round.speaker == 0:
            self.current_speaker.setText("正方")
            self.current_speaker.setStyleSheet("color: #004080;")  # 深蓝色
        elif current_round.speaker == 1:
            self.current_speaker.setText("反方")
            self.current_speaker.setStyleSheet("color: #800000;")  # 深红色
        else:
            self.current_speaker.setText("双方")
            self.current_speaker.setStyleSheet("color: black;")
        
        # 设置时间
        self.remaining_time = current_round.duration
        self.update_time_display()
        
        # 发送回合设置信号
        self.signals.set_round_signal.emit(current_round)
    
    def change_round(self, index):
        """当用户从下拉菜单选择回合时"""
        self.current_round_index = index
        self.reset_timer()
        self.update_round_display()
    
    def next_round(self):
        """切换到下一回合"""
        if self.current_round_index < len(self.rounds) - 1:
            self.current_round_index += 1
            self.round_combo.setCurrentIndex(self.current_round_index)
            self.reset_timer()
            self.update_round_display()
    
    def toggle_timer(self):
        """开始/暂停计时"""
        if self.timer_active:
            # 暂停计时
            self.timer.stop()
            self.timer_active = False
            self.toggle_button.setText("继续")
            self.signals.pause_timer_signal.emit()
        else:
            # 开始计时
            self.timer.start(1000)
            self.timer_active = True
            self.toggle_button.setText("暂停")
            self.signals.start_timer_signal.emit()
    
    def reset_timer(self):
        """重置计时器"""
        self.timer.stop()
        self.timer_active = False
        self.toggle_button.setText("开始")
        self.remaining_time = self.rounds[self.current_round_index].duration
        self.update_time_display()
        self.signals.reset_timer_signal.emit()
    
    def update_time(self):
        """更新计时器"""
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.update_time_display()
            self.signals.time_update_signal.emit(self.remaining_time)
        else:
            # 回合结束
            self.timer.stop()
            self.timer_active = False
            self.toggle_button.setText("开始")
            self.signals.round_finished_signal.emit()
    
    def update_time_display(self):
        """更新时间显示"""
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.time_display.setText(f"{minutes:02d}:{seconds:02d}")

# 回合显示部件 - 用于展示板
class RoundDisplay(QWidget):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
        
        # 当前回合信息
        self.current_round = None
        self.remaining_time = 0
        
        # 连接信号
        self.signals.set_round_signal.connect(self.set_round)
        self.signals.time_update_signal.connect(self.update_time)
        self.signals.reset_timer_signal.connect(self.reset_timer)
        
        self.init_ui()
    
    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 回合标题标签
        self.round_title_label = QLabel()
        self.round_title_label.setAlignment(Qt.AlignCenter)
        self.round_title_label.setFont(QFont("微软雅黑", 24, QFont.Bold))
        main_layout.addWidget(self.round_title_label)
        
        # 发言方标签
        self.speaker_label = QLabel()
        self.speaker_label.setAlignment(Qt.AlignCenter)
        self.speaker_label.setFont(QFont("微软雅黑", 20))
        main_layout.addWidget(self.speaker_label)
        
        # 剩余时间标签
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont("Arial", 36, QFont.Bold))
        main_layout.addWidget(self.time_label)
    
    def set_round(self, round_data):
        """设置当前回合"""
        self.current_round = round_data
        self.round_title_label.setText(round_data.title)
        
        # 设置发言方样式
        if round_data.speaker == 0:
            self.speaker_label.setText("正方发言")
            self.speaker_label.setStyleSheet("color: #004080;")  # 深蓝色
        elif round_data.speaker == 1:
            self.speaker_label.setText("反方发言")
            self.speaker_label.setStyleSheet("color: #800000;")  # 深红色
        else:
            self.speaker_label.setText("自由辩论")
            self.speaker_label.setStyleSheet("color: black;")
        
        self.remaining_time = round_data.duration
        self.update_time_display()
    
    def update_time(self, time):
        """更新剩余时间"""
        self.remaining_time = time
        self.update_time_display()
    
    def reset_timer(self):
        """重置计时器"""
        if self.current_round:
            self.remaining_time = self.current_round.duration
            self.update_time_display()
    
    def update_time_display(self):
        """更新时间显示"""
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")
