#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDP浏览器控制脚本 - 支持多分身
通过Chrome DevTools Protocol控制浏览器进行网页访问和搜索
每个分身独立端口和数据目录
"""

import socket
import subprocess
import time
import sys
import os
import json
import argparse
import urllib.request

# 配置 - 动态获取.openclaw目录
def get_openclaw_dir():
    """动态获取.openclaw目录"""
    if "OPENCLAW_PATH" in os.environ:
        return os.environ["OPENCLAW_PATH"]
    
    username = os.getenv("USERNAME") or os.getenv("USER") or "Administrator"
    openclaw_path = rf"C:\Users\{username}\.openclaw"
    
    if os.path.exists(openclaw_path):
        return openclaw_path
    
    # 尝试其他可能的用户目录
    users_dir = r"C:\Users"
    if os.path.exists(users_dir):
        for user in os.listdir(users_dir):
            user_openclaw = os.path.join(users_dir, user, ".openclaw")
            if os.path.exists(user_openclaw):
                return user_openclaw
    
    return openclaw_path


# 配置 - 动态获取工作目录
def get_workspace():
    """动态获取workspace目录"""
    # 优先使用环境变量
    if "OPENCLAW_WORKSPACE" in os.environ:
        return os.environ["OPENCLAW_WORKSPACE"]
    
    # 从.openclaw目录推断 - workspace是.openclaw的兄弟目录
    openclaw_dir = get_openclaw_dir()
    if openclaw_dir:
        # .openclaw 的父目录就是 workspace
        parent = os.path.dirname(openclaw_dir)
        workspace_candidate = os.path.join(parent, "workspace")
        if os.path.exists(workspace_candidate):
            return workspace_candidate
    
    # 从当前文件位置推断
    current_file = os.path.abspath(__file__)
    # skills/cdp-browser-control/cdp_browser.py -> skills -> workspace
    return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

WORKSPACE = get_workspace()


def get_chrome_path():
    """动态获取chromium路径 - 优先使用.openclaw目录"""
    openclaw_dir = get_openclaw_dir()
    
    # 优先查找.openclaw目录下的chromium
    openclaw_chrome = os.path.join(openclaw_dir, "chromium", "Application", "chrome.exe")
    if os.path.exists(openclaw_chrome):
        print(f"[INFO] 找到.openclaw chromium: {openclaw_chrome}")
        return openclaw_chrome
    
    # 尝试其他可能的.openclaw目录
    users_dir = r"C:\Users"
    if os.path.exists(users_dir):
        for user in os.listdir(users_dir):
            user_chrome = os.path.join(users_dir, user, ".openclaw", "chromium", "Application", "chrome.exe")
            if os.path.exists(user_chrome):
                print(f"[INFO] 找到chromium: {user_chrome}")
                return user_chrome
    
    # 最后尝试系统Chrome
    system_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for p in system_paths:
        if os.path.exists(p):
            print(f"[INFO] 找到系统Chrome: {p}")
            return p
    
    # 返回.openclaw下的默认路径
    print(f"[WARN] 未找到Chrome，使用默认路径: {openclaw_chrome}")
    return openclaw_chrome


def get_fen_port(fen_num):
    """获取分身端口号：1号=9301, 2号=9302, ..."""
    return 9300 + fen_num


def get_fen_dir(fen_num):
    """获取分身工作目录"""
    port = get_fen_port(fen_num)
    fen_dir = os.path.join(WORKSPACE, str(port))
    if not os.path.exists(fen_dir):
        os.makedirs(fen_dir, exist_ok=True)
        print(f"[INFO] 创建分身目录: {fen_dir}")
    return fen_dir


CHROME_PATH = get_chrome_path()


def check_port(host, port):
    """检查端口是否可用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0


def get_cdp_endpoints(port):
    """获取CDP端点列表"""
    cdp_json_url = f"http://localhost:{port}/json"
    try:
        with urllib.request.urlopen(cdp_json_url, timeout=5) as response:
            data = response.read()
            return json.loads(data)
    except Exception as e:
        print(f"[ERROR] 获取CDP端点失败: {e}")
        return []


def start_chrome(port, fen_num):
    """启动chromium浏览器并开启CDP"""
    fen_dir = get_fen_dir(fen_num)
    user_data_dir = os.path.join(fen_dir, "userdata")
    
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir, exist_ok=True)
    
    print(f"[INFO] 启动{fen_num}号分身浏览器")
    print(f"  - CDP端口: {port}")
    print(f"  - 用户数据目录: {user_data_dir}")
    
    cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={port}",
        f"--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--new-window",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1280,1000"
    ]
    
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[INFO] 浏览器启动命令已执行")
        
        # 等待浏览器启动
        for i in range(20):
            time.sleep(1)
            if check_port("localhost", port):
                print(f"[INFO] {fen_num}号分身浏览器已启动，CDP端口 {port} 可用")
                return True
            print(f"[INFO] 等待浏览器启动... ({i+1}/20)")
        
        print("[ERROR] 浏览器启动超时")
        return False
        
    except Exception as e:
        print(f"[ERROR] 启动浏览器失败: {e}")
        return False


def create_cdp_connection(ws_url):
    """创建CDP WebSocket连接"""
    try:
        import websocket
        ws = websocket.create_connection(ws_url, timeout=10)
        print(f"[INFO] 连接到CDP: {ws_url}")
        return ws
    except Exception as e:
        print(f"[ERROR] CDP连接失败: {e}")
        return None


def send_cdp_command(ws, method, params=None):
    """发送CDP命令"""
    if ws is None:
        return None
    
    msg = {"id": 1, "method": method}
    if params:
        msg["params"] = params
    
    try:
        ws.send(json.dumps(msg))
        response = ws.recv()
        return json.loads(response)
    except Exception as e:
        print(f"[ERROR] CDP命令失败: {e}")
        return None


def navigate_to(ws, url):
    """导航到指定URL"""
    print(f"[INFO] 导航到: {url}")
    return send_cdp_command(ws, "Page.navigate", {"url": url})


def search_baidu(ws, keyword):
    """使用百度搜索"""
    url = f"https://www.baidu.com/s?wd={keyword}"
    print(f"[INFO] 百度搜索: {keyword}")
    return navigate_to(ws, url)


def search_taobao(ws, keyword):
    """使用淘宝搜索"""
    url = f"https://s.taobao.com/search?q={keyword}"
    print(f"[INFO] 淘宝搜索: {keyword}")
    return navigate_to(ws, url)


def search_znds(ws, keyword):
    """使用znds搜索"""
    url = f"https://www.znds.com/search.php?mod=forum&searchsubmit=yes&kw={keyword}"
    print(f"[INFO] znds搜索: {keyword}")
    return navigate_to(ws, url)


def create_new_tab(ws, url=None):
    """创建新标签页"""
    params = {"url": url or "about:blank"} if url else {}
    return send_cdp_command(ws, "Target.createTarget", params)


def main():
    parser = argparse.ArgumentParser(description="CDP浏览器控制 - 多分身支持")
    
    # 分身参数 - 支持多种格式: --fen 1, --start 1, -f 1
    parser.add_argument("--fen", "-f", type=int, default=1, help="分身号码 (1, 2, 3...)")
    
    # 浏览器操作参数
    parser.add_argument("--url", "-u", help="要访问的URL")
    parser.add_argument("--search", "-s", help="搜索关键词（使用百度）")
    parser.add_argument("--taobao", "-t", help="淘宝搜索关键词")
    parser.add_argument("--znds", "-z", help="znds搜索关键词")
    parser.add_argument("--open", "-o", help="打开网站（简写）")
    parser.add_argument("--check", "-c", action="store_true", help="仅检查端口状态")
    parser.add_argument("--start", nargs="?", const="1", help="启动浏览器 (可指定分身号: --start 1)")
    parser.add_argument("--status", action="store_true", help="查看所有分身状态")
    
    args = parser.parse_args()
    
    # 支持 --start 1 格式
    if args.start is not None:
        if args.start != "":
            try:
                args.fen = int(args.start)
            except ValueError:
                pass
    
    # 计算当前分身端口和目录
    fen_port = get_fen_port(args.fen)
    fen_dir = get_fen_dir(args.fen)
    
    print(f"\n{'='*50}")
    print(f"CDP浏览器控制 - {args.fen}号分身")
    print(f"端口: {fen_port}, 目录: {fen_dir}")
    print(f"{'='*50}\n")
    
    # 查看状态
    if args.status:
        print("[INFO] 检查所有分身状态...")
        for i in range(1, 10):
            port = get_fen_port(i)
            status = "运行中" if check_port("localhost", port) else "未启动"
            dir_path = os.path.join(WORKSPACE, str(port))
            exists = "[OK]" if os.path.exists(dir_path) else "[X]"
            print(f"  {i}号分身: 端口 {port} - {status} (目录 {exists})")
        sys.exit(0)
    
    # 检查端口
    port_ok = check_port("localhost", fen_port)
    print(f"[INFO] CDP端口 {fen_port} 状态: {'可用' if port_ok else '未启动'}")
    
    if args.check:
        sys.exit(0 if port_ok else 1)
    
    # 如果需要启动浏览器或端口未启动
    if args.start or not port_ok:
        if not start_chrome(fen_port, args.fen):
            print("[ERROR] 无法启动浏览器")
            sys.exit(1)
        time.sleep(3)
    
    # 获取CDP端点
    endpoints = get_cdp_endpoints(fen_port)
    if not endpoints:
        print("[ERROR] 无法获取CDP端点")
        sys.exit(1)
    
    # 使用第一个端点的WebSocket URL
    ws_url = endpoints[0].get("webSocketDebuggerUrl")
    if not ws_url:
        print("[ERROR] 无法获取WebSocket URL")
        sys.exit(1)
    
    print(f"[INFO] 使用端点: {endpoints[0].get('title', 'Unknown')}")
    
    # 连接到CDP
    ws = create_cdp_connection(ws_url)
    if ws is None:
        print("[ERROR] 无法连接到CDP")
        sys.exit(1)
    
    try:
        # 执行操作
        if args.url:
            navigate_to(ws, args.url)
        elif args.open:
            navigate_to(ws, args.open)
        elif args.taobao:
            search_taobao(ws, args.taobao)
        elif args.znds:
            search_znds(ws, args.znds)
        elif args.search:
            search_baidu(ws, args.search)
        else:
            # 默认打开百度
            navigate_to(ws, "https://www.baidu.com")
        
        print("[INFO] 操作完成")
        
    finally:
        ws.close()


if __name__ == "__main__":
    main()
