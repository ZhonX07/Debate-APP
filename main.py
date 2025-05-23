#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
辩论计时系统 - 主程序入口

本程序用于辩论赛计时和展示，支持多轮辩论，正反方计时，自由辩论等功能。
"""

import sys
import os
import argparse
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTranslator, QLocale, QTimer

# 导入程序模块
from utils import is_low_performance, logger
from display_board import DisplayBoard
from control_panel import ControlPanel

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="辩论计时系统")
    parser.add_argument('--config', '-c', help="配置文件路径", type=str)
    parser.add_argument('--low-performance', '-l', help="低性能模式", action='store_true')
    parser.add_argument('--debug', '-d', help="调试模式", action='store_true')
    parser.add_argument('--lang', help="界面语言，默认中文", default='zh_CN', choices=['zh_CN', 'en_US'])
    return parser.parse_args()

def setup_logging(debug_mode):
    """设置日志级别"""
    if debug_mode:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.DEBUG)
        logger.debug("调试模式已开启")
    else:
        logger.setLevel(logging.INFO)
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.INFO)

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 设置日志级别
    setup_logging(args.debug)
    
    # 自动检测是否启用低性能模式
    low_performance_mode = args.low_performance
    if not low_performance_mode:
        low_performance_mode = is_low_performance()
        if low_performance_mode:
            logger.info("自动检测到低性能硬件，启用低性能模式")
    
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 设置应用程序基本信息
    app.setApplicationName("辩论赛计时系统")
    app.setOrganizationName("BianlunTech")
    app.setOrganizationDomain("example.com")
    
    # 设置语言翻译
    translator = QTranslator()
    translator_path = os.path.join(os.path.dirname(__file__), "translations")
    if args.lang != 'zh_CN':
        if translator.load(f"debate_{args.lang}", translator_path):
            app.installTranslator(translator)
            logger.info(f"已加载语言: {args.lang}")
        else:
            logger.error(f"无法加载语言文件: {args.lang}")
    
    # 创建窗口
    display_board = DisplayBoard(low_performance_mode=low_performance_mode)
    control_panel = ControlPanel(display_board)
    
    # 设置控制面板引用
    display_board.set_control_panel(control_panel)
    
    # 显示窗口
    display_board.show()
    control_panel.show()
    
    # 如果提供了配置文件，自动加载
    if args.config and os.path.exists(args.config):
        try:
            logger.info(f"正在加载配置文件: {args.config}")
            # 这里应使用控制面板的方法来加载配置
            # 但我们需要一种方式来模拟用户加载文件的操作
            QTimer.singleShot(500, lambda: control_panel.load_config_from_path(args.config))
        except Exception as e:
            logger.error(f"自动加载配置文件失败: {e}")
    
    # 运行应用
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
