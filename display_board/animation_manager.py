#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from utils import logger

class AnimationManager:
    """动画和过渡效果管理类"""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_animation = None
        
    def animate_widget_transition(self, from_widget, to_widget, stack_widget):
        """控件之间的平滑过渡动画"""
        try:
            if self.current_animation and self.current_animation.state() == QPropertyAnimation.Running:
                self.current_animation.stop()
            
            # 创建动画组
            self.current_animation = QParallelAnimationGroup()
            
            # 淡出动画
            from_opacity = from_widget.graphicsEffect()
            if from_opacity:
                fade_out = QPropertyAnimation(from_opacity, b"opacity")
                fade_out.setDuration(200)
                fade_out.setStartValue(1.0)
                fade_out.setEndValue(0.0)
                fade_out.setEasingCurve(QEasingCurve.OutQuad)
                self.current_animation.addAnimation(fade_out)
            
            # 淡入动画
            to_opacity = to_widget.graphicsEffect()
            if to_opacity:
                fade_in = QPropertyAnimation(to_opacity, b"opacity")
                fade_in.setDuration(200)
                fade_in.setStartValue(0.0)
                fade_in.setEndValue(1.0)
                fade_in.setEasingCurve(QEasingCurve.InQuad)
                self.current_animation.addAnimation(fade_in)
            
            # 动画完成后切换控件
            def on_animation_finished():
                stack_widget.setCurrentWidget(to_widget)
                if to_opacity:
                    to_opacity.setOpacity(1.0)
            
            self.current_animation.finished.connect(on_animation_finished)
            self.current_animation.start()
            
        except Exception as e:
            logger.error(f"执行控件过渡动画时出错: {e}", exc_info=True)
            # 动画失败时直接切换
            stack_widget.setCurrentWidget(to_widget)
    
    def stop_current_animation(self):
        """停止当前动画"""
        if self.current_animation and self.current_animation.state() == QPropertyAnimation.Running:
            self.current_animation.stop()
            self.current_animation = None
