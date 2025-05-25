#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, QWidget, QFrame, 
                            QGraphicsDropShadowEffect, QStackedLayout, QSizePolicy, 
                            QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QGraphicsOpacityEffect

from utils import GradientBorderFrame, logger
from custom_progress_bar import RoundedProgressBar

class UIComponents:
    """UI组件创建和管理类"""
    
    def __init__(self, parent):
        self.parent = parent
        
    def create_topic_container(self):
        """创建顶部容器"""
        topic_container = QFrame()
        topic_container.setObjectName("topicContainer")
        topic_container.setStyleSheet("""
            #topicContainer {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        # 添加阴影效果
        topic_shadow = QGraphicsDropShadowEffect()
        topic_shadow.setBlurRadius(15)
        topic_shadow.setColor(QColor(0, 0, 0, 40))
        topic_shadow.setOffset(0, 2)
        topic_container.setGraphicsEffect(topic_shadow)
        
        return topic_container
    
    def create_preview_widget_top(self):
        """创建预览灵动岛控件"""
        logger.debug("创建预览灵动岛控件")
        
        preview_widget = QWidget()
        layout = QHBoxLayout(preview_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)

        # 创建标签
        preview_title_label = QLabel("下一环节:")
        preview_title_label.setFont(QFont("微软雅黑", 18, QFont.Bold))
        preview_title_label.setAlignment(Qt.AlignCenter)
        self._optimize_label_rendering(preview_title_label, "#323130")

        preview_type_label = QLabel("类型: N/A")
        preview_type_label.setFont(QFont("微软雅黑", 22, QFont.Bold))
        preview_type_label.setAlignment(Qt.AlignCenter)
        self._optimize_label_rendering(preview_type_label, "#0078D4")

        preview_desc_label = QLabel("描述: N/A")
        preview_desc_label.setFont(QFont("微软雅黑", 16))
        preview_desc_label.setAlignment(Qt.AlignCenter)
        preview_desc_label.setWordWrap(False)
        self._optimize_label_rendering(preview_desc_label, "#605E5C")
        
        preview_time_label = QLabel("时长: N/A")
        preview_time_label.setFont(QFont("微软雅黑", 16))
        preview_time_label.setAlignment(Qt.AlignCenter)
        self._optimize_label_rendering(preview_time_label, "#605E5C")

        layout.addWidget(preview_title_label)
        layout.addWidget(preview_type_label)
        layout.addWidget(preview_desc_label)
        layout.addWidget(preview_time_label)
        
        # 添加透明度效果
        opacity_effect = QGraphicsOpacityEffect(preview_widget)
        opacity_effect.setOpacity(1.0)
        preview_widget.setGraphicsEffect(opacity_effect)
        
        # 保存标签引用
        preview_widget.title_label = preview_title_label
        preview_widget.type_label = preview_type_label
        preview_widget.desc_label = preview_desc_label
        preview_widget.time_label = preview_time_label
        
        return preview_widget
    
    def create_active_round_widget_top(self):
        """创建倒计时灵动岛控件"""
        logger.debug("创建倒计时灵动岛控件")
        
        active_widget = QWidget()
        main_layout = QVBoxLayout(active_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # 当前环节标题
        active_round_title = QLabel("当前环节")
        active_round_title.setFont(QFont("微软雅黑", 16, QFont.Bold))
        active_round_title.setAlignment(Qt.AlignCenter)
        active_round_title.setStyleSheet("color: #323130;")
        main_layout.addWidget(active_round_title)
        
        # 发言者信息
        active_speaker_info = QLabel()
        active_speaker_info.setFont(QFont("微软雅黑", 14))
        active_speaker_info.setAlignment(Qt.AlignCenter)
        active_speaker_info.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(active_speaker_info)
        
        # 创建计时器容器
        timer_containers = self._create_timer_containers()
        timer_stack = QStackedLayout()
        timer_stack.addWidget(timer_containers['standard'])
        timer_stack.addWidget(timer_containers['free_debate'])
        timer_stack.setCurrentIndex(0)
        
        main_layout.addLayout(timer_stack)
        
        # 下一环节信息
        next_round_frame = self._create_next_round_frame()
        main_layout.addWidget(next_round_frame)
        
        # 设置样式
        active_widget.setAutoFillBackground(False)
        active_widget.setStyleSheet("background-color: transparent; border: none;")

        # 添加透明度效果
        opacity_effect = QGraphicsOpacityEffect(active_widget)
        opacity_effect.setOpacity(1.0)
        active_widget.setGraphicsEffect(opacity_effect)
        
        # 保存组件引用
        active_widget.round_title = active_round_title
        active_widget.speaker_info = active_speaker_info
        active_widget.timer_stack = timer_stack
        active_widget.timer_containers = timer_containers
        active_widget.next_round_frame = next_round_frame
        
        return active_widget
    
    def _create_timer_containers(self):
        """创建计时器容器"""
        # 标准计时器容器
        standard_container = QWidget()
        timer_layout = QHBoxLayout(standard_container)
        timer_layout.setContentsMargins(0, 0, 0, 0)
        timer_layout.setSpacing(10)
        timer_layout.setAlignment(Qt.AlignCenter)
        
        standard_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # 创建环形进度条
        size = 80
        progress_bar = RoundedProgressBar()
        progress_bar.setFixedSize(size, size)
        progress_bar.setLineWidth(4)
        progress_bar.setProgressColor(QColor("#0078D4"))
        progress_bar.setTextColor(QColor("#323130"))
        
        countdown_label = QLabel()
        countdown_label.setFont(QFont("微软雅黑", 24, QFont.Bold))
        countdown_label.setAlignment(Qt.AlignCenter)
        countdown_label.setStyleSheet("color: #323130;")
        
        timer_layout.addWidget(progress_bar)
        timer_layout.addWidget(countdown_label)
        
        standard_container.progress_bar = progress_bar
        standard_container.countdown_label = countdown_label
        
        # 自由辩论计时器容器
        free_debate_container = self._create_free_debate_timers(size)
        
        return {
            'standard': standard_container,
            'free_debate': free_debate_container
        }
    
    def _create_free_debate_timers(self, size):
        """创建自由辩论双计时器"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)
        
        # 正方计时器组
        aff_group = self._create_timer_group("正方", "#0078D4", size)
        neg_group = self._create_timer_group("反方", "#C42B1C", size)
        
        layout.addWidget(aff_group)
        layout.addWidget(neg_group)
        
        container.aff_group = aff_group
        container.neg_group = neg_group
        
        return container
    
    def _create_timer_group(self, title, color, size):
        """创建单个计时器组"""
        group = QWidget()
        group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(group)
        
        # 标题
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("微软雅黑", 12, QFont.Bold))
        title_label.setStyleSheet(f"color: {color};")
        
        # 计时器布局
        timer_box = QHBoxLayout()
        
        # 进度条
        progress_bar = RoundedProgressBar()
        progress_bar.setFixedSize(size, size)
        progress_bar.setLineWidth(4)
        progress_bar.setProgressColor(QColor(color))
        progress_bar.setTextColor(QColor("#323130"))
        
        # 倒计时标签
        countdown_label = QLabel()
        countdown_label.setFont(QFont("微软雅黑", 20, QFont.Bold))
        countdown_label.setAlignment(Qt.AlignCenter)
        countdown_label.setStyleSheet("color: #323130;")
        
        timer_box.addWidget(progress_bar)
        timer_box.addWidget(countdown_label)
        layout.addWidget(title_label)
        layout.addLayout(timer_box)
        
        # 保存组件引用
        group.progress_bar = progress_bar
        group.countdown_label = countdown_label
        
        return group
    
    def _create_next_round_frame(self):
        """创建下一环节信息框"""
        frame = QFrame()
        frame.setStyleSheet("background-color: rgba(240, 240, 240, 0.5); border-radius: 5px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        next_label = QLabel("下一环节")
        next_label.setFont(QFont("微软雅黑", 10))
        next_label.setAlignment(Qt.AlignCenter)
        next_label.setStyleSheet("color: #605E5C;")
        
        next_round_info = QLabel("准备中...")
        next_round_info.setFont(QFont("微软雅黑", 12))
        next_round_info.setAlignment(Qt.AlignCenter)
        next_round_info.setStyleSheet("color: #323130; font-weight: bold;")
        
        layout.addWidget(next_label)
        layout.addWidget(next_round_info)
        
        frame.next_round_info = next_round_info
        return frame
    
    def create_side_widget(self, side_type):
        """创建正方或反方部件"""
        if side_type == 'affirmative':
            color_primary = "#0078D4"
            color_secondary = "#50B0E0"
            title = "正方"
        else:
            color_primary = "#D13438"
            color_secondary = "#E85A5E"
            title = "反方"
        
        widget = GradientBorderFrame(start_color=color_primary, end_color=color_secondary)
        widget.setObjectName(f"{side_type}Widget")
        widget.setStyleSheet(f"""
            #{side_type}Widget {{
                background-color: white;
                border-radius: 12px;
            }}
        """)
        
        # 添加阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 4)
        widget.setGraphicsEffect(shadow)
        
        # 创建布局和内容
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("微软雅黑", 48, QFont.Bold))
        title_label.setStyleSheet(f"color: {color_primary};")
        
        # 学校标签
        school_label = QLabel("")
        school_label.setAlignment(Qt.AlignCenter)
        school_label.setFont(QFont("微软雅黑", 20))
        school_label.setStyleSheet(f"color: {color_primary};")
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"background-color: rgba({self._hex_to_rgb(color_primary)}, 0.3); margin: 10px 30px;")
        separator.setFixedHeight(2)
        
        # 观点标签
        viewpoint_label = QLabel("")
        viewpoint_label.setAlignment(Qt.AlignCenter)
        viewpoint_label.setWordWrap(True)
        viewpoint_label.setFont(QFont("微软雅黑", 16))
        viewpoint_label.setStyleSheet("color: #323130;")
        
        layout.addWidget(title_label)
        layout.addWidget(school_label)
        layout.addWidget(separator)
        layout.addWidget(viewpoint_label)
        
        # 创建辩手信息框
        debaters_frame = self._create_debaters_frame(side_type, color_primary)
        layout.addWidget(debaters_frame)
        layout.addStretch()
        
        # 保存组件引用
        widget.school_label = school_label
        widget.viewpoint_label = viewpoint_label
        widget.debaters_frame = debaters_frame
        
        return widget
    
    def _create_debaters_frame(self, side_type, color):
        """创建辩手信息框"""
        frame = QFrame()
        rgb = self._hex_to_rgb(color)
        frame.setStyleSheet(f"""
            background-color: rgba({rgb}, 0.15); 
            border-radius: 10px; 
            padding: 10px;
            border: 2px solid rgba({rgb}, 0.3);
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("辩手阵容")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("微软雅黑", 16, QFont.Bold))
        title.setStyleSheet(f"color: {color}; border: none;")
        layout.addWidget(title)
        
        # 辩手网格
        grid = QGridLayout()
        grid.setSpacing(15)
        grid.setVerticalSpacing(20)
        
        # 创建辩手标签
        debater_labels = {}
        positions = [(0, 0), (0, 2), (1, 0), (1, 2)]
        role_positions = [(0, 1), (0, 3), (1, 1), (1, 3)]
        
        for i, (pos, role_pos) in enumerate(zip(positions, role_positions), 1):
            # 角色标签
            role_label = QLabel(f"{['一', '二', '三', '四'][i-1]}辩")
            role_label.setFont(QFont("微软雅黑", 13, QFont.Bold))
            role_label.setStyleSheet(f"""
                color: white; 
                background-color: {color}; 
                padding: 3px 8px;
                border-radius: 4px;
            """)
            role_label.setAlignment(Qt.AlignCenter)
            role_label.setFixedWidth(60)
            
            # 姓名标签
            name_label = QLabel("待定")
            name_label.setFont(QFont("微软雅黑", 14))
            name_label.setStyleSheet("letter-spacing: 1px;")
            name_label.setAlignment(Qt.AlignCenter)
            
            grid.addWidget(role_label, pos[0], pos[1])
            grid.addWidget(name_label, role_pos[0], role_pos[1])
            
            debater_labels[f'{side_type}_{i}'] = name_label
        
        layout.addLayout(grid)
        frame.debater_labels = debater_labels
        
        return frame
    
    def _hex_to_rgb(self, hex_color):
        """转换十六进制颜色到RGB字符串"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"
    
    def _optimize_label_rendering(self, label, color):
        """优化标签渲染效果"""
        label.setStyleSheet(f"color: {color};")
        label.setAttribute(Qt.WA_TranslucentBackground, True)
        label.setContentsMargins(0, 0, 0, 0)
