#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor
from utils import logger

class ContentUpdater:
    """内容更新和渲染管理类"""
    
    def __init__(self, parent):
        self.parent = parent
        
    def update_preview_content(self, widget, round_info, index):
        """更新预览控件内容"""
        if not round_info:
            self._set_preview_default_content(widget)
            return
            
        try:
            # 验证数据完整性
            required_keys = ['type', 'side', 'speaker', 'time']
            for key in required_keys:
                if key not in round_info:
                    logger.warning(f"环节数据缺少必需字段: {key}")
                    self._set_preview_default_content(widget)
                    return
            
            # 隐藏控件避免渲染重叠
            widget.setVisible(False)
            
            # 强制清除内容
            self._force_clear_labels(widget, ['title_label', 'type_label', 'desc_label', 'time_label'])
            QApplication.processEvents()
            
            # 设置新内容
            self._set_preview_content(widget, round_info, index)
            
            # 重新显示
            widget.setVisible(True)
            widget.update()
            widget.repaint()
            
        except Exception as e:
            logger.error(f"更新预览内容时出错: {e}", exc_info=True)
            self._set_preview_default_content(widget)
    
    def update_active_content(self, widget, round_info):
        """更新活动控件内容"""
        if not round_info:
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
    
    def _set_preview_content(self, widget, round_info, index):
        """设置预览内容"""
        try:
            # 设置标题
            if hasattr(widget, 'title_label'):
                widget.title_label.setText("下一环节:")
                widget.title_label.setStyleSheet("color: #323130; background: transparent;")
                widget.title_label.update()
                widget.title_label.repaint()
            
            # 设置类型
            if hasattr(widget, 'type_label'):
                widget.type_label.setText(round_info['type'])
                if round_info.get('type') == "自由辩论":
                    style = "color: #D13438; background: transparent;"
                else:
                    style = "color: #0078D4; background: transparent;"
                widget.type_label.setStyleSheet(style)
                widget.type_label.update()
                widget.type_label.repaint()
            
            # 设置描述
            if hasattr(widget, 'desc_label'):
                side = "正方" if round_info['side'] == 'affirmative' else "反方"
                desc_text = f"{side} {round_info['speaker']}"
                widget.desc_label.setText(desc_text)
                widget.desc_label.setStyleSheet("color: #605E5C; background: transparent;")
                widget.desc_label.update()
                widget.desc_label.repaint()
            
            # 设置时间
            if hasattr(widget, 'time_label'):
                time_value = round_info.get('time', 0)
                if isinstance(time_value, (int, float)) and time_value >= 0:
                    minutes = int(time_value) // 60
                    seconds = int(time_value) % 60
                    time_text = f"时长: {minutes:02d}:{seconds:02d}"
                else:
                    time_text = "时长: 未知"
                
                widget.time_label.setText(time_text)
                widget.time_label.setStyleSheet("color: #605E5C; background: transparent;")
                widget.time_label.update()
                widget.time_label.repaint()
            
        except Exception as e:
            logger.error(f"设置预览内容时出错: {e}", exc_info=True)
    
    def _set_preview_default_content(self, widget):
        """设置预览默认内容"""
        try:
            if hasattr(widget, 'title_label'):
                widget.title_label.setText("准备中...")
            if hasattr(widget, 'type_label'):
                widget.type_label.setText("N/A")
            if hasattr(widget, 'desc_label'):
                widget.desc_label.setText("N/A")
            if hasattr(widget, 'time_label'):
                widget.time_label.setText("N/A")
        except Exception as e:
            logger.error(f"设置预览默认内容时出错: {e}", exc_info=True)
    
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
                speaker_text = f"{side} {round_info['speaker']} - {round_info['type']}"
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
                container.progress_bar.update()
            
            if hasattr(container, 'countdown_label'):
                current_time = timer_state['current_time']
                minutes = current_time // 60
                seconds = current_time % 60
                container.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
                
                # 倒计时警告
                if current_time <= 30:
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
            
            # 更新正方计时器
            if hasattr(container, 'aff_group'):
                aff_group = container.aff_group
                aff_time = timer_state['affirmative_time']
                
                if hasattr(aff_group, 'progress_bar'):
                    # 设置进度条最大值和当前值
                    aff_group.progress_bar.setMaximum(total_time)
                    aff_group.progress_bar.setValue(aff_time)
                    aff_group.progress_bar.update()
                
                if hasattr(aff_group, 'countdown_label'):
                    minutes = aff_time // 60
                    seconds = aff_time % 60
                    aff_group.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
                    
                    if aff_time <= 30:
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
                    neg_group.progress_bar.update()
                
                if hasattr(neg_group, 'countdown_label'):
                    minutes = neg_time // 60
                    seconds = neg_time % 60
                    neg_group.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
                    
                    if neg_time <= 30:
                        style = "color: #D13438; font-weight: bold; background: transparent;"
                    else:
                        style = "color: #323130; font-weight: bold; background: transparent;"
                    neg_group.countdown_label.setStyleSheet(style)
                    
        except Exception as e:
            logger.error(f"更新自由辩论计时器时出错: {e}", exc_info=True)
    
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
