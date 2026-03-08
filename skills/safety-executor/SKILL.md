---
name: safety-executor
description: 当需要执行系统命令时候，请遵循核心原则（硬性阻止），限制原则（需要用户确认）。提供系统命令执行的安全指南，保护系统完整性和防止潜在有害操作。
---

# Command Log Skill

当需要执行系统命令时候，请核心原则 ---

## 核心原则

<HIGH_RISK_PRINCIPLES>以下操作已被禁用，AI 智能体**禁止执行**这些命令：

- **递归强制删除** (`recursive_force_delete`): 使用 rm -rf / rd /s /q 等命令无提示递归删除指定路径下所有文件及子目录。
- **磁盘格式化** (`disk_format`): 调用 format（Win）或 mkfs（Mac/Linux）清空并重构指定驱动器文件系统。
- **静默删除 C 盘内容** (`silent_delete_c_drive`): 在 Windows 下静默执行 del /f /q C:_._ 或类似高危指令。
- **注册表修改/删除** (`registry_modify_delete`): 通过 reg add/delete 或 API 修改/删除 Windows 注册表键值（含 HKEY_LOCAL_MACHINE）。

如果用户请求执行这些操作，必须：

1. 明确告知用户该操作已被禁用
2. 解释禁用原因和潜在风险
3. 建议用户在安全中心中启用对应权限（如果确实需要）
4. **绝对不要**绕过安全检查执行这些操作
   </HIGH_RISK_PRINCIPLES>

## 限制原则需要用户确认

<CONTROLLED_OPERATIONS>### 极高风险操作（默认：关闭）

这些操作可能导致**永久系统损坏**或**完全数据丢失**。默认禁用，执行前需要明确的用户确认。

#### 1. 递归强制删除 (`recursive_force_delete`)

**命令**：`recursive_force_delete`

**风险**：使用 rm -rf / rd /s /q 等命令无提示递归删除指定路径下所有文件及子目录。

**安全协议**：

- 此操作已被禁用，无法执行
- 如需启用，请在安全中心中开启对应权限
- 启用前请充分了解操作风险

#### 2. 磁盘格式化 (`disk_format`)

**命令**：`disk_format`

**风险**：调用 format（Win）或 mkfs（Mac/Linux）清空并重构指定驱动器文件系统。

**安全协议**：

- 此操作已被禁用，无法执行
- 如需启用，请在安全中心中开启对应权限
- 启用前请充分了解操作风险

#### 3. 静默删除 C 盘内容 (`silent_delete_c_drive`)

**命令**：`silent_delete_c_drive`

**风险**：在 Windows 下静默执行 del /f /q C:_._ 或类似高危指令。

**安全协议**：

- 此操作已被禁用，无法执行
- 如需启用，请在安全中心中开启对应权限
- 启用前请充分了解操作风险

### 高风险操作（默认：关闭）

这些操作可能导致**系统不稳定**或**重大数据丢失**。默认禁用。

#### 1. 注册表修改/删除 (`registry_modify_delete`)

**命令**：`registry_modify_delete`

**风险**：通过 reg add/delete 或 API 修改/删除 Windows 注册表键值（含 HKEY_LOCAL_MACHINE）。

**安全协议**：

- 此操作已被禁用，无法执行
- 如需启用，请在安全中心中开启对应权限
- 启用前请充分了解操作风险

### 中风险操作（默认：开启）

这些操作可能导致**暂时中断**或**数据丢失**。默认启用，但应谨慎使用。

#### 1. 系统关机或重启 (`system_shutdown_restart`)

**命令**：`system_shutdown_restart`

**风险**：执行 shutdown /s /t 0 或 sudo shutdown -h now 等强制指令。

**安全协议**：

- 此操作已被禁用，无法执行
- 如需启用，请在安全中心中开启对应权限
- 启用前请充分了解操作风险

#### 2. 强制结束进程 (`force_kill_process`)

**命令**：`force_kill_process`

**风险**：使用 taskkill /f /im xxx.exe 或 kill -9 PID 终止指定进程。

**安全协议**：

- 此操作已被禁用，无法执行
- 如需启用，请在安全中心中开启对应权限
- 启用前请充分了解操作风险

### 低风险操作（默认：关闭）

这些操作**影响最小**但仍需谨慎。默认禁用。

#### 1. 清空回收站 (`empty_recycle_bin`)

**命令**：`empty_recycle_bin`

**风险**：执行 shell32.dll 接口清空当前用户回收站（永久删除已删文件）。

**安全协议**：

- 此操作已被禁用，无法执行
- 如需启用，请在安全中心中开启对应权限
- 启用前请充分了解操作风险

#### 2. 修改 .ini / .conf 文件 (`modify_config_files`)

**命令**：`modify_config_files`

**风险**：通过文本写入方式修改任意 .ini、.conf、.cfg 等配置文件内容。

**安全协议**：

- 此操作已被禁用，无法执行
- 如需启用，请在安全中心中开启对应权限
- 启用前请充分了解操作风险

</CONTROLLED_OPERATIONS>

## Purpose

This skill provides guidelines for executing system commands safely while adhering to important restrictions that protect system integrity and prevent potentially harmful operations.

## Usage

When executing system commands, always follow the core principles listed above to ensure safe operation and maintain system stability.
