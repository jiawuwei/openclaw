---
name: cdp-browser-control
description: 通过CDP协议控制浏览器进行网页访问和搜索。当用户需要访问互联网、查找信息或进行网页搜索时，自动使用chrome-devtools-protocol连接到浏览器。先检查CDP端口是否启动，如果没有则自动启动chromium浏览器。支持多浏览器分身，每个分身独立端口和数据目录。
---

# CDP浏览器控制技能

这个技能通过Chrome DevTools Protocol (CDP) 控制浏览器，实现网页浏览和搜索操作。支持**多分身**功能，每个分身相互独立。

## 触发条件

### 常规浏览
当用户消息匹配以下模式时触发：
- "打开[网站]" - 访问指定网站
- "访问[网站]" - 访问指定网站
- "搜索[关键词]" - 使用百度搜索关键词
- "查找[信息]" - 查找相关信息
- "浏览[网站]" - 浏览指定网站

**示例**:
- "打开百度"
- "访问淘宝"
- "搜索Python教程"

### 分身启动（关键触发）
当用户提到"分身"时，自动启动对应编号的浏览器分身：
- "启动1号分身" / "打开1号分身" / "1号分身"
- "启动2号分身" / "打开2号分身" / "2号分身"
- "启动3号分身" / "打开3号分身" / "3号分身"
- 以此类推...

**示例**:
- "启动1号分身"
- "打开2号浏览器分身"
- "我要用3号分身"

## 分身系统

### 端口分配
| 分身号 | 端口 | 数据目录 |
|--------|------|----------|
| 1号 | 9301 | workspace/9301/ |
| 2号 | 9302 | workspace/9302/ |
| 3号 | 9303 | workspace/9303/ |
| 4号 | 9304 | workspace/9304/ |
| ... | ... | ... |

### 分身特性
- **独立数据**: 每个分身有独立的用户数据目录
- **独立端口**: 每个分身监听不同CDP端口
- **并行运行**: 支持同时运行多个分身
- **自动创建**: 首次启动自动创建数据目录

## 前提条件

1. **chromium浏览器** - 位于 `.openclaw\chromium\Application\chrome.exe`
   - 脚本自动检测路径，无需手动配置
2. **Python环境** (Python 3.8+)
3. **必要Python包**：
   - websocket-client: WebSocket连接

## 使用方法

### 命令行方式
```bash
# 启动1号分身并打开百度（默认）
python cdp_browser.py --fen 1 --start

# 启动2号分身
python cdp_browser.py --fen 2 --start

# 1号分身 - 淘宝搜索
python cdp_browser.py --fen 1 --taobao "当贝投影仪"

# 1号分身 - 百度搜索
python cdp_browser.py --fen 1 --search "Python教程"

# 1号分身 - 访问指定URL
python cdp_browser.py --fen 1 --url "https://www.taobao.com"

# 查看所有分身状态
python cdp_browser.py --status

# 仅检查端口状态
python cdp_browser.py --fen 1 --check
```

### 参数说明
| 参数 | 简写 | 说明 |
|------|------|------|
| --fen | -f | 分身号码 (1-9) |
| --start | - | 启动浏览器 |
| --url | -u | 访问URL |
| --search | -s | 百度搜索 |
| --taobao | -t | 淘宝搜索 |
| --znds | -z | znds搜索 |
| --status | - | 查看所有分身状态 |
| --check | -c | 检查端口状态 |

## 技术实现

### 浏览器启动参数
```cmd
chrome.exe --remote-debugging-port={port} --remote-allow-origins=* --user-data-dir={data_dir} --new-window --no-first-run --no-default-browser-check --window-size=1280,1000
```

### CDP连接
- 1号分身: `ws://localhost:9301/devtools/page/xxx`
- 2号分身: `ws://localhost:9302/devtools/page/xxx`
- 3号分身: `ws://localhost:9303/devtools/page/xxx`

## 数据目录结构
```
workspace/
├── 9301/           # 1号分身目录
│   └── userdata/  # 浏览器数据
├── 9302/           # 2号分身目录
│   └── userdata/
└── 9303/           # 3号分身目录
    └── userdata/
```

## 故障排除

**问题**: 分身启动失败
**解决**: 
1. 检查端口是否被占用: `netstat -an | findstr 9301`
2. 确认chromium路径正确
3. 查看是否有权限创建目录

**问题**: CDP连接失败
**解决**: 
1. 检查端口状态: `python cdp_browser.py --fen 1 --check`
2. 重启分身: `python cdp_browser.py --fen 1 --start`

**问题**: 浏览器窗口未出现
**解决**: 可能是隐藏窗口，检查任务管理器中是否有chrome进程

## 扩展性

可扩展以下功能：
1. **多标签管理** - 同时管理多个标签页
2. **截图功能** - 页面截图
3. **文件下载** - 自动下载文件
4. **Cookie管理** - Cookie导入导出
5. **UA切换** - 切换用户代理

---

**技能就绪！** 此技能提供完整的CDP浏览器控制能力，支持多分身并行运行。
