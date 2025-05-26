#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QGridLayout, QFrame, 
                            QFileDialog, QMessageBox, QGraphicsDropShadowEffect, 
                            QGroupBox, QStyle, QListWidget, QStackedLayout, QLCDNumber,
                            QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
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
    
    def load_config_from_path(self, file_path):
        """从指定路径加载配置文件"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"配置文件不存在: {file_path}")
                return False
                
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

            # 获取回合数据并验证
            rounds_data = config.get_rounds()
            logger.info(f"配置文件包含 {len(rounds_data)} 个回合")
            
            if not rounds_data:
                logger.warning("配置文件中没有回合数据")
                QMessageBox.warning(self, "警告", "配置文件中没有找到回合信息")
                return False
            
            # 更新环节列表
            self.rounds_list.clear()
            for index, round_info in enumerate(rounds_data):
                try:
                    # 验证回合数据完整性
                    if not isinstance(round_info, dict):
                        logger.error(f"回合 {index+1} 数据格式错误")
                        continue
                        
                    side = round_info.get('side', '')
                    speaker = round_info.get('speaker', '')
                    round_type = round_info.get('type', '')
                    time_seconds = round_info.get('time', 0)
                    
                    if not all([side, speaker, round_type]) and round_type != '自由辩论':
                        logger.error(f"回合 {index+1} 缺少必要信息: side={side}, speaker={speaker}, type={round_type}")
                        continue
                    
                    # 处理自由辩论特殊情况
                    if round_type == '自由辩论':
                        side_text = "双方"
                    else:
                        side_text = "正方" if side == 'affirmative' else "反方"
                    
                    item_text = f"{index+1}. [{side_text}] {speaker} - {round_type} ({time_seconds}秒)"
                    self.rounds_list.addItem(item_text)
                    logger.debug(f"添加回合: {item_text}")
                    
                except Exception as e:
                    logger.error(f"处理回合 {index+1} 时出错: {e}")
                    continue
            
            # 验证是否成功添加了回合
            if self.rounds_list.count() == 0:
                logger.error("没有成功添加任何回合到列表中")
                QMessageBox.critical(self, "错误", "配置文件中的回合数据无法解析")
                return False
            
            logger.info(f"成功添加 {self.rounds_list.count()} 个回合到列表")
            
            # 使用单次定时器确保UI完成清理
            QTimer.singleShot(100, lambda: self.display_board.set_debate_config(config.to_dict()))
            
            # 启用控制按钮
            self.enable_controls()
            self.status_value.setText("配置已加载")
            logger.info(f"配置文件加载成功: {file_path}")
            
            # 强制刷新界面并选择第一个环节
            self.rounds_list.viewport().update()  # 强制刷新列表控件
            self.rounds_list.setCurrentRow(0)
            QApplication.processEvents()  # 处理界面事件队列
            
            return True

        except ConfigValidationError as e:
            logger.error(f"配置文件验证失败: {e}")
            QMessageBox.critical(self, "配置错误", f"配置文件验证失败:\n{e}")
            return False
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"无法加载配置文件:\n{e}")
            return False
            
    def load_config(self):
        """加载配置文件"""
        logger.info("加载配置文件")
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "JSON Files (*.json)", options=options)
        if file_path:
            # 使用统一的加载方法
            self.load_config_from_path(file_path)

    def start_current_round(self):
        """开始当前选中的环节"""
        try:
            if not self.debate_config or self.rounds_list.currentRow() == -1:
                QMessageBox.warning(self, "警告", "请先选择要开始的环节")
                return

            current_index = self.rounds_list.currentRow()
            round_info = self.debate_config.get_rounds()[current_index]
            
            # 验证时间设置
            time_seconds = round_info.get('time', 0)
            if not isinstance(time_seconds, (int, float)) or time_seconds <= 0:
                QMessageBox.critical(self, "错误", "无效的时间设置")
                return

            # 更新显示板 - 传递索引而不是字典
            self.display_board.start_round(current_index)
            self.status_value.setText("进行中")
            
            # 根据环节类型初始化计时器
            timer_manager = self.display_board.timer_manager
            logger.info(f"计时器管理器类型: {type(timer_manager)}")
            
            if self.is_free_debate:
                # 自由辩论模式 - 每方分配一半时间
                half_time = time_seconds // 2
                if hasattr(self, 'aff_timer_lcd'):
                    self.aff_timer_lcd.display(self.format_time(half_time))
                if hasattr(self, 'neg_timer_lcd'):
                    self.neg_timer_lcd.display(self.format_time(half_time))
                logger.info(f"自由辩论模式：每方 {half_time} 秒")
            else:
                # 普通环节 - 设置并启动计时器
                logger.info(f"普通环节模式：总时长 {time_seconds} 秒")
                
                try:
                    # 设置计时器持续时间
                    timer_manager.set_duration(time_seconds)
                    logger.debug(f"已设置计时器持续时间: {time_seconds}秒")
                    
                    # 重置计时器到初始状态
                    timer_manager.reset()
                    logger.debug("已重置计时器")
                    
                    # 启动计时器
                    if timer_manager.start():
                        logger.debug("已启动计时器")
                    else:
                        logger.warning("计时器启动失败")
                        
                except Exception as timer_error:
                    logger.error(f"计时器操作失败: {timer_error}")
            
            # 启用计时器控制
            self.timer_control_btn.setEnabled(True)
            self.reset_timer_btn.setEnabled(True)
            
            # 更新按钮文本
            self.timer_control_btn.setText("暂停计时")
            self.timer_control_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPause")))
            
            logger.info(f"环节 {current_index+1} 已开始")

        except Exception as e:
            logger.error(f"开始环节时出错: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"无法开始环节:\n{e}")

    def toggle_timer(self):
        """切换计时器状态（开始/暂停）"""
        try:
            timer_manager = self.display_board.timer_manager
            logger.debug(f"切换计时器状态，timer_manager类型: {type(timer_manager)}")
            
            # 检查计时器是否在运行
            is_running = timer_manager.is_running()
            logger.debug(f"计时器运行状态: {is_running}")
            
            if is_running:
                # 暂停计时器
                if timer_manager.pause():
                    logger.debug("已暂停计时器")
                    self.timer_control_btn.setText("继续计时")
                    self.timer_control_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
                    self.status_value.setText("已暂停")
                else:
                    logger.warning("暂停计时器失败")
            else:
                # 启动/恢复计时器
                started = False
                if hasattr(self, 'current_round_time') and self.current_round_time > 0:
                    # 如果有当前回合时间，先设置时间再启动
                    timer_manager.set_duration(self.current_round_time)
                    started = timer_manager.start()
                else:
                    # 否则尝试恢复
                    started = timer_manager.resume()
                
                if started:
                    logger.debug("已启动/恢复计时器")
                    self.timer_control_btn.setText("暂停计时")
                    self.timer_control_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPause")))
                    self.status_value.setText("进行中")
                else:
                    logger.warning("启动/恢复计时器失败")
                
            logger.debug("计时器状态已切换")
        except Exception as e:
            logger.error(f"切换计时器状态时出错: {e}", exc_info=True)

    def reset_timer(self):
        """重置计时器到初始状态"""
        try:
            timer_manager = self.display_board.timer_manager
            logger.debug("重置计时器")
            
            # 重置计时器
            if timer_manager.reset():
                logger.debug("计时器重置成功")
            else:
                logger.warning("计时器重置失败")
            
            # 如果有当前回合时间，重新设置
            if hasattr(self, 'current_round_time') and self.current_round_time > 0:
                timer_manager.set_duration(self.current_round_time)
                logger.debug(f"已重新设置计时器时间: {self.current_round_time}秒")
            
            self.timer_control_btn.setText("开始计时")
            self.timer_control_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
            self.status_value.setText("已重置")
            
            # 重置自由辩论计时器显示
            if self.is_free_debate and hasattr(self, 'current_round_time'):
                half_time = self.current_round_time // 2
                if hasattr(self, 'aff_timer_lcd'):
                    self.aff_timer_lcd.display(self.format_time(half_time))
                if hasattr(self, 'neg_timer_lcd'):
                    self.neg_timer_lcd.display(self.format_time(half_time))
                logger.debug(f"已重置自由辩论计时器显示: {half_time}秒")
                
            logger.info("计时器已重置")
        except Exception as e:
            logger.error(f"重置计时器时出错: {e}", exc_info=True)

    def terminate_current_round(self):
        """终止当前环节"""
        try:
            timer_manager = self.display_board.timer_manager
            if timer_manager.terminate_current_round():
                logger.info("当前环节已终止")
                self.roundTerminated.emit()
                self.status_value.setText("已终止")
                QMessageBox.information(self, "提示", "环节已强制终止")
            else:
                logger.error("终止环节失败")
                QMessageBox.critical(self, "错误", "无法终止当前环节")
        except Exception as e:
            logger.error(f"终止环节时出错: {e}", exc_info=True)

    def toggle_affirmative_timer(self):
        """切换正方计时器状态"""
        try:
            if not self.is_free_debate:
                logger.warning("只有在自由辩论环节才能使用正方计时器")
                return
                
            timer_manager = self.display_board.timer_manager
            logger.debug("切换正方计时器状态")
            
            # 切换正方计时器
            if timer_manager.toggle_affirmative_timer():
                # 更新按钮状态
                timer_state = timer_manager.get_timer_state()
                if timer_state['affirmative_timer_active']:
                    self.aff_timer_btn.setText("暂停计时")
                    self.aff_timer_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPause")))
                    logger.debug("正方计时器已启动")
                else:
                    self.aff_timer_btn.setText("继续计时")
                    self.aff_timer_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
                    logger.debug("正方计时器已暂停")
            else:
                logger.warning("正方计时器切换失败")
                
            logger.debug("正方计时器状态已切换")
        except Exception as e:
            logger.error(f"切换正方计时器时出错: {e}", exc_info=True)

    def toggle_negative_timer(self):
        """切换反方计时器状态"""
        try:
            if not self.is_free_debate:
                logger.warning("只有在自由辩论环节才能使用反方计时器")
                return
                
            timer_manager = self.display_board.timer_manager
            logger.debug("切换反方计时器状态")
            
            # 切换反方计时器
            if timer_manager.toggle_negative_timer():
                # 更新按钮状态
                timer_state = timer_manager.get_timer_state()
                if timer_state['negative_timer_active']:
                    self.neg_timer_btn.setText("暂停计时")
                    self.neg_timer_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPause")))
                    logger.debug("反方计时器已启动")
                else:
                    self.neg_timer_btn.setText("继续计时")
                    self.neg_timer_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
                    logger.debug("反方计时器已暂停")
            else:
                logger.warning("反方计时器切换失败")
                
            logger.debug("反方计时器状态已切换")
        except Exception as e:
            logger.error(f"切换反方计时器时出错: {e}", exc_info=True)

    def on_round_selected(self, index):
        """当环节列表中的选中项变化时触发"""
        try:
            logger.debug(f"选择回合索引: {index}")
            
            if index < 0:
                logger.debug("索引小于0，清空显示")
                self._set_default_round_display()
                return
                
            if not self.debate_config:
                logger.warning("没有加载配置文件")
                return
                
            rounds = self.debate_config.get_rounds()
            
            # 验证索引有效性
            if index >= len(rounds):
                logger.error(f"环节索引 {index} 超出范围 (最大: {len(rounds)-1})")
                return
            
            round_info = rounds[index]
            logger.debug(f"选择的回合信息: {round_info}")
            
            # 验证环节数据完整性
            required_keys = ['side', 'speaker', 'type', 'time']
            for key in required_keys:
                if key not in round_info:
                    logger.error(f"环节数据缺少必要字段: {key}")
                    return
            
            # 更新显示内容
            side = round_info['side']
            if round_info['type'] == '自由辩论':
                side_text = "双方"
            else:
                side_text = "正方" if side == 'affirmative' else "反方"
            
            # 验证时间数据
            time_value = round_info.get('time', 0)
            if not isinstance(time_value, (int, float)) or time_value < 0:
                logger.error(f"环节时间值无效: {time_value}")
                return
            
            # 保存当前回合时间，供其他方法使用
            self.current_round_time = time_value
            
            time_min = int(time_value) // 60
            time_sec = int(time_value) % 60
            
            # 安全更新标签内容
            if hasattr(self, 'current_round_label') and self.current_round_label:
                self.current_round_label.setText(f"{side_text} {round_info['speaker']} - {round_info['type']}")
            
            if hasattr(self, 'current_time_label') and self.current_time_label:
                self.current_time_label.setText(f"时长: {time_min}分{time_sec}秒")
            
            # 判断是否为自由辩论
            self.is_free_debate = round_info['type'] == '自由辩论'
            
            # 切换计时器界面
            if hasattr(self, 'timer_controls_stack'):
                self.timer_controls_stack.setCurrentIndex(1 if self.is_free_debate else 0)
                
            # 如果是自由辩论，初始化计时器显示
            if self.is_free_debate:
                half_time = time_value // 2
                if hasattr(self, 'aff_timer_lcd'):
                    self.aff_timer_lcd.display(self.format_time(half_time))
                if hasattr(self, 'neg_timer_lcd'):
                    self.neg_timer_lcd.display(self.format_time(half_time))
            
            # 发送环节选择信号
            self.roundSelected.emit(index)
            logger.info(f"已选择回合 {index+1}: {side_text} {round_info['speaker']} - {round_info['type']}")
            
        except Exception as e:
            logger.error(f"处理环节选择时出错: {e}", exc_info=True)
            self._set_default_round_display()

    def _set_default_round_display(self):
        """设置默认的环节显示内容"""
        try:
            if hasattr(self, 'current_round_label') and self.current_round_label:
                self.current_round_label.setText("未选择环节")
            if hasattr(self, 'current_time_label') and self.current_time_label:
                self.current_time_label.setText("时长: 0分钟")
        except Exception as e:
            logger.error(f"设置默认环节显示内容时出错: {e}", exc_info=True)

    def prev_round(self):
        """切换到上一个环节"""
        try:
            current_index = self.rounds_list.currentRow()
            if current_index > 0:
                self.rounds_list.setCurrentRow(current_index - 1)
        except Exception as e:
            logger.error(f"切换到上一环节时出错: {e}", exc_info=True)

    def next_round(self):
        """切换到下一个环节"""
        try:
            current_index = self.rounds_list.currentRow()
            if current_index < self.rounds_list.count() - 1:
                self.rounds_list.setCurrentRow(current_index + 1)
        except Exception as e:
            logger.error(f"切换到下一环节时出错: {e}", exc_info=True)

    def enable_controls(self):
        """启用所有控制按钮"""
        try:
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.timer_control_btn.setEnabled(True)
            self.reset_timer_btn.setEnabled(True)
            self.terminate_round_btn.setEnabled(True)
            logger.debug("所有控制已启用")
        except Exception as e:
            logger.error(f"启用控制时出错: {e}", exc_info=True)

    def disable_controls(self):
        """禁用所有控制按钮"""
        try:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.start_btn.setEnabled(False)
            self.timer_control_btn.setEnabled(False)
            self.reset_timer_btn.setEnabled(False)
            self.terminate_round_btn.setEnabled(False)
            logger.debug("所有控制已禁用")
        except Exception as e:
            logger.error(f"禁用控制时出错: {e}", exc_info=True)

    def format_time(self, seconds: int) -> str:
        """格式化时间为MM:SS"""
        try:
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins:02d}:{secs:02d}"
        except Exception as e:
            logger.error(f"格式化时间失败: {e}")
            return "00:00"

    def update_lcd_display(self, time_seconds, timer_type=None):
        """更新LCD显示"""
        try:
            if timer_type == 'affirmative':
                # 更新正方计时器显示
                if hasattr(self, 'aff_timer_lcd'):
                    self.aff_timer_lcd.display(self.format_time(time_seconds))
            elif timer_type == 'negative':
                # 更新反方计时器显示
                if hasattr(self, 'neg_timer_lcd'):
                    self.neg_timer_lcd.display(self.format_time(time_seconds))
            else:
                # 更新标准计时器显示 - 这里可以添加标准计时器的LCD显示
                # 目前标准计时器使用的是按钮文本，不是LCD
                logger.debug(f"标准计时器时间更新: {self.format_time(time_seconds)}")
        except Exception as e:
            logger.error(f"更新LCD显示时出错: {e}", exc_info=True)

    def on_round_finished(self):
        """环节结束时的处理"""
        try:
            logger.info("环节已结束")
            # 重置按钮状态
            self.timer_control_btn.setText("开始计时")
            self.timer_control_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
            self.status_value.setText("环节结束")
            
            # 重置自由辩论按钮状态
            if hasattr(self, 'aff_timer_btn'):
                self.aff_timer_btn.setText("正方计时")
                self.aff_timer_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
            
            if hasattr(self, 'neg_timer_btn'):
                self.neg_timer_btn.setText("反方计时")
                self.neg_timer_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
            
            # 自动切换到下一环节
            current_index = self.rounds_list.currentRow()
            if current_index < self.rounds_list.count() - 1:
                QTimer.singleShot(2000, lambda: self.rounds_list.setCurrentRow(current_index + 1))
                
        except Exception as e:
            logger.error(f"处理环节结束时出错: {e}", exc_info=True)

    def on_affirmative_timer_finished(self):
        """正方计时器结束时的处理"""
        try:
            logger.info("正方计时器已结束")
            if hasattr(self, 'aff_timer_btn'):
                self.aff_timer_btn.setText("时间到")
                self.aff_timer_btn.setEnabled(False)
            if hasattr(self, 'aff_timer_lcd'):
                self.aff_timer_lcd.display("00:00")
                self.aff_timer_lcd.setStyleSheet("background-color: #FFEDED; color: #D13438; border: none;")
        except Exception as e:
            logger.error(f"处理正方计时器结束时出错: {e}", exc_info=True)

    def on_negative_timer_finished(self):
        """反方计时器结束时的处理"""
        try:
            logger.info("反方计时器已结束")
            if hasattr(self, 'neg_timer_btn'):
                self.neg_timer_btn.setText("时间到")
                self.neg_timer_btn.setEnabled(False)
            if hasattr(self, 'neg_timer_lcd'):
                self.neg_timer_lcd.display("00:00")
                self.neg_timer_lcd.setStyleSheet("background-color: #FFEDED; color: #D13438; border: none;")
        except Exception as e:
            logger.error(f"处理反方计时器结束时出错: {e}", exc_info=True)
