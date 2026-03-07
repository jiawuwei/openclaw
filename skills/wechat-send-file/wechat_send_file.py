#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信文件发送自动化脚本 (Python版本)
基于wechat-call-python架构，专为发送文件设计
支持：搜索用户 -> 进入对话框 -> 点击上传文件按钮 -> 选择文件 -> 发送
"""

import os
import sys
import time
import re
import argparse
import subprocess
from pathlib import Path

# 尝试导入依赖
try:
    import pyautogui
    import pyperclip
    from PIL import Image, ImageGrab
    import numpy as np
except ImportError as e:
    print(f"[ERROR] 缺少必要依赖: {e}")
    print("请运行: pip install pyautogui pillow pyperclip")
    sys.exit(1)

# 尝试导入OpenCV（可选）
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# 配置类
class Config:
    """配置参数管理"""
    def __init__(self):
        # 基本参数
        self.confidence = 0.85  # 搜索框匹配置信度
        self.upload_confidence = 0.9  # 上传按钮匹配置信度
        self.max_attempts = 5  # 最大扫描尝试次数
        self.scan_step = 2  # 扫描步进像素
        self.random_offset = 5  # 随机偏移范围
        self.click_delay = 0.1  # 点击延迟（秒）
        self.scan_delay = 0.5  # 扫描间隔延迟（秒）
        
        # 快捷键配置
        self.wx_hotkey = ['ctrl', 'alt', 'w']  # 唤醒微信快捷键
        
        # 路径配置
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.soupic_path = os.path.join(self.script_dir, 'soupic.png')
        self.upload_path = os.path.join(self.script_dir, 'upload_file.png')
        
        # 调试设置
        self.debug = False
        self.simulate = False
        self.use_opencv = OPENCV_AVAILABLE  # 默认使用OpenCV（如果可用）
        
        # 解析结果
        self.username = None
        self.file_path = None
        self.raw_message = None

# 日志类
class Logger:
    """日志系统"""
    def __init__(self, debug=False):
        self.debug_mode = debug
    
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def success(self, msg):
        print(f"[SUCCESS] {msg}")
    
    def warning(self, msg):
        print(f"[WARNING] {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {msg}")
    
    def debug(self, msg):
        if self.debug_mode:
            print(f"[DEBUG] {msg}")

# 工具类
class Utils:
    """工具函数集"""
    
    @staticmethod
    def copy_to_clipboard(text):
        """复制文本到剪贴板"""
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            print(f"剪贴板复制失败，尝试使用系统命令: {e}")
            # 回退方案：使用系统命令
            try:
                if sys.platform == 'win32':
                    subprocess.run(['powershell', '-Command', f'Set-Clipboard -Value "{text}"'], 
                                  capture_output=True, check=True)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['pbcopy'], input=text.encode(), check=True)
                else:  # Linux
                    subprocess.run(['xclip', '-selection', 'clipboard'], 
                                  input=text.encode(), check=True)
                return True
            except Exception as e2:
                print(f"系统剪贴板命令也失败: {e2}")
                return False
    
    @staticmethod
    def random_delay(base=0.5, variation=0.2):
        """添加随机延迟，模拟人类操作"""
        delay = base + (np.random.random() * 2 - 1) * variation
        time.sleep(max(0.1, delay))
    
    @staticmethod
    def add_random_offset(x, y, offset_range=5):
        """添加随机偏移"""
        offset_x = np.random.randint(-offset_range, offset_range)
        offset_y = np.random.randint(-offset_range, offset_range)
        return x + offset_x, y + offset_y
    
    @staticmethod
    def screenshot(filename=None):
        """截取屏幕并返回PIL图像"""
        try:
            screenshot = ImageGrab.grab()
            if filename:
                screenshot.save(filename)
            return screenshot
        except Exception as e:
            print(f"截图失败: {e}")
            return None

# 消息解析器
class MessageParser:
    """消息解析器，提取用户名和文件路径"""
    
    @staticmethod
    def parse_message(message):
        """
        解析消息，提取用户名和文件路径
        
        支持的格式：
        1. "把[文件路径]的文件用微信给[用户名]"
        2. "用微信给[用户名]发送[文件路径]的文件"  
        3. "给[用户名]发送[文件路径]的微信文件"
        4. "通过微信把[文件路径]的文件发给[用户名]"
        5. "微信发送[文件路径]的文件给[用户名]"
        6. "用微信把[文件]发给[用户名]"
        """
        patterns = [
            # 格式1: 把[文件路径]的文件用微信给[用户名]
            r'把(.+?)的文件用微信给(.+)$',
            
            # 格式2: 用微信给[用户名]发送[文件路径]的文件
            r'用微信给(.+?)发送(.+?)的文件$',
            
            # 格式3: 给[用户名]发送[文件路径]的微信文件
            r'给(.+?)发送(.+?)的微信文件$',
            
            # 格式4: 通过微信把[文件路径]的文件发给[用户名]
            r'通过微信把(.+?)的文件发给(.+)$',
            
            # 格式5: 微信发送[文件路径]的文件给[用户名]
            r'微信发送(.+?)的文件给(.+)$',
            
            # 格式6: 用微信把[文件]发给[用户名]
            r'用微信把(.+?)发给(.+)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                # 根据模式提取不同顺序的参数
                if pattern == patterns[0] or pattern == patterns[3] or pattern == patterns[4] or pattern == patterns[5]:
                    # 模式1,4,5,6: 文件路径在前，用户名在后
                    file_path = match.group(1).strip()
                    username = match.group(2).strip()
                else:
                    # 模式2,3: 用户名在前，文件路径在后
                    username = match.group(1).strip()
                    file_path = match.group(2).strip()
                
                return username, file_path
        
        # 如果没有匹配，尝试简单匹配
        simple_match = re.search(r'微信(.+?)的文件给(.+)$', message)
        if simple_match:
            file_path = simple_match.group(1).strip()
            username = simple_match.group(2).strip()
            return username, file_path
        
        return None, None
    
    @staticmethod
    def validate_file_path(file_path):
        """验证文件路径是否有效"""
        # 处理桌面路径简写
        if file_path.startswith('桌面'):
            # 去除"桌面"前缀，获取文件名
            filename = file_path[2:].lstrip('上').lstrip('\\').lstrip('/')
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            file_path = os.path.join(desktop_path, filename)
        
        # 标准化路径（处理环境变量和用户目录）
        expanded_path = os.path.expandvars(os.path.expanduser(file_path))
        
        # 如果路径是相对路径，转换为绝对路径
        if not os.path.isabs(expanded_path):
            # 相对于当前工作目录
            expanded_path = os.path.abspath(expanded_path)
        
        # 验证文件存在性
        if not os.path.exists(expanded_path):
            raise FileNotFoundError(f"文件不存在: {expanded_path}")
        
        # 验证是否是文件（不是目录）
        if not os.path.isfile(expanded_path):
            raise ValueError(f"路径不是文件: {expanded_path}")
        
        # 验证文件可读性
        if not os.access(expanded_path, os.R_OK):
            raise PermissionError(f"文件不可读: {expanded_path}")
        
        return os.path.abspath(expanded_path)

# 模板匹配器
class TemplateMatcher:
    """模板匹配器，基于wechat-call-python架构"""
    
    def __init__(self, use_opencv=True, confidence=0.8, debug=False):
        self.use_opencv = use_opencv and OPENCV_AVAILABLE
        self.confidence = confidence
        self.debug = debug
        self.logger = Logger(debug)
    
    def load_template(self, template_path):
        """加载模板图片"""
        try:
            return Image.open(template_path)
        except Exception as e:
            self.logger.error(f"无法加载模板图片 {template_path}: {e}")
            return None
    
    def find_template(self, screenshot, template, max_attempts=5, step=2):
        """
        在屏幕截图中查找模板
        返回 (x, y, confidence) 或 None
        """
        if screenshot is None or template is None:
            return None
        
        # 转换为灰度图
        screenshot_gray = screenshot.convert('L')
        template_gray = template.convert('L')
        
        if self.use_opencv:
            return self._find_with_opencv(screenshot_gray, template_gray, max_attempts, step)
        else:
            return self._find_with_pil(screenshot_gray, template_gray, max_attempts, step)
    
    def _find_with_opencv(self, screenshot, template, max_attempts, step):
        """使用OpenCV进行模板匹配"""
        import cv2
        
        # PIL图像转换为OpenCV格式
        screenshot_np = np.array(screenshot)
        template_np = np.array(template)
        
        # 模板匹配
        result = cv2.matchTemplate(screenshot_np, template_np, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= self.confidence:
            x = max_loc[0] + template_np.shape[1] // 2
            y = max_loc[1] + template_np.shape[0] // 2
            self.logger.debug(f"OpenCV匹配成功: 位置({x}, {y}), 置信度{max_val:.4f}")
            return x, y, max_val
        
        return None
    
    def _find_with_pil(self, screenshot, template, max_attempts, step):
        """使用PIL进行简单的模板匹配"""
        sw, sh = screenshot.size
        tw, th = template.size
        
        best_match = None
        best_score = 0
        
        # 步进扫描提高效率
        for y in range(0, sh - th, step):
            for x in range(0, sw - tw, step):
                # 截取区域
                region = screenshot.crop((x, y, x + tw, y + th))
                
                # 计算相似度（简单的像素差异）
                diff = np.array(region) - np.array(template)
                score = 1 - (np.abs(diff).mean() / 255)
                
                if score > best_score:
                    best_score = score
                    best_match = (x + tw // 2, y + th // 2)
        
        if best_match and best_score >= self.confidence:
            self.logger.debug(f"PIL匹配成功: 位置{best_match}, 置信度{best_score:.4f}")
            return best_match[0], best_match[1], best_score
        
        return None

# 微信文件发送器
class WeChatFileSender:
    """微信文件发送主类"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.utils = Utils()
        self.matcher_search = TemplateMatcher(
            use_opencv=config.use_opencv, 
            confidence=config.confidence, 
            debug=config.debug
        )
        self.matcher_upload = TemplateMatcher(
            use_opencv=config.use_opencv, 
            confidence=config.upload_confidence, 
            debug=config.debug
        )
        
        # 加载模板
        self.soupic_template = self.matcher_search.load_template(config.soupic_path)
        self.upload_template = self.matcher_upload.load_template(config.upload_path)
        
        if not self.soupic_template:
            self.logger.error("无法加载搜索框模板")
        if not self.upload_template:
            self.logger.error("无法加载上传文件按钮模板")
    
    def activate_wechat(self):
        """激活微信窗口"""
        self.logger.info("激活微信窗口...")
        
        if self.config.simulate:
            self.logger.debug("模拟模式：跳过微信激活")
            return True
        
        try:
            # 先返回桌面
            pyautogui.hotkey('win', 'd')
            time.sleep(0.5)
            
            # 尝试唤醒微信
            pyautogui.hotkey(*self.config.wx_hotkey)
            self.utils.random_delay(1.0)
            
            self.logger.success("微信窗口激活成功")
            return True
        except Exception as e:
            self.logger.error(f"激活微信窗口失败: {e}")
            return False
    
    def search_and_select_user(self):
        """搜索并选择用户"""
        self.logger.info(f"搜索用户: {self.config.username}")
        
        if not self.utils.copy_to_clipboard(self.config.username):
            self.logger.error("无法复制用户名到剪贴板")
            return False
        
        # 查找搜索框
        self.logger.info("查找搜索框...")
        for attempt in range(self.config.max_attempts):
            screenshot = Utils.screenshot()
            result = self.matcher_search.find_template(
                screenshot, self.soupic_template,
                max_attempts=1, step=self.config.scan_step
            )
            
            if result:
                x, y, confidence = result
                self.logger.info(f"找到搜索框: 位置({x}, {y}), 置信度{confidence:.4f}")
                
                # 点击搜索框
                click_x, click_y = self.utils.add_random_offset(x, y, self.config.random_offset)
                
                if not self.config.simulate:
                    pyautogui.click(click_x, click_y)
                    time.sleep(self.config.click_delay)
                    
                    # 粘贴用户名
                    pyautogui.hotkey('ctrl', 'v')
                    self.utils.random_delay(0.3)
                    
                    # 第一次回车：确认搜索
                    pyautogui.press('enter')
                    self.utils.random_delay(0.3)
                    
                    # 第二次回车：选择用户
                    pyautogui.press('enter')
                    self.utils.random_delay(0.3)
                    
                    # 第三次回车：进入对话框（确保进入）
                    pyautogui.press('enter')
                    self.utils.random_delay(0.5)
                
                self.logger.success("用户选择完成")
                return True
            
            self.logger.debug(f"搜索框匹配尝试 {attempt + 1}/{self.config.max_attempts}")
            time.sleep(self.config.scan_delay)
        
        self.logger.error("未找到搜索框")
        return False
    
    def click_upload_file_button(self):
        """点击上传文件按钮"""
        self.logger.info("查找上传文件按钮...")
        
        for attempt in range(self.config.max_attempts):
            screenshot = Utils.screenshot()
            result = self.matcher_upload.find_template(
                screenshot, self.upload_template,
                max_attempts=1, step=self.config.scan_step
            )
            
            if result:
                x, y, confidence = result
                self.logger.info(f"找到上传文件按钮: 位置({x}, {y}), 置信度{confidence:.4f}")
                
                # 点击上传按钮
                click_x, click_y = self.utils.add_random_offset(x, y, self.config.random_offset)
                
                if not self.config.simulate:
                    pyautogui.click(click_x, click_y)
                    time.sleep(0.5)
                
                self.logger.success("点击上传文件按钮完成")
                return True
            
            self.logger.debug(f"上传按钮匹配尝试 {attempt + 1}/{self.config.max_attempts}")
            time.sleep(self.config.scan_delay)
        
        self.logger.error("未找到上传文件按钮")
        return False
    
    def select_file_in_dialog(self):
        """在文件选择对话框中选择文件"""
        self.logger.info(f"选择文件: {self.config.file_path}")
        
        if not self.utils.copy_to_clipboard(self.config.file_path):
            self.logger.error("无法复制文件路径到剪贴板")
            return False
        
        if self.config.simulate:
            self.logger.debug("模拟模式：跳过文件选择")
            return True
        
        try:
            # 等待文件对话框出现
            time.sleep(1.0)
            
            # Windows文件对话框操作
            if sys.platform == 'win32':
                # Alt+N 聚焦到文件名输入框
                pyautogui.hotkey('alt', 'n')
                time.sleep(0.3)
                
                # 粘贴文件路径
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.5)
                
                # 回车确认选择
                pyautogui.press('enter')
                time.sleep(0.5)
                
                # 可能需要的额外回车
                pyautogui.press('enter')
                self.utils.random_delay(0.3)
            else:
                # macOS/Linux 简单处理
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(0.5)
                pyautogui.press('enter')
            
            self.logger.success("文件选择完成")
            return True
        except Exception as e:
            self.logger.error(f"文件选择失败: {e}")
            return False
    
    def cleanup_screenshots(self):
        """清理桌面截图文件"""
        self.logger.info("清理桌面截图文件...")
        
        try:
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            screenshot_patterns = ['screenshot_*.png', '微信截图_*.png']
            
            for pattern in screenshot_patterns:
                for screenshot_file in Path(desktop_path).glob(pattern):
                    try:
                        os.remove(screenshot_file)
                        self.logger.debug(f"已删除: {screenshot_file}")
                    except Exception as e:
                        self.logger.debug(f"删除失败 {screenshot_file}: {e}")
            
            self.logger.success("截图清理完成")
        except Exception as e:
            self.logger.warning(f"截图清理过程中出错: {e}")
    
    def run(self):
        """执行完整的文件发送流程"""
        self.logger.info("开始微信文件发送流程...")
        
        # 1. 解析消息
        parser = MessageParser()
        self.config.username, raw_file_path = parser.parse_message(self.config.raw_message)
        
        if not self.config.username or not raw_file_path:
            self.logger.error("无法从消息中解析用户名和文件路径")
            return False
        
        self.logger.info(f"解析结果 - 用户名: {self.config.username}, 文件路径: {raw_file_path}")
        
        # 2. 验证文件路径
        try:
            self.config.file_path = parser.validate_file_path(raw_file_path)
            self.logger.info(f"验证文件路径成功: {self.config.file_path}")
        except Exception as e:
            self.logger.error(f"文件路径验证失败: {e}")
            return False
        
        # 3. 检查模板
        if not self.soupic_template or not self.upload_template:
            self.logger.error("模板文件缺失，无法继续")
            return False
        
        # 4. 激活微信窗口
        if not self.activate_wechat():
            return False
        
        # 5. 搜索并选择用户
        if not self.search_and_select_user():
            return False
        
        # 6. 点击上传文件按钮
        if not self.click_upload_file_button():
            return False
        
        # 7. 选择文件
        if not self.select_file_in_dialog():
            return False
        
        # 8. 清理工作
        self.cleanup_screenshots()
        
        self.logger.success("[SUCCESS] 微信文件发送流程完成！")
        return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='微信文件发送自动化脚本')
    parser.add_argument('--message', '-m', required=True, help='完整消息内容，如"把C:\\文件.docx的文件用微信给张三"')
    parser.add_argument('--debug', '-d', action='store_true', help='显示详细调试信息')
    parser.add_argument('--simulate', '-s', action='store_true', help='模拟模式，不执行实际操作')
    parser.add_argument('--confidence', type=float, default=0.85, help='搜索框匹配置信度阈值 (默认: 0.85)')
    parser.add_argument('--upload-confidence', type=float, default=0.9, help='上传按钮匹配置信度阈值 (默认: 0.9)')
    parser.add_argument('--use-opencv', action='store_true', help='使用OpenCV进行模板匹配（如果可用）')
    parser.add_argument('--no-opencv', action='store_true', help='不使用OpenCV（即使可用）')
    
    args = parser.parse_args()
    
    # 配置
    config = Config()
    config.debug = args.debug
    config.simulate = args.simulate
    config.confidence = args.confidence
    config.upload_confidence = args.upload_confidence
    config.raw_message = args.message
    
    if args.no_opencv:
        config.use_opencv = False
    elif args.use_opencv:
        config.use_opencv = True
    
    # 日志
    logger = Logger(config.debug)
    
    # 显示配置信息
    logger.info(f"微信文件发送脚本启动")
    logger.info(f"消息内容: {args.message}")
    logger.info(f"模式: {'模拟' if config.simulate else '执行'}")
    logger.info(f"调试模式: {'开启' if config.debug else '关闭'}")
    logger.info(f"OpenCV: {'可用' if OPENCV_AVAILABLE else '不可用'} ({'启用' if config.use_opencv else '禁用'})")
    
    # 创建发送器并运行
    sender = WeChatFileSender(config, logger)
    success = sender.run()
    
    if success:
        logger.success("脚本执行成功")
        sys.exit(0)
    else:
        logger.error("脚本执行失败")
        sys.exit(1)

if __name__ == '__main__':
    main()