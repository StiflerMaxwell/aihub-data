# AI工具数据导入系统 🚀

一个完整的AI工具数据自动化处理系统，支持从CSV文件解析、网站数据抓取、AI内容增强到WordPress导入的全流程自动化，并提供强大的API服务。

## ✨ 功能特色

- 🔄 **全自动化流程**: CSV解析 → Firecrawl抓取 → Gemini增强 → 图像获取 → WordPress导入
- 🤖 **AI智能增强**: 使用Gemini AI自动生成产品描述、优缺点分析等
- 🌐 **网站数据抓取**: 基于Firecrawl API的结构化数据抓取
- 🖼️ **图像资源处理**: 自动获取网站favicon和logo
- 📊 **WordPress集成**: 完整的ACF字段支持和自定义文章类型
- 🚀 **强大API服务**: 完整的RESTful API，支持30+字段数据查询
- ⚙️ **灵活配置**: 环境变量配置，支持调试模式和批量限制
- 🔧 **模块化设计**: 清晰的组件分离，易于维护和扩展

## 🏗️ 系统架构

### 数据处理流程
```
CSV数据解析 → Firecrawl抓取 → Gemini增强 → 图像获取 → WordPress导入
```

### API服务架构
```
WordPress API插件 → 认证验证 → 数据查询 → JSON响应
```

## 📁 项目结构

### 🔄 数据处理核心
- **csv_data_processor.py**: CSV数据解析器
- **firecrawl_scraper.py**: 网站数据抓取器  
- **gemini_enhancer.py**: AI数据增强器
- **favicon_logo_helper.py**: 图像资源获取器
- **screenshot_helper.py**: 截图助手

### 🚀 主要执行脚本
- **main_import.py**: 完整导入流程脚本
- **main_import_simple.py**: 简化导入流程脚本
- **wordpress_importer.py**: WordPress数据导入器

### 🔧 API核心功能
- **wordpress_custom_api_fixed.php**: 完整WordPress API插件
- **test_api_usage.py**: API功能测试脚本
- **manage_api_keys.py**: API Key管理工具

### ⚙️ 系统配置
- **config.py**: 配置管理系统
- **logger.py**: 日志管理系统
- **requirements.txt**: Python依赖包

## 🚀 快速开始

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

### 3. WordPress设置

确保WordPress已安装并配置：

1. **自定义文章类型**: 创建 `aihub` CPT
2. **ACF字段组**: 配置相应的自定义字段
3. **API插件安装**: 上传 `wordpress_custom_api_fixed.php` 到插件目录并激活
4. **应用密码**: 为WordPress用户生成应用密码

### 4. 数据准备

系统包含示例数据文件：
- **AI工具汇总-工作表2.csv**: 原始AI工具数据
- **ai_tool_firecrawl_schema.json**: Firecrawl抓取字段定义

### 5. 运行系统

```bash
# 完整数据导入流程
python main_import.py

# 简化导入流程  
python main_import_simple.py

# API功能测试
python test_api_usage.py

# API Key管理
python manage_api_keys.py
```

## 🔧 API服务功能

### API端点

| 端点 | 功能 | 示例 |
|------|------|------|
| `/wp-json/ai-tools/v1/tools` | 获取工具列表 | 支持分页、搜索、筛选 |
| `/wp-json/ai-tools/v1/tools/{id}` | 获取单个工具详情 | 完整的30+字段数据 |
| `/wp-json/ai-tools/v1/tools/by-url` | 通过URL查找工具 | URL匹配查询 |
| `/wp-json/ai-tools/v1/tools/random` | 随机工具推荐 | 随机返回工具 |
| `/wp-json/ai-tools/v1/tools/popular` | 热门工具排行 | 按热度排序 |
| `/wp-json/ai-tools/v1/categories` | 获取分类列表 | 所有AI工具分类 |
| `/wp-json/ai-tools/v1/tags` | 获取标签列表 | 所有工具标签 |
| `/wp-json/ai-tools/v1/stats` | 获取统计信息 | 总数、分类统计等 |

### 认证方式

支持三种API认证方式：

```bash
# 1. X-API-Key 头部认证（推荐）
curl -H "X-API-Key: ak_your_api_key_here" \
     "https://yourdomain.com/wp-json/ai-tools/v1/tools"

# 2. Authorization Bearer 头部认证
curl -H "Authorization: Bearer ak_your_api_key_here" \
     "https://yourdomain.com/wp-json/ai-tools/v1/tools"

# 3. URL参数认证
curl "https://yourdomain.com/wp-json/ai-tools/v1/tools?api_key=ak_your_api_key_here"
```

### 高级功能

- **智能搜索**: 全文搜索工具名称和描述
- **多维筛选**: 按定价、分类、输入输出类型筛选
- **数据统计**: 获取详细的统计信息
- **速率限制**: 支持API调用频率控制
- **CORS支持**: 支持跨域访问

## ⚙️ 详细配置

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

### 支持的数据字段（30+字段）

- **基础信息**: 产品名称、官网URL、Logo图片、公司信息
- **功能特性**: 输入输出类型、定价详情、功能列表
- **评价数据**: 用户评分、热度评分、验证状态
- **AI增强**: 智能描述、优缺点分析、工作影响评估
- **关联数据**: 替代工具、相关推荐、标签分类

## 📖 使用示例

### 数据导入示例

```bash
# 调试模式（处理少量数据）
export DEBUG_MODE=true
export MAX_TOOLS_TO_PROCESS=3
python main_import.py

# 生产模式（处理全部数据）
export DEBUG_MODE=false
python main_import.py
```

### API使用示例

```python
import requests

# 获取所有工具
response = requests.get(
    "https://yourdomain.com/wp-json/ai-tools/v1/tools",
    headers={"X-API-Key": "ak_your_api_key_here"}
)

# 搜索工具
response = requests.get(
    "https://yourdomain.com/wp-json/ai-tools/v1/tools",
    params={"search": "ChatGPT", "pricing": "Free"},
    headers={"X-API-Key": "ak_your_api_key_here"}
)
```

### 组件测试示例

```python
# 测试CSV解析
from csv_data_processor import parse_ai_tools_csv
tools = parse_ai_tools_csv('AI工具汇总-工作表2.csv')

# 测试API功能
python test_api_usage.py

# 管理API Key
python manage_api_keys.py
```

## 🔍 故障排除

### 常见问题

1. **配置验证失败**
   - 检查 `.env` 文件是否存在且配置正确
   - 确认所有必需的API密钥已设置

2. **WordPress连接失败**
   - 验证WordPress URL和认证信息
   - 确认API插件已安装并激活
   - 检查用户权限和应用密码

3. **Firecrawl抓取失败**
   - 验证Firecrawl API密钥
   - 检查网络连接和API配额
   - 确认Schema文件格式正确

4. **API访问失败**
   - 检查API Key是否有效
   - 验证WordPress插件是否正确安装
   - 确认用户权限设置

### 日志查看

系统会自动生成详细的日志：

```bash
# 查看导入日志
tail -f import_log.txt

# 查看API日志
# 检查WordPress错误日志
```

## 📚 文档资源

- **API_Documentation.md**: 完整的API使用文档
- **API_功能总结.md**: API功能特性总结
- **项目功能总结.md**: 整体项目功能介绍
- **最终项目结构.md**: 项目结构说明

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [Firecrawl](https://firecrawl.dev/) - 网站数据抓取服务
- [Google Gemini](https://gemini.google.com/) - AI内容增强服务
- [WordPress](https://wordpress.org/) - 内容管理系统
- [ACF](https://www.advancedcustomfields.com/) - 高级自定义字段插件

---

⭐ 如果这个项目对您有帮助，请给它一个星标！ 