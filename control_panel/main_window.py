from PyQt5.QtWidgets import QProgressBar, QWidget, QGraphicsOpacityEffect, QLabel, QMainWindow
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
        
        # 固定尺寸 - 增加尺寸确保能完整显示
        self.setFixedSize(120, 120)  # 增加尺寸
        
        # 关闭默认样式，确保完全透明
        self.setTextVisible(False)  # 关闭默认文本显示
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
            QProgressBar::chunk {
                background-color: transparent;
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
        # 新增：强制立即重绘，确保进度条及时上色
        self.repaint()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        
        # 确保背景完全透明并清除背景
        painter.fillRect(self.rect(), Qt.transparent)
        
        # 调整绘制区域 - 确保整个圆环都在可见区域内
        size = min(self.width(), self.height()) - self.line_width * 2
        
        # 定义弧的边界矩形，考虑线宽并居中
        x_offset = (self.width() - size) / 2
        y_offset = (self.height() - size) / 2
        arc_rect = QRectF(x_offset, y_offset, size, size)
        
        # 首先绘制完整的背景环
        bg_pen = QPen(QColor(230, 230, 230, 70), self.line_width, Qt.SolidLine, Qt.RoundCap)
        bg_pen.setCosmetic(True)
        painter.setPen(bg_pen)
        painter.drawEllipse(arc_rect)
        
        # 绘制进度环
        progress = max(0.0, min(1.0, self._value / self._maximum))
        angle = 360 * progress
        
        # 设置进度环画笔
        pen = QPen(self.progress_color, self.line_width, Qt.SolidLine, Qt.RoundCap)
        pen.setCosmetic(True)
        painter.setPen(pen)
        
        # 修复：处理特殊情况
        if progress <= 0:
            # 进度为0时不绘制
            pass
        elif progress >= 1.0:
            # 进度为100%时绘制完整圆环
            painter.drawEllipse(arc_rect)
        else:
            # 正常情况绘制弧线
            # 注意：drawArc需要整数角度，转换为整数
            start_angle = int(90 * 16)  # QPainter使用16为单位的角度
            span_angle = int(-angle * 16)  # 逆时针，所以是负数
            
            # 正确的drawArc调用
            painter.drawArc(arc_rect, start_angle, span_angle)

        # 绘制中间文字
        painter.setPen(QPen(self.text_color, 1, Qt.SolidLine))
        
        # 修改：显示实际分秒而不是百分比 
        minutes = int(self._value) // 60
        seconds = int(self._value) % 60
        text = f"{minutes:02d}:{seconds:02d}"  # 显示为 mm:ss 格式
        
        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)  # 设置合适的字体大小
        painter.setFont(font)
        fm = painter.fontMetrics()
        text_rect = fm.boundingRect(text)
        
        # 修复: 使用整数坐标而不是浮点数
        center_x = int(self.width() / 2)
        center_y = int(self.height() / 2)
        painter.drawText(center_x - text_rect.width()//2,
                        center_y + text_rect.height()//2 - fm.descent(),
                        text)

class RoundedProgressBar(CircularProgressBar):
    """适配原有接口的环形进度条"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置为完全透明背景
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # 删除位置调整，让布局管理器控制
        self.setRadius(35)  # 增大尺寸
        self.setLineWidth(6)  # 确保线宽合适
        
    def setFormat(self, fmt):
        # 重写文字显示逻辑
        pass  # 文字已经在paintEvent中直接绘制

    def resizeEvent(self, event):
        """当控件大小改变时确保重绘"""
        super().resizeEvent(event)
        self.update()

    def showEvent(self, event):
        """当控件显示时确保完全重绘"""
        super().showEvent(event)
        self.update()
        self.repaint()

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

class ControlPanel(QMainWindow):
    """控制面板主窗口"""
    
    def __init__(self, display_board=None):
        super().__init__()
        # 初始化参数
        self.display_board = display_board
        self.rounds = []  # 存储回合信息的列表
        self.round_in_progress = False  # 回合进行中标志
        
        # 设置窗口标题
        self.setWindowTitle("辩论计时器 - 控制面板")
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口大小
        self.resize(800, 600)
        
        # 禁用窗口最大化
        self.setFixedSize(self.size())
        
        # 中心区域 - 用于放置主要控件
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # 布局管理
        from PyQt5.QtWidgets import QVBoxLayout
        layout = QVBoxLayout(central_widget)
        
        # 添加其他控件和布局
        # ... 这里是其他控件的初始化代码 ...
        
        # 初始化完成后，加载默认的回合设置
        self.load_default_rounds()
        
    def load_default_rounds(self):
        """加载默认的回合设置"""
        self.rounds = [
            {"description": "第一回合", "type": "自由辩论"},
            {"description": "第二回合", "type": "提问环节"},
            {"description": "第三回合", "type": "总结发言"},
        ]
        
        # 更新UI以显示加载的回合
        self.update_rounds_list()
        
    def update_rounds_list(self):
        """更新回合列表显示"""
        try:
            if not self.rounds_list:
                return
            
            # 清空现有项
            self.rounds_list.clear()
            
            # 添加回合描述
            for round_info in self.rounds:
                self.rounds_list.addItem(round_info.get("description", "未知回合"))
                
            # 自动选择第一项
            if self.rounds_list.count() > 0:
                self.rounds_list.setCurrentRow(0)
                
        except Exception as e:
            logger.error(f"更新回合列表时出错: {e}", exc_info=True)
    
    def start_round(self):
        """开始当前选择的环节"""
        try:
            if not self.display_board:
                self.show_error_message("未连接展示窗口")
                return
                
            # 获取当前选择的环节索引
            index = self.rounds_list.currentRow()
            if index < 0:
                self.show_error_message("请先选择一个环节")
                return
                
            # 设置回合进行中标志
            self.round_in_progress = True
            
            # 禁用左侧环节选择栏
            self.rounds_list.setEnabled(False)
            
            # 修改开始按钮状态
            self.start_button.setText("环节进行中...")
            self.start_button.setEnabled(False)
            
            # 启用结束按钮
            self.end_button.setEnabled(True)
            
            # 启动计时器
            success = self.display_board.start_round(index)
            if success:
                # 启用暂停和重置按钮
                self.toggle_button.setEnabled(True)
                self.reset_button.setEnabled(True)
                
                # 显示回合信息
                round_data = self.rounds[index]
                self.show_status_message(f"环节 {index+1} 已开始: {round_data.get('description', '')}")
                
                # 根据环节类型启用相应按钮
                is_free_debate = round_data.get('type') == "自由辩论"
                self.toggle_affirmative_button.setEnabled(is_free_debate)
                self.toggle_negative_button.setEnabled(is_free_debate)
                
            else:
                self.show_error_message("无法启动环节")
                
                # 恢复状态
                self.round_in_progress = False
                self.rounds_list.setEnabled(True)
                self.start_button.setText("开始环节")
                self.start_button.setEnabled(True)
                self.end_button.setEnabled(False)
                
        except Exception as e:
            logger.error(f"开始环节时出错: {e}", exc_info=True)
            self.show_error_message(f"开始环节时出错: {str(e)}")
    
    def end_round(self):
        """结束当前环节"""
        try:
            if not self.display_board:
                self.show_error_message("未连接展示窗口")
                return
                
            # 强制终止当前环节
            success = self.display_board.terminate_current_round()
            
            # 恢复界面状态
            self.round_in_progress = False
            self.rounds_list.setEnabled(True)
            self.start_button.setText("开始环节")
            self.start_button.setEnabled(True)
            self.end_button.setEnabled(False)
            
            # 禁用计时器控制按钮
            self.toggle_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            self.toggle_affirmative_button.setEnabled(False)
            self.toggle_negative_button.setEnabled(False)
            
            # 重置LCD显示
            self.reset_lcd_display()
            
            if success:
                self.show_status_message("环节已结束")
            else:
                self.show_error_message("无法结束环节")
                
        except Exception as e:
            logger.error(f"结束环节时出错: {e}", exc_info=True)
            self.show_error_message(f"结束环节时出错: {str(e)}")
    
    def on_round_finished(self):
        """当计时器自然结束时调用"""
        try:
            # 恢复界面状态
            self.round_in_progress = False
            self.rounds_list.setEnabled(True)
            self.start_button.setText("开始环节")
            self.start_button.setEnabled(True)
            self.end_button.setEnabled(False)
            
            # 禁用计时器控制按钮
            self.toggle_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            self.toggle_affirmative_button.setEnabled(False)
            self.toggle_negative_button.setEnabled(False)
            
            # 显示结束消息
            self.show_status_message("环节计时结束")
            
            # 自动选择下一个环节
            current_row = self.rounds_list.currentRow()
            if current_row < self.rounds_list.count() - 1:
                self.rounds_list.setCurrentRow(current_row + 1)
                
        except Exception as e:
            logger.error(f"处理环节结束事件时出错: {e}", exc_info=True)
    
    def on_round_selection_changed(self):
        """当环节选择改变时调用"""
        try:
            # 只有在非进行中状态才处理选择变更
            if not self.round_in_progress:
                current_row = self.rounds_list.currentRow()
                if current_row >= 0:
                    # 发送信号给展示窗口预览选择的环节
                    self.roundSelected.emit(current_row)
                    
                    # 更新当前选择的环节信息
                    round_data = self.rounds[current_row]
                    description = round_data.get('description', '')
                    is_free_debate = round_data.get('type') == "自由辩论"
                    
                    self.show_status_message(f"已选择回合 {current_row+1}: {description}")
                    logger.info(f"已选择回合 {current_row+1}: {description}")
                    
                    # 在环节更改时重置计时器
                    if hasattr(self, 'display_board') and self.display_board:
                        # 重置 LCD 显示
                        self.reset_lcd_display()
                        
                        # 重置计时器
                        self.display_board.reset_timer()
            
        except Exception as e:
            logger.error(f"处理环节选择变更时出错: {e}", exc_info=True)
    
    def next_round(self):
        """切换到下一个环节"""
        try:
            current_row = self.rounds_list.currentRow()
            if current_row < self.rounds_list.count() - 1:
                # 结束当前环节
                self.end_round()
                
                # 选择下一个环节
                self.rounds_list.setCurrentRow(current_row + 1)
                
                # 自动开始下一个环节
                self.start_round()
            else:
                self.show_status_message("已经是最后一个环节")
                
        except Exception as e:
            logger.error(f"切换到下一个环节时出错: {e}", exc_info=True)
    
    def prev_round(self):
        """切换到上一个环节"""
        try:
            current_row = self.rounds_list.currentRow()
            if current_row > 0:
                # 结束当前环节
                self.end_round()
                
                # 选择上一个环节
                self.rounds_list.setCurrentRow(current_row - 1)
                
                # 自动开始上一个环节
                self.start_round()
            else:
                self.show_status_message("已经是第一个环节")
                
        except Exception as e:
            logger.error(f"切换到上一个环节时出错: {e}", exc_info=True)
    
    def reset_lcd_display(self):
        """重置LCD显示"""
        self.lcd_display.display("00:00")
        self.affirmative_lcd.display("00:00")
        self.negative_lcd.display("00:00")