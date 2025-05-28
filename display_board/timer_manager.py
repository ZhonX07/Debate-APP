#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from utils import logger
import os
from PyQt5.QtMultimedia import QSound

class TimerManager(QObject):
    """计时器管理类，处理所有计时相关功能"""
    
    # 信号定义
    timeUpdated = pyqtSignal()
    timerFinished = pyqtSignal()
    affirmativeTimerFinished = pyqtSignal()
    negativeTimerFinished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # 计时器状态
        self.current_time = 0
        self.total_time = 0
        self.affirmative_time = 0
        self.negative_time = 0
        self.timer_active = False
        self.affirmative_timer_active = False
        self.negative_timer_active = False
        self.is_free_debate = False
        self.current_round = None
        
        # 创建计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer)
        
        # 声音文件路径
        self.media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media")
        self.notification_sound = os.path.join(self.media_dir, "noti.wav")
        self.timeover_sound = os.path.join(self.media_dir, "timeover.wav")
        
        # 倒计时提醒标记
        self.notified_at_60s = False
        self.notified_at_30s = False
        self.notified_at_15s = False
        self.last_10s_tick = 0
        
        # 添加闪烁控制
        self.flash_count = 0
        self.flash_target = 0
        self.flash_color = None
        self.flash_widget = None

    def set_current_round(self, round_data):
        """设置当前环节"""
        try:
            self.current_round = round_data
            if round_data:
                self.is_free_debate = round_data.get('type') == "自由辩论"
                duration = round_data.get('time', 0)
                
                if self.is_free_debate:
                    logger.info(f"设置自由辩论环节，每方时间: {duration//2}秒")
                    self.affirmative_time = duration // 2
                    self.negative_time = duration // 2
                else:
                    logger.info(f"设置标准环节，时间: {duration}秒")
                    self.current_time = duration
                    
                self.total_time = duration
                
                # 重置提醒标记
                self._reset_notification_flags()
                
        except Exception as e:
            logger.error(f"设置当前环节时出错: {e}", exc_info=True)

    def get_timer_state(self):
        """获取计时器状态"""
        return {
            'current_time': self.current_time,
            'total_time': self.total_time,
            'affirmative_time': self.affirmative_time,
            'negative_time': self.negative_time,
            'timer_active': self.timer_active,
            'affirmative_timer_active': self.affirmative_timer_active,
            'negative_timer_active': self.negative_timer_active,
            'is_free_debate': self.is_free_debate
        }

    def toggle_timer(self):
        """开启或暂停标准计时器"""
        if self.is_free_debate:
            logger.info("自由辩论模式下，请使用正方/反方专用计时器控制")
            return False
        
        if self.timer_active:
            return self.pause()
        else:
            return self.start()
    
    def toggle_affirmative_timer(self):
        """开启或暂停正方计时器"""
        try:
            if not self.is_free_debate:
                logger.warning("非自由辩论模式不应调用正方计时器")
                return False
            
            if self.affirmative_timer_active:
                logger.info("正方计时器暂停")
                self.timer.stop()
                self.affirmative_timer_active = False
                return True
            else:
                # 确保两个计时器不同时运行
                if self.negative_timer_active:
                    self.negative_timer_active = False
                
                logger.info("正方计时器启动")
                if self.affirmative_time > 0:
                    self.timer.start(1000)
                    self.affirmative_timer_active = True
                    return True
                else:
                    logger.warning("正方时间已用完")
                    return False
        except Exception as e:
            logger.error(f"切换正方计时器时出错: {e}", exc_info=True)
            return False
    
    def toggle_negative_timer(self):
        """开启或暂停反方计时器"""
        try:
            if not self.is_free_debate:
                logger.warning("非自由辩论模式不应调用反方计时器")
                return False
            
            if self.negative_timer_active:
                logger.info("反方计时器暂停")
                self.timer.stop()
                self.negative_timer_active = False
                return True
            else:
                # 确保两个计时器不同时运行
                if self.affirmative_timer_active:
                    self.affirmative_timer_active = False
                
                logger.info("反方计时器启动")
                if self.negative_time > 0:
                    self.timer.start(1000)
                    self.negative_timer_active = True
                    return True
                else:
                    logger.warning("反方时间已用完")
                    return False
        except Exception as e:
            logger.error(f"切换反方计时器时出错: {e}", exc_info=True)
            return False

    def start(self):
        """启动计时器"""
        if self.is_free_debate:
            logger.warning("自由辩论模式下请使用专用计时器控制")
            return False
        
        if self.current_time > 0:
            logger.info(f"启动标准计时器，剩余时间: {self.current_time}秒")
            self.timer.start(1000)
            self.timer_active = True
            return True
        else:
            logger.warning("计时器时间为0，无法启动")
            return False
    
    def pause(self):
        """暂停计时器"""
        logger.info("暂停计时器")
        self.timer.stop()
        self.timer_active = False
        return True
    
    def stop(self):
        """停止计时器"""
        logger.info("停止计时器")
        self.timer.stop()
        self.timer_active = False
        self.affirmative_timer_active = False
        self.negative_timer_active = False
        return True

    def reset_timer(self, duration=None):
        """重置计时器"""
        logger.info("计时器重置")
        self.timer.stop()
        self.timer_active = False
        self.affirmative_timer_active = False
        self.negative_timer_active = False
        
        # 重置提醒标记
        self._reset_notification_flags()
        
        if duration is not None:
            self.total_time = duration
            if self.is_free_debate:
                half_time = duration // 2
                self.affirmative_time = half_time
                self.negative_time = half_time
            else:
                self.current_time = duration
        else:
            # 重置到环节开始时的时间
            if self.current_round:
                duration = self.current_round.get('time', 0)
                self.total_time = duration
                if self.is_free_debate:
                    self.affirmative_time = duration // 2
                    self.negative_time = duration // 2
                else:
                    self.current_time = duration
        
        self.timeUpdated.emit()
        return True
    
    def terminate_current_round(self):
        """强制终止当前回合"""
        logger.info("终止当前回合")
        try:
            self.timer.stop()
            self.timer_active = False
            self.affirmative_timer_active = False
            self.negative_timer_active = False
            return True
        except Exception as e:
            logger.error(f"终止回合时出错: {e}", exc_info=True)
            return False

    def is_running(self):
        """检查计时器是否在运行"""
        if self.is_free_debate:
            return self.affirmative_timer_active or self.negative_timer_active
        else:
            return self.timer_active
    
    def isActive(self):
        """检查计时器是否激活（与is_running相同）"""
        return self.is_running()
    
    @property
    def running(self):
        """计时器运行状态属性"""
        return self.is_running()

    def _update_timer(self):
        """更新计时器"""
        try:
            if self.is_free_debate:
                # 自由辩论模式：更新活动中的一方计时器
                if self.affirmative_timer_active and self.affirmative_time > 0:
                    self.affirmative_time -= 1
                    if self.affirmative_time == 0:
                        self.timer.stop()
                        self.affirmative_timer_active = False
                        self._play_timeover()
                        self.affirmativeTimerFinished.emit()
                        return
                
                elif self.negative_timer_active and self.negative_time > 0:
                    self.negative_time -= 1
                    if self.negative_time == 0:
                        self.timer.stop()
                        self.negative_timer_active = False
                        self._play_timeover()
                        self.negativeTimerFinished.emit()
                        return
                
                # 检查总体时间是否结束
                if self.affirmative_time == 0 and self.negative_time == 0:
                    logger.info("自由辩论环节结束")
                    self.timer.stop()
                    self._play_timeover()
                    self.timerFinished.emit()
                    return
            else:
                # 标准计时模式
                if self.current_time > 0:
                    self.current_time -= 1
                    if self.current_time == 0:
                        self.timer.stop()
                        self.timer_active = False
                        self._play_timeover()
                        self.timerFinished.emit()
                        return
            
            # 检查是否需要发出提醒
            self._check_time_notifications()
            
            # 发送时间更新信号
            self.timeUpdated.emit()
            
        except Exception as e:
            logger.error(f"更新计时器时出错: {e}", exc_info=True)
    
    def _check_time_notifications(self):
        """检查是否需要发出时间提醒"""
        try:
            if self.is_free_debate:
                # 自由辩论模式
                if self.affirmative_timer_active:
                    current_time = self.affirmative_time
                    color = "#0078D4"  # 正方蓝色
                elif self.negative_timer_active:
                    current_time = self.negative_time
                    color = "#D13438"  # 反方红色
                else:
                    return
            else:
                # 标准模式
                current_time = self.current_time
                # 获取当前环节的辩方
                side = self.current_round.get('side') if self.current_round else None
                if side == "affirmative":
                    color = "#0078D4"  # 正方蓝色
                else:
                    color = "#D13438"  # 反方红色
            
            # 1分钟提醒
            if current_time == 60 and not self.notified_at_60s:
                self.notified_at_60s = True
                self._play_notification()
                self._trigger_flash(1, color)
                logger.info("剩余时间1分钟提醒")
            
            # 30秒提醒
            elif current_time == 30 and not self.notified_at_30s:
                self.notified_at_30s = True
                self._play_notification()
                self._trigger_flash(2, color)
                logger.info("剩余时间30秒提醒")
            
            # 15秒提醒
            elif current_time == 15 and not self.notified_at_15s:
                self.notified_at_15s = True
                self._play_notification()
                self._trigger_flash(3, color)
                logger.info("剩余时间15秒提醒")
            
            # 最后10秒每秒提醒
            elif 1 <= current_time <= 10:
                # 确保只在整秒时提醒
                if current_time != self.last_10s_tick:
                    self.last_10s_tick = current_time
                    self._play_notification()
                    self._trigger_flash(1, color)
                    logger.info(f"倒计时最后{current_time}秒")
            
        except Exception as e:
            logger.error(f"检查时间提醒时出错: {e}", exc_info=True)
    
    def _reset_notification_flags(self):
        """重置提醒标记"""
        self.notified_at_60s = False
        self.notified_at_30s = False
        self.notified_at_15s = False
        self.last_10s_tick = 0
    
    def _play_notification(self):
        """播放通知声音"""
        try:
            if os.path.exists(self.notification_sound):
                QSound.play(self.notification_sound)
            else:
                logger.warning(f"通知声音文件不存在: {self.notification_sound}")
        except Exception as e:
            logger.error(f"播放通知声音时出错: {e}", exc_info=True)
    
    def _play_timeover(self):
        """播放时间结束声音"""
        try:
            if os.path.exists(self.timeover_sound):
                QSound.play(self.timeover_sound)
            else:
                logger.warning(f"时间结束声音文件不存在: {self.timeover_sound}")
        except Exception as e:
            logger.error(f"播放时间结束声音时出错: {e}", exc_info=True)
    
    def _trigger_flash(self, count, color):
        """触发闪烁效果"""
        self.flash_count = 0
        self.flash_target = count
        self.flash_color = color
        # 发送闪烁信号 - 将在content_updater中处理
        # 通过timeUpdated信号间接触发UI更新

    # 兼容性方法
    def update_time(self):
        """更新时间（兼容性方法）"""
        self._update_timer()
    
    def set_duration(self, duration):
        """设置计时器持续时间"""
        logger.info(f"设置计时器持续时间: {duration}秒")
        self.total_time = duration
        
        if self.is_free_debate:
            half_time = duration // 2
            self.affirmative_time = half_time
            self.negative_time = half_time
        else:
            self.current_time = duration
        
        # 重置提醒标记
        self._reset_notification_flags()
        
        self.timeUpdated.emit()
        return True
    
    def resume(self):
        """恢复计时器"""
        if self.is_free_debate:
            logger.warning("自由辩论模式下请使用专用计时器控制")
            return False
        
        if self.current_time > 0:
            logger.info(f"恢复标准计时器，剩余时间: {self.current_time}秒")
            self.timer.start(1000)
            self.timer_active = True
            return True
        else:
            logger.warning("计时器时间为0，无法恢复")
            return False
