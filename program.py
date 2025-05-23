#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import os
import re  # 添加 re 模块导入
from html import escape  # 添加HTML转义以防XSS攻击
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                            QHBoxLayout, QWidget, QPushButton, QInputDialog, 
                            QGridLayout, QSpinBox, QLineEdit, QListWidget, 
                            QFrame, QFileDialog, QMessageBox, QGraphicsDropShadowEffect, 
                            QGroupBox, QStyle, QGraphicsColorizeEffect, QStackedLayout,
                            QProgressBar, QGraphicsOpacityEffect, QSizePolicy, QLCDNumber) # 添加 QLCDNumber
from PyQt5.QtCore import (Qt, QTimer, QSize, QTime, pyqtSignal, pyqtSlot, QPropertyAnimation, 
                        QRect, QPoint, QEasingCurve, QSequentialAnimationGroup, 
                        QParallelAnimationGroup, QRectF, QAbstractAnimation) # 添加 QAbstractAnimation, QTime
from PyQt5.QtGui import QFont, QKeyEvent, QPalette, QColor, QPainter, QPen, QLinearGradient, QPixmap, QBrush # 添加 QPainter, QPen

import logging
from logging.handlers import RotatingFileHandler
import ctypes  # 添加ctypes库用于Windows API调用

# 引入配置管理模块
try:
    from config_manager import DebateConfig, ConfigValidationError
except ImportError:
    # 如果模块不存在，定义一个最小占位符，防止程序崩溃
    class ConfigValidationError(Exception):
        pass

    class DebateConfig:
        @classmethod
        def from_file(cls, file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return cls(data)
            except Exception as e:
                raise ConfigValidationError(f"配置文件解析失败: {e}")

        def __init__(self, data):
            self.data = data

        def to_dict(self):
            return self.data

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
        print(f"启用亚克力效果失败: {e}")

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
        print(f"启用DWM合成失败: {e}")

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

# 修复日志配置 - 确保格式正确并使用绝对路径
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'logs'))
try:
    os.makedirs(log_dir, exist_ok=True)
except PermissionError:
    logger.error("无权限创建日志目录，回退到临时目录")
    log_dir = os.path.join(tempfile.gettempdir(), 'debate_logs')
    os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger('debate_app')
logger.setLevel(logging.DEBUG)
# 修复了格式化字符串，确保没有"levellevel"这样的错误
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
file_handler = RotatingFileHandler(os.path.join(log_dir, 'app.log'), maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# 确保日志处理器不重复添加
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# 在程序顶部引入自定义进度条
try:
    from custom_progress_bar import RoundedProgressBar
except ImportError:
    # 如果模块不存在，使用基本进度条替代
    RoundedProgressBar = QProgressBar

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


class DisplayBoard(QMainWindow):
    """前台展示窗口，用于显示给观众"""
    def __init__(self, low_performance_mode=False):
        super().__init__()
        logger.info("DisplayBoard 初始化")
        self.title = "辩论背景看板"
        self.topic = "等待设置辩题" # 内部仍可存储，但不显示
        self.affirmative_school = ""
        self.affirmative_viewpoint = "" # 新增
        self.negative_school = ""
        self.negative_viewpoint = ""  # 新增
        self.debater_roles = {}  # 存储辩手角色到姓名的映射
        self.low_performance_mode = low_performance_mode  # 添加低性能模式标志
        
        self.current_time = 0
        # 新增：自由辩论双计时器时间变量
        self.affirmative_time = 0
        self.negative_time = 0
        self.timer_active = False
        # 新增：正反方计时器状态
        self.affirmative_timer_active = False
        self.negative_timer_active = False
        self.current_round = None
        self.rounds = []
        self.current_round_index = -1
        self.is_fullscreen = False
        self.control_panel = None  # 添加对控制面板的引用
        self.is_free_debate = False  # 新增：是否为自由辩论标志
        
        # 低性能模式下的特殊处理
        if low_performance_mode:
            logger.info("启用低性能模式")
            # 减少窗口阴影和特效
            self.setGraphicsEffect(None)
        
        # 移除透明背景设置
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setStyleSheet("background-color: transparent;")
        
        # 设置白色背景
        self.setStyleSheet("background-color: white;")
        
        # 优化渲染属性
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)
        
        # 移除此处的OpenGL设置（窗口句柄尚未准备好）
        # if not self.low_performance_mode:
        #     self.windowHandle().setSurfaceType(QWindow.OpenGLSurface)
        
        self.initUI()
        logger.info("DisplayBoard UI 初始化完成")
        
        # 启用Windows硬件加速（如果可用）
        if sys.platform == 'win32':
            try:
                enable_dwm_composition()  # 启用DWM硬件加速
                # 在show()之后，使用self.winId()获取窗口句柄来启用亚克力效果
            except Exception as e:
                logger.error(f"无法启用Windows硬件加速: {e}")

    def initUI(self):
        logger.debug("DisplayBoard.initUI 开始")
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 1680, 945) # 默认窗口大小
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 设置背景 - 移除背景图片引用，改用纯色背景
        self.bg_label = QLabel(central_widget)
        self.bg_label.setObjectName("backgroundLabel")
        self.bg_label.setStyleSheet("background-color: #f5f5f5;")  # 使用浅灰色作为背景
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        
        # 毛玻璃效果层 - 半透明白色层
        self.blur_effect = QLabel(central_widget)
        self.blur_effect.setObjectName("blurEffect")
        self.blur_effect.setStyleSheet("background-color: rgba(255, 255, 255, 1.0);")
        self.blur_effect.setGeometry(0, 0, self.width(), self.height())
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 创建顶部容器 - 用于辩题显示
        topic_container = QFrame()
        topic_container.setObjectName("topicContainer")
        topic_container.setStyleSheet("""
            #topicContainer {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        # 为顶部容器添加阴影效果
        topic_shadow = QGraphicsDropShadowEffect()
        topic_shadow.setBlurRadius(15)
        topic_shadow.setColor(QColor(0, 0, 0, 40))
        topic_shadow.setOffset(0, 2)
        topic_container.setGraphicsEffect(topic_shadow)
        
        # self.topic_stack 原来包含 topic_label, round_info_label, next_info_label
        # 现在我们用新的控件替换它们
        if hasattr(self, 'topic_label'): self.topic_label.deleteLater()
        if hasattr(self, 'round_info_label'): self.round_info_label.deleteLater()
        if hasattr(self, 'next_info_label'): self.next_info_label.deleteLater()

        self.topic_stack = QStackedLayout(topic_container) # Re-assign or ensure it's clean

        self._create_preview_widget_top()
        self._create_active_round_widget_top()

        self.topic_stack.addWidget(self.preview_widget_top)  # Index 0
        self.topic_stack.addWidget(self.active_round_widget_top) # Index 1
        
        self.topic_stack.setCurrentWidget(self.preview_widget_top)
        self.current_top_widget_anim = None # To manage ongoing animations

        main_layout.addWidget(topic_container, 10) # Adjusted stretch factor for top container
        
        # 创建左右两侧的布局
        sides_layout = QHBoxLayout()
        sides_layout.setContentsMargins(0, 0, 0, 0)
        sides_layout.setSpacing(15)
        
        # 创建正方（左侧）部件 - 使用渐变边框
        affirmative_widget = GradientBorderFrame(start_color="#0078D4", end_color="#50B0E0")
        affirmative_widget.setObjectName("affirmativeWidget")
        affirmative_widget.setStyleSheet("""
            #affirmativeWidget {
                background-color: white;
                border-radius: 12px;
            }
        """)
        affirmative_shadow = QGraphicsDropShadowEffect()
        affirmative_shadow.setBlurRadius(20)
        affirmative_shadow.setColor(QColor(0, 0, 0, 50))
        affirmative_shadow.setOffset(0, 4)
        affirmative_widget.setGraphicsEffect(affirmative_shadow)
        self.affirmative_layout = QVBoxLayout(affirmative_widget)
        self.affirmative_layout.setContentsMargins(20, 20, 20, 20)
        self.affirmative_layout.setSpacing(10)
        affirmative_title = QLabel("正方")
        affirmative_title.setAlignment(Qt.AlignCenter)
        affirmative_title.setFont(QFont("微软雅黑", 48, QFont.Bold))
        affirmative_title.setStyleSheet("color: #0078D4;")
        self.affirmative_school_label = QLabel(self.affirmative_school)
        self.affirmative_school_label.setAlignment(Qt.AlignCenter)
        self.affirmative_school_label.setFont(QFont("微软雅黑", 20))
        self.affirmative_school_label.setStyleSheet("color: #0078D4;")
        affirmative_separator = QFrame()
        affirmative_separator.setFrameShape(QFrame.HLine)
        affirmative_separator.setFrameShadow(QFrame.Sunken)
        affirmative_separator.setStyleSheet("background-color: rgba(0, 120, 212, 0.3); margin: 10px 30px;")
        affirmative_separator.setFixedHeight(2)
        self.affirmative_viewpoint_label = QLabel(self.affirmative_viewpoint)
        self.affirmative_viewpoint_label.setAlignment(Qt.AlignCenter)
        self.affirmative_viewpoint_label.setWordWrap(True)
        self.affirmative_viewpoint_label.setFont(QFont("微软雅黑", 16))
        self.affirmative_viewpoint_label.setStyleSheet("color: #323130;")
        self.affirmative_layout.addWidget(affirmative_title)
        self.affirmative_layout.addWidget(self.affirmative_school_label)
        self.affirmative_layout.addWidget(affirmative_separator)
        self.affirmative_layout.addWidget(self.affirmative_viewpoint_label)
        self.affirmative_layout.addStretch()
        
        # 创建反方（右侧）部件 - 使用渐变边框
        negative_widget = GradientBorderFrame(start_color="#D13438", end_color="#E85A5E")
        negative_widget.setObjectName("negativeWidget")
        negative_widget.setStyleSheet("""
            #negativeWidget {
                background-color: white;
                border-radius: 12px;
            }
        """)
        negative_shadow = QGraphicsDropShadowEffect()
        negative_shadow.setBlurRadius(20)
        negative_shadow.setColor(QColor(0, 0, 0, 50))
        negative_shadow.setOffset(0, 4)
        negative_widget.setGraphicsEffect(negative_shadow)
        self.negative_layout = QVBoxLayout(negative_widget)
        self.negative_layout.setContentsMargins(20, 20, 20, 20)
        self.negative_layout.setSpacing(10)
        negative_title = QLabel("反方")
        negative_title.setAlignment(Qt.AlignCenter)
        negative_title.setFont(QFont("微软雅黑", 48, QFont.Bold))
        negative_title.setStyleSheet("color: #D13438;")
        self.negative_school_label = QLabel(self.negative_school)
        self.negative_school_label.setAlignment(Qt.AlignCenter)
        self.negative_school_label.setFont(QFont("微软雅黑", 20))
        self.negative_school_label.setStyleSheet("color: #D13438;")
        negative_separator = QFrame()
        negative_separator.setFrameShape(QFrame.HLine)
        negative_separator.setFrameShadow(QFrame.Sunken)
        negative_separator.setStyleSheet("background-color: rgba(209, 52, 56, 0.3); margin: 10px 30px;")
        negative_separator.setFixedHeight(2)
        self.negative_viewpoint_label = QLabel(self.negative_viewpoint)
        self.negative_viewpoint_label.setAlignment(Qt.AlignCenter)
        self.negative_viewpoint_label.setWordWrap(True)
        self.negative_viewpoint_label.setFont(QFont("微软雅黑", 16))
        self.negative_viewpoint_label.setStyleSheet("color: #323130;")
        self.negative_layout.addWidget(negative_title)
        self.negative_layout.addWidget(self.negative_school_label)
        self.negative_layout.addWidget(negative_separator)
        self.negative_layout.addWidget(self.negative_viewpoint_label)
        self.negative_layout.addStretch()
        
        sides_layout.addWidget(affirmative_widget)
        sides_layout.addWidget(negative_widget)
        
        # --------- 只保留北京时间的底部区域 ---------
        self.beijing_time_label = QLabel()
        self.beijing_time_label.setAlignment(Qt.AlignCenter)
        self.beijing_time_label.setFont(QFont("微软雅黑", 32, QFont.Bold))
        self.beijing_time_label.setStyleSheet("color: #323130;")
        self.update_beijing_time()  # 初始化一次
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_beijing_time)
        self.clock_timer.start(1000)
        main_layout.addLayout(sides_layout, 78)
        main_layout.addWidget(self.beijing_time_label, 10)
        # --------- END ---------

        # 设置计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.bg_label.lower()

        self.showNormal()
        logger.debug("DisplayBoard.initUI 结束")

    def update_beijing_time(self):
        """更新北京时间"""
        current_time = QTime.currentTime()
        time_text = f"北京时间：{current_time.toString('HH:mm:ss')}"
        self.beijing_time_label.setText(time_text)
        logger.debug(f"更新时间：{time_text}")

    def _optimize_label_rendering(self, label, color):
        """优化标签渲染效果"""
        label.setStyleSheet(f"color: {color};")
        label.setFont(QFont("微软雅黑", 12))  # 根据实际需要调整字体大小
        label.setGraphicsEffect(QGraphicsColorizeEffect())  # 添加颜色效果
        label.setAttribute(Qt.WA_TranslucentBackground)     # 启用透明背景
        label.setAttribute(Qt.WA_TranslucentBackground, True)
        label.setContentsMargins(0, 0, 0, 0)
    
    def _create_preview_widget_top(self):
        logger.debug("创建预览灵动岛控件")
        if hasattr(self, 'preview_widget_top'):
            self.preview_widget_top.deleteLater()
        self.preview_widget_top = QWidget()
        layout = QHBoxLayout(self.preview_widget_top) # 修改为 QHBoxLayout
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15) # 添加标签之间的间距

        self.preview_title_label = QLabel("下一环节:") # 添加冒号以示区分
        self.preview_title_label.setFont(QFont("微软雅黑", 18, QFont.Bold))
        self.preview_title_label.setAlignment(Qt.AlignCenter)
        # 优化文本渲染
        self._optimize_label_rendering(self.preview_title_label, "#323130")

        self.preview_type_label = QLabel("类型: N/A")
        self.preview_type_label.setFont(QFont("微软雅黑", 22, QFont.Bold)) # 可以考虑统一字体大小
        self.preview_type_label.setAlignment(Qt.AlignCenter)
        self._optimize_label_rendering(self.preview_type_label, "#0078D4")

        self.preview_desc_label = QLabel("描述: N/A")
        self.preview_desc_label.setFont(QFont("微软雅黑", 16))
        self.preview_desc_label.setAlignment(Qt.AlignCenter)
        self.preview_desc_label.setWordWrap(False) # 在单行中通常不希望自动换行
        self._optimize_label_rendering(self.preview_desc_label, "#605E5C")
        
        self.preview_time_label = QLabel("时长: N/A")
        self.preview_time_label.setFont(QFont("微软雅黑", 16))
        self.preview_time_label.setAlignment(Qt.AlignCenter)
        self._optimize_label_rendering(self.preview_time_label, "#605E5C")

        layout.addWidget(self.preview_title_label)
        layout.addWidget(self.preview_type_label)
        layout.addWidget(self.preview_desc_label)
        layout.addWidget(self.preview_time_label)
        
        # Opacity effect for animation
        opacity_effect = QGraphicsOpacityEffect(self.preview_widget_top)
        opacity_effect.setOpacity(1.0)
        self.preview_widget_top.setGraphicsEffect(opacity_effect)

    def _create_active_round_widget_top(self):
        logger.debug("创建倒计时灵动岛控件")
        self.active_round_widget_top = QWidget()
        # 使用垂直布局组织所有元素
        main_layout = QVBoxLayout(self.active_round_widget_top)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # 添加当前环节标题信息
        self.active_round_title = QLabel("当前环节")
        self.active_round_title.setFont(QFont("微软雅黑", 16, QFont.Bold))
        self.active_round_title.setAlignment(Qt.AlignCenter)
        self.active_round_title.setStyleSheet("color: #323130;")
        main_layout.addWidget(self.active_round_title)
        
        # 添加当前发言者信息
        self.active_speaker_info = QLabel()
        self.active_speaker_info.setFont(QFont("微软雅黑", 14))
        self.active_speaker_info.setAlignment(Qt.AlignCenter)
        self.active_speaker_info.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.active_speaker_info)
        
        # 创建两个定时器容器：标准模式和自由辩论模式
        self.standard_timer_container = QWidget()
        self.free_debate_timer_container = QWidget()
        
        # 标准模式定时器布局
        timer_layout = QHBoxLayout(self.standard_timer_container)
        timer_layout.setContentsMargins(0, 0, 0, 0)
        timer_layout.setSpacing(10)
        timer_layout.setAlignment(Qt.AlignCenter)
        
        # 设置容器的大小策略为固定或首选
        self.standard_timer_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # 创建环形进度条
        self.active_progress_bar_top = RoundedProgressBar()
        size = int(min(self.width(), self.height()) * 0.15)
        size = max(80, size)  # 确保最小尺寸为80
        self.active_progress_bar_top.setFixedSize(size, size)
        
        # 设置颜色样式
        self.active_progress_bar_top.setLineWidth(4)
        self.active_progress_bar_top.setProgressColor(QColor("#0078D4"))
        self.active_progress_bar_top.setTextColor(QColor("#323130"))
        
        # 添加具体的倒计时数字标签
        self.countdown_label = QLabel()
        self.countdown_label.setFont(QFont("微软雅黑", 24, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("color: #323130;")
        
        # 添加进度条和倒计时到布局
        timer_layout.addWidget(self.active_progress_bar_top)
        timer_layout.addWidget(self.countdown_label)
        
        # 自由辩论模式下的双计时器布局
        free_debate_layout = QHBoxLayout(self.free_debate_timer_container)
        free_debate_layout.setContentsMargins(0, 0, 0, 0)
        free_debate_layout.setSpacing(10)
        free_debate_layout.setAlignment(Qt.AlignCenter)
        
        # 正方计时器组 - 修复重复定义问题
        aff_timer_group = QWidget()
        aff_timer_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        aff_timer_layout = QVBoxLayout(aff_timer_group)
        
        aff_title = QLabel("正方")
        aff_title.setAlignment(Qt.AlignCenter)
        aff_title.setFont(QFont("微软雅黑", 12, QFont.Bold))
        aff_title.setStyleSheet("color: #0078D4;")
        
        # 创建正方计时器布局，不再重复创建 aff_timer_group
        aff_timer_box = QHBoxLayout()
        
        # 创建正方环形进度条
        self.aff_progress_bar = RoundedProgressBar()
        self.aff_progress_bar.setFixedSize(size, size)
        self.aff_progress_bar.setLineWidth(4)
        self.aff_progress_bar.setProgressColor(QColor("#0078D4"))
        self.aff_progress_bar.setTextColor(QColor("#323130"))
        self.aff_progress_bar.setObjectName("aff_progress_bar")
        
        # 正方倒计时标签
        self.aff_countdown_label = QLabel()
        self.aff_countdown_label.setFont(QFont("微软雅黑", 20, QFont.Bold))
        self.aff_countdown_label.setAlignment(Qt.AlignCenter)
        self.aff_countdown_label.setStyleSheet("color: #323130;")
        
        aff_timer_box.addWidget(self.aff_progress_bar)
        aff_timer_box.addWidget(self.aff_countdown_label)
        aff_timer_layout.addWidget(aff_title)
        aff_timer_layout.addLayout(aff_timer_box)
        
        # 反方计时器组 - 同样修复重复定义问题
        neg_timer_group = QWidget()
        neg_timer_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        neg_timer_layout = QVBoxLayout(neg_timer_group)
        
        neg_title = QLabel("反方")
        neg_title.setAlignment(Qt.AlignCenter)
        neg_title.setFont(QFont("微软雅黑", 12, QFont.Bold))
        neg_title.setStyleSheet("color: #C42B1C;")
        
        # 创建反方计时器布局，不再重复创建 neg_timer_group
        neg_timer_box = QHBoxLayout()
        
        # 创建反方环形进度条
        self.neg_progress_bar = RoundedProgressBar()
        self.neg_progress_bar.setFixedSize(size, size)
        self.neg_progress_bar.setLineWidth(4)
        self.neg_progress_bar.setProgressColor(QColor("#C42B1C"))
        self.neg_progress_bar.setTextColor(QColor("#323130"))
        self.neg_progress_bar.setObjectName("neg_progress_bar")
        
        # 反方倒计时标签
        self.neg_countdown_label = QLabel()
        self.neg_countdown_label.setFont(QFont("微软雅黑", 20, QFont.Bold))
        self.neg_countdown_label.setAlignment(Qt.AlignCenter)
        self.neg_countdown_label.setStyleSheet("color: #323130;")
        
        neg_timer_box.addWidget(self.neg_progress_bar)
        neg_timer_box.addWidget(self.neg_countdown_label)
        neg_timer_layout.addWidget(neg_title)
        neg_timer_layout.addLayout(neg_timer_box)
        
        free_debate_layout.addWidget(aff_timer_group)
        free_debate_layout.addWidget(neg_timer_group)
        
        # 创建计时器容器堆栈
        self.timer_stack = QStackedLayout()
        self.timer_stack.addWidget(self.standard_timer_container)
        self.timer_stack.addWidget(self.free_debate_timer_container)
        self.timer_stack.setCurrentIndex(0)  # 默认显示标准计时器
        
        # 将计时器堆栈添加到主布局
        main_layout.addLayout(self.timer_stack)
        
        # 添加下一环节信息
        next_round_frame = QFrame()
        next_round_frame.setStyleSheet("background-color: rgba(240, 240, 240, 0.5); border-radius: 5px;")
        next_round_layout = QVBoxLayout(next_round_frame)
        next_round_layout.setContentsMargins(5, 5, 5, 5)
        next_round_layout.setSpacing(2)
        
        next_label = QLabel("下一环节")
        next_label.setFont(QFont("微软雅黑", 10))
        next_label.setAlignment(Qt.AlignCenter)
        next_label.setStyleSheet("color: #605E5C;")
        
        self.next_round_info = QLabel("准备中...")
        self.next_round_info.setFont(QFont("微软雅黑", 12))
        self.next_round_info.setAlignment(Qt.AlignCenter)
        self.next_round_info.setStyleSheet("color: #323130; font-weight: bold;")
        
        next_round_layout.addWidget(next_label)
        next_round_layout.addWidget(self.next_round_info)
        main_layout.addWidget(next_round_frame)
        
        # 配置为无背景和边框
        self.active_round_widget_top.setAutoFillBackground(False)
        self.active_round_widget_top.setStyleSheet(
            "background-color: transparent; border: none;"
        )

        # Opacity effect for animation
        opacity_effect_active = QGraphicsOpacityEffect(self.active_round_widget_top)
        opacity_effect_active.setOpacity(1.0) # Start with full opacity, will be set to 0 before fade-in
        self.active_round_widget_top.setGraphicsEffect(opacity_effect_active)

    def _update_active_round_widget_top_content(self):
        if not self.current_round:
            return
        
        # 获取当前环节数据
        current_round = self.current_round
        side = "正方" if current_round['side'] == 'affirmative' else "反方"
        side_color = "#0078D4" if current_round['side'] == 'affirmative' else "#C42B1C"
        # 检查是否是自由辩论环节
        self.is_free_debate = current_round.get('type') == "自由辩论"
        
        total = max(current_round.get('time', 0), 1)
        
        if self.is_free_debate:
            # 自由辩论模式 - 设置双计时器
            half_time = total // 2
            # 正方计时器
            self.aff_progress_bar.setRange(0, half_time)
            self.aff_progress_bar.setValue(0)
            self.affirmative_time = half_time
            minutes = self.affirmative_time // 60
            seconds = self.affirmative_time % 60
            self.aff_countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
            
            # 反方计时器
            self.neg_progress_bar.setRange(0, half_time)
            self.neg_progress_bar.setValue(0)
            self.negative_time = half_time
            minutes = self.negative_time // 60
            seconds = self.negative_time % 60
            self.neg_countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
        else:
            # 标准模式 - 设置单个计时器
            self.active_progress_bar_top.setProgressColor(QColor(side_color))
            self.active_progress_bar_top.setRange(0, total)
            self.active_progress_bar_top.setValue(0)
            
            # 设置倒计时文本
            minutes = total // 60
            seconds = total % 60
            self.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        # 更新下一环节信息
        next_round_idx = self.current_round_index + 1
        if next_round_idx < len(self.rounds):
            next_round = self.rounds[next_round_idx]
            next_side = "正方" if next_round['side'] == 'affirmative' else "反方"
            next_info = f"{next_side}{next_round['speaker']} - {next_round['type']}"
            self.next_round_info.setText(next_info)
        else:
            self.next_round_info.setText("辩论结束")

    def toggle_timer(self):
        """开启或暂停计时器"""
        if self.is_free_debate:
            # 在自由辩论模式下，此方法不直接操作计时器
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
    
    # 新增：正方计时器控制
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
                # 更新控制面板按钮状态
                if self.control_panel:
                    self.control_panel.aff_timer_btn.setText("开始")
                    self.control_panel.aff_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
            else:
                # 确保两个计时器不同时运行
                if self.negative_timer_active:
                    logger.info("停止反方计时，切换到正方")
                    self.timer.stop()
                    self.negative_timer_active = False
                    # 更新反方按钮状态
                    if self.control_panel:
                        self.control_panel.neg_timer_btn.setText("开始")
                        self.control_panel.neg_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
                
                logger.info("正方计时器启动")
                if self.affirmative_time > 0:
                    self.timer.start(1000)
                    self.affirmative_timer_active = True
                    # 更新控制面板按钮状态
                    if self.control_panel:
                        self.control_panel.aff_timer_btn.setText("暂停")
                        self.control_panel.aff_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPause")))
                else:
                    # 时间为0时给出提示
                    if self.control_panel:
                        QMessageBox.information(self.control_panel, "提示", "正方发言时间已用完")
        except Exception as e:
            logger.error(f"切换正方计时器时出错: {e}", exc_info=True)
    
    # 新增：反方计时器控制
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
                # 更新控制面板按钮状态
                if self.control_panel:
                    self.control_panel.neg_timer_btn.setText("开始")
                    self.control_panel.neg_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
            else:
                # 确保两个计时器不同时运行
                if self.affirmative_timer_active:
                    logger.info("停止正方计时，切换到反方")
                    self.timer.stop()
                    self.affirmative_timer_active = False
                    # 更新正方按钮状态
                    if self.control_panel:
                        self.control_panel.aff_timer_btn.setText("开始")
                        self.control_panel.aff_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
                
                logger.info("反方计时器启动")
                if self.negative_time > 0:
                    self.timer.start(1000)
                    self.negative_timer_active = True
                    # 更新控制面板按钮状态
                    if self.control_panel:
                        self.control_panel.neg_timer_btn.setText("暂停")
                        self.control_panel.neg_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPause")))
                else:
                    # 时间为0时给出提示
                    if self.control_panel:
                        QMessageBox.information(self.control_panel, "提示", "反方发言时间已用完")
        except Exception as e:
            logger.error(f"切换反方计时器时出错: {e}", exc_info=True)

    def reset_timer(self, duration=None):
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
                    half_time = self.current_round.get('time', 0) // 2
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
                    self.current_time = self.current_round.get('time', 0)
                else:
                    self.current_time = 0
        self.update_timer_display()
    
    # 新增：终止当前回合:
    def terminate_current_round(self):
        """强制终止当前回合，停止所有计时器并返回预览模式"""
        logger.info("终止当前回合")
        try:
            # 停止所有计时器
            self.timer.stop()
            self.timer_active = False
            self.affirmative_timer_active = False
            self.negative_timer_active = False
            
            # 重置计时显示
            self.reset_timer(duration=0)
            
            # 切换到下一环节的预览
            next_idx = self.current_round_index + 1
            if next_idx < len(self.rounds):
                self._update_preview_widget_top_content(next_idx)
            else:
                self._update_preview_widget_top_content(self.current_round_index)
                
            # 动画过渡到预览模式
            self._animate_top_widget_transition(self.active_round_widget_top, self.preview_widget_top)
            self.topic_stack.setCurrentWidget(self.preview_widget_top)
            return True
        except Exception as e:
            logger.error(f"终止回合时出错: {e}", exc_info=True)
            return False

    def update_time(self):
        if self.is_free_debate:
            # 自由辩论模式：更新活动中的一方计时器
            if self.affirmative_timer_active and self.affirmative_time > 0:
                self.affirmative_time -= 1
                # 更新控制面板上的LCD显示
                if self.control_panel:
                    minutes = self.affirmative_time // 60
                    seconds = self.affirmative_time % 60
                    self.control_panel.aff_timer_lcd.display(f"{minutes:02d}:{seconds:02d}")
                
                if self.affirmative_time == 0:
                    logger.info("正方发言时间结束")
                    self.timer.stop()
                    self.affirmative_timer_active = False
                    # 更新控制面板按钮状态
                    if self.control_panel:
                        self.control_panel.aff_timer_btn.setText("开始")
                        self.control_panel.aff_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
                        self.control_panel.neg_timer_btn.setEnabled(True)
            
            elif self.negative_timer_active and self.negative_time > 0:
                self.negative_time -= 1
                # 更新控制面板上的LCD显示
                if self.control_panel:
                    minutes = self.negative_time // 60
                    seconds = self.negative_time % 60
                    self.control_panel.neg_timer_lcd.display(f"{minutes:02d}:{seconds:02d}")
                
                if self.negative_time == 0:
                    logger.info("反方发言时间结束")
                    self.timer.stop()
                    self.negative_timer_active = False
                    # 更新控制面板按钮状态
                    if self.control_panel:
                        self.control_panel.neg_timer_btn.setText("开始")
                        self.control_panel.neg_timer_btn.setIcon(self.control_panel.style().standardIcon(getattr(QStyle, "SP_MediaPlay")))
                        self.control_panel.aff_timer_btn.setEnabled(True)
            
            # 检查总体时间是否结束
            if self.affirmative_time == 0 and self.negative_time == 0:
                logger.info("自由辩论环节结束")
                self.timer.stop()
                next_round_idx = self.current_round_index + 1
                self._update_preview_widget_top_content(next_round_idx)
                self._animate_top_widget_transition(self.active_round_widget_top, self.preview_widget_top)
                
                # 更新控制面板状态
                if self.control_panel:
                    self.control_panel.aff_timer_btn.setEnabled(True)
                    self.control_panel.status_value.setText("自由辩论环节已结束")
        else:
            # 标准计时模式
            if self.current_time > 0:
                self.current_time -= 1
                if self.current_time == 0:
                    logger.info("当前环节倒计时结束")
                    self.timer.stop()
                    self.timer_active = False
                    next_round_idx = self.current_round_index + 1
                    self._update_preview_widget_top_content(next_round_idx)
                    self._animate_top_widget_transition(self.active_round_widget_top, self.preview_widget_top)
            
        self.update_timer_display()
    
    def update_timer_display(self):
        if self.is_free_debate:
            # 更新正方计时器()
            if hasattr(self, 'aff_progress_bar') and hasattr(self, 'aff_countdown_label'):
                total = self.current_round['time'] // 2
                current = total - self.affirmative_time
                self.aff_progress_bar._value = current
                self.aff_progress_bar.update()
                
                # 更新正方倒计时文本
                minutes = self.affirmative_time // 60
                seconds = self.affirmative_time % 60
                self.aff_countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
                
                # 当倒计时接近结束时改变文本颜色
                if self.affirmative_time <= 30:
                    self.aff_countdown_label.setStyleSheet("color: #C42B1C; font-weight: bold;")
                else:
                    self.aff_countdown_label.setStyleSheet("color: #323130; font-weight: bold;")
            
            # 更新反方计时器
            if hasattr(self, 'neg_progress_bar') and hasattr(self, 'neg_countdown_label'):
                total = self.current_round['time'] // 2
                current = total - self.negative_time
                self.neg_progress_bar._value = current
                self.neg_progress_bar.update()
                
                # 更新反方倒计时文本
                minutes = self.negative_time // 60
                seconds = self.negative_time % 60
                self.neg_countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
                
                # 当倒计时接近结束时改变文本颜色
                if self.negative_time <= 30:
                    self.neg_countdown_label.setStyleSheet("color: #C42B1C; font-weight: bold;")
                else:
                    self.neg_countdown_label.setStyleSheet("color: #323130; font-weight: bold;")
        else:
            # 标准模式计时器更新
            if self.current_round:
                total = self.current_round['time']
                current = total - self.current_time
                progress = current / total
            
                # 直接设置进度值
                self.active_progress_bar_top._value = current
                self.active_progress_bar_top.update()
                
                # 更新倒计时文本
                minutes = self.current_time // 60
                seconds = self.current_time % 60
                self.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
                
                # 当倒计时接近结束时，改变文本颜色提醒
                if self.current_time <= 30:
                    self.countdown_label.setStyleSheet("color: #C42B1C; font-weight: bold;")
                else:
                    self.countdown_label.setStyleSheet("color: #323130; font-weight: bold;")

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
                    index = control_panel.rounds_list.currentRow()
                    if index >= 0:
                        self._update_preview_widget_top_content(index)
            
        except Exception as e:
            logger.error(f"设置控制面板引用时出错: {e}", exc_info=True)
    
    def set_debate_config(self, config):
        """设置辩论配置信息
        
        Args:
            config: 包含辩论信息的字典，包括题目、学校、辩手和环节
        """
        logger.info("设置辩论配置")
        # 设置辩题和学校信息
        if 'topic' in config:
            self.topic = config['topic']
            self.setWindowTitle(f"辩论背景看板 - {self.topic}")
        
        # 设置正方信息
        if 'affirmative' in config:
            affirmative = config['affirmative']
            if 'school' in affirmative:
                self.affirmative_school = affirmative['school']
                self.affirmative_school_label.setText(self.affirmative_school)
            if 'viewpoint' in affirmative:
                self.affirmative_viewpoint = affirmative['viewpoint']
                # 调用高亮函数，并标记为富文本显示
                rich_html = highlight_markers(self.affirmative_viewpoint, "#0078D4")
                self.affirmative_viewpoint_label.setTextFormat(Qt.RichText)
                self.affirmative_viewpoint_label.setText(rich_html)
                
        # 设置反方信息
        if 'negative' in config:
            negative = config['negative']
            if 'school' in negative:
                self.negative_school = negative['school']
                self.negative_school_label.setText(self.negative_school)
            if 'viewpoint' in negative:
                self.negative_viewpoint = negative['viewpoint']
                # 调用高亮函数，并标记为富文本显示
                rich_html = highlight_markers(self.negative_viewpoint, "#D13438")
                self.negative_viewpoint_label.setTextFormat(Qt.RichText)
                self.negative_viewpoint_label.setText(rich_html)
                
        # 设置辩手角色映射
        if 'debaters' in config:
            self.debater_roles = config['debaters']
            # 更新辩手信息显示
            self.update_debaters_info()
        
        # 设置辩论环节
        if 'rounds' in config:
            self.rounds = config['rounds']
            self._update_preview_widget_top_content(0)
        logger.info("辩论配置已应用")
        return True

    def _update_preview_widget_top_content(self, index=None):
        """更新预览控件内容
        
        Args:
            index: 要预览的环节索引，如果为None则使用下一个环节
        """
        if not self.rounds:
            return
        
        # 确定要显示的环节
        if index is None:
            index = self.current_round_index + 1
        round_info = self.rounds[index]
        
        # 设置标题和类型
        self.preview_title_label.setText("下一环节:")
        self.preview_type_label.setText(round_info['type'])
        # 如果是自由辩论，特别标记
        if round_info.get('type') == "自由辩论":
            self.preview_type_label.setStyleSheet("color: #D13438; font-weight: bold;")
        else:
            self.preview_type_label.setStyleSheet("color: #0078D4; font-weight: bold;")
        
        # 设置描述
        side = "正方" if round_info['side'] == 'affirmative' else "反方"
        self.preview_desc_label.setText(f"{side} {round_info['speaker']}")
        
        # 设置时间
        minutes = round_info['time'] // 60
        seconds = round_info['time'] % 60
        self.preview_time_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        # 更新下一环节信息
        next_round_idx = self.current_round_index + 1
        if next_round_idx < len(self.rounds):
            next_round = self.rounds[next_round_idx]
            next_side = "正方" if next_round['side'] == 'affirmative' else "反方"
            next_info = f"{next_side}{next_round['speaker']} - {next_round['type']}"
            self.next_round_info.setText(next_info)
        else:
            self.next_round_info.setText("辩论结束")
        
        # 切换到预览模式时，重置动画
        if self.topic_stack.currentWidget() == self.preview_widget_top:
            self.current_top_widget_anim = None

    def _animate_top_widget_transition(self, from_widget, to_widget):
        """动画过渡两个顶部显示控件
        
        Args:
            from_widget: 当前显示的控件
            to_widget: 要切换到的控件
        """
        # 如果已经有动画在运行，先停止它
        if self.current_top_widget_anim:  self.current_top_widget_anim.stop()
        
        # 低性能模式下简化动画或直接切换
        if self.low_performance_mode:
            # 直接切换控件，不使用动画
            self.topic_stack.setCurrentWidget(to_widget)
            return
        
        # 创建一个并行动画组
        anim_group = QParallelAnimationGroup(self)    
        
        # 当前控件淡出效果
        fade_out = QPropertyAnimation(from_widget.graphicsEffect(), b"opacity")
        fade_out.setDuration(300)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.OutCubic)
        
        # 目标控件淡入效果
        fade_in = QPropertyAnimation(to_widget.graphicsEffect(), b"opacity")
        fade_in.setDuration(300)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.InCubic)
        
        # 添加动画到组
        anim_group.addAnimation(fade_out)
        anim_group.addAnimation(fade_in)
        
        # 保存并启动动画组
        self.current_top_widget_anim = anim_group
        anim_group.start()

    def start_round(self, index):
        """开始指定的辩论环节
        
        Args:
            index: 要开始的环节索引
        Returns:
            bool: 开始成功返回True，失败返回False
        """
        logger.info(f"开始环节: index={index}")
        if 0 <= index < len(self.rounds):
            self.current_round_index = index
            self.current_round = self.rounds[index]
            
            # 设置计时器
            self.current_time = self.current_round['time']
            # 配置活动控件
            self._update_active_round_widget_top_content()
            # 切换到活动视图
            self._animate_top_widget_transition(self.preview_widget_top, self.active_round_widget_top)
            return True
        return False
    
    def next_round(self):
        """切换到下一个环节
        
        Returns:
            bool: 切换成功返回True，失败返回False
        """
        logger.info("切换到下一环节")
        next_index = self.current_round_index + 1
        if 0 <= next_index < len(self.rounds):
            self.current_round_index = next_index
            self._update_preview_widget_top_content(next_index)
            return True
        return False
    
    def prev_round(self):
        """切换到上一个环节
        
        Returns:
            bool: 切换成功返回True，失败返回False
        """
        logger.info("切换到上一环节")
        prev_index = self.current_round_index - 1
        if prev_index >= 0:
            self.current_round_index = prev_index
            self._update_preview_widget_top_content(prev_index)
            return True
        return False
    
    def showEvent(self, event):
        logger.info("DisplayBoard 显示")
        try:
            super().showEvent(event)
            # 修复跨平台兼容问题
            if not self.low_performance_mode and sys.platform == 'win32' and self.windowHandle() is not None:
                try:
                    from PyQt5.QtGui import QSurface
                    self.windowHandle().setSurfaceType(QSurface.OpenGLSurface)
                except Exception as e:
                    logger.error(f"设置OpenGL表面失败: {e}")
        except Exception as e:
            logger.error(f"显示事件处理出错: {e}", exc_info=True)
    
    def update_debaters_info(self):
        """将辩手信息映射到界面标签"""
        logger.debug("更新辩手信息")
        try:
            roles = self.debater_roles
            # 这里假设UI中已定义了相应标签，实际应根据具体UI布局调整
            if hasattr(self, 'chair_label') and '主席' in roles:
                self.chair_label.setText(roles['主席'])
            if hasattr(self, 'recorder_label') and '记录' in roles:
                self.recorder_label.setText(roles['记录'])
                
            # 添加正方辩手信息
            for i in range(1, 5):
                role_key = f"正方{i}辩"
                if role_key in roles and hasattr(self, f'aff_{i}_label'):
                    getattr(self, f'aff_{i}_label').setText(roles[role_key])
                    
            # 添加反方辩手信息
            for i in range(1, 5):
                role_key = f"反方{i}辩"
                if role_key in roles and hasattr(self, f'neg_{i}_label'):
                    getattr(self, f'neg_{i}_label').setText(roles[role_key])
            
            logger.debug("辩手信息更新完成")
        except Exception as e:
            logger.error(f"更新辩手信息时出错: {e}", exc_info=True)

    def terminate_current_round(self):
        """强制终止当前回合，停止所有计时器并返回预览模式"""
        logger.info("终止当前回合")
        try:
            # 停止所有计时器
            self.timer.stop()
            self.timer_active = False
            self.affirmative_timer_active = False
            self.negative_timer_active = False
            
            # 重置计时显示
            self.reset_timer(duration=0)
            
            # 切换到下一环节的预览
            next_idx = self.current_round_index + 1
            if next_idx < len(self.rounds):
                self._update_preview_widget_top_content(next_idx)
            else:
                self._update_preview_widget_top_content(self.current_round_index)
                
            # 动画过渡到预览模式
            self._animate_top_widget_transition(self.active_round_widget_top, self.preview_widget_top)
            self.topic_stack.setCurrentWidget(self.preview_widget_top)
            return True
        except Exception as e:
            logger.error(f"终止回合时出错: {e}", exc_info=True)
            return False

    def onRoundSelected(self, index):
        """响应控制端环节选择，更新预览视图或当前环节"""
        logger.info(f"收到环节选择信号: index={index}")
        try:
            # 更新预览内容
            self._update_preview_widget_top_content(index)
            
            # 如果不是在计时中，则可以直接切换到预览模式
            if not self.timer_active:
                self.topic_stack.setCurrentWidget(self.preview_widget_top)
        except Exception as e:
            logger.error(f"处理环节选择时出错: {e}", exc_info=True)

# ControlPanel 类需要添加和修复的方法
class ControlPanel(QMainWindow): 
    """后台控制窗口，用于管理辩论计时和设置"""
    # 定义自定义信号
    roundSelected = pyqtSignal(int)
    roundTerminated = pyqtSignal()  # 新增：回合终止信号
    
    def __init__(self, display_board):
        super().__init__()
        logger.info("ControlPanel 初始化")
        self.display_board = display_board
        self.title = "辩论控制面板"
        self.current_config_file = ""
        self.debate_config = None
        self.is_free_debate = False  # 新增：标记当前是否为自由辩论回合
        
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
        config_layout = QHBoxLayout() #E1EFFF; color: #0078D4; } }
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
        main_layout.addWidget(rounds_frame, 1)
        
        # 右侧面板（控制区）)
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
        self.current_time_label.setStyleSheet("color: #605E5C;")
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
        timer_layout.addWidget(self.standard_timer_controls)
        
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
        
        # 添加终止按钮
        self.terminate_round_btn = QPushButton("结束回合")
        self.terminate_round_btn.setIcon(self.style().standardIcon(getattr(QStyle, "SP_DialogCancelButton")))
        self.terminate_round_btn.setStyleSheet("QPushButton { background-color: #D83B01; } QPushButton:hover { background-color: #B83301; } QPushButton:pressed { background-color: #A32D01; }")
        self.terminate_round_btn.clicked.connect(self.terminate_current_round)
        
        # 添加控件到计时器布局
        timer_layout.addLayout(self.timer_controls_stack)
        timer_layout.addWidget(self.terminate_round_btn)
        
        main_layout.addWidget(controls_frame, 2)
        
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
        main_layout.addWidget(status_frame, 0)

        # 初始化时禁用所有控制
        self.disable_controls()
        
    def load_config(self):
        """加载配置文件"""
        logger.info("加载配置文件")
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "JSON Files (*.json)", options=options
        )
        if file_path:
            try:
                # 读取并验证配置文件
                config = DebateConfig.from_file(file_path)
                self.current_config_file = file_path
                self.config_path_label.setText(os.path.basename(file_path))
                
                # 更新显示面板配置
                self.display_board.set_debate_config(config.to_dict())
                
                # 更新环节列表
                self.rounds_list.clear()
                for index, round_info in enumerate(config.data.get('rounds', [])):
                    side = "正方" if round_info['side'] == 'affirmative' else "反方"
                    item = QListWidgetItem(
                        f"{index+1}. [{side}] {round_info['speaker']} - {round_info['type']} ({round_info['time']}秒)"
                    )
                    self.rounds_list.addItem(item)
                
                # 启用控制按钮
                self.enable_controls()
                self.status_value.setText("配置已加载")
                logger.info(f"配置文件加载成功: {file_path}")
                
            except ConfigValidationError as e:
                QMessageBox.critical(self, "配置错误", f"配置文件验证失败:\n{e}")
                logger.error(f"配置文件验证失败: {e}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法加载配置文件:\n{e}")
                logger.error(f"加载配置文件失败: {e}", exc_info=True)
    
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
            if index >= 0 and hasattr(self, 'debate_config') and self.debate_config:
                round_info = self.debate_config.data['rounds'][index]
                side = "正方" if round_info['side'] == 'affirmative' else "反方"
                time_min = round_info['time'] // 60
                time_sec = round_info['time'] % 60
                self.current_round_label.setText(f"{side} {round_info['speaker']} - {round_info['type']}")
                self.current_time_label.setText(f"时长: {time_min}分{time_sec}秒")
                # 发射信号通知显示板更新预览
                self.roundSelected.emit(index)
                logger.debug(f"已选择环节: {index}")
        except Exception as e:
            logger.error(f"处理环节选择时出错: {e}", exc_info=True)

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
    
    def disable_controls(self):
        """禁用所有控制，直到加载配置"""
        logger.info("禁用所有控制")
        
        # 检查控制器按钮是否存在，避免引用不存在的控件
        if hasattr(self, 'save_config_btn'):
            self.save_config_btn.setEnabled(False)
        if hasattr(self, 'start_debate_btn'):
            self.start_debate_btn.setEnabled(False)
    
        # 计时器相关按钮
        self.timer_control_btn.setEnabled(False)
        self.reset_timer_btn.setEnabled(False)
        self.aff_timer_btn.setEnabled(False)
        self.neg_timer_btn.setEnabled(False)
        self.reset_free_debate_btn.setEnabled(False)
        
        # 导航按钮
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        
    def enable_controls(self):
        """启用所有控制"""
        logger.info("启用所有控制")
        # 计时器相关
        self.timer_control_btn.setEnabled(True)
        self.reset_timer_btn.setEnabled(True)
        self.aff_timer_btn.setEnabled(True)
        self.neg_timer_btn.setEnabled(True)
        self.reset_free_debate_btn.setEnabled(True)
        # 导航按钮
        self.prev_btn.setEnabled(True)
        self.next_btn.setEnabled(True)

    def start_current_round(self):
        """开始当前选中环节"""
        index = self.rounds_list.currentRow()
        if index < 0:
            QMessageBox.warning(self, "提示", "请先选择一个环节！")
            return
        # 调用显示面板的start_round方法
        if self.display_board.start_round(index):
            self.status_value.setText(f"已开始第{index+1}个环节")
            self.timer_controls_stack.setCurrentIndex(
                1 if self.display_board.is_free_debate else 0
            )
        else:
            QMessageBox.warning(self, "提示", "无法开始该环节！")