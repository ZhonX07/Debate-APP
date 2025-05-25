#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QGridLayout, QFrame, 
                            QFileDialog, QMessageBox, QGraphicsDropShadowEffect, 
                            QGroupBox, QStyle, QListWidget, QStackedLayout, QLCDNumber)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

import os
import logging
from typing import Dict, Any, Optional

# 导入自定义模块
from utils import logger
from config_manager import DebateConfig, ConfigValidationError

class ControlPanel(QMainWindow): 
    """后台控制窗口，用于管理辩论计时和设置"""
    
    # 定义自定义信号
    roundSelected = pyqtSignal(int)
    roundTerminated = pyqtSignal()  # 回合终止信号
    
    def __init__(self, display_board):
        super().__init__()
        logger.info("ControlPanel 初始化")
        self.display_board = display_board
        self.title = "辩论控制面板"
        self.current_config_file = ""
        self.debate_config = None
        self.is_free_debate = False  # 标记当前是否为自由辩论回合
        
        self.setStyleSheet("""
            QMainWindow { background-color: #F5F5F5; }
            QLabel { color: #323130; }
            QPushButton { background-color: #0078D4; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; min-height: 32px; }
            QPushButton:hover { background-color: #106EBE; }
            QPushButton:pressed { background-color: #005A9E; }
            QPushButton:disabled { background-color: #C8C8C8; color: #6E6E6E; }
            QListWidget { background-color: white; border: 1px solid #E1DFDD; border-radius: 4px; padding: 5px; }
            QListWidget::item { padding: 8px; border-radius: 4px; }
            QListWidget::item:selected { background-color: #E1EFFF; color: #0078D4; }
            QListWidget::item:hover:!selected { background-color: #F3F2F1; }
        """)
        self.initUI()
        logger.info("ControlPanel UI 初始化完成")

    def initUI(self):
        logger.debug("ControlPanel.initUI 开始")
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 900, 650)
        
        # 创建中央部件来承载布局
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setStyleSheet("#headerFrame { background-color: white; border-radius: 8px; border-left: 4px solid #0078D4; }")
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(15)
        header_shadow.setColor(QColor(0, 0, 0, 30))
        header_shadow.setOffset(0, 2)
        header_frame.setGraphicsEffect(header_shadow)
        header_layout = QVBoxLayout(header_frame)
        title_label = QLabel("辩论赛控制系统")
        title_label.setFont(QFont("微软雅黑", 16, QFont.Bold))
        title_label.setStyleSheet("color: #0078D4; margin-bottom: 5px;")
        config_layout = QHBoxLayout()
        config_layout.setContentsMargins(0, 5, 0, 5)
        load_config_btn = QPushButton("加载配置文件")
        load_config_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_DialogOpenButton")))
        load_config_btn.setStyleSheet("QPushButton { background-color: #0078D4; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold; }")
        load_config_btn.clicked.connect(self.load_config)
        load_config_btn.setFixedWidth(150)
        self.config_path_label = QLabel("未加载配置文件")
        self.config_path_label.setStyleSheet("color: #605E5C; padding: 0px 10px;")
        config_layout.addWidget(load_config_btn)
        config_layout.addWidget(self.config_path_label, 1)
        header_layout.addWidget(title_label)
        header_layout.addLayout(config_layout)
        main_layout.addWidget(header_frame)
        
        # 内容区域
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # 左侧面板（环节列表）
        rounds_frame = QFrame()
        rounds_frame.setObjectName("roundsFrame")
        rounds_frame.setStyleSheet("#roundsFrame { background-color: white; border-radius: 8px; }")
        rounds_shadow = QGraphicsDropShadowEffect()
        rounds_shadow.setBlurRadius(15)
        rounds_shadow.setColor(QColor(0, 0, 0, 30))
        rounds_shadow.setOffset(0, 2)
        rounds_frame.setGraphicsEffect(rounds_shadow)
        rounds_layout = QVBoxLayout(rounds_frame)
        rounds_header = QLabel("辩论流程")
        rounds_header.setFont(QFont("微软雅黑", 14, QFont.Bold))
        rounds_header.setStyleSheet("color: #323130; margin-bottom: 10px;")
        self.rounds_list = QListWidget()
        self.rounds_list.setFont(QFont("微软雅黑", 12))
        self.rounds_list.currentRowChanged.connect(self.on_round_selected)
        self.rounds_list.setAlternatingRowColors(True)
        self.rounds_list.setStyleSheet("QListWidget { alternate-background-color: #FAFAFA; }")
        rounds_layout.addWidget(rounds_header)
        rounds_layout.addWidget(self.rounds_list)
        content_layout.addWidget(rounds_frame)
        
        # 右侧面板（控制区）
        controls_frame = QFrame()
        controls_frame.setObjectName("controlsFrame")
        controls_frame.setStyleSheet("#controlsFrame { background-color: white; border-radius: 8px; }")
        controls_shadow = QGraphicsDropShadowEffect()
        controls_shadow.setBlurRadius(15)
        controls_shadow.setColor(QColor(0, 0, 0, 30))
        controls_shadow.setOffset(0, 2)
        controls_frame.setGraphicsEffect(controls_shadow)
        controls_layout = QVBoxLayout(controls_frame)
        controls_header = QLabel("控制面板")
        controls_header.setFont(QFont("微软雅黑", 14, QFont.Bold))
        controls_header.setStyleSheet("color: #323130; margin-bottom: 10px;")
        controls_layout.addWidget(controls_header)
        
        # 当前环节信息框
        current_round_frame = QFrame()
        current_round_frame.setStyleSheet("QFrame { background-color: #F0F8FF; border-radius: 6px; padding: 10px; }")
        current_round_layout = QVBoxLayout(current_round_frame)
        current_round_layout.setContentsMargins(15, 15, 15, 15)
        self.current_round_label = QLabel("未选择环节")
        self.current_round_label.setFont(QFont("微软雅黑", 12, QFont.Bold))
        self.current_round_label.setStyleSheet("color: #0078D4;")
        self.current_time_label = QLabel("时长: 0分钟")
        self.current_time_label.setFont(QFont("微软雅黑", 11))
        self.current_time_label.setStyleSheet("color: #605E5E;")
        self.current_time_label.setAlignment(Qt.AlignCenter)
        current_round_layout.addWidget(self.current_round_label)
        current_round_layout.addWidget(self.current_time_label)
        controls_layout.addWidget(current_round_frame)
        
        # 导航按钮
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 10, 0, 10)
        self.prev_btn = QPushButton("上一环节")
        self.prev_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_ArrowLeft")))
        self.prev_btn.clicked.connect(self.prev_round)
        self.next_btn = QPushButton("下一环节")
        self.next_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_ArrowRight")))
        self.next_btn.setLayoutDirection(Qt.RightToLeft)
        self.next_btn.clicked.connect(self.next_round)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        controls_layout.addLayout(nav_layout)
        
        # 开始当前环节按钮
        start_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始当前环节")
        self.start_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
        self.start_btn.setStyleSheet("QPushButton { background-color: #107C10; font-size: 14px; min-height: 40px; } QPushButton:hover { background-color: #0B6A0B; } QPushButton:pressed { background-color: #094509; }")
        self.start_btn.clicked.connect(self.start_current_round)
        start_layout.addWidget(self.start_btn)
        controls_layout.addLayout(start_layout)
        
        # 计时器控制组
        timer_group = QGroupBox("计时器控制")
        timer_group.setStyleSheet("QGroupBox { font-size: 12px; font-weight: bold; border: 1px solid #E1DFDD; border-radius: 6px; margin-top: 15px; padding-top: 15px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 10px; }")
        timer_layout = QVBoxLayout(timer_group)
        
        # 标准模式计时器控制
        self.standard_timer_controls = QWidget()
        standard_timer_layout = QHBoxLayout(self.standard_timer_controls)
        standard_timer_layout.setContentsMargins(0, 0, 0, 0)
        standard_timer_layout.setSpacing(10)
        standard_timer_layout.setAlignment(Qt.AlignCenter)
        
        self.timer_control_btn = QPushButton("开始/暂停计时")
        self.timer_control_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPause")))
        self.timer_control_btn.setStyleSheet("QPushButton { background-color: #5C2D91; } QPushButton:hover { background-color: #4B2477; } QPushButton:pressed { background-color: #3A1B5E; }")
        self.timer_control_btn.clicked.connect(self.toggle_timer)
        
        self.reset_timer_btn = QPushButton("重置计时")
        self.reset_timer_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaStop")))
        self.reset_timer_btn.setStyleSheet("QPushButton { background-color: #D13438; } QPushButton:hover { background-color: #BA2B2F; } QPushButton:pressed { background-color: #A42427; }")
        self.reset_timer_btn.clicked.connect(self.reset_timer)
        
        standard_timer_layout.addWidget(self.timer_control_btn)
        standard_timer_layout.addWidget(self.reset_timer_btn)
        
        # 自由辩论计时器控制
        self.free_debate_timer_controls = QWidget()
        free_debate_layout = QVBoxLayout(self.free_debate_timer_controls)
        free_debate_layout.setContentsMargins(0, 0, 0, 0)
        
        # 正方计时器控制
        aff_timer_controls = QHBoxLayout()
        self.aff_timer_lcd = QLCDNumber()
        self.aff_timer_lcd.setDigitCount(5)  # MM:SS
        self.aff_timer_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.aff_timer_lcd.display("00:00")
        self.aff_timer_lcd.setStyleSheet("background-color: #E1EFFF; color: #0078D4; border: none;")
        self.aff_timer_btn = QPushButton("正方计时")
        self.aff_timer_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
        self.aff_timer_btn.setStyleSheet("QPushButton { background-color: #0078D4; } QPushButton:hover { background-color: #106EBE; } QPushButton:pressed { background-color: #005A9E; }")
        self.aff_timer_btn.clicked.connect(self.toggle_affirmative_timer)
        
        aff_timer_controls.addWidget(self.aff_timer_lcd)
        aff_timer_controls.addWidget(self.aff_timer_btn)
        
        free_debate_layout.addLayout(aff_timer_controls)
        
        # 反方计时器控制
        neg_timer_controls = QHBoxLayout()
        self.neg_timer_lcd = QLCDNumber()
        self.neg_timer_lcd.setDigitCount(5)  # MM:SS
        self.neg_timer_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.neg_timer_lcd.display("00:00")
        self.neg_timer_lcd.setStyleSheet("background-color: #FFEDED; color: #D13438; border: none;")
        self.neg_timer_btn = QPushButton("反方计时")
        self.neg_timer_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
        self.neg_timer_btn.setStyleSheet("QPushButton { background-color: #D13438; } QPushButton:hover { background-color: #BA2B2F; } QPushButton:pressed { background-color: #A42427; }")
        self.neg_timer_btn.clicked.connect(self.toggle_negative_timer)
        
        neg_timer_controls.addWidget(self.neg_timer_lcd)
        neg_timer_controls.addWidget(self.neg_timer_btn)
        
        free_debate_layout.addLayout(neg_timer_controls)
        
        # 自由辩论重置按钮
        self.reset_free_debate_btn = QPushButton("重置计时")
        self.reset_free_debate_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaStop")))
        self.reset_free_debate_btn.setStyleSheet("QPushButton { background-color: #D13438; } QPushButton:hover { background-color: #BA2B2F; } QPushButton:pressed { background-color: #A42427; }")
        self.reset_free_debate_btn.clicked.connect(self.reset_timer)
        
        free_debate_layout.addWidget(self.reset_free_debate_btn)
        
        # 计时器控制堆栈
        self.timer_controls_stack = QStackedLayout()
        self.timer_controls_stack.addWidget(self.standard_timer_controls)
        self.timer_controls_stack.addWidget(self.free_debate_timer_controls)
        self.timer_controls_stack.setCurrentIndex(0)  # 默认标准计时器
        
        timer_layout.addLayout(self.timer_controls_stack)
        
        # 添加终止按钮
        self.terminate_round_btn = QPushButton("结束回合")
        self.terminate_round_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_DialogCancelButton")))
        self.terminate_round_btn.setStyleSheet("QPushButton { background-color: #D83B01; } QPushButton:hover { background-color: #B83301; } QPushButton:pressed { background-color: #A32D01; }")
        self.terminate_round_btn.clicked.connect(self.terminate_current_round)
        timer_layout.addWidget(self.terminate_round_btn)
        
        controls_layout.addWidget(timer_group)
        content_layout.addWidget(controls_frame, 2)  # 2倍宽度
        main_layout.addLayout(content_layout)
        
        # 底部状态栏
        status_frame = QFrame()
        status_frame.setStyleSheet("QFrame { background-color: #F3F2F1; border-radius: 4px; }")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 5, 10, 5)
        status_label = QLabel("辩论状态:")
        status_label.setFont(QFont("微软雅黑", 10))
        status_label.setAlignment(Qt.AlignLeft)
        status_label.setStyleSheet("color: #323130;")
        self.status_value = QLabel("就绪")
        self.status_value.setFont(QFont("微软雅黑", 10))
        self.status_value.setStyleSheet("color: #107C10;")
        shortcuts_label = QLabel("快捷键: F11-切换全屏 | ESC-关闭")
        shortcuts_label.setFont(QFont("微软雅黑", 10))
        shortcuts_label.setAlignment(Qt.AlignRight)
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_value)
        status_layout.addStretch()
        status_layout.addWidget(shortcuts_label)
        main_layout.addWidget(status_frame, 0)  # 0意味着尽量减少高度

        # 初始化时禁用所有控制
        self.disable_controls()
        logger.debug("ControlPanel.initUI 结束")
    
    def load_config(self):
        """加载配置文件"""
        logger.info("加载配置文件")
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "JSON Files (*.json)", options=options
        )
        if file_path:
            try:
                # 清除所有相关区域内容
                self.rounds_list.clear()
                self.current_round_label.setText("未选择环节")
                self.current_time_label.setText("时长: 0分钟")
                self.status_value.setText("就绪")
                
                # 读取并验证配置文件
                config = DebateConfig.from_file(file_path)
                self.debate_config = config
                self.current_config_file = file_path
                self.config_path_label.setText(os.path.basename(file_path))
                
                # 更新显示面板配置
                self.display_board.set_debate_config(config.to_dict())
                
                # 更新环节列表
                self.rounds_list.clear()
                for index, round_info in enumerate(config.get_rounds()):
                    side = "正方" if round_info['side'] == 'affirmative' else "反方"
                    item_text = f"{index+1}. [{side}] {round_info['speaker']} - {round_info['type']} ({round_info['time']}秒)"
                    self.rounds_list.addItem(item_text)
                
                # 启用控制按钮
                self.enable_controls()
                self.status_value.setText("配置已加载")
                logger.info(f"配置文件加载成功: {file_path}")
                
                # 选择第一个环节
                if self.rounds_list.count() > 0:
                    self.rounds_list.setCurrentRow(0)
                    
            except ConfigValidationError as e:
                QMessageBox.critical(self, "配置错误", f"配置文件验证失败:\n{e}")
                logger.error(f"配置文件验证失败: {e}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法加载配置文件:\n{e}")
                logger.error(f"加载配置文件失败: {e}", exc_info=True)
    
    def load_config_from_path(self, file_path):
        """从指定路径加载配置文件
        
        Args:
            file_path: 配置文件路径
        """
        if not os.path.exists(file_path):
            logger.error(f"配置文件不存在: {file_path}")
            QMessageBox.critical(self, "错误", f"找不到配置文件: {file_path}")
            return False
        
        try:
            # 清除所有相关区域内容
            self.rounds_list.clear()
            self.current_round_label.setText("未选择环节")
            self.current_time_label.setText("时长: 0分钟")
            self.status_value.setText("就绪")
            
            # 读取并验证配置文件
            config = DebateConfig.from_file(file_path)
            self.debate_config = config
            self.current_config_file = file_path
            self.config_path_label.setText(os.path.basename(file_path))
            
            # 更新显示面板配置
            self.display_board.set_debate_config(config.to_dict())
            
            # 更新环节列表
            self.rounds_list.clear()
            for index, round_info in enumerate(config.get_rounds()):
                side = "正方" if round_info['side'] == 'affirmative' else "反方"
                item_text = f"{index+1}. [{side}] {round_info['speaker']} - {round_info['type']} ({round_info['time']}秒)"
                self.rounds_list.addItem(item_text)
            
            # 启用控制按钮
            self.enable_controls()
            self.status_value.setText("配置已加载")
            logger.info(f"配置文件加载成功: {file_path}")
            
            # 选择第一个环节
            if self.rounds_list.count() > 0:
                self.rounds_list.setCurrentRow(0)
                
            # 添加检查辩手信息是否正确加载的日志
            if 'debater_roles' in config.to_dict():
                roles = config.to_dict()['debater_roles']
                logger.info(f"已加载辩手信息: {len(roles)} 条记录")
            
            return True
                
        except ConfigValidationError as e:
            QMessageBox.critical(self, "配置错误", f"配置文件验证失败:\n{e}")
            logger.error(f"配置文件验证失败: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载配置文件:\n{e}")
            logger.error(f"加载配置文件失败: {e}", exc_info=True)
        
        return False
    
    def disable_controls(self):
        """禁用所有控制，直到加载配置"""
        logger.info("禁用所有控制")
        
        # 计时器相关按钮
        self.timer_control_btn.setEnabled(False)
        self.reset_timer_btn.setEnabled(False)
        self.aff_timer_btn.setEnabled(False)
        self.neg_timer_btn.setEnabled(False)
        self.reset_free_debate_btn.setEnabled(False)
        self.terminate_round_btn.setEnabled(False)
        
        # 导航按钮
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        
    def enable_controls(self):
        """启用所有控制"""
        logger.info("启用所有控制")
        # 计时器相关
        self.timer_control_btn.setEnabled(True)
        self.reset_timer_btn.setEnabled(True)
        self.aff_timer_btn.setEnabled(True)
        self.neg_timer_btn.setEnabled(True)
        self.reset_free_debate_btn.setEnabled(True)
        self.terminate_round_btn.setEnabled(True)
        # 导航按钮
        self.prev_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
    
    def prev_round(self):
        """切换到上一个环节：更新选中行并发射信号"""
        logger.info("切换到上一环节")
        current = self.rounds_list.currentRow()
        if current > 0:
            new_index = current - 1
            self.rounds_list.setCurrentRow(new_index)
            self.roundSelected.emit(new_index)
            logger.info(f"切换到上一环节: {new_index}")

    def next_round(self):
        """切换到下一个环节：更新选中行并发射信号"""
        logger.info("切换到下一环节")
        current = self.rounds_list.currentRow()
        if current < self.rounds_list.count() - 1:
            new_index = current + 1
            self.rounds_list.setCurrentRow(new_index)
            self.roundSelected.emit(new_index)
            logger.info(f"切换到下一环节: {new_index}")

    def on_round_selected(self, index):
        """当环节列表中的选中项变化时触发"""
        try:
            if index >= 0 and self.debate_config:
                rounds = self.debate_config.get_rounds()
                round_info = rounds[index]
                side = "正方" if round_info['side'] == 'affirmative' else "反方"
                time_min = round_info['time'] // 60
                time_sec = round_info['time'] % 60
                self.current_round_label.setText(f"{side} {round_info['speaker']} - {round_info['type']}")
                self.current_time_label.setText(f"时长: {time_min}分{time_sec}秒")
                
                # 检查是否为自由辩论环节
                self.is_free_debate = round_info.get('type') == "自由辩论"
                
                # 更新计时器控制界面
                if self.is_free_debate:
                    # 显示自由辩论计时器控制
                    self.timer_controls_stack.setCurrentIndex(1)
                    half_time = round_info['time'] // 2
                    min_half = half_time // 60
                    sec_half = half_time % 60
                    self.aff_timer_lcd.display(f"{min_half:02d}:{sec_half:02d}")
                    self.neg_timer_lcd.display(f"{min_half:02d}:{sec_half:02d}")
                else:
                    # 显示标准计时器控制
                    self.timer_controls_stack.setCurrentIndex(0)
                
                # 发射信号通知显示板更新预览
                self.roundSelected.emit(index)
                logger.debug(f"已选择环节: {index}")
        except Exception as e:
            logger.error(f"处理环节选择时出错: {e}", exc_info=True)

    def start_current_round(self):
        """开始当前选中环节"""
        index = self.rounds_list.currentRow()
        if index < 0:
            QMessageBox.warning(self, "提示", "请先选择一个环节！")
            return
        # 调用显示面板的start_round方法
        if self.display_board.start_round(index):
            self.status_value.setText(f"已开始第{index+1}个环节")
            # 根据环节类型设置计时器控制界面
            if self.is_free_debate:
                self.timer_controls_stack.setCurrentIndex(1)
            else:
                self.timer_controls_stack.setCurrentIndex(0)
        else:
            QMessageBox.warning(self, "提示", "无法开始该环节！")

    def toggle_timer(self):
        """开始/暂停计时"""
        if self.display_board:
            self.display_board.toggle_timer()
            # 更新按钮状态
            if self.display_board.timer_active:
                self.timer_control_btn.setText("暂停计时")
                self.timer_control_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPause")))
                self.status_value.setText("计时中...")
            else:
                self.timer_control_btn.setText("继续计时")
                self.timer_control_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
                self.status_value.setText("计时已暂停")

    def toggle_affirmative_timer(self):
        """正方计时器控制"""
        if self.display_board:
            self.display_board.toggle_affirmative_timer()
            # 按钮状态将在DisplayBoard中处理

    def toggle_negative_timer(self):
        """反方计时器控制"""
        if self.display_board:
            self.display_board.toggle_negative_timer()
            # 按钮状态将在DisplayBoard中处理

    def reset_timer(self):
        """重置计时器"""
        if self.display_board:
            self.display_board.reset_timer()
            self.timer_control_btn.setText("开始计时")
            self.timer_control_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
            self.status_value.setText("计时已重置")
            
            # 重置自由辩论LCD显示
            if self.is_free_debate and hasattr(self, 'debate_config'):
                current_round = self.debate_config.get_rounds()[self.rounds_list.currentRow()]
                half_time = current_round['time'] // 2
                min_half = half_time // 60
                sec_half = half_time % 60
                self.aff_timer_lcd.display(f"{min_half:02d}:{sec_half:02d}")
                self.neg_timer_lcd.display(f"{min_half:02d}:{sec_half:02d}")

    def terminate_current_round(self):
        """终止当前回合"""
        try:
            if not self.display_board:
                logger.warning("显示面板未连接，无法终止当前回合")
                return
                
            logger.info("请求终止当前回合")
            if self.display_board.terminate_current_round():
                self.status_value.setText("回合已终止")
                # 更新控制面板状态
                index = self.rounds_list.currentRow()
                next_index = index + 1
                if next_index < self.rounds_list.count():
                    self.rounds_list.setCurrentRow(next_index)
                self.roundTerminated.emit()
        except Exception as e:
            logger.error(f"终止当前回合时出错: {e}", exc_info=True)

    def keyPressEvent(self, event):
        """处理键盘事件"""
        # Enter键 - 开始当前环节
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.start_btn.isEnabled():
                self.start_current_round()
        # 空格键 - 开始/暂停计时
        elif event.key() == Qt.Key_Space:
            if self.timer_control_btn.isEnabled():
                self.toggle_timer()
        # Esc键 - 关闭窗口
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
