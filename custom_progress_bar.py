from PyQt5.QtWidgets import QProgressBar, QWidget, QGraphicsOpacityEffect, QLabel
from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint, QPointF
from PyQt5.QtGui import QPainter, QColor, QFontMetrics, QPen, QBrush, QPainterPath, QConicalGradient
import logging
import math

logger = logging.getLogger('debate_app.custom_progress_bar')
class CircularProgressBar(QProgressBar):
    """空心环形进度条 - 完全透明背景，无阴影效果"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 默认样式设置
        self.line_width = 6               # 环形宽度
        self.background_color = Qt.transparent   # 设置背景为透明
        self.progress_color = "#0078D4"    # 进度环颜色
        self.text_color = Qt.black        # 文字颜色
        self.radius = 40                  # 环形半径
        self._value = 0
        self._maximum = 100               # 添加最大值属性
        
        # 固定尺寸
        self.setFixedSize(100, 100)
        
        # 关闭默认样式，确保完全透明
        self.setTextVisible(True)
        self.setStyleSheet("""
            QProgressBar {
                background-color: transparent;
                border: none;
                font-family: 微软雅黑;
                font-size: 14px;
                font-weight: bold;
                /* 移除所有可能的阴影和边框效果 */
                outline: none;
                margin: 0px;
                padding: 0px;
            }
        """)
        
        # 确保控件本身也是完全透明的
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint)

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

    def setMaximum(self, value):
        """设置最大值"""
        self._maximum = max(1, value)  # 确保最大值至少为1
        self.update()
        
    def maximum(self):
        """获取最大值"""
        return self._maximum
        
    def setValue(self, value):
        """设置当前值"""
        self._value = min(max(0, value), self._maximum)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        
        # 确保背景完全透明
        painter.fillRect(self.rect(), Qt.transparent)
        
        # 计算中心点和半径
        center = self.rect().center()
        
        # 绘制进度环
        progress = max(0.0, min(1.0, self._value / self._maximum))
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
        
        # 设置进度环画笔，无阴影效果
        pen = QPen(self.progress_color, self.line_width, Qt.SolidLine, Qt.RoundCap)
        pen.setCosmetic(True)  # 确保线条不受缩放影响
        painter.setPen(pen)
        painter.drawPath(progress_path)

        # 绘制中间文字，无阴影效果
        painter.setPen(QPen(self.text_color, 1, Qt.SolidLine))
        text = f"{int(progress*100)}%"
        fm = painter.fontMetrics()
        text_rect = fm.boundingRect(text)
        painter.drawText(center.x() - text_rect.width()//2,
                        center.y() + text_rect.height()//2 - fm.descent(),
                        text)

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
        logger.info("DynamicIslandManager: 更新回合显示")
        self.force_clear_all()       # 安全清除残留内容
        self.update_existing_elements()  # 更新现有控件内容

    def update_existing_elements(self):
        """复用现有控件更新内容"""
        if self.parent:
            # 确保只更新文本内容而不创建新控件
            existing_labels = [child for child in self.parent.children() if isinstance(child, QLabel)]
            for label in existing_labels:
                label.setText("")  # 清空旧内容
                label.setStyleSheet("")  # 重置样式
                # 这里可以添加具体的内容更新逻辑

    def force_clear_all(self):
        """安全清除内容而不销毁控件"""
        logger.info("安全清除灵动岛内容")
        try:
            # 立即停止所有动画
            for anim in self.animations:
                if anim and anim.state() == anim.Running:
                    anim.stop()
            self.animations.clear()
            
            # 清除当前元素
            self.current_elements.clear()
            
            # 移除所有阴影效果
            self.remove_all_shadow_effects()
            
            # 如果有父控件，强制重绘
            if self.parent:
                # 隐藏父控件以避免渲染重叠
                was_visible = self.parent.isVisible()
                self.parent.setVisible(False)
                
                # 强制处理所有待处理事件
                try:
                    from PyQt5.QtWidgets import QApplication
                    QApplication.processEvents()
                except ImportError:
                    logger.warning("无法导入 QApplication，跳过 processEvents 调用")
                
                # 强制清除和重绘
                self.parent.update()
                self.parent.repaint()
                
                # 恢复可见性
                if was_visible:
                    self.parent.setVisible(True)
                    
        except Exception as e:
            logger.error(f"强制清除灵动岛内容时出错: {e}", exc_info=True)

    def remove_all_shadow_effects(self):
        """移除所有控件的阴影效果"""
        try:
            if not self.parent:
                return
                
            # 递归移除所有子控件的阴影效果
            self._remove_widget_shadows(self.parent)
            
            logger.info("已移除所有控件的阴影效果")
            
        except Exception as e:
            logger.error(f"移除阴影效果时出错: {e}", exc_info=True)
    
    def _remove_widget_shadows(self, widget):
        """递归移除控件及其子控件的阴影效果"""
        try:
            from PyQt5.QtWidgets import QGraphicsDropShadowEffect
            
            # 移除当前控件的阴影效果
            effect = widget.graphicsEffect()
            if isinstance(effect, QGraphicsDropShadowEffect):
                widget.setGraphicsEffect(None)
                logger.debug(f"已移除控件 {widget.objectName()} 的阴影效果")
            
            # 递归处理子控件
            for child in widget.children():
                if hasattr(child, 'graphicsEffect'):
                    self._remove_widget_shadows(child)
                    
        except Exception as e:
            logger.warning(f"处理控件阴影时出错: {e}")

    def force_text_update(self, target_widget, new_text, style=""):
        """强制更新文本，确保没有残留和阴影效果"""
        try:
            if not target_widget:
                return
                
            # 隐藏控件
            was_visible = target_widget.isVisible()
            target_widget.setVisible(False)
            
            # 移除阴影效果
            from PyQt5.QtWidgets import QGraphicsDropShadowEffect
            effect = target_widget.graphicsEffect()
            if isinstance(effect, QGraphicsDropShadowEffect):
                target_widget.setGraphicsEffect(None)
            
            # 清除旧文本
            target_widget.clear()
            target_widget.setStyleSheet("")
            
            # 强制处理事件
            try:
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
            except ImportError:
                pass
            
            # 设置新文本和无阴影样式
            target_widget.setText(new_text)
            enhanced_style = style + """
                border: none;
                outline: none;
                background-color: transparent;
            """
            if enhanced_style:
                target_widget.setStyleSheet(enhanced_style)
            
            # 强制重绘
            target_widget.update()
            target_widget.repaint()
            
            # 恢复可见性
            if was_visible:
                target_widget.setVisible(True)
                target_widget.update()
                target_widget.repaint()
                
        except Exception as e:
            logger.error(f"强制文本更新时出错: {e}", exc_info=True)

    def animate_elements_out(self):
        logger.info("执行现有元素的下沉动画")
        # 停止任何正在运行的动画
        for anim in self.animations:
            if anim and anim.state() == anim.Running:
                anim.stop()
        self.animations.clear()

    def clear_elements(self):
        """清除所有元素"""
        self.current_elements.clear()
        if self.parent:
            self.parent.update()

    def ensure_island_empty(self):
        """确保灵动岛区域完全为空"""
        self.current_elements.clear()
        if self.parent:
            # 强制立即重绘
            self.parent.update()
            self.parent.repaint()

    def draw_progress_bar(self):
        """绘制进度条"""
        logger.info("开始绘制新的进度条")
        # 实现进度条绘制逻辑
        pass

# 使用示例
# 创建 DynamicIslandManager 实例，并在每个回合调用 start_round()。# 使用示例# 创建 DynamicIslandManager 实例，并在每个回合调用 start_round()。
