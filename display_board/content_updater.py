#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QApplication, QWidget  # 添加 QWidget 导入
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QTimer
from utils import logger

class ContentUpdater:
    """内容更新和渲染管理类"""
    
    def __init__(self, parent):
        self.parent = parent
        # 添加闪烁控制
        self.flash_timer = QTimer()
        self.flash_timer.setInterval(300)  # 300毫秒闪烁间隔
        self.flash_timer.timeout.connect(self._on_flash_timer)
        self.flash_count = 0
        self.flash_max = 0
        self.flash_color = None
        self.flash_original_style = None
        self.flash_widget = None
        self.flash_state = False  # False表示显示原色，True表示显示闪烁色
    
    def update_active_content(self, widget, round_info):
        """更新活动控件内容"""
        if not round_info:
            # 若无内容，清空显示
            self._force_clear_labels(widget, ['round_title', 'speaker_info'])
            if hasattr(widget, 'timer_stack'):
                widget.timer_stack.setCurrentIndex(0)
            return
            
        try:
            # 验证数据完整性
            required_keys = ['side', 'speaker', 'type', 'time']
            for key in required_keys:
                if key not in round_info:
                    logger.warning(f"当前环节数据缺少必需字段: {key}")
                    return
            
            side = "正方" if round_info['side'] == 'affirmative' else "反方"
            side_color = "#0078D4" if round_info['side'] == 'affirmative' else "#C42B1C"
            is_free_debate = round_info.get('type') == "自由辩论"
            
            # 隐藏控件
            widget.setVisible(False)
            
            # 清除现有内容
            self._force_clear_labels(widget, ['round_title', 'speaker_info'])
            QApplication.processEvents()
            
            # 设置新内容
            self._set_active_content(widget, round_info, side, side_color, is_free_debate)
            
            # 检查是否为最后一回合，如果是则隐藏下一环节信息
            if hasattr(self.parent, 'rounds') and hasattr(widget, 'next_round_frame'):
                rounds = self.parent.rounds
                current_index = self.parent.current_round_index if hasattr(self.parent, 'current_round_index') else -1
                
                # 如果是最后一回合，隐藏下一环节信息
                if rounds and current_index >= 0 and current_index >= len(rounds) - 1:
                    widget.next_round_frame.setVisible(False)
                else:
                    widget.next_round_frame.setVisible(True)
            
            # 重新显示
            widget.setVisible(True)
            widget.update()
            widget.repaint()
            
        except Exception as e:
            logger.error(f"更新活动内容时出错: {e}", exc_info=True)
    
    def update_timer_display(self, widget, timer_state):
        """更新计时器显示"""
        try:
            if timer_state['is_free_debate']:
                self._update_free_debate_timers(widget, timer_state)
            else:
                self._update_standard_timer(widget, timer_state)
        except Exception as e:
            logger.error(f"更新计时器显示时出错: {e}", exc_info=True)
    
    def update_debaters_info(self, side_widget, debater_roles, side_type):
        """更新辩手信息显示"""
        try:
            if not debater_roles:
                return
                
            prefix = side_type
            positions = ['first', 'second', 'third', 'fourth']
            
            for i, pos in enumerate(positions, 1):
                key = f"{prefix}_{pos}"
                label_key = f"{side_type}_{i}"
                
                if hasattr(side_widget.debaters_frame, 'debater_labels'):
                    labels = side_widget.debaters_frame.debater_labels
                    if label_key in labels:
                        name = debater_roles.get(key, '待定')
                        
                        # 检查是否包含富文本标记
                        if '**' in name:
                            from utils import highlight_markers
                            from PyQt5.QtCore import Qt
                            rich_name = highlight_markers(name, side=side_type)
                            labels[label_key].setTextFormat(Qt.RichText)
                            labels[label_key].setText(rich_name)
                        else:
                            labels[label_key].setText(name)
                        
        except Exception as e:
            logger.error(f"更新辩手信息时出错: {e}", exc_info=True)
    
    def highlight_active_debater(self, side_widgets, current_round):
        """高亮当前发言的辩手"""
        try:
            if not current_round:
                return
            
            # 重置所有样式
            self._reset_all_debater_styles(side_widgets)
            
            side = current_round['side']
            speaker = current_round['speaker']
            
            # 确定目标标签
            side_widget = side_widgets[side]
            speaker_map = {'一辩': f'{side}_1', '二辩': f'{side}_2', 
                          '三辩': f'{side}_3', '四辩': f'{side}_4'}
            
            target_key = speaker_map.get(speaker)
            if target_key and hasattr(side_widget.debaters_frame, 'debater_labels'):
                labels = side_widget.debaters_frame.debater_labels
                if target_key in labels:
                    labels[target_key].setStyleSheet("""
                        background-color: #FFD700; 
                        color: #000000; 
                        border: 2px solid #FFA500; 
                        border-radius: 4px; 
                        padding: 2px; 
                        font-weight: bold;
                        letter-spacing: 1px;
                    """)
                    logger.debug(f"高亮辩手: {side} {speaker}")
                    
        except Exception as e:
            logger.error(f"高亮辩手时出错: {e}", exc_info=True)
    
    def _force_clear_labels(self, widget, label_names):
        """强制清除标签内容"""
        try:
            for label_name in label_names:
                if hasattr(widget, label_name):
                    label = getattr(widget, label_name)
                    if label:
                        label.clear()
                        label.update()
                        label.repaint()
        except Exception as e:
            logger.error(f"强制清除标签时出错: {e}", exc_info=True)
    
    def _set_active_content(self, widget, round_info, side, side_color, is_free_debate):
        """设置活动内容"""
        try:
            # 设置标题
            if hasattr(widget, 'round_title'):
                title_text = round_info.get('description', "当前环节")
                widget.round_title.setText(title_text)
                widget.round_title.setStyleSheet("color: #323130; background: transparent;")
                widget.round_title.update()
                widget.round_title.repaint()
            
            # 设置发言者信息
            if hasattr(widget, 'speaker_info'):
                # 修改：自由辩论环节不显示"正方/反方 - 自由辩手"，只显示"自由辩论"
                if is_free_debate:
                    speaker_text = "自由辩论"
                else:
                    speaker_text = f"{side} {round_info['speaker']} - {round_info['type']}"
                
                # 检查是否包含富文本标记
                if '**' in speaker_text:
                    from utils import highlight_markers
                    from PyQt5.QtCore import Qt
                    rich_text = highlight_markers(speaker_text, hl_color=side_color)
                    widget.speaker_info.setTextFormat(Qt.RichText)
                    widget.speaker_info.setText(rich_text)
                else:
                    widget.speaker_info.setText(speaker_text)
                    
                style = f"color: {side_color}; font-weight: bold; background: transparent;"
                widget.speaker_info.setStyleSheet(style)
                widget.speaker_info.update()
                widget.speaker_info.repaint()
            
            # 设置计时器显示模式
            if hasattr(widget, 'timer_stack'):
                index = 1 if is_free_debate else 0
                widget.timer_stack.setCurrentIndex(index)
                
        except Exception as e:
            logger.error(f"设置活动内容时出错: {e}", exc_info=True)
    
    def _update_standard_timer(self, widget, timer_state):
        """更新标准计时器"""
        try:
            if not hasattr(widget, 'timer_containers'):
                return
                
            container = widget.timer_containers['standard']
            
            if hasattr(container, 'progress_bar'):
                current_time = timer_state['current_time']
                total_time = 100  # 默认最大值
                
                # 获取总时间，用于计算进度
                if hasattr(widget, 'current_round') and widget.current_round:
                    total_time = widget.current_round.get('time', 100)
                
                # 设置进度条最大值和当前值
                container.progress_bar.setMaximum(total_time)
                container.progress_bar.setValue(current_time)
                # 强制刷新进度条
                container.progress_bar.update()
                container.progress_bar.repaint()
                # 强制刷新容器
                container.update()
                container.repaint()
            
            if hasattr(container, 'countdown_label'):
                current_time = timer_state['current_time']
                minutes = current_time // 60
                seconds = current_time % 60
                container.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
                
                # 获取当前环节的辩方颜色
                side = self.parent.current_round.get('side') if self.parent.current_round else None
                side_color = "#0078D4" if side == "affirmative" else "#D13438"
                
                # 检查是否需要闪烁
                if hasattr(self.parent.timer_manager, 'flash_target') and self.parent.timer_manager.flash_target > 0:
                    # 启动闪烁效果
                    self._start_flashing(
                        container.countdown_label, 
                        self.parent.timer_manager.flash_target,
                        self.parent.timer_manager.flash_color,
                        "color: #323130; font-weight: bold; background: transparent;"
                    )
                    # 重置计时器管理器中的闪烁目标
                    self.parent.timer_manager.flash_target = 0
                
                # 默认样式 - 根据时间变化颜色
                elif not self.flash_timer.isActive() or self.flash_widget != container.countdown_label:
                    if current_time <= 10:
                        style = f"color: {side_color}; font-weight: bold; background: transparent;"
                    elif current_time <= 30:
                        style = "color: #D13438; font-weight: bold; background: transparent;"
                    else:
                        style = "color: #323130; font-weight: bold; background: transparent;"
                    container.countdown_label.setStyleSheet(style)
                
        except Exception as e:
            logger.error(f"更新标准计时器时出错: {e}", exc_info=True)
    
    def _update_free_debate_timers(self, widget, timer_state):
        """更新自由辩论计时器"""
        try:
            if not hasattr(widget, 'timer_containers'):
                return
                
            container = widget.timer_containers['free_debate']
            
            # 获取总时间，用于计算进度
            total_time = 100  # 默认最大值
            if hasattr(widget, 'current_round') and widget.current_round:
                total_time = widget.current_round.get('time', 100) // 2  # 自由辩论时间的一半
            
            # 每次都强制重新布局以确保进度条正确显示
            container.layout().update()
            QApplication.processEvents()
            
            # 更新正方计时器
            if hasattr(container, 'aff_group'):
                aff_group = container.aff_group
                aff_time = timer_state['affirmative_time']
                
                if hasattr(aff_group, 'progress_bar'):
                    # 设置进度条最大值和当前值
                    aff_group.progress_bar.setMaximum(total_time)
                    aff_group.progress_bar.setValue(aff_time)
                    # 强制刷新进度条
                    aff_group.progress_bar.update()
                    aff_group.progress_bar.repaint()
                
                if hasattr(aff_group, 'countdown_label'):
                    minutes = aff_time // 60
                    seconds = aff_time % 60
                    aff_group.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
                    
                    # 检查是否需要闪烁（仅当正方计时器活动时）
                    if timer_state['affirmative_timer_active'] and hasattr(self.parent.timer_manager, 'flash_target') and self.parent.timer_manager.flash_target > 0:
                        # 启动闪烁效果
                        self._start_flashing(
                            aff_group.countdown_label, 
                            self.parent.timer_manager.flash_target,
                            "#0078D4",  # 正方蓝色
                            "color: #323130; font-weight: bold; background: transparent;"
                        )
                        # 重置计时器管理器中的闪烁目标
                        self.parent.timer_manager.flash_target = 0
                    
                    # 默认样式 - 根据时间变化颜色
                    elif not self.flash_timer.isActive() or self.flash_widget != aff_group.countdown_label:
                        if aff_time <= 10:
                            style = "color: #0078D4; font-weight: bold; background: transparent;"
                        elif aff_time <= 30:
                            style = "color: #D13438; font-weight: bold; background: transparent;"
                        else:
                            style = "color: #323130; font-weight: bold; background: transparent;"
                        aff_group.countdown_label.setStyleSheet(style)
            
            # 更新反方计时器
            if hasattr(container, 'neg_group'):
                neg_group = container.neg_group
                neg_time = timer_state['negative_time']
                
                if hasattr(neg_group, 'progress_bar'):
                    # 设置进度条最大值和当前值
                    neg_group.progress_bar.setMaximum(total_time)
                    neg_group.progress_bar.setValue(neg_time)
                    # 新增：强制刷新进度条
                    neg_group.progress_bar.update()
                    neg_group.progress_bar.repaint()
                    # 新增：强制刷新容器
                    neg_group.update()
                    neg_group.repaint()
                    
                if hasattr(neg_group, 'countdown_label'):
                    minutes = neg_time // 60
                    seconds = neg_time % 60
                    neg_group.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
                    
                    # 检查是否需要闪烁（仅当反方计时器活动时）
                    if timer_state['negative_timer_active'] and hasattr(self.parent.timer_manager, 'flash_target') and self.parent.timer_manager.flash_target > 0:
                        # 启动闪烁效果
                        self._start_flashing(
                            neg_group.countdown_label, 
                            self.parent.timer_manager.flash_target,
                            "#D13438",  # 反方红色
                            "color: #323130; font-weight: bold; background: transparent;"
                        )
                        # 重置计时器管理器中的闪烁目标
                        self.parent.timer_manager.flash_target = 0
                    
                    # 默认样式 - 根据时间变化颜色
                    elif not self.flash_timer.isActive() or self.flash_widget != neg_group.countdown_label:
                        if neg_time <= 10:
                            style = "color: #D13438; font-weight: bold; background: transparent;"
                        elif neg_time <= 30:
                            style = "color: #D13438; font-weight: bold; background: transparent;"
                        else:
                            style = "color: #323130; font-weight: bold; background: transparent;"
                        neg_group.countdown_label.setStyleSheet(style)
                    
            # 最后强制更新整个容器及其所有子控件
            for child in container.findChildren(QWidget):  # 现在正确引用了QWidget
                child.update()
                child.repaint()
            
            container.update()
            container.repaint()
            
            # 确保内容已渲染到屏幕
            QApplication.processEvents()
                
        except Exception as e:
            logger.error(f"更新自由辩论计时器时出错: {e}", exc_info=True)
    
    def _start_flashing(self, widget, count, color, original_style):
        """开始闪烁效果"""
        try:
            # 保存闪烁相关信息
            self.flash_widget = widget
            self.flash_max = count * 2  # 每次闪烁包括开和关两个状态
            self.flash_count = 0
            self.flash_color = color
            self.flash_original_style = original_style
            self.flash_state = True  # 从高亮状态开始
            
            # 应用第一个闪烁状态
            widget.setStyleSheet(f"color: {color}; font-weight: bold; background: transparent;")
            
            # 启动闪烁计时器
            self.flash_timer.start()
            
        except Exception as e:
            logger.error(f"启动闪烁效果时出错: {e}", exc_info=True)
    
    def _on_flash_timer(self):
        """闪烁计时器触发事件"""
        try:
            if not self.flash_widget or self.flash_count >= self.flash_max:
                # 闪烁结束，恢复原样式
                if self.flash_widget:
                    self.flash_widget.setStyleSheet(self.flash_original_style)
                # 停止计时器
                self.flash_timer.stop()
                return
            
            # 切换闪烁状态
            self.flash_state = not self.flash_state
            
            if self.flash_state:
                # 高亮状态
                self.flash_widget.setStyleSheet(f"color: {self.flash_color}; font-weight: bold; background: transparent;")
            else:
                # 正常状态
                self.flash_widget.setStyleSheet(self.flash_original_style)
            
            # 增加计数
            self.flash_count += 1
            
        except Exception as e:
            logger.error(f"闪烁计时器事件处理时出错: {e}", exc_info=True)
            self.flash_timer.stop()
    
    def _reset_all_debater_styles(self, side_widgets):
        """重置所有辩手样式"""
        try:
            default_style = "letter-spacing: 1px;"
            
            for side_widget in side_widgets.values():
                if hasattr(side_widget.debaters_frame, 'debater_labels'):
                    labels = side_widget.debaters_frame.debater_labels
                    for label in labels.values():
                        label.setStyleSheet(default_style)
                        
        except Exception as e:
            logger.error(f"重置辩手样式时出错: {e}", exc_info=True)
