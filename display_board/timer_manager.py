#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from utils import logger

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
        self.affirmative_time = 0
        self.negative_time = 0
        self.timer_active = False
        self.affirmative_timer_active = False
        self.negative_timer_active = False
        self.is_free_debate = False
        self.current_round = None
        
        # 创建计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        
    def toggle_timer(self):
        """开启或暂停标准计时器"""
        if self.is_free_debate:
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
            else:
                # 确保两个计时器不同时运行
                if self.negative_timer_active:
                    self.negative_timer_active = False
                
                logger.info("正方计时器启动")
                if self.affirmative_time > 0:
                    self.timer.start(1000)
                    self.affirmative_timer_active = True
                else:
                    logger.warning("正方时间已用完")
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
            else:
                # 确保两个计时器不同时运行
                if self.affirmative_timer_active:
                    self.affirmative_timer_active = False
                
                logger.info("反方计时器启动")
                if self.negative_time > 0:
                    self.timer.start(1000)
                    self.negative_timer_active = True
                else:
                    logger.warning("反方时间已用完")
        except Exception as e:
            logger.error(f"切换反方计时器时出错: {e}", exc_info=True)

    def reset_timer(self, duration=None):
        """重置计时器"""
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
                    half_time = self.current_round['time'] // 2
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
                    self.current_time = self.current_round['time']
                else:
                    self.current_time = 0
        
        self.timeUpdated.emit()
    
    def terminate_current_round(self):
        """强制终止当前回合"""
        logger.info("终止当前回合")
        try:
            self.timer.stop()
            self.timer_active = False
            self.affirmative_timer_active = False
            self.negative_timer_active = False
            self.reset_timer(duration=0)
            return True
        except Exception as e:
            logger.error(f"终止回合时出错: {e}", exc_info=True)
            return False

    def update_time(self):
        """更新计时器时间"""
        if self.is_free_debate:
            # 自由辩论模式：更新活动中的一方计时器
            if self.affirmative_timer_active and self.affirmative_time > 0:
                self.affirmative_time -= 1
                if self.affirmative_time == 0:
                    self.affirmativeTimerFinished.emit()
            
            elif self.negative_timer_active and self.negative_time > 0:
                self.negative_time -= 1
                if self.negative_time == 0:
                    self.negativeTimerFinished.emit()
            
            # 检查总体时间是否结束
            if self.affirmative_time == 0 and self.negative_time == 0:
                logger.info("自由辩论环节结束")
                self.timer.stop()
                self.timerFinished.emit()
        else:
            # 标准计时模式
            if self.current_time > 0:
                self.current_time -= 1
                if self.current_time == 0:
                    self.timerFinished.emit()
        
        self.timeUpdated.emit()
    
    def set_current_round(self, round_data):
        """设置当前环节数据"""
        self.current_round = round_data
        self.is_free_debate = round_data.get('type') == "自由辩论" if round_data else False
        
        if round_data:
            self.current_time = round_data['time']
            if self.is_free_debate:
                half_time = round_data['time'] // 2
                self.affirmative_time = half_time
                self.negative_time = half_time
            
    def get_timer_state(self):
        """获取计时器状态"""
        return {
            'current_time': self.current_time,
            'affirmative_time': self.affirmative_time,
            'negative_time': self.negative_time,
            'timer_active': self.timer_active,
            'affirmative_timer_active': self.affirmative_timer_active,
            'negative_timer_active': self.negative_timer_active,
            'is_free_debate': self.is_free_debate
        }
