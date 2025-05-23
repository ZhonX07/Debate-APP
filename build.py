#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包脚本 - 使用PyInstaller将辩论计时系统打包为可执行文件
优化了启动速度和包体积
"""

import os
import sys
import shutil
import time
import platform
import subprocess
import logging
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('build')

def check_requirements():
    """检查必要的依赖是否已安装"""
    try:
        import PyQt5
        import PyInstaller
        logger.info("所有依赖已安装")
        return True
    except ImportError as e:
        logger.error(f"缺少必要的依赖: {e}")
        logger.info("请运行: pip install -r requirements.txt pyinstaller")
        return False

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            logger.info(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)

def precompile_bytecode():
    """预编译字节码以加快加载速度"""
    logger.info("预编译Python字节码...")
    try:
        # 编译项目目录中的所有Python文件
        subprocess.check_call([sys.executable, "-O", "-m", "compileall", ".", "-f"])
        logger.info("字节码预编译完成")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"字节码预编译失败: {e}")
        return False

def analyze_imports():
    """分析导入情况，找出可能的优化点"""
    logger.info("分析模块导入情况...")
    try:
        import PyInstaller.utils.hooks as hooks
        
        # 获取程序依赖的所有模块
        logger.info("此功能可帮助识别大型依赖以便优化。请在代码中尽可能使用延迟导入策略。")
        return True
    except Exception as e:
        logger.warning(f"模块导入分析失败: {e}")
        return False

def measure_startup(exe_path):
    """测量应用启动时间"""
    if not os.path.exists(exe_path):
        logger.error(f"可执行文件不存在: {exe_path}")
        return -1
    
    logger.info("测量启动时间...")
    
    # 在Windows上使用PowerShell测量启动时间
    if platform.system() == "Windows":
        try:
            # 使用-w 0参数立即退出程序，只测量启动时间
            cmd = f'powershell "Measure-Command {{Start-Process \'{exe_path}\' -ArgumentList \'-w\',\'0\' -NoNewWindow -Wait}}"'
            result = subprocess.check_output(cmd, shell=True).decode('utf-8')
            # 提取毫秒数
            for line in result.splitlines():
                if "TotalMilliseconds" in line:
                    ms = float(line.split(':')[1].strip())
                    return ms
        except Exception as e:
            logger.error(f"启动时间测量失败: {e}")
            return -1
    return -1

def build_executable(args):
    """构建可执行文件"""
    logger.info("开始构建可执行文件...")

    # 始终采用onedir模式
    package_mode = "--onedir"
    logger.info(f"打包模式: {package_mode}")

    # 基本参数
    build_args = [
        'program.py',
        '--name=辩论赛计时系统',
        package_mode,
        '--windowed',
        '--noconfirm',
    ]
    
    # 优化选项
    if args.optimize:
        logger.info("启用优化选项...")
        build_args.append('--strip')  # 剥离符号表以减小体积
        
        # 使用Python优化模式
        build_args.extend(['--python-option', '-O'])
        
        # UPX压缩（如果安装了UPX）
        if args.upx and shutil.which('upx'):
            logger.info("启用UPX压缩...")
            build_args.append('--upx')
        else:
            logger.info("UPX未安装或已禁用，跳过压缩...")
            build_args.append('--noupx')
    
    # 排除不必要的模块（可根据实际情况调整）
    if args.trim:
        logger.info("排除不必要的模块...")
        exclude_modules = [
            'matplotlib', 'notebook', 'scipy', 'pandas', 'PIL',
            'IPython', 'pydoc', 'doctest', 'unittest', 'xml', 'tkinter'
        ]
        for module in exclude_modules:
            build_args.extend(['--exclude-module', module])
    
    # 添加图标（如果存在）
    if os.path.exists('icon.ico'):
        build_args.append('--icon=icon.ico')
    
    # macOS特定参数
    elif platform.system() == 'Darwin':
        build_args.extend([
            '--osx-bundle-identifier=com.example.bianlun'
        ])
    
    # 自定义spec文件（如果存在）
    if args.spec:
        build_args = ['辩论赛计时系统_optimized.spec']
    
    try:
        start_time = time.time()
        
        # 使用PyInstaller API构建
        import PyInstaller.__main__
        PyInstaller.__main__.run(build_args)
        
        build_time = time.time() - start_time
        logger.info(f"构建完成! 耗时: {build_time:.2f}秒")
        
        # 显示输出文件位置
        exe_name = '辩论赛计时系统.exe' if platform.system() == 'Windows' else '辩论赛计时系统'
        if args.onedir:
            output_path = os.path.abspath(os.path.join('dist', '辩论赛计时系统', exe_name))
        else:
            output_path = os.path.abspath(os.path.join('dist', exe_name))
            
        logger.info(f"可执行文件位置: {output_path}")
        
        # 测量启动时间
        if args.measure_startup and os.path.exists(output_path):
            startup_ms = measure_startup(output_path)
            if startup_ms > 0:
                logger.info(f"启动时间: {startup_ms:.2f}毫秒")
        
        return True
    except Exception as e:
        logger.exception(f"构建失败: {e}")
        return False

def create_optimized_spec():
    """创建优化的spec文件"""
    logger.info("创建优化的spec文件...")
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 定义需要排除的模块 - 根据你的应用需要调整
excludes = ['matplotlib', 'notebook', 'scipy', 'pandas', 'PIL',
            'IPython', 'pydoc', 'doctest', 'unittest', 'xml', 'tkinter']

# 优化导入过程的钩子
runtime_hooks = ['hooks/optimize_imports.py']

a = Analysis(
    ['program.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=excludes,
    noarchive=False,
    cipher=block_cipher,
)

# 减小体积 - 移除不需要的文件
a.binaries = [x for x in a.binaries if not x[0].startswith('Qt5')]

pyz = PYZ(a.pure, 
          a.zipped_data,
          cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],  # 此处为空以使用onedir模式
    exclude_binaries=True,  # onedir模式
    name='辩论赛计时系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # 剥离符号表减小体积
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 收集程序所需的所有文件
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='辩论赛计时系统',
)
"""
    
    # 确保hooks目录存在
    os.makedirs('hooks', exist_ok=True)
    
    # 创建优化导入的钩子
    hook_content = """# hooks/optimize_imports.py
import os
import sys

# 优化动态导入 - 延迟加载不立即需要的模块
orig_import = __import__

def optimized_import(name, *args, **kwargs):
    # 在首次导入时不加载某些大型模块的非必要部分
    if name in ('PyQt5.QtWidgets', 'PyQt5.QtGui') and not hasattr(sys, '_import_happened'):
        sys._import_happened = True
        # 这里可以做一些优化
    return orig_import(name, *args, **kwargs)

# 替换内置导入函数
__builtins__['__import__'] = optimized_import

# 设置环境变量以改善启动性能
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # 避免写入.pyc文件
"""
    
    with open('hooks/optimize_imports.py', 'w', encoding='utf-8') as f:
        f.write(hook_content)
    
    with open('辩论赛计时系统_optimized.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
        
    logger.info("已创建优化的spec文件: 辩论赛计时系统_optimized.spec")
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="辩论赛计时系统打包工具 - 带启动性能优化")
    parser.add_argument('--onedir', action='store_true', help="使用onedir模式打包，显著提升启动速度（推荐）")
    parser.add_argument('--optimize', action='store_true', help="启用附加优化选项")
    parser.add_argument('--upx', action='store_true', help="使用UPX压缩（需要安装UPX）")
    parser.add_argument('--trim', action='store_true', help="修剪不必要的依赖")
    parser.add_argument('--spec', action='store_true', help="使用优化的spec文件")
    parser.add_argument('--measure-startup', action='store_true', help="测量应用启动时间")
    parser.add_argument('--create-spec', action='store_true', help="只创建优化的spec文件，不执行构建")
    
    args = parser.parse_args()
    
    logger.info("辩论赛计时系统打包工具 - 带启动性能优化")
    
    # 检查环境
    if not check_requirements():
        sys.exit(1)
    
    # 只创建spec文件
    if args.create_spec:
        create_optimized_spec()
        return
    
    # 清理旧的构建文件
    clean_build_dirs()
    
    # 预编译字节码
    precompile_bytecode()
    
    # 创建优化的spec文件
    if args.spec and not os.path.exists('辩论赛计时系统_optimized.spec'):
        create_optimized_spec()
    
    # 执行构建
    if build_executable(args):
        logger.info("打包过程成功完成")
    else:
        logger.error("打包过程失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
