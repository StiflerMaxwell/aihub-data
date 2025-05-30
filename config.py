import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

def get_bool_env(key, default=False):
    """从环境变量获取布尔值"""
    value = os.getenv(key, '').lower()
    return value in ('true', '1', 'yes', 'on')

def get_int_env(key, default=None):
    """从环境变量获取整数值"""
    value = os.getenv(key)
    if value:
        try:
            return int(value)
        except ValueError:
            pass
    return default

def get_float_env(key, default=None):
    """从环境变量获取浮点数值"""
    value = os.getenv(key)
    if value:
        try:
            return float(value)
        except ValueError:
            pass
    return default

# === Firecrawl配置 ===
FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY', 'fc-YOUR_FIRECRAWL_API_KEY')

# === WordPress配置 ===
WP_USERNAME = os.getenv('WP_USERNAME', 'your_wordpress_admin_username')
WP_APP_PASSWORD = os.getenv('WP_APP_PASSWORD', 'your_wordpress_application_password')
WP_API_BASE_URL = os.getenv('WP_API_BASE_URL', 'https://yourdomain.com/wp-json/wp/v2')

# === 文件路径配置 ===
INPUT_CSV_FILE = os.getenv('INPUT_CSV_FILE', 'AI工具汇总-工作表2.csv')
SCHEMA_FILE = os.getenv('SCHEMA_FILE', 'ai_tool_firecrawl_schema.json')
OUTPUT_RAW_FIRECRAWL_DATA = os.getenv('OUTPUT_RAW_FIRECRAWL_DATA', 'raw_firecrawl_data.json')
LOG_FILE = os.getenv('LOG_FILE', 'import_log.txt')

# === 抓取配置 ===
SCRAPE_DELAY = get_float_env('SCRAPE_DELAY', 2.0)
IMPORT_DELAY = get_float_env('IMPORT_DELAY', 1.0)

# 超时设置（秒）
REQUEST_TIMEOUT = get_int_env('REQUEST_TIMEOUT', 30)
FIRECRAWL_TIMEOUT = get_int_env('FIRECRAWL_TIMEOUT', 120)

# === WordPress自定义分类法设置 ===
CATEGORY_TAXONOMY = os.getenv('CATEGORY_TAXONOMY', 'ai_tool_category')
TAG_TAXONOMY = os.getenv('TAG_TAXONOMY', 'ai_tool_tag')

# === Firecrawl Actions配置 ===
# 根据目标网站的具体结构调整这些动作
FIRECRAWL_ACTIONS = [
    {"type": "wait", "milliseconds": 2000},  # 等待页面加载
    {"type": "scroll", "direction": "down"},  # 向下滚动
    {"type": "wait", "milliseconds": 1000},   # 等待内容加载
    # 如果目标网站有标签页，可以添加点击动作
    # {"type": "click", "selector": ".pricing-tab"},
    # {"type": "wait", "milliseconds": 500},
    # {"type": "click", "selector": ".features-tab"},
    # {"type": "wait", "milliseconds": 500},
]

# === 调试配置 ===
DEBUG_MODE = get_bool_env('DEBUG_MODE', True)
MAX_TOOLS_TO_PROCESS = get_int_env('MAX_TOOLS_TO_PROCESS', None)

# === 配置验证 ===
def validate_config():
    """验证配置是否正确"""
    errors = []
    
    if FIRECRAWL_API_KEY == 'fc-YOUR_FIRECRAWL_API_KEY':
        errors.append("请在.env文件中设置FIRECRAWL_API_KEY")
    
    if WP_USERNAME == 'your_wordpress_admin_username':
        errors.append("请在.env文件中设置WP_USERNAME")
    
    if WP_APP_PASSWORD == 'your_wordpress_application_password':
        errors.append("请在.env文件中设置WP_APP_PASSWORD")
    
    if WP_API_BASE_URL == 'https://yourdomain.com/wp-json/wp/v2':
        errors.append("请在.env文件中设置WP_API_BASE_URL")
    
    return errors

def print_config_summary():
    """打印配置摘要（隐藏敏感信息）"""
    print("=== 配置摘要 ===")
    print(f"Firecrawl API Key: {FIRECRAWL_API_KEY[:10]}..." if FIRECRAWL_API_KEY != 'fc-YOUR_FIRECRAWL_API_KEY' else "Firecrawl API Key: 未设置")
    print(f"WordPress 用户名: {WP_USERNAME}")
    print(f"WordPress API URL: {WP_API_BASE_URL}")
    print(f"调试模式: {DEBUG_MODE}")
    print(f"处理限制: {MAX_TOOLS_TO_PROCESS if MAX_TOOLS_TO_PROCESS else '无限制'}")
    print(f"抓取延迟: {SCRAPE_DELAY}秒")
    print(f"导入延迟: {IMPORT_DELAY}秒")
    print("================")

if __name__ == "__main__":
    # 当直接运行config.py时，显示配置摘要和验证结果
    print_config_summary()
    
    errors = validate_config()
    if errors:
        print("\n⚠️  配置错误:")
        for error in errors:
            print(f"  - {error}")
        print("\n请创建.env文件并设置正确的配置。参考env.example文件。")
    else:
        print("\n✅ 配置验证通过！") 