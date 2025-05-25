from PyQt5.QtWidgets import QProgressBar, QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint, QPointF
from PyQt5.QtGui import QPainter, QColor, QFontMetrics, QPen, QBrush, QPainterPath, QConicalGradient
import logging
import math

logger = logging.getLogger('debate_app.custom_progress_bar')
class CircularProgressBar(QProgressBar):
    """空心环形进度条"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 默认样式设置
        self.line_width = 6               # 环形宽度
        self.background_color = Qt.transparent   # 设置背景为透明
        self.progress_color = "#0078D4"    # 进度环颜色
        self.text_color = Qt.black        # 文字颜色
        self.radius = 40                  # 环形半径
        self._value = 0
        
        # 固定尺寸
        self.setFixedSize(100, 100)
        
        # 关闭默认样式
        self.setTextVisible(True)
        self.setStyleSheet("""
            QProgressBar {
                background-color: transparent;
                border: none;
                font-family: 微软雅黑;
                font-size: 14px;
                font-weight: bold;
            }
        """)

    def setLineWidth(self, width):
        self.line_width = width
        self.update()

    def setRadius(self, radius):
        # 改进8: 考虑DPI缩放
        try:
            device_pixel_ratio = self.devicePixelRatioF()
        except AttributeError:  # 低版本Qt可能没有这个方法
            device_pixel_ratio = 1.0
        self.radius = radius * device_pixel_ratio
        self.update()

    def setProgressColor(self, color):
        self.progress_color = QColor(color)
        self.update()

    def setBackgroundColor(self, color):
        # This method might still be called, but the paintEvent won't use self.background_color for drawing a background ring.
        self.background_color = QColor(color)
        self.update()

    def setTextColor(self, color):
        self.text_color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        
        # 计算中心点和半径
        center = self.rect().center()
        # radius = min(self.width(), self.height()) // 2 - self.line_width # This radius was for the background ring

        # 绘制进度环
        # The progress ring will be drawn based on the widget's rect directly
        progress = max(0.0, min(1.0, self._value / (self.maximum() - self.minimum())))
        angle = 360 * progress
        
        progress_path = QPainterPath()
        # Define the bounding rectangle for the arc, considering the line width
        arc_rect_x = self.line_width / 2
        arc_rect_y = self.line_width / 2
        arc_rect_w = self.width() - self.line_width
        arc_rect_h = self.height() - self.line_width
        arc_rect = QRectF(arc_rect_x, arc_rect_y, arc_rect_w, arc_rect_h)

        progress_path.arcMoveTo(arc_rect, 90)  # 从12点方向开始
        progress_path.arcTo(arc_rect, 90, -angle)  # 逆时针绘制
        
        painter.setPen(QPen(self.progress_color, self.line_width, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(progress_path)

        # 绘制中间文字
        painter.setPen(self.text_color)
        text = f"{int(progress*100)}%"
        fm = painter.fontMetrics() # Use painter.fontMetrics()
        text_rect = fm.boundingRect(text)
        painter.drawText(center.x() - text_rect.width()//2,
                        center.y() + text_rect.height()//2 - fm.descent(),
                        text)

    def setValue(self, value):
        self._value = value
        self.update()

class RoundedProgressBar(CircularProgressBar):
    """适配原有接口的环形进度条"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 位置调整到左上角
        self.move(20, 20)  # 根据实际布局调整坐标
        self.setRadius(30)  # 更紧凑的尺寸
        
    def setFormat(self, fmt):
        # 重写文字显示逻辑
        pass  # 文字已经在paintEvent中直接绘制

class DynamicIslandManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.current_elements = []  # 存储当前绘制的元素
        self.animations = []  # 存储活动动画

    def start_round(self):
        """开始新的回合时更新灵动岛的显示逻辑"""
        logger.info("DynamicIslandManager: 初始化新回合")
        self.animate_elements_out()  # 下沉现有元素
        self.clear_elements()        # 清除所有内容
        self.ensure_island_empty()   # 确保岛内无元素
        self.draw_progress_bar()     # 开始绘制进度条

    def animate_elements_out(self):
        logger.info("执行现有元素的下沉动画")
        # 停止任何正在运行的动画
        for anim in self.animations:
            if anim and anim.state() == QPropertyAnimation.Running:
                anim.stop()
                anim.deleteLater()
        
        self.animations.clear()
        
        for element in self.current_elements:
            anim = QPropertyAnimation(element, b"pos")
            anim.setDuration(300)
            anim.setEasingCurve(QEasingCurve.InQuad)
            anim.setStartValue(element.pos())
            anim.setEndValue(element.pos() + QPoint(0, 50))
            
            # 存储动画引用以防止提前垃圾回收
            element.animation = anim
            self.animations.append(anim)
            
            anim.start()

    def clear_elements(self):
        logger.info("清除灵动岛上的所有内容")
        # 改进3: 更安全的资源清理
        for element in self.current_elements:
            # 停止关联的动画
            if hasattr(element, 'animation'):
                if element.animation and element.animation.state() == QPropertyAnimation.Running:
                    element.animation.stop()
                element.animation = None
            
            # 从UI中删除元素
            element.hide()
            element.deleteLater()
            
        # 确保动画也被清理
        for anim in self.animations:
            if anim:
                anim.stop()
                anim.deleteLater()
                
        self.animations.clear()
        self.current_elements.clear()

    def ensure_island_empty(self):
        # 改进9: 防御性编程，避免断言崩溃
        if self.current_elements:
            logger.warning("灵动岛未完全清空，强制清理残留元素")
            self.clear_elements()
        else:
            logger.info("确认灵动岛内无元素")

    def draw_progress_bar(self):
        logger.info("开始绘制进度条")
        if not self.parent:
            logger.error("无法绘制进度条：父容器未设置")
            return
            
        progress_bar = CircularProgressBar(self.parent)
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        
        # 改进2: 动态居中定位
        parent_width = self.parent.width() if hasattr(self.parent, 'width') else 400
        size = 100  # 默认大小
        
        # 水平居中布局
        progress_bar.setGeometry(
            (parent_width - size) // 2,  # 水平居中
            20,  # 顶部间距
            size, 
            size
        )

        self.current_elements.append(progress_bar)
        progress_bar.show()
        
        # 添加入场动画
        opacity_effect = QGraphicsOpacityEffect(progress_bar)
        opacity_effect.setOpacity(0.0)
        progress_bar.setGraphicsEffect(opacity_effect)
        
        anim = QPropertyAnimation(opacity_effect, b"opacity")
        anim.setDuration(500)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # 存储动画引用
        progress_bar.animation = anim
        self.animations.append(anim)
        
        anim.start()

# 使用示例
# 创建 DynamicIslandManager 实例，并在每个回合调用 start_round()。