#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, 
                            QWidget, QStackedLayout, QApplication, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal
from PyQt5.QtGui import QFont

from utils import enable_dwm_composition, logger
from .timer_manager import TimerManager
from .ui_components import UIComponents
from .content_updater import ContentUpdater
from .animation_manager import AnimationManager

class DisplayBoard(QMainWindow):
    """前台展示窗口，用于显示给观众"""
    
    # 自定义信号
    roundChanged = pyqtSignal(int)
    
    def __init__(self, low_performance_mode=False):
        super().__init__()
        logger.info("DisplayBoard 初始化")
        
        # 基本属性
        self.title = "辩论背景看板"
        self.topic = "等待设置辩题"
        self.affirmative_school = ""
        self.affirmative_viewpoint = ""
        self.negative_school = ""
        self.negative_viewpoint = ""
        self.debater_roles = {}
        self.low_performance_mode = low_performance_mode
        
        # 环节管理
        self.current_round = None
        self.rounds = []
        self.current_round_index = -1
        self.control_panel = None
        
        # 初始化管理器
        self.timer_manager = TimerManager(self)
        self.ui_components = UIComponents(self)
        self.content_updater = ContentUpdater(self)
        self.animation_manager = AnimationManager(self)
        
        # 连接信号
        self._connect_signals()
        
        # 设置样式
        self.setStyleSheet("background-color: white;")
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)
        
        # 初始化UI
        self.initUI()
        logger.info("DisplayBoard UI 初始化完成")
        
        # 启用硬件加速
        if sys.platform == 'win32':
            try:
                enable_dwm_composition()
            except Exception as e:
                logger.error(f"无法启用Windows硬件加速: {e}")

    def _connect_signals(self):
        """连接信号"""
        self.timer_manager.timeUpdated.connect(self._on_timer_updated)
        self.timer_manager.timerFinished.connect(self._on_timer_finished)
        self.timer_manager.affirmativeTimerFinished.connect(self._on_affirmative_timer_finished)
        self.timer_manager.negativeTimerFinished.connect(self._on_negative_timer_finished)

    def initUI(self):
        """初始化用户界面"""
        logger.debug("DisplayBoard.initUI 开始")
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 1680, 945)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建背景
        self._create_background(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 创建顶部容器
        topic_container = self.ui_components.create_topic_container()
        self._setup_topic_stack(topic_container)
        main_layout.addWidget(topic_container, 10)
        
        # 创建左右两侧布局
        sides_layout = self._create_sides_layout()
        main_layout.addLayout(sides_layout, 78)
        
        # 创建底部时间显示
        self._create_time_display(main_layout)
        
        logger.debug("DisplayBoard.initUI 结束")

    def _create_background(self, central_widget):
        """创建背景"""
        # 背景标签
        self.bg_label = QLabel(central_widget)
        self.bg_label.setObjectName("backgroundLabel")
        self.bg_label.setStyleSheet("background-color: #f5f5f5;")
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        
        # 毛玻璃效果层
        self.blur_effect = QLabel(central_widget)
        self.blur_effect.setObjectName("blurEffect")
        self.blur_effect.setStyleSheet("background-color: rgba(255, 255, 255, 1.0);")
        self.blur_effect.setGeometry(0, 0, self.width(), self.height())
        
        self.bg_label.lower()

    def _setup_topic_stack(self, topic_container):
        """设置顶部堆栈布局"""
        self.topic_stack = QStackedLayout(topic_container)
        
        # 创建预览和活动控件
        self.preview_widget_top = self.ui_components.create_preview_widget_top()
        self.active_round_widget_top = self.ui_components.create_active_round_widget_top()
        
        # 移除所有阴影效果
        self._remove_shadow_from_widget(self.preview_widget_top)
        self._remove_shadow_from_widget(self.active_round_widget_top)
        
        self.topic_stack.addWidget(self.preview_widget_top)
        self.topic_stack.addWidget(self.active_round_widget_top)
        self.topic_stack.setCurrentWidget(self.preview_widget_top)
        
    def _remove_shadow_from_widget(self, widget):
        """递归移除控件及其子控件的阴影效果"""
        if not widget:
            return
            
        # 移除当前控件的阴影效果
        if isinstance(widget.graphicsEffect(), QGraphicsDropShadowEffect):
            widget.setGraphicsEffect(None)
            
        # 递归处理所有子控件
        for child in widget.findChildren(QWidget):
            if isinstance(child.graphicsEffect(), QGraphicsDropShadowEffect):
                child.setGraphicsEffect(None)
                
    def _create_sides_layout(self):
        """创建左右两侧布局"""
        sides_layout = QHBoxLayout()
        sides_layout.setContentsMargins(0, 0, 0, 0)
        sides_layout.setSpacing(15)
        
        # 创建正方和反方部件
        self.affirmative_widget = self.ui_components.create_side_widget('affirmative')
        self.negative_widget = self.ui_components.create_side_widget('negative')
        
        sides_layout.addWidget(self.affirmative_widget)
        sides_layout.addWidget(self.negative_widget)
        
        return sides_layout

    def _create_time_display(self, main_layout):
        """创建时间显示"""
        self.beijing_time_label = QLabel()
        self.beijing_time_label.setAlignment(Qt.AlignCenter)
        self.beijing_time_label.setFont(QFont("微软雅黑", 32, QFont.Bold))
        self.beijing_time_label.setStyleSheet("color: #323130;")
        
        # 时钟计时器
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_beijing_time)
        self.clock_timer.start(1000)
        self.update_beijing_time()
        
        main_layout.addWidget(self.beijing_time_label, 10)

    def update_beijing_time(self):
        """更新北京时间"""
        current_time = QTime.currentTime()
        time_text = f"北京时间：{current_time.toString('HH:mm:ss')}"
        self.beijing_time_label.setText(time_text)

    # 计时器事件处理
    def _on_timer_updated(self):
        """计时器更新事件"""
        try:
            timer_state = self.timer_manager.get_timer_state()
            self.content_updater.update_timer_display(self.active_round_widget_top, timer_state)
            
            # 更新控制面板显示
            if self.control_panel and hasattr(self.control_panel, 'update_lcd_display'):
                if timer_state['is_free_debate']:
                    if timer_state['affirmative_timer_active']:
                        self.control_panel.update_lcd_display(timer_state['affirmative_time'], 'affirmative')
                    elif timer_state['negative_timer_active']:
                        self.control_panel.update_lcd_display(timer_state['negative_time'], 'negative')
                else:
                    self.control_panel.update_lcd_display(timer_state['current_time'])
        except Exception as e:
            logger.error(f"计时器更新事件处理时出错: {e}", exc_info=True)

    def _on_timer_finished(self):
        """计时器结束事件"""
        try:
            logger.info("标准计时器结束")
            next_round_idx = self.current_round_index + 1
            
            # 重置辩手高亮
            side_widgets = {
                'affirmative': self.affirmative_widget,
                'negative': self.negative_widget
            }
            self.content_updater.highlight_active_debater(side_widgets, None)
            
            # 更新预览内容
            if next_round_idx < len(self.rounds):
                round_data = self.rounds[next_round_idx]
            else:
                round_data = self.rounds[self.current_round_index] if self.current_round_index >= 0 else None
                
            self.content_updater.update_preview_content(
                self.preview_widget_top, round_data, next_round_idx
            )
            
            # 切换到预览模式
            self.animation_manager.animate_widget_transition(
                self.active_round_widget_top, 
                self.preview_widget_top, 
                self.topic_stack
            )
            
            # 更新控制面板状态
            if self.control_panel and hasattr(self.control_panel, 'on_round_finished'):
                self.control_panel.on_round_finished()
        except Exception as e:
            logger.error(f"计时器结束事件处理时出错: {e}", exc_info=True)

    def _on_affirmative_timer_finished(self):
        """正方计时器结束事件"""
        try:
            logger.info("正方计时器结束")
            if self.control_panel and hasattr(self.control_panel, 'on_affirmative_timer_finished'):
                self.control_panel.on_affirmative_timer_finished()
        except Exception as e:
            logger.error(f"正方计时器结束事件处理时出错: {e}", exc_info=True)

    def _on_negative_timer_finished(self):
        """反方计时器结束事件"""
        try:
            logger.info("反方计时器结束")
            if self.control_panel and hasattr(self.control_panel, 'on_negative_timer_finished'):
                self.control_panel.on_negative_timer_finished()
        except Exception as e:
            logger.error(f"反方计时器结束事件处理时出错: {e}", exc_info=True)

    # 公共方法接口
    def set_debate_config(self, config):
        """设置辩论配置信息"""
        logger.info("设置辩论配置")
        
        try:
            if not isinstance(config, dict):
                logger.error("配置数据格式错误：应为字典类型")
                return False
            
            # 应用配置数据
            self._apply_config_data(config)
            
            # 更新显示
            self.update()
            self.repaint()
            
            logger.info("辩论配置已成功应用")
            return True
            
        except Exception as e:
            logger.error(f"设置辩论配置时出错: {e}", exc_info=True)
            return False

    def _apply_config_data(self, config):
        """应用配置数据"""
        try:
            # 设置基本信息
            if 'topic' in config and config['topic']:
                self.topic = str(config['topic'])
                self.setWindowTitle(f"辩论背景看板 - {self.topic}")
            
            # 设置正方信息
            if 'affirmative' in config:
                self._set_side_info('affirmative', config['affirmative'])
                
            # 设置反方信息
            if 'negative' in config:
                self._set_side_info('negative', config['negative'])
                
            # 设置辩手角色映射
            if 'debater_roles' in config:
                self.debater_roles = config['debater_roles']
                self.update_debaters_info()
        
            # 设置辩论环节
            if 'rounds' in config and isinstance(config['rounds'], list):
                self.rounds = config['rounds']
                self.content_updater.update_preview_content(
                    self.preview_widget_top, 
                    self.rounds[0] if self.rounds else None, 
                    0
                )
                
        except Exception as e:
            logger.error(f"应用配置数据时出错: {e}", exc_info=True)

    def _set_side_info(self, side, data):
        """设置正方或反方信息"""
        try:
            widget = self.affirmative_widget if side == 'affirmative' else self.negative_widget
            
            if 'school' in data and data['school']:
                setattr(self, f"{side}_school", str(data['school']))
                widget.school_label.setText(str(data['school']))
                widget.school_label.update()
                widget.school_label.repaint()
            
            if 'viewpoint' in data and data['viewpoint']:
                setattr(self, f"{side}_viewpoint", str(data['viewpoint']))
                widget.viewpoint_label.setText(str(data['viewpoint']))
                widget.viewpoint_label.update()
                widget.viewpoint_label.repaint()
                
        except Exception as e:
            logger.error(f"设置{side}信息时出错: {e}", exc_info=True)

    # 计时器相关方法（委托给TimerManager）
    def toggle_timer(self):
        """开启或暂停计时器"""
        self.timer_manager.toggle_timer()
    
    def toggle_affirmative_timer(self):
        """开启或暂停正方计时器"""
        self.timer_manager.toggle_affirmative_timer()
    
    def toggle_negative_timer(self):
        """开启或暂停反方计时器"""
        self.timer_manager.toggle_negative_timer()

    def reset_timer(self, duration=None):
        """重置计时器"""
        self.timer_manager.reset_timer(duration)

    def terminate_current_round(self):
        """强制终止当前回合"""
        success = self.timer_manager.terminate_current_round()
        if success:
            # 重置辩手样式
            side_widgets = {
                'affirmative': self.affirmative_widget,
                'negative': self.negative_widget
            }
            self.content_updater.highlight_active_debater(side_widgets, None)
            
            # 切换到预览模式
            next_idx = self.current_round_index + 1
            if next_idx < len(self.rounds):
                round_data = self.rounds[next_idx]
            else:
                round_data = self.rounds[self.current_round_index] if self.current_round_index >= 0 else None
                
            self.content_updater.update_preview_content(
                self.preview_widget_top, round_data, next_idx
            )
            
            self.animation_manager.animate_widget_transition(
                self.active_round_widget_top, 
                self.preview_widget_top, 
                self.topic_stack
            )
        return success

    # 环节管理方法
    def start_round(self, index):
        """开始指定的辩论环节"""
        logger.info(f"开始环节: index={index}")
        if 0 <= index < len(self.rounds):
            self.current_round_index = index
            self.current_round = self.rounds[index]
            
            # 设置计时器管理器的当前环节
            self.timer_manager.set_current_round(self.current_round)
            
            # 更新活动控件内容
            self.content_updater.update_active_content(
                self.active_round_widget_top, 
                self.current_round
            )
            
            # 保存当前环节信息到活动控件中，供计时器使用
            self.active_round_widget_top.current_round = self.current_round
            
            # 切换到活动视图
            self.animation_manager.animate_widget_transition(
                self.preview_widget_top, 
                self.active_round_widget_top, 
                self.topic_stack
            )
            
            # 高亮当前环节的活跃辩手
            side_widgets = {
                'affirmative': self.affirmative_widget,
                'negative': self.negative_widget
            }
            self.content_updater.highlight_active_debater(side_widgets, self.current_round)
            
            # 发送环节变化信号
            self.roundChanged.emit(index)
            return True
        return False

    def update_debaters_info(self):
        """更新辩手信息显示"""
        logger.debug("更新辩手信息显示")
        try:
            if not self.debater_roles:
                logger.warning("辩手角色映射为空")
                return
            
            # 更新正方辩手信息
            self.content_updater.update_debaters_info(
                self.affirmative_widget, 
                self.debater_roles, 
                'affirmative'
            )
            
            # 更新反方辩手信息
            self.content_updater.update_debaters_info(
                self.negative_widget, 
                self.debater_roles, 
                'negative'
            )
            
        except Exception as e:
            logger.error(f"更新辩手信息时出错: {e}", exc_info=True)

    # 控制面板相关方法
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
                    self.content_updater.update_preview_content(
                        self.preview_widget_top,
                        self.rounds[0] if self.rounds else None,
                        0
                    )
            
        except Exception as e:
            logger.error(f"设置控制面板引用时出错: {e}", exc_info=True)

    def onRoundSelected(self, index):
        """响应控制端环节选择，更新预览视图或当前环节"""
        logger.info(f"收到环节选择信号: index={index}")
        try:
            # 更新预览内容
            round_data = self.rounds[index] if 0 <= index < len(self.rounds) else None
            self.content_updater.update_preview_content(
                self.preview_widget_top, round_data, index
            )
            
            # 如果不是在计时中，则可以直接切换到预览模式
            timer_state = self.timer_manager.get_timer_state()
            if not timer_state['timer_active']:
                self.topic_stack.setCurrentWidget(self.preview_widget_top)
                
        except Exception as e:
            logger.error(f"处理环节选择时出错: {e}", exc_info=True)

    # 数据重置方法
    def _reset_all_data(self):
        """重置所有数据"""
        try:
            self.current_round = None
            self.current_round_index = -1
            self.timer_manager.reset_timer(0)
            
        except Exception as e:
            logger.error(f"重置数据时出错: {e}", exc_info=True)

    def _set_preview_default_content(self):
        """设置预览默认内容"""
        try:
            if hasattr(self.preview_widget_top, 'title_label'):
                self.preview_widget_top.title_label.setText("准备中...")
            if hasattr(self.preview_widget_top, 'type_label'):
                self.preview_widget_top.type_label.setText("N/A")
            if hasattr(self.preview_widget_top, 'desc_label'):
                self.preview_widget_top.desc_label.setText("N/A")
            if hasattr(self.preview_widget_top, 'time_label'):
                self.preview_widget_top.time_label.setText("N/A")
        except Exception as e:
            logger.error(f"设置预览默认内容时出错: {e}", exc_info=True)
