# AI工具数据导入系统

一个完整的AI工具数据自动化处理系统，支持从CSV文件解析、网站数据抓取、AI内容增强到WordPress导入的全流程自动化。

## 功能特色

- 🔄 **全自动化流程**: CSV解析 → Firecrawl抓取 → Gemini增强 → Favicon获取 → WordPress导入
- 🤖 **AI智能增强**: 使用Gemini AI自动生成产品描述、优缺点分析等
- 🌐 **网站数据抓取**: 基于Firecrawl API的结构化数据抓取
- 🖼️ **图像资源处理**: 自动获取网站favicon和logo
- 📊 **WordPress集成**: 完整的ACF字段支持和自定义文章类型
- ⚙️ **灵活配置**: 环境变量配置，支持调试模式和批量限制

## 系统架构

```
CSV数据 → 数据解析 → Firecrawl抓取 → Gemini增强 → Favicon获取 → WordPress导入
```

### 核心组件

- **config.py**: 统一配置管理
- **logger.py**: 日志管理系统
- **csv_data_processor.py**: CSV数据解析器
- **firecrawl_scraper.py**: Firecrawl网站抓取器
- **gemini_enhancer.py**: Gemini AI数据增强器
- **favicon_logo_helper.py**: Favicon和Logo获取器
- **wordpress_importer.py**: WordPress数据导入器
- **main_import.py**: 主导入脚本
- **test_system.py**: 系统测试脚本

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd ai-tools-import-system

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
```

### 2. 配置设置

编辑 `.env` 文件，设置必要的配置：

```env
# Firecrawl API配置
FIRECRAWL_API_KEY=fc-your_firecrawl_api_key_here

# Gemini API配置 (可选)
GEMINI_API_KEY=your_gemini_api_key_here
ENABLE_GEMINI_ENHANCEMENT=true

# WordPress配置
WP_USERNAME=your_wordpress_admin_username
WP_APP_PASSWORD=your_wordpress_application_password
WP_API_BASE_URL=https://yourdomain.com/wp-json/wp/v2

# 可选配置
DEBUG_MODE=true
MAX_TOOLS_TO_PROCESS=5
SCRAPE_DELAY=2
IMPORT_DELAY=1
```

### 3. WordPress准备

确保WordPress已安装并配置：

1. **自定义文章类型**: 创建 `aihub` CPT
2. **ACF字段组**: 配置相应的自定义字段
3. **自定义API插件**: 安装 `wordpress_custom_api.php` 插件
4. **应用密码**: 为WordPress用户生成应用密码

### 4. 数据准备

将AI工具数据整理到CSV文件中，确保格式正确：

- 文件名: `AI工具汇总-工作表2.csv`
- 格式: 横向分类格式，包含产品名称和网址列

### 5. 运行系统

```bash
# 运行系统测试
python test_system.py

# 执行完整导入流程
python main_import.py
```

## 详细配置

### 环境变量说明

| 变量名 | 必需 | 说明 |
|--------|------|------|
| `FIRECRAWL_API_KEY` | 是 | Firecrawl API密钥 |
| `GEMINI_API_KEY` | 否 | Gemini API密钥（启用AI增强时必需） |
| `WP_USERNAME` | 是 | WordPress管理员用户名 |
| `WP_APP_PASSWORD` | 是 | WordPress应用密码 |
| `WP_API_BASE_URL` | 是 | WordPress REST API基础URL |
| `ENABLE_GEMINI_ENHANCEMENT` | 否 | 是否启用Gemini增强（默认true） |
| `DEBUG_MODE` | 否 | 调试模式（默认true） |
| `MAX_TOOLS_TO_PROCESS` | 否 | 最大处理工具数量（留空处理全部） |
| `SCRAPE_DELAY` | 否 | 抓取延迟秒数（默认2） |
| `IMPORT_DELAY` | 否 | 导入延迟秒数（默认1） |

### WordPress ACF字段结构

系统支持以下ACF字段组：

1. **AI Tool Basic Info**: 基础信息字段
2. **AI Tool IO**: 输入输出类型
3. **AI Tool Pricing**: 定价信息
4. **AI Tool Releases**: 版本发布历史
5. **AI Tool Reviews**: 评论和评分
6. **AI Tool Job Impacts**: 工作影响分析
7. **AI Tool Pros & Cons**: 优缺点列表
8. **AI Tool Alternatives**: 替代工具
9. **AI Tool See Also**: 相关推荐

## 使用示例

### 基本使用

```bash
# 测试系统配置
python test_system.py

# 运行完整导入（处理所有工具）
python main_import.py
```

### 调试模式

```bash
# 设置环境变量启用调试
export DEBUG_MODE=true
export MAX_TOOLS_TO_PROCESS=3

# 运行导入
python main_import.py
```

### 单独测试组件

```python
# 测试CSV解析
from csv_data_processor import parse_ai_tools_csv
tools = parse_ai_tools_csv('AI工具汇总-工作表2.csv')

# 测试Firecrawl抓取
from firecrawl_scraper import FirecrawlScraper
scraper = FirecrawlScraper()
schema = scraper.load_schema()
result = scraper.scrape_website('https://chat.openai.com', schema)

# 测试WordPress连接
from wordpress_importer import WordPressImporter
importer = WordPressImporter()
importer.test_connection()
```

## 故障排除

### 常见问题

1. **配置验证失败**
   - 检查 `.env` 文件是否存在且配置正确
   - 确认所有必需的API密钥已设置

2. **WordPress连接失败**
   - 验证WordPress URL和认证信息
   - 确认自定义API插件已安装并激活
   - 检查用户权限和应用密码

3. **Firecrawl抓取失败**
   - 验证Firecrawl API密钥
   - 检查网络连接和API配额
   - 确认Schema文件格式正确

4. **Gemini增强失败**
   - 验证Gemini API密钥
   - 检查API配额和网络连接
   - 可以禁用Gemini增强继续使用

### 日志查看

系统会自动生成详细的日志文件：

```bash
# 查看日志
tail -f import_log.txt

# 查看最近的错误
grep "ERROR" import_log.txt
```

## 开发指南

### 扩展新功能

1. **添加新的数据源**
   - 在相应的抓取器中添加新方法
   - 更新Schema定义

2. **增加新的增强器**
   - 创建新的增强器类
   - 在主流程中集成

3. **自定义WordPress字段**
   - 更新ACF字段定义
   - 修改导入器的字段映射

### 代码结构

```
├── config.py              # 配置管理
├── logger.py               # 日志系统
├── csv_data_processor.py   # CSV解析
├── firecrawl_scraper.py    # 网站抓取
├── gemini_enhancer.py      # AI增强
├── favicon_logo_helper.py  # 图像获取
├── wordpress_importer.py   # WordPress导入
├── main_import.py          # 主程序
├── test_system.py          # 系统测试
├── requirements.txt        # 依赖包
├── env.example            # 配置示例
└── README.md              # 说明文档
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 支持

如果遇到问题，请：

1. 查看日志文件获取详细错误信息
2. 运行系统测试检查各组件状态
3. 检查配置文件和环境变量
4. 提交Issue描述问题和环境信息 