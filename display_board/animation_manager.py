#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QGraphicsOpacityEffect
from utils import logger

class AnimationManager:
    """动画和过渡效果管理类"""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_animation = None
        
    def animate_widget_transition(self, from_widget, to_widget, stack_widget):
        """控件之间的平滑过渡动画，移除阴影效果避免层级感"""
        try:
            if self.current_animation and self.current_animation.state() == QPropertyAnimation.Running:
                self.current_animation.stop()
            
            # 移除控件的阴影效果
            self._remove_shadow_effects(from_widget)
            self._remove_shadow_effects(to_widget)
            
            # 创建动画组
            self.current_animation = QParallelAnimationGroup()
            
            # 确保控件有透明度效果，如果没有则创建
            from_opacity = self._ensure_opacity_effect(from_widget)
            to_opacity = self._ensure_opacity_effect(to_widget)
            
            # 淡出动画
            if from_opacity:
                fade_out = QPropertyAnimation(from_opacity, b"opacity")
                fade_out.setDuration(200)
                fade_out.setStartValue(1.0)
                fade_out.setEndValue(0.0)
                fade_out.setEasingCurve(QEasingCurve.OutQuad)
                self.current_animation.addAnimation(fade_out)
            
            # 淡入动画
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
    
    def _remove_shadow_effects(self, widget):
        """移除控件的阴影效果"""
        try:
            if widget:
                effect = widget.graphicsEffect()
                if isinstance(effect, QGraphicsDropShadowEffect):
                    widget.setGraphicsEffect(None)
                    logger.debug(f"已移除控件 {widget.objectName()} 的阴影效果")
        except Exception as e:
            logger.warning(f"移除阴影效果时出错: {e}")
    
    def _ensure_opacity_effect(self, widget):
        """确保控件有透明度效果，如果没有则创建"""
        try:
            if not widget:
                return None
                
            effect = widget.graphicsEffect()
            if not isinstance(effect, QGraphicsOpacityEffect):
                # 移除现有效果并创建透明度效果
                widget.setGraphicsEffect(None)
                opacity_effect = QGraphicsOpacityEffect()
                opacity_effect.setOpacity(1.0)
                widget.setGraphicsEffect(opacity_effect)
                return opacity_effect
            return effect
        except Exception as e:
            logger.warning(f"设置透明度效果时出错: {e}")
            return None
    
    def stop_current_animation(self):
        """停止当前动画"""
        if self.current_animation and self.current_animation.state() == QPropertyAnimation.Running:
            self.current_animation.stop()
            self.current_animation = None
