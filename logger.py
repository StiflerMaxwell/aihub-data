"""
AI工具导入系统 - 日志管理
"""

import datetime
from config import config

class Logger:
    """统一日志管理器"""
    
    def __init__(self):
        self.log_file = config.LOG_FILE
        self.debug_mode = config.DEBUG_MODE
    
    def log(self, message, level="INFO"):
        """记录日志消息"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # 输出到控制台
        print(log_entry)
        
        # 写入日志文件
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"写入日志文件失败: {e}")
    
    def info(self, message):
        """信息日志"""
        self.log(message, "INFO")
    
    def warning(self, message):
        """警告日志"""
        self.log(message, "WARNING")
    
    def error(self, message):
        """错误日志"""
        self.log(message, "ERROR")
    
    def debug(self, message):
        """调试日志"""
        if self.debug_mode:
            self.log(message, "DEBUG")
    
    def success(self, message):
        """成功日志"""
        self.log(f"✓ {message}", "SUCCESS")
    
    def failure(self, message):
        """失败日志"""
        self.log(f"✗ {message}", "FAILURE")

# 全局日志实例
logger = Logger() 