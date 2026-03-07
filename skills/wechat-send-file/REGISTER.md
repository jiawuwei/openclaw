# 微信文件发送技能注册指南

## 注册到Web控制台

要将此技能注册到Moltbot的Web控制台，您需要将其添加到系统的技能配置中。以下是具体步骤：

## 1. 确保技能文件完整

首先确认技能目录包含以下文件：
```
skills/wechat-send-file/
├── SKILL.md                    # 技能描述文件（核心）
├── wechat_send_file.py         # 主程序文件
├── soupic.png                  # 搜索框模板
├── upload_file.png             # 上传文件按钮模板（需要准备）
├── requirements.txt            # 依赖列表
├── send_file.bat              # Windows批处理文件
├── test_trigger.py            # 触发测试脚本
└── README-upload-template.md  # 模板准备说明
```

## 2. 准备上传文件按钮模板

**重要**: 您需要自己准备 `upload_file.png` 文件：

1. 打开微信桌面客户端
2. 进入任意对话框
3. 截取右下角的"文件"按钮（纸夹图标）
4. 保存为 `skills/wechat-send-file/upload_file.png`
5. 尺寸建议：40×40像素

如果已有 `wenjian.png` 文件，可以尝试使用：
```bash
copy wenjian.png upload_file.png
```

## 3. 安装Python依赖

```bash
# 进入技能目录
cd skills/wechat-send-file

# 安装依赖
pip install -r requirements.txt

# 或者手动安装
pip install pyautogui pillow pyperclip
```

## 4. 测试技能触发

```bash
# 测试消息解析
python test_trigger.py

# 模拟测试（不执行实际操作）
python wechat_send_file.py --message "把C:\test.docx的文件用微信给测试用户" --simulate --debug

# 真实测试（确保已登录微信）
python wechat_send_file.py --message "把C:\test.docx的文件用微信给测试用户" --debug
```

## 5. 在Web控制台中注册

### 方法1：自动注册（如果系统支持）
如果Moltbot支持自动技能发现，新技能应该会自动出现在技能列表中。

### 方法2：手动添加配置
如果需要在配置文件中手动添加，可以在Moltbot配置中添加：

```yaml
# 技能配置示例
skills:
  wechat-send-file-python:
    name: "微信文件发送"
    description: "通过微信发送文件给指定用户"
    triggerPatterns:
      - "把{filePath}的文件用微信给{userName}"
      - "用微信给{userName}发送{filePath}的文件"
      - "给{userName}发送{filePath}的微信文件"
    executable: "skills/wechat-send-file/wechat_send_file.py"
    workingDirectory: "skills/wechat-send-file"
    arguments:
      - "--message"
      - "{fullMessage}"
```

### 方法3：通过Web界面添加
1. 打开Moltbot Web控制台
2. 进入"技能管理"页面
3. 点击"添加新技能"
4. 填写以下信息：
   - **技能名称**: wechat-send-file-python
   - **显示名称**: 微信文件发送
   - **描述**: 通过微信发送文件给指定用户
   - **触发模式**: 
     ```
     把{filePath}的文件用微信给{userName}
     用微信给{userName}发送{filePath}的文件
     给{userName}发送{filePath}的微信文件
     ```
   - **执行命令**: `python wechat_send_file.py --message "{fullMessage}"`
   - **工作目录**: `skills/wechat-send-file`
   - **超时时间**: 60秒

## 6. 验证技能注册

注册后，可以通过以下方式验证：

### 在Web聊天中测试：
```
用户: 把C:\Users\Administrator\Desktop\test.txt的文件用微信给可乐煮鸡
```

应该触发技能执行。

### 查看技能列表：
在Web控制台的技能管理页面，应该能看到"微信文件发送"技能。

## 7. 故障排除

### 问题1：技能未触发
**检查**:
- 触发模式是否正确匹配
- 技能文件路径是否正确
- Python环境是否配置正确

### 问题2：模板匹配失败
**解决**:
- 确保 `upload_file.png` 模板正确
- 调整置信度参数：`--confidence 0.8 --upload-confidence 0.85`
- 检查微信界面是否已完全加载

### 问题3：文件选择失败
**解决**:
- 确保文件路径存在且可读
- 检查Windows文件对话框是否正常弹出
- 尝试手动操作一次了解对话框行为

## 8. 安全注意事项

1. **文件权限**: 技能仅访问用户指定的文件
2. **本地操作**: 所有操作均在本地执行
3. **隐私保护**: 自动清理所有截图文件
4. **用户确认**: 发送前验证文件存在性

## 9. 技能更新

如果需要更新技能：

1. 修改 `SKILL.md` 更新描述
2. 修改 `wechat_send_file.py` 改进功能
3. 在Web控制台中重新加载技能配置
4. 测试更新后的功能

---

**注册完成！** 现在可以通过Web聊天界面使用微信文件发送功能了。