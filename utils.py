#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import logging
import logging.handlers  # 添加这行以导入 handlers 子模块
import tempfile
import ctypes
from html import escape
from PyQt5.QtWidgets import QFrame, QApplication
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient, QBrush
#123123
# 配置日志
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'logs'))
try:
    os.makedirs(log_dir, exist_ok=True)
except PermissionError:
    log_dir = os.path.join(tempfile.gettempdir(), 'debate_logs')
    os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger('debate_app')
logger.setLevel(logging.DEBUG)
# 修复了格式化字符串，确保没有"levellevel"这样的错误
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(log_dir, 'app.log'), 
    maxBytes=5*1024*1024, 
    backupCount=3, 
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# 确保日志处理器不重复添加
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

def highlight_markers(text, hl_color):
    """用指定颜色高亮文本中的 **标记内容**，并将整个文本加粗"""
    try:
        # 先进行HTML转义，防止XSS攻击
        text = escape(text)
        
        # 仅匹配成对出现的标记
        def repl(m):
            return f'<span style="color:{hl_color}; font-weight:bold;">{m.group(1)}</span>'
        
        # 修复正则表达式，确保只匹配完整的 **标记**
        html = re.sub(r'\*\*([^*]+?)\*\*', repl, text)
        
        # 将整个文本加粗（保留已经处理过的高亮部分）
        html = f'<span style="font-weight:bold;">{html}</span>'
        return html
    except Exception as e:
        logger.error(f"处理高亮标记时出错: {e}", exc_info=True)
        return escape(text)  # 出错时返回纯转义文本，确保安全

class GradientBorderFrame(QFrame):
    """创建带有渐变色边框的框架"""
    def __init__(self, *args, start_color, end_color, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_color = start_color
        self.end_color = end_color
        self.border_width = 4
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setContentsMargins(self.border_width, self.border_width,
                                self.border_width, self.border_width)

    def paintEvent(self, event):
        super().paintEvent(event)
        rect = QRectF(self.border_width/2, self.border_width/2,
                      self.width()-self.border_width,
                      self.height()-self.border_width)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor(self.start_color))
        gradient.setColorAt(1, QColor(self.end_color))
        pen = QPen()
        pen.setWidth(self.border_width)
        pen.setBrush(gradient)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 12, 12)

# Windows特效相关函数
def enable_acrylic_effect(hwnd, color):
    """
    为指定窗口启用亚克力模糊效果（Windows 10/11）
    
    Args:
        hwnd: 窗口句柄
        color: ARGB颜色值
    """
    if sys.platform != 'win32':
        return
        
    try:
        # Windows 10 1803+ 支持的SetWindowCompositionAttribute方法
        user32 = ctypes.windll.user32
        dwm = ctypes.windll.dwmapi
        
        class AccentPolicy(ctypes.Structure):
            _fields_ = [
                ('AccentState', ctypes.c_uint),
                ('AccentFlags', ctypes.c_uint),
                ('GradientColor', ctypes.c_uint),
                ('AnimationId', ctypes.c_uint)
            ]
            
        class WindowCompositionAttributeData(ctypes.Structure):
            _fields_ = [
                ('Attribute', ctypes.c_int),
                ('Data', ctypes.POINTER(AccentPolicy)),
                ('SizeOfData', ctypes.c_size_t)
            ]
        
        # 设置亚克力模糊
        policy = AccentPolicy()
        policy.AccentState = 3  # ACCENT_ENABLE_BLURBEHIND
        policy.GradientColor = color  # ARGB颜色
        
        data = WindowCompositionAttributeData()
        data.Attribute = 19  # WCA_ACCENT_POLICY
        data.Data = ctypes.pointer(policy)
        data.SizeOfData = ctypes.sizeof(policy)
        
        user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
    except Exception as e:
        logger.error(f"启用亚克力效果失败: {e}")

def enable_dwm_composition():
    """启用DWM硬件加速合成功能"""
    if sys.platform != 'win32':
        return
        
    try:
        # 尝试启用DWM硬件加速
        dwm = ctypes.windll.dwmapi
        
        # 检查是否支持DWM
        enabled = ctypes.c_bool()
        retcode = dwm.DwmIsCompositionEnabled(ctypes.byref(enabled))
        if retcode == 0 and not enabled:
            # 启用DWM硬件合成
            dwm.DwmEnableComposition(1)  # 1=DWM_EC_ENABLECOMPOSITION
            
    except Exception as e:
        logger.error(f"启用DWM合成失败: {e}")

# 添加低性能系统检测函数
def is_low_performance():
    """检测系统是否为低性能配置"""
    try:
        import platform
        import psutil
    except ImportError:
        # 如果无法导入psutil，默认非低性能
        return False
    try:
        # 检测Windows版本
        is_win7_or_older = False
        if platform.system() == 'Windows':
            win_ver = platform.version()
            # Windows 7或更早的版本
            is_win7_or_older = int(win_ver.split('.')[0]) < 10
        
        # 检测CPU性能
        cpu_count = psutil.cpu_count(logical=False)
        if cpu_count is None:
            cpu_count = psutil.cpu_count(logical=True)
        
        # 检测内存
        mem = psutil.virtual_memory()
        low_memory = mem.total < 4 * 1024 * 1024 * 1024  # 小于4GB内存
        
        # 如果是Windows 7或更早版本，并且CPU核心数少于4或内存小于4GB
        return is_win7_or_older and (cpu_count < 4 or low_memory)
    except Exception as e:
        logger.error(f"性能检测失败: {e}")
        return False
