# AI工具数据导入系统

一个完整的Python系统，用于从CSV文件读取AI工具列表，使用Firecrawl进行数据抓取，然后导入到WordPress的自定义文章类型(CPT) + ACF结构中。

## 📋 系统概述

本系统支持两种导入方式：

### 1. 标准WordPress REST API
使用WordPress内置REST API端点进行数据导入。

### 2. 自定义WordPress API ⭐（推荐）
使用专门开发的WordPress自定义API，提供更好的性能和功能。

## 🎯 主要功能

- **CSV数据解析**: 支持多列格式的AI工具数据
- **Firecrawl集成**: 自动抓取网站结构化数据
- **WordPress集成**: 完整的CPT + ACF + 分类法支持
- **图片处理**: 自动下载和上传图片到WordPress媒体库
- **批量导入**: 高效的批量处理功能
- **重复检测**: 智能检测和更新现有工具
- **错误处理**: 完整的错误处理和日志记录

## 📁 文件结构

```
aihub-data/
├── 核心文件
│   ├── ai_tools_import.py          # 主导入脚本（标准API）
│   ├── csv_data_processor.py       # CSV数据解析器
│   ├── config.py                   # 配置管理
│   └── requirements.txt            # Python依赖
│
├── 自定义API ⭐
│   ├── wordpress_custom_api.php    # WordPress自定义API插件
│   ├── ai_tools_custom_api_client.py     # 基础自定义API客户端
│   ├── ai_tools_custom_api_advanced.py   # 高级自定义API客户端（含Firecrawl）
│   └── CUSTOM_API_SETUP.md         # 自定义API安装指南
│
├── 配置文件
│   ├── ai_tool_firecrawl_schema.json     # Firecrawl抓取Schema
│   ├── env.example                       # 环境变量模板
│   └── .gitignore                        # Git忽略文件
│
├── 数据文件
│   └── AI工具汇总-工作表2.csv      # AI工具数据源
│
└── 文档
    ├── README.md                   # 本文档
    ├── CUSTOM_API_SETUP.md         # 自定义API详细指南
    └── wordpress_api_examples.md    # WordPress API使用示例
```

## 🚀 快速开始

### 方法一：使用自定义API（推荐）

1. **安装WordPress插件**
   ```bash
   # 上传 wordpress_custom_api.php 到 WordPress 插件目录
   # 在WordPress后台启用插件
   ```

2. **配置环境**
   ```bash
   # 复制环境变量模板
   cp env.example .env
   
   # 编辑 .env 文件，填入您的配置
   nano .env
   ```

3. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **运行导入**
   ```bash
   # 基础版本（仅CSV数据）
   python ai_tools_custom_api_client.py
   
   # 高级版本（CSV + Firecrawl抓取）
   python ai_tools_custom_api_advanced.py
   ```

### 方法二：使用标准WordPress API

```bash
# 配置环境变量
cp env.example .env
nano .env

# 安装依赖
pip install -r requirements.txt

# 运行主导入脚本
python ai_tools_import.py
```

## ⚙️ 环境配置

创建 `.env` 文件并配置以下变量：

```env
# WordPress配置
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_PASSWORD=your_application_password

# CSV文件路径
CSV_FILE_PATH=AI工具汇总-工作表2.csv

# Firecrawl配置（可选）
FIRECRAWL_API_KEY=your_firecrawl_api_key
FIRECRAWL_BASE_URL=https://api.firecrawl.dev

# 调试设置
DEBUG_MODE=true
MAX_TOOLS_TO_PROCESS=5
```

## 📊 数据结构

### CSV数据格式
系统支持多列格式的CSV文件，包含10个AI工具类别：
- AI Search Engine
- AI ChatBots  
- AI Character Generator
- AI Presentation Maker
- AI Image Generator
- AI Image Editor
- AI Image Enhancer
- AI Video Generator
- AI Video Editing
- AI Music Generator

### WordPress数据结构
- **自定义文章类型**: `ai_tool`
- **自定义分类法**: `ai_tool_category`
- **ACF字段组**: 包含30+个字段，支持各种数据类型

## 🔧 WordPress配置要求

### 必需组件
1. **WordPress 5.0+**
2. **ACF Pro插件**
3. **自定义文章类型**: `ai_tool`
4. **自定义分类法**: `ai_tool_category`

### ACF字段配置
系统需要以下ACF字段：

**基本信息字段**:
- `product_url` (URL)
- `short_introduction` (Textarea)
- `product_story` (Textarea)
- `primary_task` (Text)
- `author_company` (Text)
- `general_price_tag` (Text)
- `initial_release_date` (Date)
- `is_verified_tool` (True/False)

**媒体字段**:
- `logo_img` (Image)
- `overview_img` (Image)

**数值字段**:
- `popularity_score` (Number)
- `number_of_tools_by_author` (Number)
- `average_rating` (Number)
- `rating_count` (Number)

**Repeater字段**:
- `inputs` (Repeater with `input_type`)
- `outputs` (Repeater with `output_type`)
- `pros_list` (Repeater with `pro_item`)
- `cons_list` (Repeater with `con_item`)
- `related_tasks` (Repeater with `task_item`)

## 🔄 API对比

| 特性 | 标准WordPress API | 自定义API |
|------|------------------|-----------|
| 设置复杂度 | 低 | 中 |
| 性能 | 一般 | 优秀 |
| API调用次数 | 多（每个操作一次） | 少（批量处理） |
| 错误处理 | 基础 | 高级 |
| 批量导入 | 支持 | 优化支持 |
| 重复检测 | 手动 | 自动 |
| 图片处理 | 分步骤 | 集成 |
| 自定义逻辑 | 有限 | 完全可控 |

## 📈 性能特点

- **CSV解析**: 成功处理123个AI工具数据
- **Firecrawl集成**: 支持结构化数据提取
- **批量处理**: 支持可配置的批量大小
- **错误恢复**: 完整的错误处理和重试机制
- **图片优化**: 自动下载、验证和上传图片
- **重复检测**: 基于URL和名称的智能重复检测

## 🛡️ 安全特性

- **环境变量**: 敏感信息通过 `.env` 文件管理
- **WordPress认证**: 使用应用密码而非实际密码
- **权限验证**: API端点包含权限检查
- **数据验证**: 输入数据完整验证和清理
- **速率限制**: 内置延迟机制防止服务器过载

## 📝 使用示例

### 自定义API导入
```python
from ai_tools_custom_api_advanced import AdvancedCustomAPIClient
from config import Config

# 初始化
config = Config()
client = AdvancedCustomAPIClient(config)

# 测试连接
if client.test_connection():
    # 加载和导入数据
    # ... (详见脚本文件)
```

### 标准API导入
```python
from ai_tools_import import main

# 运行导入
main()
```

## 🔍 日志和调试

系统提供详细的日志记录：

- **标准API**: `ai_tools_import.log`
- **自定义API基础版**: `custom_api_import.log`
- **自定义API高级版**: `advanced_api_import.log`

调试选项：
- `DEBUG_MODE=true` - 启用详细日志
- `MAX_TOOLS_TO_PROCESS=5` - 限制处理数量用于测试

## 🚨 故障排除

### 常见问题

1. **API连接失败**
   - 检查WordPress URL和认证信息
   - 确认使用应用密码而非普通密码

2. **ACF字段未更新**
   - 验证ACF Pro已安装和配置
   - 检查字段名称匹配

3. **图片上传失败**
   - 检查WordPress上传权限
   - 验证图片URL可访问性

4. **Firecrawl抓取失败**
   - 验证API密钥有效性
   - 检查网站可访问性

### 调试步骤

1. 启用调试模式
2. 限制处理数量进行测试
3. 查看相应日志文件
4. 验证WordPress配置

## 📚 详细文档

- **[自定义API安装指南](CUSTOM_API_SETUP.md)** - 完整的自定义API设置说明
- **[WordPress API示例](wordpress_api_examples.md)** - WordPress REST API使用示例

## 🔄 版本历史

- **v1.3** - 添加自定义WordPress API支持
- **v1.2** - 环境变量重构和安全改进
- **v1.1** - Firecrawl集成和批量导入
- **v1.0** - 基础CSV导入和WordPress集成

## 📋 系统要求

- **Python 3.7+**
- **WordPress 5.0+**
- **ACF Pro插件**
- **requests库**
- **python-dotenv库**

## 🤝 贡献

欢迎提交问题和改进建议！

## 📄 许可证

本项目采用MIT许可证。 