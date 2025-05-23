#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, 
                            QWidget, QFrame, QGraphicsDropShadowEffect, 
                            QGroupBox, QStackedLayout, QSizePolicy, QMessageBox, QStyle,
                            QGraphicsOpacityEffect, QGraphicsColorizeEffect)
from PyQt5.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve, 
                        QParallelAnimationGroup, QTime, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import QFont, QColor

import logging
import sys
from typing import Dict, Any, Optional, List

# 导入自定义模块
from utils import highlight_markers, GradientBorderFrame, enable_dwm_composition, logger
from custom_progress_bar import RoundedProgressBar

class DisplayBoard(QMainWindow):
    """前台展示窗口，用于显示给观众"""
    
    # 自定义信号
    roundChanged = pyqtSignal(int)
    
    def __init__(self, low_performance_mode=False):
        super().__init__()
        logger.info("DisplayBoard 初始化")
        self.title = "辩论背景看板"
        self.topic = "等待设置辩题" # 内部仍可存储，但不显示
        self.affirmative_school = ""
        self.affirmative_viewpoint = "" # 新增
        self.negative_school = ""
        self.negative_viewpoint = ""  # 新增
        self.debater_roles = {}  # 存储辩手角色到姓名的映射
        self.low_performance_mode = low_performance_mode  # 添加低性能模式标志
        
        self.current_time = 0
        # 新增：自由辩论双计时器时间变量
        self.affirmative_time = 0
        self.negative_time = 0
        self.timer_active = False
        # 新增：正反方计时器状态
        self.affirmative_timer_active = False
        self.negative_timer_active = False
        self.current_round = None
        self.rounds = []
        self.current_round_index = -1
        self.is_fullscreen = False
        self.control_panel = None  # 添加对控制面板的引用
        self.is_free_debate = False  # 新增：是否为自由辩论标志
        
        # 低性能模式下的特殊处理
        if low_performance_mode:
            logger.info("启用低性能模式")
            # 减少窗口阴影和特效
            self.setGraphicsEffect(None)
        
        # 设置白色背景
        self.setStyleSheet("background-color: white;")
        
        # 优化渲染属性
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)
        
        self.initUI()
        logger.info("DisplayBoard UI 初始化完成")
        
        # 启用Windows硬件加速（如果可用）
        if sys.platform == 'win32':
            try:
                enable_dwm_composition()  # 启用DWM硬件加速
            except Exception as e:
                logger.error(f"无法启用Windows硬件加速: {e}")

    def initUI(self):
        logger.debug("DisplayBoard.initUI 开始")
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 1680, 945) # 默认窗口大小
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 设置背景 - 移除背景图片引用，改用纯色背景
        self.bg_label = QLabel(central_widget)
        self.bg_label.setObjectName("backgroundLabel")
        self.bg_label.setStyleSheet("background-color: #f5f5f5;")  # 使用浅灰色作为背景
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        
        # 毛玻璃效果层 - 半透明白色层
        self.blur_effect = QLabel(central_widget)
        self.blur_effect.setObjectName("blurEffect")
        self.blur_effect.setStyleSheet("background-color: rgba(255, 255, 255, 1.0);")
        self.blur_effect.setGeometry(0, 0, self.width(), self.height())
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 创建顶部容器 - 用于辩题显示
        topic_container = QFrame()
        topic_container.setObjectName("topicContainer")
        topic_container.setStyleSheet("""
            #topicContainer {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        # 为顶部容器添加阴影效果
        topic_shadow = QGraphicsDropShadowEffect()
        topic_shadow.setBlurRadius(15)
        topic_shadow.setColor(QColor(0, 0, 0, 40))
        topic_shadow.setOffset(0, 2)
        topic_container.setGraphicsEffect(topic_shadow)
        
        # self.topic_stack 原来包含 topic_label, round_info_label, next_info_label
        # 现在我们用新的控件替换它们
        if hasattr(self, 'topic_label'): self.topic_label.deleteLater()
        if hasattr(self, 'round_info_label'): self.round_info_label.deleteLater()
        if hasattr(self, 'next_info_label'): self.next_info_label.deleteLater()

        self.topic_stack = QStackedLayout(topic_container) # Re-assign or ensure it's clean

        self._create_preview_widget_top()
        self._create_active_round_widget_top()

        self.topic_stack.addWidget(self.preview_widget_top)  # Index 0
        self.topic_stack.addWidget(self.active_round_widget_top) # Index 1
        
        self.topic_stack.setCurrentWidget(self.preview_widget_top)
        self.current_top_widget_anim = None # To manage ongoing animations

        main_layout.addWidget(topic_container, 10) # Adjusted stretch factor for top container
        
        # 创建左右两侧的布局
        sides_layout = QHBoxLayout()
        sides_layout.setContentsMargins(0, 0, 0, 0)
        sides_layout.setSpacing(15)
        
        # 创建正方（左侧）部件 - 使用渐变边框
        affirmative_widget = GradientBorderFrame(start_color="#0078D4", end_color="#50B0E0")
        affirmative_widget.setObjectName("affirmativeWidget")
        affirmative_widget.setStyleSheet("""
            #affirmativeWidget {
                background-color: white;
                border-radius: 12px;
            }
        """)
        affirmative_shadow = QGraphicsDropShadowEffect()
        affirmative_shadow.setBlurRadius(20)
        affirmative_shadow.setColor(QColor(0, 0, 0, 50))
        affirmative_shadow.setOffset(0, 4)
        affirmative_widget.setGraphicsEffect(affirmative_shadow)
        self.affirmative_layout = QVBoxLayout(affirmative_widget)
        self.affirmative_layout.setContentsMargins(20, 20, 20, 20)
        self.affirmative_layout.setSpacing(10)
        affirmative_title = QLabel("正方")
        affirmative_title.setAlignment(Qt.AlignCenter)
        affirmative_title.setFont(QFont("微软雅黑", 48, QFont.Bold))
        affirmative_title.setStyleSheet("color: #0078D4;")
        self.affirmative_school_label = QLabel(self.affirmative_school)
        self.affirmative_school_label.setAlignment(Qt.AlignCenter)
        self.affirmative_school_label.setFont(QFont("微软雅黑", 20))
        self.affirmative_school_label.setStyleSheet("color: #0078D4;")
        affirmative_separator = QFrame()
        affirmative_separator.setFrameShape(QFrame.HLine)
        affirmative_separator.setFrameShadow(QFrame.Sunken)
        affirmative_separator.setStyleSheet("background-color: rgba(0, 120, 212, 0.3); margin: 10px 30px;")
        affirmative_separator.setFixedHeight(2)
        self.affirmative_viewpoint_label = QLabel(self.affirmative_viewpoint)
        self.affirmative_viewpoint_label.setAlignment(Qt.AlignCenter)
        self.affirmative_viewpoint_label.setWordWrap(True)
        self.affirmative_viewpoint_label.setFont(QFont("微软雅黑", 16))
        self.affirmative_viewpoint_label.setStyleSheet("color: #323130;")
        self.affirmative_layout.addWidget(affirmative_title)
        self.affirmative_layout.addWidget(self.affirmative_school_label)
        self.affirmative_layout.addWidget(affirmative_separator)
        self.affirmative_layout.addWidget(self.affirmative_viewpoint_label)
        self.affirmative_layout.addStretch()
        
        # 创建反方（右侧）部件 - 使用渐变边框
        negative_widget = GradientBorderFrame(start_color="#D13438", end_color="#E85A5E")
        negative_widget.setObjectName("negativeWidget")
        negative_widget.setStyleSheet("""
            #negativeWidget {
                background-color: white;
                border-radius: 12px;
            }
        """)
        negative_shadow = QGraphicsDropShadowEffect()
        negative_shadow.setBlurRadius(20)
        negative_shadow.setColor(QColor(0, 0, 0, 50))
        negative_shadow.setOffset(0, 4)
        negative_widget.setGraphicsEffect(negative_shadow)
        self.negative_layout = QVBoxLayout(negative_widget)
        self.negative_layout.setContentsMargins(20, 20, 20, 20)
        self.negative_layout.setSpacing(10)
        negative_title = QLabel("反方")
        negative_title.setAlignment(Qt.AlignCenter)
        negative_title.setFont(QFont("微软雅黑", 48, QFont.Bold))
        negative_title.setStyleSheet("color: #D13438;")
        self.negative_school_label = QLabel(self.negative_school)
        self.negative_school_label.setAlignment(Qt.AlignCenter)
        self.negative_school_label.setFont(QFont("微软雅黑", 20))
        self.negative_school_label.setStyleSheet("color: #D13438;")
        negative_separator = QFrame()
        negative_separator.setFrameShape(QFrame.HLine)
        negative_separator.setFrameShadow(QFrame.Sunken)
        negative_separator.setStyleSheet("background-color: rgba(209, 52, 56, 0.3); margin: 10px 30px;")
        negative_separator.setFixedHeight(2)
        self.negative_viewpoint_label = QLabel(self.negative_viewpoint)
        self.negative_viewpoint_label.setAlignment(Qt.AlignCenter)
        self.negative_viewpoint_label.setWordWrap(True)
        self.negative_viewpoint_label.setFont(QFont("微软雅黑", 16))
        self.negative_viewpoint_label.setStyleSheet("color: #323130;")
        self.negative_layout.addWidget(negative_title)
        self.negative_layout.addWidget(self.negative_school_label)
        self.negative_layout.addWidget(negative_separator)
        self.negative_layout.addWidget(self.negative_viewpoint_label)
        self.negative_layout.addStretch()
        
        sides_layout.addWidget(affirmative_widget)
        sides_layout.addWidget(negative_widget)
        
        # --------- 只保留北京时间的底部区域 ---------
        self.beijing_time_label = QLabel()
        self.beijing_time_label.setAlignment(Qt.AlignCenter)
        self.beijing_time_label.setFont(QFont("微软雅黑", 32, QFont.Bold))
        self.beijing_time_label.setStyleSheet("color: #323130;")
        self.update_beijing_time()  # 初始化一次
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_beijing_time)
        self.clock_timer.start(1000)
        main_layout.addLayout(sides_layout, 78)
        main_layout.addWidget(self.beijing_time_label, 10)
        # --------- END ---------

        # 设置计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.bg_label.lower()

        self.showNormal()
        logger.debug("DisplayBoard.initUI 结束")

    def update_beijing_time(self):
        """更新北京时间"""
        current_time = QTime.currentTime()
        time_text = f"北京时间：{current_time.toString('HH:mm:ss')}"
        self.beijing_time_label.setText(time_text)
        logger.debug(f"更新时间：{time_text}")

    def _optimize_label_rendering(self, label, color):
        """优化标签渲染效果"""
        label.setStyleSheet(f"color: {color};")
        label.setAttribute(Qt.WA_TranslucentBackground, True)
        label.setContentsMargins(0, 0, 0, 0)
    
    def _create_preview_widget_top(self):
        logger.debug("创建预览灵动岛控件")
        if hasattr(self, 'preview_widget_top'):
            self.preview_widget_top.deleteLater()
        self.preview_widget_top = QWidget()
        layout = QHBoxLayout(self.preview_widget_top) # 修改为 QHBoxLayout
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15) # 添加标签之间的间距

        self.preview_title_label = QLabel("下一环节:") # 添加冒号以示区分
        self.preview_title_label.setFont(QFont("微软雅黑", 18, QFont.Bold))
        self.preview_title_label.setAlignment(Qt.AlignCenter)
        # 优化文本渲染
        self._optimize_label_rendering(self.preview_title_label, "#323130")

        self.preview_type_label = QLabel("类型: N/A")
        self.preview_type_label.setFont(QFont("微软雅黑", 22, QFont.Bold)) # 可以考虑统一字体大小
        self.preview_type_label.setAlignment(Qt.AlignCenter)
        self._optimize_label_rendering(self.preview_type_label, "#0078D4")

        self.preview_desc_label = QLabel("描述: N/A")
        self.preview_desc_label.setFont(QFont("微软雅黑", 16))
        self.preview_desc_label.setAlignment(Qt.AlignCenter)
        self.preview_desc_label.setWordWrap(False) # 在单行中通常不希望自动换行
        self._optimize_label_rendering(self.preview_desc_label, "#605E5C")
        
        self.preview_time_label = QLabel("时长: N/A")
        self.preview_time_label.setFont(QFont("微软雅黑", 16))
        self.preview_time_label.setAlignment(Qt.AlignCenter)
        self._optimize_label_rendering(self.preview_time_label, "#605E5C")

        layout.addWidget(self.preview_title_label)
        layout.addWidget(self.preview_type_label)
        layout.addWidget(self.preview_desc_label)
        layout.addWidget(self.preview_time_label)
        
        # Opacity effect for animation
        opacity_effect = QGraphicsOpacityEffect(self.preview_widget_top)
        opacity_effect.setOpacity(1.0)
        self.preview_widget_top.setGraphicsEffect(opacity_effect)

    def _create_active_round_widget_top(self):
        logger.debug("创建倒计时灵动岛控件")
        self.active_round_widget_top = QWidget()
        # 使用垂直布局组织所有元素
        main_layout = QVBoxLayout(self.active_round_widget_top)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # 添加当前环节标题信息
        self.active_round_title = QLabel("当前环节")
        self.active_round_title.setFont(QFont("微软雅黑", 16, QFont.Bold))
        self.active_round_title.setAlignment(Qt.AlignCenter)
        self.active_round_title.setStyleSheet("color: #323130;")
        main_layout.addWidget(self.active_round_title)
        
        # 添加当前发言者信息
        self.active_speaker_info = QLabel()
        self.active_speaker_info.setFont(QFont("微软雅黑", 14))
        self.active_speaker_info.setAlignment(Qt.AlignCenter)
        self.active_speaker_info.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.active_speaker_info)
        
        # 创建两个定时器容器：标准模式和自由辩论模式
        self.standard_timer_container = QWidget()
        self.free_debate_timer_container = QWidget()
        
        # 标准模式定时器布局
        timer_layout = QHBoxLayout(self.standard_timer_container)
        timer_layout.setContentsMargins(0, 0, 0, 0)
        timer_layout.setSpacing(10)
        timer_layout.setAlignment(Qt.AlignCenter)
        
        # 设置容器的大小策略为固定或首选
        self.standard_timer_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # 创建环形进度条
        self.active_progress_bar_top = RoundedProgressBar()
        size = int(min(self.width(), self.height()) * 0.15)
        size = max(80, size)  # 确保最小尺寸为80
        self.active_progress_bar_top.setFixedSize(size, size)
        
        # 设置颜色样式
        self.active_progress_bar_top.setLineWidth(4)
        self.active_progress_bar_top.setProgressColor(QColor("#0078D4"))
        self.active_progress_bar_top.setTextColor(QColor("#323130"))
        
        # 添加具体的倒计时数字标签
        self.countdown_label = QLabel()
        self.countdown_label.setFont(QFont("微软雅黑", 24, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("color: #323130;")
        
        # 添加进度条和倒计时到布局
        timer_layout.addWidget(self.active_progress_bar_top)
        timer_layout.addWidget(self.countdown_label)
        
        # 自由辩论模式下的双计时器布局
        free_debate_layout = QHBoxLayout(self.free_debate_timer_container)
        free_debate_layout.setContentsMargins(0, 0, 0, 0)
        free_debate_layout.setSpacing(10)
        free_debate_layout.setAlignment(Qt.AlignCenter)
        
        # 正方计时器组 - 修复重复定义问题
        aff_timer_group = QWidget()
        aff_timer_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        aff_timer_layout = QVBoxLayout(aff_timer_group)
        
        aff_title = QLabel("正方")
        aff_title.setAlignment(Qt.AlignCenter)
        aff_title.setFont(QFont("微软雅黑", 12, QFont.Bold))
        aff_title.setStyleSheet("color: #0078D4;")
        
        # 创建正方计时器布局，不再重复创建 aff_timer_group
        aff_timer_box = QHBoxLayout()
        
        # 创建正方环形进度条
        self.aff_progress_bar = RoundedProgressBar()
        self.aff_progress_bar.setFixedSize(size, size)
        self.aff_progress_bar.setLineWidth(4)
        self.aff_progress_bar.setProgressColor(QColor("#0078D4"))
        self.aff_progress_bar.setTextColor(QColor("#323130"))
        self.aff_progress_bar.setObjectName("aff_progress_bar")
        
        # 正方倒计时标签
        self.aff_countdown_label = QLabel()
        self.aff_countdown_label.setFont(QFont("微软雅黑", 20, QFont.Bold))
        self.aff_countdown_label.setAlignment(Qt.AlignCenter)
        self.aff_countdown_label.setStyleSheet("color: #323130;")
        
        aff_timer_box.addWidget(self.aff_progress_bar)
        aff_timer_box.addWidget(self.aff_countdown_label)
        aff_timer_layout.addWidget(aff_title)
        aff_timer_layout.addLayout(aff_timer_box)
        
        # 反方计时器组 - 同样修复重复定义问题
        neg_timer_group = QWidget()
        neg_timer_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        neg_timer_layout = QVBoxLayout(neg_timer_group)
        
        neg_title = QLabel("反方")
        neg_title.setAlignment(Qt.AlignCenter)
        neg_title.setFont(QFont("微软雅黑", 12, QFont.Bold))
        neg_title.setStyleSheet("color: #C42B1C;")
        
        # 创建反方计时器布局，不再重复创建 neg_timer_group
        neg_timer_box = QHBoxLayout()
        
        # 创建反方环形进度条
        self.neg_progress_bar = RoundedProgressBar()
        self.neg_progress_bar.setFixedSize(size, size)
        self.neg_progress_bar.setLineWidth(4)
        self.neg_progress_bar.setProgressColor(QColor("#C42B1C"))
        self.neg_progress_bar.setTextColor(QColor("#323130"))
        self.neg_progress_bar.setObjectName("neg_progress_bar")
        
        # 反方倒计时标签
        self.neg_countdown_label = QLabel()
        self.neg_countdown_label.setFont(QFont("微软雅黑", 20, QFont.Bold))
        self.neg_countdown_label.setAlignment(Qt.AlignCenter)
        self.neg_countdown_label.setStyleSheet("color: #323130;")
        
        neg_timer_box.addWidget(self.neg_progress_bar)
        neg_timer_box.addWidget(self.neg_countdown_label)
        neg_timer_layout.addWidget(neg_title)
        neg_timer_layout.addLayout(neg_timer_box)
        
        free_debate_layout.addWidget(aff_timer_group)
        free_debate_layout.addWidget(neg_timer_group)
        
        # 创建计时器容器堆栈
        self.timer_stack = QStackedLayout()
        self.timer_stack.addWidget(self.standard_timer_container)
        self.timer_stack.addWidget(self.free_debate_timer_container)
        self.timer_stack.setCurrentIndex(0)  # 默认显示标准计时器
        
        # 将计时器堆栈添加到主布局
        main_layout.addLayout(self.timer_stack)
        
        # 添加下一环节信息
        next_round_frame = QFrame()
        next_round_frame.setStyleSheet("background-color: rgba(240, 240, 240, 0.5); border-radius: 5px;")
        next_round_layout = QVBoxLayout(next_round_frame)
        next_round_layout.setContentsMargins(5, 5, 5, 5)
        next_round_layout.setSpacing(2)
        
        next_label = QLabel("下一环节")
        next_label.setFont(QFont("微软雅黑", 10))
        next_label.setAlignment(Qt.AlignCenter)
        next_label.setStyleSheet("color: #605E5C;")
        
        self.next_round_info = QLabel("准备中...")
        self.next_round_info.setFont(QFont("微软雅黑", 12))
        self.next_round_info.setAlignment(Qt.AlignCenter)
        self.next_round_info.setStyleSheet("color: #323130; font-weight: bold;")
        
        next_round_layout.addWidget(next_label)
        next_round_layout.addWidget(self.next_round_info)
        main_layout.addWidget(next_round_frame)
        
        # 配置为无背景和边框
        self.active_round_widget_top.setAutoFillBackground(False)
        self.active_round_widget_top.setStyleSheet(
            "background-color: transparent; border: none;"
        )

        # Opacity effect for animation
        opacity_effect_active = QGraphicsOpacityEffect(self.active_round_widget_top)
        opacity_effect_active.setOpacity(1.0) # Start with full opacity, will be set to 0 before fade-in
        self.active_round_widget_top.setGraphicsEffect(opacity_effect_active)

    def _update_active_round_widget_top_content(self):
        if not self.current_round:
            return
        
        # 获取当前环节数据
        current_round = self.current_round
        side = "正方" if current_round['side'] == 'affirmative' else "反方"
        side_color = "#0078D4" if current_round['side'] == 'affirmative' else "#C42B1C"
        # 检查是否是自由辩论环节
        self.is_free_debate = current_round.get('type') == "自由辩论"
        
        total = max(current_round.get('time', 0), 1)
        
        if self.is_free_debate:
            # 自由辩论模式 - 设置双计时器
            half_time = total // 2
            # 正方计时器
            self.aff_progress_bar.setRange(0, half_time)
            self.aff_progress_bar.setValue(0)
            self.affirmative_time = half_time
            minutes = self.affirmative_time // 60
            seconds = self.affirmative_time % 60
            self.aff_countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
            
            # 反方计时器
            self.neg_progress_bar.setRange(0, half_time)
            self.neg_progress_bar.setValue(0)
            self.negative_time = half_time
            minutes = self.negative_time // 60
            seconds = self.negative_time % 60
            self.neg_countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
            
            # 切换到自由辩论计时器界面
            self.timer_stack.setCurrentIndex(1)
        else:
            # 标准模式 - 设置单个计时器
            self.active_progress_bar_top.setProgressColor(QColor(side_color))
            self.active_progress_bar_top.setRange(0, total)
            self.active_progress_bar_top.setValue(0)
            
            # 设置倒计时文本
            minutes = total // 60
            seconds = total % 60
            self.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
            
            # 切换到标准计时器界面
            self.timer_stack.setCurrentIndex(0)
            
            # 设置发言方信息
            speaker_info = f"{side} {current_round['speaker']} - {current_round['type']}"
            self.active_speaker_info.setText(speaker_info)
            self.active_speaker_info.setStyleSheet(f"color: {side_color}; font-weight: bold;")
            
            # 设置标题
            self.active_round_title.setText(current_round['description'] if 'description' in current_round else "当前环节")
        
        # 更新下一环节信息
        next_round_idx = self.current_round_index + 1
        if next_round_idx < len(self.rounds):
            next_round = self.rounds[next_round_idx]
            next_side = "正方" if next_round['side'] == 'affirmative' else "反方"
            next_info = f"{next_side}{next_round['speaker']} - {next_round['type']}"
            self.next_round_info.setText(next_info)
        else:
            self.next_round_info.setText("辩论结束")

    def toggle_timer(self):
        """开启或暂停计时器"""
        if self.is_free_debate:
            # 在自由辩论模式下，此方法不直接操作计时器
            logger.info("自由辩论模式下，请使用正方/反方专用计时器控制")
            return
        
        if self.timer_active:
            logger.info("计时器暂停")
            self.timer.stop()
            self.timer_active = False
        else:
            logger.info("计时器启动")
            if self.current_time > 0:
                self.timer.start(1000)
                self.timer_active = True
    
    def toggle_affirmative_timer(self):
        """开启或暂停正方计时器"""
        try:
            if not self.is_free_debate:
                logger.warning("非自由辩论模式不应调用正方计时器")
                return
            
            if self.affirmative_timer_active:
                logger.info("正方计时器暂停")
                self.timer.stop()
                self.affirmative_timer_active = False
                # 更新控制面板按钮状态
                if self.control_panel:
                    self.control_panel.aff_timer_btn.setText("开始")
                    self.control_panel.aff_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
            else:
                # 确保两个计时器不同时运行
                if self.negative_timer_active:
                    logger.info("停止反方计时，切换到正方")
                    self.timer.stop()
                    self.negative_timer_active = False
                    # 更新反方按钮状态
                    if self.control_panel:
                        self.control_panel.neg_timer_btn.setText("开始")
                        self.control_panel.neg_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
                
                logger.info("正方计时器启动")
                if self.affirmative_time > 0:
                    self.timer.start(1000)
                    self.affirmative_timer_active = True
                    # 更新控制面板按钮状态
                    if self.control_panel:
                        self.control_panel.aff_timer_btn.setText("暂停")
                        self.control_panel.aff_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPause")))
                else:
                    # 时间为0时给出提示
                    if self.control_panel:
                        QMessageBox.information(self.control_panel, "提示", "正方发言时间已用完")
        except Exception as e:
            logger.error(f"切换正方计时器时出错: {e}", exc_info=True)
    
    def toggle_negative_timer(self):
        """开启或暂停反方计时器"""
        try:
            if not self.is_free_debate:
                logger.warning("非自由辩论模式不应调用反方计时器")
                return
            
            if self.negative_timer_active:
                logger.info("反方计时器暂停")
                self.timer.stop()
                self.negative_timer_active = False
                # 更新控制面板按钮状态
                if self.control_panel:
                    self.control_panel.neg_timer_btn.setText("开始")
                    self.control_panel.neg_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
            else:
                # 确保两个计时器不同时运行
                if self.affirmative_timer_active:
                    logger.info("停止正方计时，切换到反方")
                    self.timer.stop()
                    self.affirmative_timer_active = False
                    # 更新正方按钮状态
                    if self.control_panel:
                        self.control_panel.aff_timer_btn.setText("开始")
                        self.control_panel.aff_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
                
                logger.info("反方计时器启动")
                if self.negative_time > 0:
                    self.timer.start(1000)
                    self.negative_timer_active = True
                    # 更新控制面板按钮状态
                    if self.control_panel:
                        self.control_panel.neg_timer_btn.setText("暂停")
                        self.control_panel.neg_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPause")))
                else:
                    # 时间为0时给出提示
                    if self.control_panel:
                        QMessageBox.information(self.control_panel, "提示", "反方发言时间已用完")
        except Exception as e:
            logger.error(f"切换反方计时器时出错: {e}", exc_info=True)

    def reset_timer(self, duration=None):
        logger.info("计时器重置")
        self.timer.stop()
        self.timer_active = False
        self.affirmative_timer_active = False
        self.negative_timer_active = False
        
        if self.is_free_debate:
            if duration is not None:
                half_time = duration // 2
                self.affirmative_time = half_time
                self.negative_time = half_time
            else:
                if self.current_round:
                    half_time = self.current_round.get('time', 0) // 2
                    self.affirmative_time = half_time
                    self.negative_time = half_time
                else:
                    self.affirmative_time = 0
                    self.negative_time = 0
        else:
            if duration is not None:
                self.current_time = duration
            else:
                if self.current_round:
                    self.current_time = self.current_round.get('time', 0)
                else:
                    self.current_time = 0
        self.update_timer_display()
    
    def terminate_current_round(self):
        """强制终止当前回合，停止所有计时器并返回预览模式"""
        logger.info("终止当前回合")
        try:
            # 停止所有计时器
            self.timer.stop()
            self.timer_active = False
            self.affirmative_timer_active = False
            self.negative_timer_active = False
            
            # 重置计时显示
            self.reset_timer(duration=0)
            
            # 切换到下一环节的预览
            next_idx = self.current_round_index + 1
            if next_idx < len(self.rounds):
                self._update_preview_widget_top_content(next_idx)
            else:
                self._update_preview_widget_top_content(self.current_round_index)
                
            # 动画过渡到预览模式
            self._animate_top_widget_transition(self.active_round_widget_top, self.preview_widget_top)
            self.topic_stack.setCurrentWidget(self.preview_widget_top)
            return True
        except Exception as e:
            logger.error(f"终止回合时出错: {e}", exc_info=True)
            return False

    def update_time(self):
        if self.is_free_debate:
            # 自由辩论模式：更新活动中的一方计时器
            if self.affirmative_timer_active and self.affirmative_time > 0:
                self.affirmative_time -= 1
                # 更新控制面板上的LCD显示
                if self.control_panel:
                    minutes = self.affirmative_time // 60
                    seconds = self.affirmative_time % 60
                    self.control_panel.aff_timer_lcd.display(f"{minutes:02d}:{seconds:02d}")
                
                if self.affirmative_time == 0:
                    logger.info("正方发言时间结束")
                    self.timer.stop()
                    self.affirmative_timer_active = False
                    # 更新控制面板按钮状态
                    if self.control_panel:
                        self.control_panel.aff_timer_btn.setText("开始")
                        self.control_panel.aff_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
                        self.control_panel.neg_timer_btn.setEnabled(True)
            
            elif self.negative_timer_active and self.negative_time > 0:
                self.negative_time -= 1
                # 更新控制面板上的LCD显示
                if self.control_panel:
                    minutes = self.negative_time // 60
                    seconds = self.negative_time % 60
                    self.control_panel.neg_timer_lcd.display(f"{minutes:02d}:{seconds:02d}")
                
                if self.negative_time == 0:
                    logger.info("反方发言时间结束")
                    self.timer.stop()
                    self.negative_timer_active = False
                    # 更新控制面板按钮状态
                    if self.control_panel:
                        self.control_panel.neg_timer_btn.setText("开始")
                        self.control_panel.neg_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
                        self.control_panel.aff_timer_btn.setEnabled(True)
            
            # 检查总体时间是否结束
            if self.affirmative_time == 0 and self.negative_time == 0:
                logger.info("自由辩论环节结束")
                self.timer.stop()
                next_round_idx = self.current_round_index + 1
                self._update_preview_widget_top_content(next_round_idx)
                self._animate_top_widget_transition(self.active_round_widget_top, self.preview_widget_top)
                
                # 更新控制面板状态
                if self.control_panel:
                    self.control_panel.aff_timer_btn.setEnabled(True)
                    self.control_panel.status_value.setText("自由辩论环节已结束")
        else:
            # 标准计时模式
            if self.current_time > 0:
                self.current_time -= 1
                if self.current_time == 0:
                    logger.info("当前环节倒计时结束")
                    self.timer.stop()
                    self.timer_active = False
                    next_round_idx = self.current_round_index + 1
                    self._update_preview_widget_top_content(next_round_idx)
                    self._animate_top_widget_transition(self.active_round_widget_top, self.preview_widget_top)
            
        self.update_timer_display()
    
    def update_timer_display(self):
        if self.is_free_debate:
            # 更新正方计时器()
            if hasattr(self, 'aff_progress_bar') and hasattr(self, 'aff_countdown_label'):
                total = self.current_round['time'] // 2
                current = total - self.affirmative_time
                self.aff_progress_bar._value = current
                self.aff_progress_bar.update()
                
                # 更新正方倒计时文本
                minutes = self.affirmative_time // 60
                seconds = self.affirmative_time % 60
                self.aff_countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
                
                # 当倒计时接近结束时改变文本颜色
                if self.affirmative_time <= 30:
                    self.aff_countdown_label.setStyleSheet("color: #C42B1C; font-weight: bold;")
                else:
                    self.aff_countdown_label.setStyleSheet("color: #323130; font-weight: bold;")
            
            # 更新反方计时器
            if hasattr(self, 'neg_progress_bar') and hasattr(self, 'neg_countdown_label'):
                total = self.current_round['time'] // 2
                current = total - self.negative_time
                self.neg_progress_bar._value = current
                self.neg_progress_bar.update()
                
                # 更新反方倒计时文本
                minutes = self.negative_time // 60
                seconds = self.negative_time % 60
                self.neg_countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
                
                # 当倒计时接近结束时改变文本颜色
                if self.negative_time <= 30:
                    self.neg_countdown_label.setStyleSheet("color: #C42B1C; font-weight: bold;")
                else:
                    self.neg_countdown_label.setStyleSheet("color: #323130; font-weight: bold;")
        else:
            # 标准模式计时器更新
            if self.current_round:
                total = self.current_round['time']
                current = total - self.current_time
                progress = current / total
            
                # 直接设置进度值
                self.active_progress_bar_top._value = current
                self.active_progress_bar_top.update()
                
                # 更新倒计时文本
                minutes = self.current_time // 60
                seconds = self.current_time % 60
                self.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
                
                # 当倒计时接近结束时，改变文本颜色提醒
                if self.current_time <= 30:
                    self.countdown_label.setStyleSheet("color: #C42B1C; font-weight: bold;")
                else:
                    self.countdown_label.setStyleSheet("color: #323130; font-weight: bold;")

    def _update_preview_widget_top_content(self, index=None):
        """更新预览控件内容，先清除旧内容再设置新内容
    
        Args:
            index: 要预览的环节索引，如果为None则使用下一个环节
        """
        if not self.rounds:
            return
        
        # 确定要显示的环节
        if index is None:
            index = self.current_round_index + 1
        
        # 防止索引越界
        if index < 0 or index >= len(self.rounds):
            logger.warning(f"环节索引 {index} 超出范围")
            return
            
        round_info = self.rounds[index]
        
        # 先清除所有标签内容
        self.preview_title_label.clear()
        self.preview_type_label.clear()
        self.preview_desc_label.clear()
        self.preview_time_label.clear()
        
        # 使用QTimer延迟一小段时间后再设置新内容，确保先前内容已清除
        QTimer.singleShot(10, lambda: self._set_preview_content(round_info, index))

    def _set_preview_content(self, round_info, index):
        """设置预览内容，在清除旧内容后调用"""
        # 设置标题和类型
        self.preview_title_label.setText("下一环节:")
        self.preview_type_label.setText(round_info['type'])
        # 如果是自由辩论，特别标记
        if round_info.get('type') == "自由辩论":
            self.preview_type_label.setStyleSheet("color: #D13438; font-weight: bold;")
        else:
            self.preview_type_label.setStyleSheet("color: #0078D4; font-weight: bold;")
        
        # 设置描述
        side = "正方" if round_info['side'] == 'affirmative' else "反方"
        self.preview_desc_label.setText(f"{side} {round_info['speaker']}")
        
        # 设置时间
        minutes = round_info['time'] // 60
        seconds = round_info['time'] % 60
        self.preview_time_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        # 更新下一环节信息
        next_round_idx = index + 1
        if next_round_idx < len(self.rounds):
            next_round = self.rounds[next_round_idx]
            next_side = "正方" if next_round['side'] == 'affirmative' else "反方"
            next_info = f"{next_side}{next_round['speaker']} - {next_round['type']}"
            self.next_round_info.setText(next_info)
        else:
            self.next_round_info.setText("辩论结束")

    def _animate_top_widget_transition(self, from_widget, to_widget):
        """动画过渡两个顶部显示控件，带有强制结束机制
    
        Args:
            from_widget: 当前显示的控件
            to_widget: 要切换到的控件
        """
        # 强制结束任何正在运行的动画
        if self.current_top_widget_anim:
            self.current_top_widget_anim.stop()
            self.current_top_widget_anim = None
    
        # 低性能模式下简化动画或直接切换
        if self.low_performance_mode:
            # 直接切换控件，不使用动画
            self.topic_stack.setCurrentWidget(to_widget)
            return
        
        # 确保两个控件的透明度效果正确初始化
        from_effect = from_widget.graphicsEffect()
        to_effect = to_widget.graphicsEffect()
    
        if not isinstance(from_effect, QGraphicsOpacityEffect):
            from_effect = QGraphicsOpacityEffect(from_widget)
            from_effect.setOpacity(1.0)
            from_widget.setGraphicsEffect(from_effect)
    
        if not isinstance(to_effect, QGraphicsOpacityEffect):
            to_effect = QGraphicsOpacityEffect(to_widget)
            to_effect.setOpacity(0.0)
            to_widget.setGraphicsEffect(to_effect)
    
        # 创建一个并行动画组
        anim_group = QParallelAnimationGroup(self)
    
        # 当前控件淡出效果
        fade_out = QPropertyAnimation(from_effect, b"opacity")
        fade_out.setDuration(300)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.OutCubic)
    
        # 目标控件淡入效果
        fade_in = QPropertyAnimation(to_effect, b"opacity")
        fade_in.setDuration(300)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.InCubic)
    
        # 添加动画到组
        anim_group.addAnimation(fade_out)
        anim_group.addAnimation(fade_in)
    
        # 切换到要显示的控件，确保它在动画开始时是可见的
        self.topic_stack.setCurrentWidget(to_widget)
    
        # 保存并启动动画组
        self.current_top_widget_anim = anim_group
        anim_group.start()

    def _update_preview_widget_top_content(self, index=None):
        """更新预览控件内容
        
        Args:
            index: 要预览的环节索引，如果为None则使用下一个环节
        """
        if not self.rounds:
            return
        
        # 确定要显示的环节
        if index is None:
            index = self.current_round_index + 1
        
        # 防止索引越界
        if index < 0 or index >= len(self.rounds):
            logger.warning(f"环节索引 {index} 超出范围")
            return
            
        round_info = self.rounds[index]
        
        # 设置标题和类型
        self.preview_title_label.setText("下一环节:")
        self.preview_type_label.setText(round_info['type'])
        # 如果是自由辩论，特别标记
        if round_info.get('type') == "自由辩论":
            self.preview_type_label.setStyleSheet("color: #D13438; font-weight: bold;")
        else:
            self.preview_type_label.setStyleSheet("color: #0078D4; font-weight: bold;")
        
        # 设置描述
        side = "正方" if round_info['side'] == 'affirmative' else "反方"
        self.preview_desc_label.setText(f"{side} {round_info['speaker']}")
        
        # 设置时间
        minutes = round_info['time'] // 60
        seconds = round_info['time'] % 60
        self.preview_time_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        # 更新下一环节信息
        next_round_idx = index + 1
        if next_round_idx < len(self.rounds):
            next_round = self.rounds[next_round_idx]
            next_side = "正方" if next_round['side'] == 'affirmative' else "反方"
            next_info = f"{next_side}{next_round['speaker']} - {next_round['type']}"
            self.next_round_info.setText(next_info)
        else:
            self.next_round_info.setText("辩论结束")
        
        # 切换到预览模式时，重置动画
        if self.topic_stack.currentWidget() == self.preview_widget_top:
            self.current_top_widget_anim = None
    
    def set_control_panel(self, control_panel):
        """设置控制面板引用"""
        logger.debug("设置控制面板引用")
        try:
            self.control_panel = control_panel
            # 连接控制面板的环节选择信号到本地槽
            if hasattr(control_panel, 'roundSelected'):
                control_panel.roundSelected.connect(self.onRoundSelected)
                
                # 如果控制面板已经加载了环节数据，更新预览内容
                if hasattr(control_panel, 'rounds_list') and control_panel.rounds_list.count() > 0:
                    index = control_panel.rounds_list.currentRow()
                    if index >= 0:
                        self._update_preview_widget_top_content(index)
            
        except Exception as e:
            logger.error(f"设置控制面板引用时出错: {e}", exc_info=True)

    def set_debate_config(self, config):
        """设置辩论配置信息
        
        Args:
            config: 包含辩论信息的字典，包括题目、学校、辩手和环节
        """
        logger.info("设置辩论配置")
        # 设置辩题和学校信息
        if 'topic' in config:
            self.topic = config['topic']
            self.setWindowTitle(f"辩论背景看板 - {self.topic}")
        
        # 设置正方信息
        if 'affirmative' in config:
            affirmative = config['affirmative']
            if 'school' in affirmative:
                self.affirmative_school = affirmative['school']
                self.affirmative_school_label.setText(self.affirmative_school)
            if 'viewpoint' in affirmative:
                self.affirmative_viewpoint = affirmative['viewpoint']
                # 调用高亮函数，并标记为富文本显示
                rich_html = highlight_markers(self.affirmative_viewpoint, "#0078D4")
                self.affirmative_viewpoint_label.setTextFormat(Qt.RichText)
                self.affirmative_viewpoint_label.setText(rich_html)
                
        # 设置反方信息
        if 'negative' in config:
            negative = config['negative']
            if 'school' in negative:
                self.negative_school = negative['school']
                self.negative_school_label.setText(self.negative_school)
            if 'viewpoint' in negative:
                self.negative_viewpoint = negative['viewpoint']
                # 调用高亮函数，并标记为富文本显示
                rich_html = highlight_markers(self.negative_viewpoint, "#D13438")
                self.negative_viewpoint_label.setTextFormat(Qt.RichText)
                self.negative_viewpoint_label.setText(rich_html)
                
        # 设置辩手角色映射
        if 'debater_roles' in config:
            self.debater_roles = config['debater_roles']
            # 更新辩手信息显示
            self.update_debaters_info()
        
        # 设置辩论环节
        if 'rounds' in config:
            self.rounds = config['rounds']
            self._update_preview_widget_top_content(0)
        logger.info("辩论配置已应用")
        return True

    def update_debaters_info(self):
        """将辩手信息映射到界面标签"""
        logger.debug("更新辩手信息")
        try:
            roles = self.debater_roles
            # 这里假设UI中已定义了相应标签，实际应根据具体UI布局调整
            if hasattr(self, 'chair_label') and 'chair' in roles:
                self.chair_label.setText(roles['chair'])
            if hasattr(self, 'recorder_label') and 'recorder' in roles:
                self.recorder_label.setText(roles['recorder'])
                
            # 添加正方辩手信息
            for i in range(1, 5):
                role_key = f"affirmative_{i}"
                if role_key in roles and hasattr(self, f'aff_{i}_label'):
                    getattr(self, f'aff_{i}_label').setText(roles[role_key])
                    
            # 添加反方辩手信息
            for i in range(1, 5):
                role_key = f"negative_{i}"
                if role_key in roles and hasattr(self, f'neg_{i}_label'):
                    getattr(self, f'neg_{i}_label').setText(roles[role_key])
            
            logger.debug("辩手信息更新完成")
        except Exception as e:
            logger.error(f"更新辩手信息时出错: {e}", exc_info=True)

    def start_round(self, index):
        """开始指定的辩论环节
        
        Args:
            index: 要开始的环节索引
        Returns:
            bool: 开始成功返回True，失败返回False
        """
        logger.info(f"开始环节: index={index}")
        if 0 <= index < len(self.rounds):
            self.current_round_index = index
            self.current_round = self.rounds[index]
            
            # 设置计时器
            self.current_time = self.current_round['time']
            # 配置活动控件
            self._update_active_round_widget_top_content()
            # 切换到活动视图
            self._animate_top_widget_transition(self.preview_widget_top, self.active_round_widget_top)
            self.topic_stack.setCurrentWidget(self.active_round_widget_top)
            # 发送环节变化信号
            self.roundChanged.emit(index)
            return True
        return False
    
    def next_round(self):
        """切换到下一个环节
        
        Returns:
            bool: 切换成功返回True，失败返回False
        """
        logger.info("切换到下一环节")
        next_index = self.current_round_index + 1
        if 0 <= next_index < len(self.rounds):
            self.current_round_index = next_index
            self._update_preview_widget_top_content(next_index)
            # 发送环节变化信号
            self.roundChanged.emit(next_index)
            return True
        return False
    
    def prev_round(self):
        """切换到上一个环节
        
        Returns:
            bool: 切换成功返回True，失败返回False
        """
        logger.info("切换到上一环节")
        prev_index = self.current_round_index - 1
        if prev_index >= 0:
            self.current_round_index = prev_index
            self._update_preview_widget_top_content(prev_index)
            # 发送环节变化信号
            self.roundChanged.emit(prev_index)
            return True
        return False

    def onRoundSelected(self, index):
        """响应控制端环节选择，更新预览视图或当前环节"""
        logger.info(f"收到环节选择信号: index={index}")
        try:
            # 更新预览内容
            self._update_preview_widget_top_content(index)
            
            # 如果不是在计时中，则可以直接切换到预览模式
            if not self.timer_active:
                self.topic_stack.setCurrentWidget(self.preview_widget_top)
        except Exception as e:
            logger.error(f"处理环节选择时出错: {e}", exc_info=True)

    def keyPressEvent(self, event):
        """处理键盘事件"""
        # F11 - 切换全屏
        if event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
                self.is_fullscreen = False
            else:
                self.showFullScreen()
                self.is_fullscreen = True
        # Esc - 退出全屏
        elif event.key() == Qt.Key_Escape and self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        """处理窗口大小变化事件"""
        # 调整背景和毛玻璃效果的大小
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.blur_effect.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)
