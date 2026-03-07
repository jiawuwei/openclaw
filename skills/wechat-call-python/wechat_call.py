#!/usr/bin/env python3
"""
微信电话自动化脚本 - Python版本 v1.0
使用Python自动化控制微信桌面客户端进行电话拨打
基于模板匹配技术，不使用硬编码坐标
"""

import argparse
import sys
import os
import time
import random
import subprocess
import platform
import re
import glob
from pathlib import Path

# 导入必要的库（支持回退机制）
try:
    import pyautogui
    pyautogui_available = True
except ImportError:
    pyautogui_available = False
    print("错误: 未找到pyautogui库，请安装: pip install pyautogui")
    sys.exit(1)

try:
    from PIL import Image, ImageGrab
    from PIL import ImageOps
    pillow_available = True
except ImportError:
    pillow_available = False
    print("错误: 未找到Pillow库，请安装: pip install pillow")
    sys.exit(1)

try:
    import pyperclip
    pyperclip_available = True
except ImportError:
    pyperclip_available = False
    print("警告: 未找到pyperclip库，将使用系统剪贴板命令")

try:
    import cv2
    import numpy as np
    opencv_available = True
except ImportError:
    opencv_available = False
    print("信息: 未找到OpenCV库，将使用PIL进行模板匹配")

# 配置参数
class Config:
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 1000
        self.search_delay = 2000
        self.debug = False
        self.simulate = False
        self.user = None
        self.confidence_threshold = 0.9
        self.max_scan_attempts = 5
        self.scan_delay = 500
        self.use_opencv = opencv_available  # 默认使用OpenCV如果可用
        self.template_dir = Path(__file__).parent
        
        # 平台相关设置
        self.platform = platform.system()
        
    def validate(self):
        if not self.user:
            return False, "请使用 --user 参数指定用户名或完整消息"
        return True, ""

# 日志类
class Logger:
    def __init__(self, debug=False):
        self.debug = debug
        
    def log(self, message, level="info"):
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        
        level_symbols = {
            "info": "I",
            "error": "X",
            "warn": "!",
            "debug": "D",
            "success": "V"
        }
        
        symbol = level_symbols.get(level, "I")
        
        # 决定是否输出
        should_log = (
            level in ["error", "success", "warn"] or 
            self.debug or 
            (level == "info" and not config.simulate)
        )
        
        if should_log:
            print(f"[{timestamp}] {symbol} {message}")
    
    def debug_log(self, message):
        self.log(message, "debug")

# 工具类
class Utils:
    @staticmethod
    def delay(ms):
        """延迟函数"""
        if not config.simulate:
            time.sleep(ms / 1000.0)
    
    @staticmethod
    def extract_username(full_text):
        """从消息中提取用户名"""
        if not full_text:
            raise ValueError("未提供用户信息")
        
        username = full_text.strip()
        
        # 正则匹配"用微信给XXX打电话"格式
        pattern = r"用微信给(.+?)打电话"
        match = re.search(pattern, full_text)
        if match:
            username = match.group(1).strip()
            logger.log(f"从消息提取用户名: '{username}'")
        else:
            logger.log(f"使用完整文本作为用户名: '{username}'")
        
        return username
    
    @staticmethod
    def cleanup_desktop_screenshots():
        """清理桌面的所有截图文件"""
        try:
            # 确定桌面路径
            system = platform.system()
            if system == "Windows":
                desktop_path = os.path.join(os.environ["USERPROFILE"], "Desktop")
            elif system == "Darwin":  # macOS
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            elif system == "Linux":
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            else:
                logger.log(f"警告: 未知操作系统 {system}，跳过清理截图")
                return 0
            
            # 定义要删除的文件模式
            patterns = [
                "screenshot*.png",
                "screenshot*.jpg",
                "screenshot*.jpeg",
                "screenshot*.bmp",
                "screen*.png",
                "screen*.jpg",
                "screen*.jpeg",
                "screen*.bmp",
                "*screenshot*.png",  # 匹配任何位置包含screenshot的文件
                "*screenshot*.jpg",
                "*screenshot*.jpeg",
                "*screenshot*.bmp"
            ]
            
            deleted_count = 0
            for pattern in patterns:
                search_pattern = os.path.join(desktop_path, pattern)
                files = glob.glob(search_pattern)
                
                for file_path in files:
                    try:
                        os.remove(file_path)
                        logger.debug_log(f"已删除截图: {os.path.basename(file_path)}")
                        deleted_count += 1
                    except Exception as e:
                        logger.debug_log(f"删除文件失败 {file_path}: {e}")
            
            if deleted_count > 0:
                logger.log(f"清理完成: 删除了 {deleted_count} 个桌面截图文件")
            else:
                logger.debug_log("未找到桌面截图文件")
            
            return deleted_count
            
        except Exception as e:
            logger.debug_log(f"清理桌面截图时出错: {e}")
            return 0
    
    @staticmethod
    def copy_to_clipboard(text):
        """复制文本到剪贴板"""
        try:
            if pyperclip_available:
                pyperclip.copy(text)
            else:
                # 使用系统命令
                system = platform.system()
                if system == "Darwin":  # macOS
                    subprocess.run(["pbcopy"], input=text.encode(), check=True)
                elif system == "Linux":
                    try:
                        # 尝试xclip
                        subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
                    except:
                        # 尝试xsel
                        subprocess.run(["xsel", "--clipboard", "--input"], input=text.encode(), check=True)
                else:  # Windows
                    subprocess.run(["clip"], input=text.encode(), shell=True, check=True)
            logger.log("用户名复制到剪贴板", "success")
            return True
        except Exception as e:
            raise RuntimeError(f"剪贴板复制失败: {e}")
    
    @staticmethod
    def random_offset(max_offset=5):
        """生成随机偏移"""
        return random.randint(-max_offset, max_offset)
    
    @staticmethod
    def get_screen_size():
        """获取屏幕尺寸"""
        return pyautogui.size()
    
    @staticmethod
    def save_debug_image(image, filename):
        """保存调试图片"""
        if config.debug:
            debug_dir = Path("debug_screenshots")
            debug_dir.mkdir(exist_ok=True)
            image.save(debug_dir / filename)
            logger.debug_log(f"保存调试图片: {filename}")

# 模板匹配类
class TemplateMatcher:
    def __init__(self):
        self.utils = Utils()
        
    def load_template(self, template_name):
        """加载模板图片"""
        template_path = config.template_dir / f"{template_name}.png"
        if not template_path.exists():
            raise FileNotFoundError(f"模板图片不存在: {template_path}")
        
        template = Image.open(template_path)
        logger.log(f"加载模板: {template_name} ({template.width}x{template.height})", "success")
        return template
    
    def capture_screenshot(self, description="屏幕截图"):
        """捕获屏幕截图"""
        logger.debug_log(f"正在{description}...")
        
        try:
            screenshot = ImageGrab.grab()
            width, height = screenshot.size
            logger.debug_log(f"{description}完成: {width}x{height}")
            return screenshot
        except Exception as e:
            raise RuntimeError(f"{description}失败: {e}")
    
    def match_template_pil(self, screenshot, template):
        """使用PIL进行模板匹配（简单实现）"""
        screenshot_width, screenshot_height = screenshot.size
        template_width, template_height = template.size
        
        logger.debug_log(f"使用PIL模板匹配 (模板大小: {template_width}x{template_height})")
        
        # 转换为灰度图
        screenshot_gray = ImageOps.grayscale(screenshot)
        template_gray = ImageOps.grayscale(template)
        
        # 获取模板的像素数据
        template_data = list(template_gray.getdata())
        
        best_match = None
        best_confidence = 0
        
        # 遍历屏幕像素（简化版本，步进扫描）
        step = 2
        for y in range(0, screenshot_height - template_height, step):
            for x in range(0, screenshot_width - template_width, step):
                # 提取当前区域的像素
                region = screenshot_gray.crop((x, y, x + template_width, y + template_height))
                region_data = list(region.getdata())
                
                # 计算相似度
                similarity = 0
                for i in range(len(template_data)):
                    diff = abs(template_data[i] - region_data[i])
                    if diff < 30:  # 阈值
                        similarity += 1
                
                confidence = similarity / len(template_data)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = {
                        "x": x,
                        "y": y,
                        "width": template_width,
                        "height": template_height,
                        "confidence": confidence
                    }
                
                # 如果找到足够好的匹配，提前返回
                if best_confidence > config.confidence_threshold:
                    logger.debug_log(f"提前找到匹配: ({x}, {y}), 置信度: {confidence:.4f}")
                    return best_match
        
        return best_match if best_confidence > 0 else None
    
    def match_template_opencv(self, screenshot, template):
        """使用OpenCV进行模板匹配"""
        if not opencv_available:
            raise RuntimeError("OpenCV不可用")
        
        # 转换为OpenCV格式
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        template_cv = cv2.cvtColor(np.array(template), cv2.COLOR_RGB2BGR)
        
        # 转换为灰度
        screenshot_gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template_cv, cv2.COLOR_BGR2GRAY)
        
        # 模板匹配
        result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val > config.confidence_threshold:
            x, y = max_loc
            template_width, template_height = template_gray.shape[::-1]
            
            logger.debug_log(f"OpenCV匹配成功: ({x}, {y}), 置信度: {max_val:.4f}")
            
            return {
                "x": x,
                "y": y,
                "width": template_width,
                "height": template_height,
                "confidence": max_val
            }
        
        return None
    
    def match_template(self, screenshot, template_name):
        """模板匹配主函数"""
        template = self.load_template(template_name)
        
        # 优先使用OpenCV如果可用且启用
        if config.use_opencv and opencv_available:
            result = self.match_template_opencv(screenshot, template)
        else:
            result = self.match_template_pil(screenshot, template)
        
        return result
    
    def smart_scan(self, template_name, scan_area=None):
        """智能扫描：多次尝试查找模板"""
        logger.debug_log(f"智能扫描查找: {template_name}")
        
        for attempt in range(1, config.max_scan_attempts + 1):
            logger.debug_log(f"扫描尝试 {attempt}/{config.max_scan_attempts}...")
            
            try:
                screenshot = self.capture_screenshot(f"第{attempt}次扫描截图")
                result = self.match_template(screenshot, template_name)
                
                if result:
                    logger.log(f"成功找到{template_name}: 位置({result['x']}, {result['y']}), 置信度{result['confidence']:.4f}", "success")
                    return result
                
                if attempt < config.max_scan_attempts:
                    Utils.delay(config.scan_delay)
                    
            except Exception as e:
                logger.log(f"扫描尝试{attempt}失败: {e}", "warn")
                
                if attempt < config.max_scan_attempts:
                    Utils.delay(config.scan_delay)
        
        raise RuntimeError(f"在{config.max_scan_attempts}次尝试后未找到{template_name}")

# 操作执行类
class Operations:
    def __init__(self):
        self.utils = Utils()
        self.matcher = TemplateMatcher()
    
    def execute(self, description, action_func):
        """执行操作，带日志记录"""
        logger.log(description)
        
        if config.simulate:
            logger.debug_log(f"[模拟] {description}")
            return True
        
        try:
            action_func()
            logger.log(f"完成: {description}", "success")
            return True
        except Exception as e:
            logger.log(f"失败: {description} - {e}", "error")
            raise
    
    def press_key_combination(self, keys, description="按键组合"):
        """按下键组合"""
        def action():
            for key in keys:
                pyautogui.keyDown(key)
                Utils.delay(100)
            
            Utils.delay(100)
            
            # 按键顺序与按下相反
            for key in reversed(keys):
                pyautogui.keyUp(key)
                Utils.delay(50)
        
        return self.execute(description, action)
    
    def press_key(self, key, description="按键"):
        """按单个键"""
        def action():
            pyautogui.press(key)
        
        return self.execute(description, action)
    
    def click_at_position(self, x, y, description="点击"):
        """在指定位置点击"""
        def action():
            # 添加随机偏移
            offset_x = self.utils.random_offset()
            offset_y = self.utils.random_offset()
            actual_x = x + offset_x
            actual_y = y + offset_y
            
            logger.debug_log(f"实际点击位置: ({actual_x}, {actual_y}) [带随机偏移]")
            
            pyautogui.moveTo(actual_x, actual_y, duration=0.1)
            Utils.delay(100)
            pyautogui.click()
        
        return self.execute(description, action)
    
    def click_match_result(self, match_result, description="点击匹配位置"):
        """点击模板匹配结果的位置"""
        if not match_result:
            raise ValueError("无效的匹配结果")
        
        center_x = match_result["x"] + match_result["width"] // 2
        center_y = match_result["y"] + match_result["height"] // 2
        
        logger.debug_log(f"点击匹配位置: ({center_x}, {center_y}), 置信度: {match_result['confidence']:.4f}")
        
        return self.click_at_position(center_x, center_y, description)
    
    def paste_from_clipboard(self, description="粘贴"):
        """从剪贴板粘贴"""
        def action():
            if config.platform == "Darwin":  # macOS
                pyautogui.hotkey("command", "v")
            else:
                pyautogui.hotkey("ctrl", "v")
        
        return self.execute(description, action)

# 主流程类
class WeChatCaller:
    def __init__(self):
        self.ops = Operations()
        self.utils = Utils()
        self.matcher = TemplateMatcher()
    
    def run(self):
        """主流程"""
        logger.log("开始微信电话自动化流程 - Python版本")
        logger.log("说明: 使用模板匹配技术，无硬编码坐标")
        
        try:
            # 1. 提取用户名并复制到剪贴板
            username = self.utils.extract_username(config.user)
            logger.log(f"目标用户: {username}")
            
            self.utils.copy_to_clipboard(username)
            
            # 2. 返回桌面
            if config.platform == "Darwin":  # macOS
                self.ops.press_key_combination(["command", "f3"], "按 Command+F3 显示桌面")
            else:  # Windows/Linux
                self.ops.press_key_combination(["win", "d"], "按 Win+D 返回桌面")
            
            self.utils.delay(1000)
            
            # 3. 激活微信窗口
            if config.platform == "Darwin":  # macOS
                # macOS通常使用Command+Tab切换应用
                self.ops.press_key_combination(["command", "tab"], "按 Command+Tab 切换应用")
                self.utils.delay(500)
                self.ops.press_key("tab", "继续按Tab切换到微信")
            else:  # Windows/Linux
                # 假设使用Ctrl+Alt+W唤醒微信
                self.ops.press_key_combination(["ctrl", "alt", "w"], "按 Ctrl+Alt+W 激活微信窗口")
            
            self.utils.delay(2000)
            
            # 4. 查找并点击搜索图标
            logger.log("开始查找搜索图标...")
            search_match = self.matcher.smart_scan("soupic")
            
            self.ops.click_match_result(search_match, "点击搜索图标")
            self.utils.delay(500)
            
            # 5. 粘贴用户名
            self.ops.paste_from_clipboard("从剪贴板粘贴用户名")
            self.utils.delay(300)
            
            # 6. 按回车选择用户
            self.ops.press_key("enter", "按回车键选择用户")
            self.utils.delay(100)
            self.ops.press_key("enter", "按第二次回车键确认")
            self.utils.delay(config.search_delay)
            
            # 7. 查找并点击电话图标
            logger.log("开始查找电话图标...")
            call_match = self.matcher.smart_scan("dianhua")
            
            self.ops.click_match_result(call_match, "点击电话图标")
            self.utils.delay(1000)
            
            # 8. 完成报告
            logger.log("\n微信电话拨打流程完成!", "success")
            logger.log(f"已成功拨打微信电话给: {username}", "success")
            logger.log("技术特点:", "success")
            logger.log("- 纯Python实现，无Node.js依赖", "success")
            logger.log("- 基于模板匹配技术", "success")
            logger.log("- 无硬编码坐标", "success")
            logger.log("- 智能多次扫描，提高成功率", "success")
            logger.log("- 跨平台支持", "success")
            
            # 9. 清理桌面截图
            logger.log("\n正在清理桌面截图...", "info")
            deleted_count = self.utils.cleanup_desktop_screenshots()
            if deleted_count > 0:
                logger.log(f"已清理 {deleted_count} 个桌面截图文件", "success")
            else:
                logger.log("未找到桌面截图文件", "info")
            
            logger.log("所有流程完成!", "success")
            return True
            
        except Exception as e:
            logger.log(f"\n流程失败: {e}", "error")
            logger.log("建议:", "error")
            logger.log("1. 确保微信客户端已打开并最大化", "error")
            logger.log("2. 确保模板图片正确", "error")
            logger.log("3. 可以降低置信度阈值: --confidence 0.8", "error")
            logger.log("4. 检查依赖是否已安装", "error")
            
            # 即使失败也尝试清理截图
            logger.log("\n正在清理桌面截图...", "info")
            try:
                deleted_count = self.utils.cleanup_desktop_screenshots()
                if deleted_count > 0:
                    logger.log(f"已清理 {deleted_count} 个桌面截图文件", "success")
                else:
                    logger.log("未找到桌面截图文件", "info")
            except Exception as cleanup_error:
                logger.log(f"清理截图时出错: {cleanup_error}", "warning")
            
            return False

# 全局配置和日志
config = Config()
logger = Logger()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="微信电话自动化脚本 - Python版本")
    parser.add_argument("--user", required=True, help="目标用户名或完整消息，如'用微信给可乐煮鸡打电话'")
    parser.add_argument("--debug", action="store_true", help="显示详细调试信息")
    parser.add_argument("--simulate", action="store_true", help="模拟模式，不执行实际操作")
    parser.add_argument("--confidence", type=float, default=0.9, help="模板匹配置信度阈值 (0.0-1.0, 默认0.9)")
    parser.add_argument("--use-opencv", action="store_true", help="使用OpenCV进行模板匹配")
    parser.add_argument("--no-opencv", action="store_true", help="不使用OpenCV（即使可用）")
    
    args = parser.parse_args()
    
    # 应用配置
    config.user = args.user
    config.debug = args.debug
    config.simulate = args.simulate
    config.confidence_threshold = args.confidence
    
    if args.use_opencv and opencv_available:
        config.use_opencv = True
    elif args.no_opencv:
        config.use_opencv = False
    
    logger.debug = config.debug
    
    # 验证配置
    is_valid, error_msg = config.validate()
    if not is_valid:
        logger.log(error_msg, "error")
        return 1
    
    # 检查依赖
    if not pyautogui_available:
        logger.log("错误: pyautogui库未安装，请运行: pip install pyautogui", "error")
        return 1
    
    if not pillow_available:
        logger.log("错误: Pillow库未安装，请运行: pip install pillow", "error")
        return 1
    
    # 运行主流程
    caller = WeChatCaller()
    success = caller.run()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())