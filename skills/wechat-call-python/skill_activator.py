#!/usr/bin/env python3
"""
微信电话自动化技能激活器
用于在Moltbot中激活Python版本的wechat-call技能
"""

import os
import sys
import subprocess
import re
from pathlib import Path

# 技能配置
SKILL_NAME = "wechat-call-python"
SKILL_DIR = Path(__file__).parent
PYTHON_SCRIPT = SKILL_DIR / "wechat_call.py"

# 触发模式
TRIGGER_PATTERNS = [
    r"用微信给(.+?)打电话",
    r"用微信给(.+?)拨打语音",
    r"微信电话(.+?)",
    r"拨打微信语音(.+?)",
    r"微信打电话给(.+)"
]

def extract_username(message):
    """从消息中提取用户名"""
    for pattern in TRIGGER_PATTERNS:
        match = re.search(pattern, message)
        if match:
            return match.group(1).strip()
    
    # 如果没有匹配的模式，返回原消息
    return message.strip()

def should_activate(message):
    """检查是否应该激活技能"""
    message = message.strip()
    
    # 检查是否匹配任何触发模式
    for pattern in TRIGGER_PATTERNS:
        if re.search(pattern, message):
            return True
    
    return False

def activate_skill(message, debug=False, simulate=False, confidence=0.9):
    """激活技能"""
    if not PYTHON_SCRIPT.exists():
        return {
            "success": False,
            "error": f"Python脚本不存在: {PYTHON_SCRIPT}"
        }
    
    # 提取用户名
    username = extract_username(message)
    
    # 构建命令行参数
    cmd = [sys.executable, str(PYTHON_SCRIPT), "--user", username]
    
    if debug:
        cmd.append("--debug")
    
    if simulate:
        cmd.append("--simulate")
    
    if confidence != 0.9:
        cmd.extend(["--confidence", str(confidence)])
    
    try:
        # 执行Python脚本
        result = subprocess.run(
            cmd,
            cwd=SKILL_DIR,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300  # 5分钟超时
        )
        
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd)
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "执行超时（5分钟）"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="微信电话自动化技能激活器")
    parser.add_argument("message", help="用户消息")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--simulate", action="store_true", help="模拟模式")
    parser.add_argument("--confidence", type=float, default=0.9, help="模板匹配置信度")
    parser.add_argument("--check-only", action="store_true", help="仅检查是否激活")
    
    args = parser.parse_args()
    
    if args.check_only:
        # 仅检查是否应该激活
        should = should_activate(args.message)
        username = extract_username(args.message) if should else None
        print(f"检查结果: {'激活' if should else '不激活'}")
        if should:
            print(f"提取的用户名: {username}")
        sys.exit(0 if should else 1)
    
    # 激活技能
    result = activate_skill(
        args.message,
        debug=args.debug,
        simulate=args.simulate,
        confidence=args.confidence
    )
    
    if result["success"]:
        print("技能执行成功!")
        if result["stdout"]:
            print("\n输出:")
            print(result["stdout"])
    else:
        print("技能执行失败!")
        print(f"错误: {result.get('error', '未知错误')}")
        if result.get("stderr"):
            print("\n错误输出:")
            print(result["stderr"])
        sys.exit(1)

if __name__ == "__main__":
    main()