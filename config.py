"""
AI工具导入系统 - 配置管理
"""

import os
from dotenv import load_dotenv

# 安全加载.env文件
try:
    # 尝试加载.env文件，如果不存在则跳过
    if os.path.exists('.env'):
        load_dotenv('.env', encoding='utf-8')
    else:
        print("注意: .env文件不存在，将使用env.example作为参考创建")
except Exception as e:
    print(f"警告: 加载.env文件时出错: {e}")
    print("将使用默认配置或环境变量")

class Config:
    """配置管理类"""
    
    def __init__(self):
        # === API配置 ===
        self.FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY', '')
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
        self.SCREENSHOT_API_KEY = os.getenv('SCREENSHOT_API_KEY', '')
        
        # === WordPress配置 ===
        self.WP_USERNAME = os.getenv('WP_USERNAME', '')
        self.WP_APP_PASSWORD = os.getenv('WP_APP_PASSWORD', '')
        self.WP_API_BASE_URL = os.getenv('WP_API_BASE_URL', '')
        
        # 确保WP_API_BASE_URL不为空时再构建自定义API URL
        if self.WP_API_BASE_URL:
            self.WP_CUSTOM_API_BASE_URL = f"{self.WP_API_BASE_URL.replace('/wp/v2', '')}/ai-tools/v1"
        else:
            self.WP_CUSTOM_API_BASE_URL = ""
        
        # === 功能开关 ===
        self.ENABLE_FIRECRAWL = self._get_bool('ENABLE_FIRECRAWL', True)
        self.ENABLE_GEMINI_ENHANCEMENT = self._get_bool('ENABLE_GEMINI_ENHANCEMENT', True)
        self.DEBUG_MODE = self._get_bool('DEBUG_MODE', True)
        
        # === 处理参数 ===
        self.MAX_TOOLS_TO_PROCESS = self._get_int('MAX_TOOLS_TO_PROCESS', None)
        self.SCRAPE_DELAY = self._get_float('SCRAPE_DELAY', 2.0)
        self.IMPORT_DELAY = self._get_float('IMPORT_DELAY', 1.0)
        self.REQUEST_TIMEOUT = self._get_int('REQUEST_TIMEOUT', 30)
        self.FIRECRAWL_TIMEOUT = self._get_int('FIRECRAWL_TIMEOUT', 120)
        
        # === 文件路径 ===
        self.INPUT_CSV_FILE = 'AI工具汇总-工作表2.csv'
        self.SCHEMA_FILE = 'ai_tool_firecrawl_schema.json'
        self.OUTPUT_JSON_FILE = 'processed_tools_data.json'
        self.LOG_FILE = 'import_log.txt'
    
    def _get_bool(self, key, default=False):
        """从环境变量获取布尔值"""
        value = os.getenv(key, '').lower()
        return value in ('true', '1', 'yes', 'on') if value else default
    
    def _get_int(self, key, default=None):
        """从环境变量获取整数值"""
        value = os.getenv(key)
        if value:
            try:
                return int(value)
            except ValueError:
                pass
        return default
    
    def _get_float(self, key, default=None):
        """从环境变量获取浮点数值"""
        value = os.getenv(key)
        if value:
            try:
                return float(value)
            except ValueError:
                pass
        return default
    
    def validate(self):
        """验证配置"""
        errors = []
        
        if self.ENABLE_FIRECRAWL and not self.FIRECRAWL_API_KEY:
            errors.append("请设置FIRECRAWL_API_KEY或设置ENABLE_FIRECRAWL=false")
        
        if self.ENABLE_GEMINI_ENHANCEMENT and not self.GEMINI_API_KEY:
            errors.append("请设置GEMINI_API_KEY或禁用Gemini增强")
        
        if not self.WP_USERNAME:
            errors.append("请设置WP_USERNAME")
        
        if not self.WP_APP_PASSWORD:
            errors.append("请设置WP_APP_PASSWORD")
        
        if not self.WP_API_BASE_URL:
            errors.append("请设置WP_API_BASE_URL")
        
        return errors
    
    def print_summary(self):
        """打印配置摘要"""
        print("=== 配置摘要 ===")
        print(f"Firecrawl抓取: {'启用' if self.ENABLE_FIRECRAWL else '禁用'}")
        print(f"Firecrawl API: {'已配置' if self.FIRECRAWL_API_KEY else '未配置'}")
        print(f"Gemini增强: {'启用' if self.ENABLE_GEMINI_ENHANCEMENT else '禁用'}")
        print(f"WordPress: {self.WP_API_BASE_URL or '未配置'}")
        print(f"处理限制: {self.MAX_TOOLS_TO_PROCESS or '无限制'}")
        print(f"调试模式: {'开启' if self.DEBUG_MODE else '关闭'}")
        print("================")
        
        if not self.ENABLE_FIRECRAWL:
            print("⚠️  注意: Firecrawl已禁用，将使用CSV基础数据")
    
    def create_env_file(self):
        """创建.env文件"""
        if not os.path.exists('.env'):
            try:
                # 复制env.example到.env
                with open('env.example', 'r', encoding='utf-8') as source:
                    content = source.read()
                
                with open('.env', 'w', encoding='utf-8') as target:
                    target.write(content)
                
                print("✅ 已创建.env文件，请编辑其中的配置信息")
                return True
            except Exception as e:
                print(f"❌ 创建.env文件失败: {e}")
                return False
        else:
            print("ℹ️  .env文件已存在")
            return True

# 全局配置实例
config = Config()

if __name__ == "__main__":
    # 如果.env文件不存在，尝试创建
    if not os.path.exists('.env'):
        print("检测到.env文件不存在，正在创建...")
        config.create_env_file()
        print("\n请编辑.env文件并设置正确的配置，然后重新运行程序。")
    else:
        config.print_summary()
        errors = config.validate()
        if errors:
            print("\n配置错误:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\n✅ 配置验证通过！") 