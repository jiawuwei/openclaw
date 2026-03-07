#!/usr/bin/env python3
"""
微信电话自动化技能安装脚本
用于设置Python环境和依赖
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """打印横幅"""
    print("=" * 60)
    print("微信电话自动化技能 - Python版本安装脚本")
    print("=" * 60)
    print()

def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    
    version = sys.version_info
    print(f"当前Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("错误: 需要Python 3.8或更高版本")
        return False
    
    print("✓ Python版本检查通过")
    print()
    return True

def check_platform():
    """检查平台"""
    print("检查平台...")
    
    current_platform = platform.system()
    print(f"当前平台: {current_platform}")
    
    supported_platforms = ["Windows", "Darwin", "Linux"]
    if current_platform not in supported_platforms:
        print(f"警告: 平台 {current_platform} 可能不完全支持")
        print(f"支持平台: {', '.join(supported_platforms)}")
    else:
        print(f"✓ 平台 {current_platform} 支持")
    
    print()
    return current_platform

def install_dependencies():
    """安装依赖"""
    print("安装依赖...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"错误: 找不到 requirements.txt 文件: {requirements_file}")
        return False
    
    print(f"使用依赖文件: {requirements_file}")
    
    try:
        # 安装依赖
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 依赖安装成功")
            if result.stdout:
                print("安装输出:")
                print(result.stdout[:500])  # 只显示前500字符
        else:
            print("✗ 依赖安装失败")
            if result.stderr:
                print("错误输出:")
                print(result.stderr)
            return False
        
    except Exception as e:
        print(f"✗ 安装过程中出现异常: {e}")
        return False
    
    print()
    return True

def check_dependencies():
    """检查依赖是否已安装"""
    print("检查依赖...")
    
    dependencies = [
        ("pyautogui", "pyautogui"),
        ("Pillow", "PIL"),
        ("numpy", "numpy"),
        ("pyperclip", "pyperclip")
    ]
    
    all_installed = True
    
    for display_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"✓ {display_name} 已安装")
        except ImportError:
            print(f"✗ {display_name} 未安装")
            all_installed = False
    
    # 检查可选依赖
    try:
        __import__("cv2")
        print("✓ OpenCV (opencv-python) 已安装 (可选)")
    except ImportError:
        print("• OpenCV (opencv-python) 未安装 (可选依赖)")
    
    print()
    return all_installed

def test_basic_functionality():
    """测试基本功能"""
    print("测试基本功能...")
    
    tests = [
        ("模板文件检查", lambda: check_template_files()),
        ("脚本可执行性", lambda: check_script_executability()),
        ("导入测试", lambda: check_imports()),
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                print(f"✓ {test_name} 通过")
            else:
                print(f"✗ {test_name} 失败")
                all_passed = False
        except Exception as e:
            print(f"✗ {test_name} 异常: {e}")
            all_passed = False
    
    print()
    return all_passed

def check_template_files():
    """检查模板文件"""
    skill_dir = Path(__file__).parent
    
    required_files = ["soupic.png", "dianhua.png"]
    
    for file_name in required_files:
        file_path = skill_dir / file_name
        if not file_path.exists():
            print(f"  警告: 缺少模板文件: {file_name}")
            return False
    
    return True

def check_script_executability():
    """检查脚本可执行性"""
    skill_dir = Path(__file__).parent
    
    required_scripts = ["wechat_call.py", "skill_activator.py"]
    
    for script_name in required_scripts:
        script_path = skill_dir / script_name
        if not script_path.exists():
            print(f"  警告: 缺少脚本文件: {script_name}")
            return False
    
    return True

def check_imports():
    """检查导入"""
    skill_dir = Path(__file__).parent
    sys.path.insert(0, str(skill_dir))
    
    try:
        # 尝试导入主要模块
        from wechat_call import Config, Logger, Utils
        return True
    except Exception as e:
        print(f"  导入失败: {e}")
        return False

def create_quick_start_guide():
    """创建快速开始指南"""
    print("快速开始指南:")
    print("-" * 40)
    print()
    
    skill_dir = Path(__file__).parent
    
    print("1. 模拟测试:")
    print(f"   python {skill_dir / 'skill_activator.py'} \"用微信给测试用户打电话\" --simulate")
    print()
    
    print("2. 带调试的实际测试:")
    print(f"   python {skill_dir / 'skill_activator.py'} \"用微信给测试用户打电话\" --debug")
    print()
    
    print("3. 实际拨打电话:")
    print(f"   python {skill_dir / 'skill_activator.py'} \"用微信给可乐煮鸡打电话\"")
    print()
    
    print("4. 使用自定义置信度:")
    print(f"   python {skill_dir / 'skill_activator.py'} \"用微信给测试用户打电话\" --confidence 0.85")
    print()
    
    print("5. 运行测试套件:")
    print(f"   python {skill_dir / 'test_wechat_call.py'}")
    print()
    
    print("-" * 40)

def main():
    """主函数"""
    print_banner()
    
    # 检查Python版本
    if not check_python_version():
        return 1
    
    # 检查平台
    current_platform = check_platform()
    
    # 询问是否安装依赖
    print("安装选项:")
    print("1. 自动安装所有依赖")
    print("2. 仅检查当前依赖状态")
    print("3. 退出")
    
    choice = input("\n请选择 (1-3): ").strip()
    
    if choice == "3":
        print("退出安装")
        return 0
    
    if choice == "1":
        if not install_dependencies():
            return 1
    
    # 检查依赖
    dependencies_ok = check_dependencies()
    
    if not dependencies_ok and choice != "1":
        print("警告: 部分依赖未安装")
        print("建议运行安装选项1来自动安装依赖")
        retry = input("是否现在安装依赖? (y/n): ").strip().lower()
        if retry == 'y':
            if not install_dependencies():
                return 1
            dependencies_ok = check_dependencies()
    
    # 测试功能
    if not test_basic_functionality():
        print("警告: 部分功能测试失败")
        print("技能可能无法正常工作")
    
    # 平台特定建议
    print("平台特定建议:")
    if current_platform == "Windows":
        print("• Windows平台: 确保微信客户端已安装并登录")
        print("• 快捷键: Ctrl+Alt+W 用于激活微信窗口")
    elif current_platform == "Darwin":
        print("• macOS平台: 可能需要权限设置")
        print("• 快捷键: Command+Tab 用于切换应用")
        print("• 需要在系统偏好设置中授予辅助功能权限")
    elif current_platform == "Linux":
        print("• Linux平台: 确保已安装必要的X11工具")
        print("• 可能需要设置DISPLAY环境变量")
    
    print()
    
    # 显示快速开始指南
    create_quick_start_guide()
    
    print("=" * 60)
    print("安装完成!")
    print("现在可以在Moltbot中使用微信电话自动化技能了")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n安装被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n安装过程中出现未预期的错误: {e}")
        sys.exit(1)