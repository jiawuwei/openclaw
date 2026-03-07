/**
 * 微信电话自动化技能包装器 (Python版本)
 * 用于在Moltbot中调用Python技能
 */

const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

// 技能配置
const SKILL_DIR = __dirname;
const PYTHON_ACTIVATOR = path.join(SKILL_DIR, 'skill_activator.py');

// 触发模式
const TRIGGER_PATTERNS = [
    /用微信给(.+?)打电话/,
    /用微信给(.+?)拨打语音/,
    /微信电话(.+?)/,
    /拨打微信语音(.+?)/,
    /微信打电话给(.+)/
];

/**
 * 检查消息是否触发技能
 */
function shouldActivate(message) {
    const trimmed = message.trim();
    
    for (const pattern of TRIGGER_PATTERNS) {
        if (pattern.test(trimmed)) {
            return true;
        }
    }
    
    return false;
}

/**
 * 提取用户名
 */
function extractUsername(message) {
    for (const pattern of TRIGGER_PATTERNS) {
        const match = message.match(pattern);
        if (match) {
            return match[1].trim();
        }
    }
    
    return message.trim();
}

/**
 * 激活技能
 */
function activateSkill(message, options = {}) {
    return new Promise((resolve, reject) => {
        // 检查Python激活器是否存在
        if (!fs.existsSync(PYTHON_ACTIVATOR)) {
            return reject(new Error(`Python激活器不存在: ${PYTHON_ACTIVATOR}`));
        }
        
        // 提取用户名
        const username = extractUsername(message);
        
        // 构建命令行
        let cmd = `python "${PYTHON_ACTIVATOR}" "${message}"`;
        
        if (options.debug) {
            cmd += ' --debug';
        }
        
        if (options.simulate) {
            cmd += ' --simulate';
        }
        
        if (options.confidence && options.confidence !== 0.9) {
            cmd += ` --confidence ${options.confidence}`;
        }
        
        // 执行Python脚本
        exec(cmd, {
            cwd: SKILL_DIR,
            encoding: 'utf8',
            timeout: 300000, // 5分钟超时
            maxBuffer: 1024 * 1024 * 5 // 5MB缓冲区
        }, (error, stdout, stderr) => {
            if (error) {
                // 超时错误
                if (error.killed) {
                    return reject(new Error('执行超时（5分钟）'));
                }
                
                // 其他错误
                const result = {
                    success: false,
                    error: error.message,
                    exitCode: error.code,
                    stderr: stderr,
                    stdout: stdout
                };
                return resolve(result);
            }
            
            // 成功执行
            const result = {
                success: true,
                stdout: stdout,
                stderr: stderr,
                exitCode: 0
            };
            resolve(result);
        });
    });
}

/**
 * Moltbot技能接口
 */
module.exports = {
    name: 'wechat-call-python',
    description: '使用Python自动化控制微信桌面客户端进行电话拨打',
    
    /**
     * 检查是否应该激活技能
     */
    shouldActivate(message) {
        return shouldActivate(message);
    },
    
    /**
     * 激活技能
     */
    async activate(message, context = {}) {
        try {
            // 检查Python环境
            const pythonCheck = await new Promise((resolve) => {
                exec('python --version', (error) => {
                    resolve(!error);
                });
            });
            
            if (!pythonCheck) {
                throw new Error('Python环境不可用，请确保Python已安装并添加到PATH');
            }
            
            // 检查依赖
            const depsCheck = await new Promise((resolve) => {
                const checkCmd = `python -c "import pyautogui, PIL; print('依赖检查通过')"`;
                exec(checkCmd, (error) => {
                    resolve(!error);
                });
            });
            
            if (!depsCheck) {
                throw new Error('Python依赖缺失，请运行: pip install pyautogui pillow');
            }
            
            // 执行技能
            const result = await activateSkill(message, {
                debug: context.debug || false,
                simulate: context.simulate || false,
                confidence: context.confidence || 0.9
            });
            
            return result;
            
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    },
    
    /**
     * 获取技能信息
     */
    getInfo() {
        return {
            name: 'wechat-call-python',
            version: '1.0.0',
            description: 'Python版本的微信电话自动化技能',
            requirements: [
                'Python 3.8+',
                'pyautogui (pip install pyautogui)',
                'Pillow (pip install pillow)',
                '可选: opencv-python (pip install opencv-python)'
            ],
            triggerPatterns: TRIGGER_PATTERNS.map(p => p.toString())
        };
    }
};