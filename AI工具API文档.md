# AI工具API文档

## 概述

AI工具API提供了完整的AI工具数据管理功能，支持工具的导入、查询、更新等操作。所有API响应均为JSON格式，并支持丰富的工具数据字段。

**基础URL**: `https://vertu.com/wp-json/ai-tools/v1`

## 认证

所有API请求需要在请求头中包含API密钥：

```
X-API-Key: your_api_key_here
```

## API端点

### 1. 获取工具列表

**GET** `/tools`

获取所有AI工具的列表信息。

#### 请求参数
无

#### 响应示例
```json
{
  "success": true,
  "data": [
    {
      "id": 100027,
      "product_name": "ChatGPT",
      "short_introduction": "AI ChatBots tool for intelligent conversations",
      "category": "AI ChatBots",
      "product_url": "https://chat.openai.com",
      "logo_img_url": "",
      "general_price_tag": "Freemium",
      "average_rating": 4.8,
      "popularity_score": 100,
      "user_ratings_count": 150,
      "author_company": "OpenAI",
      "primary_task": "Text Generation",
      "initial_release_date": "2022-11-30",
      "faq": [
        {
          "question": "What is ChatGPT?",
          "answer": "ChatGPT is an AI ChatBots tool that helps users with AI-powered tasks."
        }
      ]
    }
  ],
  "count": 1
}
```

### 2. 获取单个工具详情

**GET** `/tools/{id}`

获取指定工具的详细信息。

#### 请求参数
- `id` (integer): 工具ID

#### 响应示例
```json
{
  "success": true,
  "data": {
    "id": 100027,
    "product_name": "ChatGPT",
    "short_introduction": "AI ChatBots tool for intelligent conversations",
    "product_story": "ChatGPT is a state-of-the-art conversational AI...",
    "category": "AI ChatBots",
    "product_url": "https://chat.openai.com",
    "logo_img_url": "",
    "overview_img_url": "",
    "demo_video_url": "",
    "general_price_tag": "Freemium",
    "average_rating": 4.8,
    "popularity_score": 100,
    "user_ratings_count": 150,
    "author_company": "OpenAI",
    "primary_task": "Text Generation",
    "initial_release_date": "2022-11-30",
    "message": "Hello! How can I help you today?",
    "inputs": ["Text", "Voice"],
    "outputs": ["Text", "Code"],
    "features": [
      {
        "feature_name": "自然语言理解",
        "feature_description": "强大的自然语言理解能力"
      }
    ],
    "pros_list": [
      "强大的对话能力",
      "支持多种语言",
      "持续学习改进"
    ],
    "cons_list": [
      "可能生成不准确信息",
      "需要网络连接"
    ],
    "related_tasks": [
      "内容创作",
      "代码编写",
      "问题解答"
    ],
    "job_impacts": [
      {
        "job_title": "内容编辑",
        "impact_type": "提升效率",
        "impact_description": "可以协助内容创作和编辑工作"
      }
    ],
    "alternative_tools": [
      "Claude",
      "Gemini",
      "Copilot"
    ],
    "faq": [
      {
        "question": "What is ChatGPT?",
        "answer": "ChatGPT is an AI ChatBots tool that helps users with AI-powered tasks."
      },
      {
        "question": "How do I use ChatGPT?",
        "answer": "Simply visit the website, create an account if needed, and start using the AI ChatBots features."
      }
    ],
    "pricing_details": {
      "pricing_model": "Freemium",
      "paid_options_from": 20,
      "currency": "USD",
      "billing_frequency": "monthly"
    },
    "releases": [
      {
        "version": "4.0",
        "release_date": "2023-03-14",
        "features": ["Enhanced reasoning", "Multimodal capabilities"]
      }
    ],
    "ratings_data": {
      "average_rating": 4.8,
      "popularity_score": 100,
      "user_ratings_count": 150,
      "rating_distribution": {
        "5": 120,
        "4": 20,
        "3": 7,
        "2": 2,
        "1": 1
      }
    }
  }
}
```

### 3. 获取热门工具

**GET** `/tools/popular`

获取按人气评分排序的热门工具列表。

#### 请求参数
- `limit` (integer, 可选): 返回工具数量，默认为10

#### 响应示例
```json
{
  "success": true,
  "data": [
    {
      "id": 100027,
      "product_name": "ChatGPT",
      "popularity_score": 100,
      "category": "AI ChatBots",
      "short_introduction": "AI ChatBots tool for intelligent conversations",
      "average_rating": 4.8,
      "user_ratings_count": 150
    },
    {
      "id": 100028,
      "product_name": "Visual Search",
      "popularity_score": 92,
      "category": "AI Search Engine",
      "short_introduction": "AI-powered visual search tool",
      "average_rating": 4.6,
      "user_ratings_count": 80
    }
  ],
  "count": 2
}
```

### 4. 导入工具

**POST** `/import`

导入新的AI工具或更新现有工具。

#### 请求头
```
Content-Type: application/json
X-API-Key: your_api_key_here
```

#### 请求体
```json
{
  "tool_data": {
    "product_name": "New AI Tool",
    "product_url": "https://example.com",
    "short_introduction": "A powerful AI tool",
    "category": "AI Assistant",
    "product_story": "This tool helps users...",
    "author_company": "AI Company",
    "general_price_tag": "Free"
  },
  "post_id": null,
  "update_mode": false
}
```

#### 响应示例
```json
{
  "success": true,
  "message": "工具导入成功",
  "post_id": 100030,
  "tool_name": "New AI Tool",
  "enhanced_fields": [
    "faq",
    "features",
    "popularity_score",
    "inputs",
    "outputs"
  ]
}
```

## 数据字段说明

### 工具基础信息
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | integer | 工具唯一标识符 |
| `product_name` | string | 工具名称 |
| `short_introduction` | string | 简短介绍 |
| `product_story` | string | 详细产品描述 |
| `category` | string | 工具分类 |
| `product_url` | string | 工具官网URL |
| `logo_img_url` | string | Logo图片URL |
| `overview_img_url` | string | 概览图片URL |
| `demo_video_url` | string | 演示视频URL |

### 定价信息
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `general_price_tag` | string | 定价标签 (Free/Freemium/Paid/Enterprise) |
| `pricing_details` | object | 详细定价信息 |
| `pricing_details.pricing_model` | string | 定价模式 |
| `pricing_details.paid_options_from` | number | 付费版起价 |
| `pricing_details.currency` | string | 货币单位 |
| `pricing_details.billing_frequency` | string | 计费周期 |

### 评分和人气
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `average_rating` | number | 平均评分 (0-5) |
| `popularity_score` | integer | 人气评分 (0-100) |
| `user_ratings_count` | integer | 用户评分数量 |
| `ratings_data` | object | 详细评分数据 |
| `ratings_data.rating_distribution` | object | 评分分布 |

### 功能特性
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `inputs` | array | 支持的输入类型 |
| `outputs` | array | 生成的输出类型 |
| `features` | array | 功能特性列表 |
| `features[].feature_name` | string | 功能名称 |
| `features[].feature_description` | string | 功能描述 |

### 分析和比较
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `pros_list` | array | 优点列表 |
| `cons_list` | array | 缺点列表 |
| `related_tasks` | array | 相关任务 |
| `alternative_tools` | array | 替代工具 |
| `job_impacts` | array | 工作影响分析 |
| `job_impacts[].job_title` | string | 职位名称 |
| `job_impacts[].impact_type` | string | 影响类型 |
| `job_impacts[].impact_description` | string | 影响描述 |

### FAQ常见问题
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `faq` | array | 常见问题列表 |
| `faq[].question` | string | 问题 |
| `faq[].answer` | string | 答案 |

### 版本发布
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `releases` | array | 版本发布历史 |
| `releases[].version` | string | 版本号 |
| `releases[].release_date` | string | 发布日期 |
| `releases[].features` | array | 新功能列表 |

### 公司信息
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `author_company` | string | 开发公司 |
| `initial_release_date` | string | 首次发布日期 |
| `primary_task` | string | 主要功能 |

### UI文本
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `message` | string | 欢迎消息 |
| `how_would_you_rate_text` | string | 评分提示文本 |
| `help_other_people_text` | string | 帮助他人文本 |
| `your_rating_text` | string | 评分标签文本 |
| `post_review_button_text` | string | 发布评论按钮文本 |
| `feature_requests_intro` | string | 功能请求介绍 |
| `request_feature_button_text` | string | 请求功能按钮文本 |

## 特殊功能

### Gemini AI增强
导入工具时，系统会自动使用Gemini AI增强以下字段：
- **FAQ生成**: 自动生成5个相关的常见问题
- **功能特性**: 智能分析工具功能
- **人气评分**: 基于多因素算法计算(25-100分)
- **输入输出类型**: 自动识别支持的数据类型
- **优缺点分析**: 客观分析工具优势和局限
- **相关任务**: 识别适用的使用场景
- **工作影响**: 分析对不同职业的影响

### 人气评分算法
人气评分(25-100分)基于以下因素：
- **知名度加权**: 知名工具(ChatGPT、Claude等)获得额外分数
- **分类基础分**: 不同类别有不同基础分数
- **评分影响**: 用户评分影响最终分数
- **用户数量**: 用户基数影响权重
- **发布时间**: 较新工具获得时间奖励
- **随机因子**: 增加分数多样性

## 错误处理

### 错误响应格式
```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE"
}
```

### 常见错误代码
- `INVALID_API_KEY`: API密钥无效
- `TOOL_NOT_FOUND`: 工具未找到
- `INVALID_PARAMETERS`: 参数无效
- `SERVER_ERROR`: 服务器内部错误

## 使用示例

### Python示例
```python
import requests

# API配置
API_KEY = "your_api_key_here"
BASE_URL = "https://vertu.com/wp-json/ai-tools/v1"
headers = {'X-API-Key': API_KEY}

# 获取工具列表
response = requests.get(f'{BASE_URL}/tools', headers=headers)
tools = response.json()

# 获取热门工具
popular_response = requests.get(f'{BASE_URL}/tools/popular', headers=headers)
popular_tools = popular_response.json()

# 导入新工具
tool_data = {
    "tool_data": {
        "product_name": "New AI Assistant",
        "product_url": "https://example.com",
        "category": "AI Assistant",
        "short_introduction": "A powerful AI assistant",
        "general_price_tag": "Free"
    },
    "update_mode": False
}

import_response = requests.post(
    f'{BASE_URL}/import', 
    headers={'X-API-Key': API_KEY, 'Content-Type': 'application/json'},
    json=tool_data
)
result = import_response.json()
```

### JavaScript示例
```javascript
const API_KEY = 'your_api_key_here';
const BASE_URL = 'https://vertu.com/wp-json/ai-tools/v1';

// 获取工具列表
fetch(`${BASE_URL}/tools`, {
  headers: {
    'X-API-Key': API_KEY
  }
})
.then(response => response.json())
.then(data => console.log(data));

// 获取热门工具
fetch(`${BASE_URL}/tools/popular`, {
  headers: {
    'X-API-Key': API_KEY
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

## 版本历史

### v1.3.0 (当前版本)
- ✅ 新增FAQ字段自动生成
- ✅ 优化人气评分算法
- ✅ 增强Gemini AI功能
- ✅ 完善工具数据结构

### v1.2.0
- ✅ 新增热门工具API端点
- ✅ 增加人气评分功能
- ✅ 优化数据增强流程

### v1.1.0
- ✅ 完善工具导入功能
- ✅ 增加Gemini AI增强
- ✅ 优化API响应格式

### v1.0.0
- ✅ 基础API功能
- ✅ 工具CRUD操作
- ✅ API认证系统

---

**联系信息**: 如需技术支持或有任何问题，请联系开发团队。

**更新时间**: 2025年6月16日 