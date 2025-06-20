# AI工具API完整说明文档

## 📋 概述

AI工具API是一个功能完整的RESTful API服务，提供AI工具数据的查询、导入、管理功能。API采用WordPress REST API框架构建，支持智能推荐、分类筛选、搜索等高级功能。

**基础URL**: `https://your-domain.com/wp-json/ai-tools/v1`

## 🔐 认证方式

所有API请求都需要在请求头中包含API密钥：

```http
X-API-Key: your_api_key_here
```

### API密钥管理
- 管理员可通过WordPress后台生成和管理API密钥
- 每个密钥支持自定义名称、描述和速率限制
- 密钥具有访问控制和使用统计功能

## 🛠️ API端点

### 1. 工具列表查询

#### GET `/tools`
获取AI工具列表，支持分页、搜索、分类筛选。

**请求参数**：
- `page` (int, 可选): 页码，默认1
- `per_page` (int, 可选): 每页数量，默认20，最大100
- `search` (string, 可选): 搜索关键词
- `category` (string, 可选): 分类筛选

**请求示例**：
```bash
# 获取第一页工具列表
GET /wp-json/ai-tools/v1/tools?page=1&per_page=10

# 搜索聊天机器人工具
GET /wp-json/ai-tools/v1/tools?search=chatbot&category=AI%20ChatBots

# 分类筛选
GET /wp-json/ai-tools/v1/tools?category=AI%20Music%20Generator
```

**响应结构**：
```json
{
  "success": true,
  "data": [
    {
      "id": 100377,
      "title": "Suno",
      "product_name": "Suno",
      "short_introduction": "Make any song you can imagine with high-quality music creation accessible to all.",
      "category": "AI Music Generator",
      "product_url": "https://suno.com",
      "logo_img_url": "https://suno.com/auras-v2/Aura-1-Hero-Web.jpg",
      "overview_img_url": "https://suno.com/auras-v2/Aura-1-Hero-Web.jpg",
      "general_price_tag": "Unknown",
      "average_rating": 4.5,
      "popularity_score": 261000,
      "author_company": "Suno Team",
      "primary_task": "AI Processing",
      "initial_release_date": "2023",
      "categories": ["AI Music Generator"],
      "tags": ["Audio", "Freemium", "Music Creation"]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 25,
    "total_pages": 3
  },
  "timestamp": "2025-06-19T16:33:52+08:00"
}
```

### 2. 单个工具详情

#### GET `/tools/{id}`
获取指定工具的完整详细信息。

**请求参数**：
- `id` (int, 必需): 工具ID

**请求示例**：
```bash
GET /wp-json/ai-tools/v1/tools/100377
```

**响应结构**：
```json
{
  "success": true,
  "data": {
    "id": 100377,
    "title": "Suno",
    "slug": "suno",
    "content": "Suno is an AI Music Generator tool.",
    "excerpt": "Make any song you can imagine with high-quality music creation accessible to all.",
    "url": "https://vertu.com/aihub/suno/",
    "date_created": "2025-06-16T15:34:34+08:00",
    "date_modified": "2025-06-16T18:09:14+08:00",
    
    // 基础信息
    "product_name": "Suno",
    "product_url": "https://suno.com",
    "short_introduction": "Make any song you can imagine with high-quality music creation accessible to all.",
    "product_story": "Whether you have a melody in your head, lyrics you've written, or just a feeling you want to hear—Suno makes high-quality music creation accessible to all.",
    "author_company": "Suno Team",
    "primary_task": "AI Processing",
    "category": "AI Music Generator",
    "original_category_name": "AI Music Generator",
    "initial_release_date": "2023",
    "general_price_tag": "Unknown",
    
    // 媒体资源
    "logo_img_url": "https://suno.com/auras-v2/Aura-1-Hero-Web.jpg",
    "overview_img_url": "https://suno.com/auras-v2/Aura-1-Hero-Web.jpg",
    "demo_video_url": "https://www.youtube.com/watch?v=xmQWCvGMH0Y",
    
    // 评分数据
    "average_rating": 4.5,
    "popularity_score": 261000,
    "user_ratings_count": 5300,
    "is_verified_tool": true,
    "number_of_tools_by_author": 1,
    
    // UI文本
    "message": "Try Suno",
    "copy_url_text": "Copy URL",
    "save_button_text": "Save",
    "vote_best_ai_tool_text": "Vote for Best AI Tool",
    "how_would_you_rate_text": "How would you rate this tool?",
    "help_other_people_text": "Help others by rating this tool!",
    "your_rating_text": "Your Rating",
    "post_review_button_text": "Post Review",
    "feature_requests_intro": "Have a feature request? Let us know!",
    "request_feature_button_text": "Request Feature",
    "view_more_pros_text": "View More Pros",
    "view_more_cons_text": "View More Cons",
    "alternatives_count_text": "See 5 alternatives",
    "view_more_alternatives_text": "View more alternatives",
    "if_you_liked_text": "If you liked Suno, you might also like:",
    
    // FAQ
    "faq": [
      {
        "question": "What is Suno?",
        "answer": "Suno is an AI Music Generator tool that helps users with AI-powered tasks."
      }
    ],
    
    // 功能特性
    "inputs": ["Text", "Audio", "Images", "Videos"],
    "outputs": ["Music Tracks", "Playlists", "Lyrics"],
    "features": [
      "AI-powered processing",
      "User-friendly interface",
      "Fast performance",
      "Reliable results",
      "Easy integration"
    ],
    "pros_list": [
      "High music quality",
      "Rich styles",
      "Flexible creation",
      "Clear copyright"
    ],
    "cons_list": [
      "Questionable originality",
      "Style limitations",
      "Insufficient professional production"
    ],
    "related_tasks": [
      "Songwriting",
      "Music Production",
      "Audio Editing"
    ],
    
    // 智能推荐 - 基于真实WordPress数据库
    "alternative_tools": [
      {
        "id": 100508,
        "product_name": "Riffusion",
        "product_url": "https://www.riffusion.com/",
        "short_introduction": "Explore and create music with Riffusion.",
        "category": "AI Music Generator",
        "logo_img_url": "https://www.riffusion.com/logo.svg",
        "overview_img_url": "https://www.riffusion.com/_next/image?url=%2Fcompact_logo.png&w=128&q=75",
        "demo_video_url": "",
        "general_price_tag": "Unknown",
        "average_rating": 4.3,
        "popularity_score": 64
      }
    ],
    "featured_matches": [
      {
        "id": 100027,
        "product_name": "ChatGPT",
        "product_url": "https://chatgpt.com/",
        "short_introduction": "ChatGPT is an AI language model that can assist with a variety of tasks through conversational interactions.",
        "category": "AI ChatBots",
        "logo_img_url": "https://www.google.com/s2/favicons?domain=chatgpt.com&sz=64",
        "overview_img_url": "https://image.thum.io/get/width/1200/crop/800/noanimate/https://chatgpt.com/",
        "demo_video_url": "https://www.youtube.com/watch?v=JTxsNm9IdYU",
        "general_price_tag": "Unknown",
        "average_rating": 4.6,
        "popularity_score": 100
      }
    ],
    "other_tools": [
      // 同类别的其他工具...
    ],
    
    // 定价信息
    "pricing_details": {
      "pricing_model": "Subscription",
      "paid_options_from": 8,
      "currency": "USD",
      "billing_frequency": "Monthly"
    },
    
    // 版本发布
    "releases": [
      {
        "product_name": "Suno v4.1",
        "release_date": "2026-11-15",
        "release_notes": "Introduced a new set of ambient and lofi genre styles.",
        "release_author": "Product Team"
      }
    ],
    
    // 职业影响
    "job_impacts": [
      {
        "job_type": "Musician",
        "impact_description": "Suno allows musicians to create high-quality music easily and efficiently.",
        "tasks_affected": "Songwriting, Music Production, Audio Editing",
        "ai_skills_required": "Basic understanding of music production software."
      }
    ],
    
    // 分类和标签
    "categories": ["AI Music Generator"],
    "tags": ["Audio", "Freemium", "Music Creation", "Music Tracks", "Playlists"]
  },
  "timestamp": "2025-06-19T16:33:52+08:00"
}
```

### 3. 随机工具

#### GET `/tools/random`
获取随机AI工具列表。

**请求参数**：
- `count` (int, 可选): 返回数量，默认5，最大20

**请求示例**：
```bash
GET /wp-json/ai-tools/v1/tools/random?count=3
```

### 4. 热门工具

#### GET `/tools/popular`
获取按流行度排序的热门工具。

**请求参数**：
- `count` (int, 可选): 返回数量，默认10，最大50

**请求示例**：
```bash
GET /wp-json/ai-tools/v1/tools/popular?count=5
```

### 5. 工具导入

#### POST `/import`
导入或更新AI工具数据。

**请求参数**：
- `tool_data` (object, 必需): 工具数据对象
- `post_id` (int, 可选): 更新现有工具时的ID
- `update_mode` (bool, 可选): 是否为更新模式

### 6. 连接测试

#### GET `/test`
测试API连接状态。

**响应结构**：
```json
{
  "success": true,
  "message": "API连接正常",
  "version": "1.0",
  "server_time": "2025-06-19T16:33:52+08:00",
  "wordpress_version": "6.4.2",
  "php_version": "8.1.0"
}
```

## 🎯 智能推荐系统

### 推荐算法特点
- **真实数据**: 所有推荐来自WordPress数据库中的实际工具
- **语义相关**: 基于9个关键词组的智能分类匹配
- **动态发现**: 实时从数据库扫描可用分类和工具
- **智能排序**: 综合评分(70%) + 流行度(30%)的评分算法
- **去重逻辑**: 避免推荐工具本身

### 推荐类型
1. **Alternative Tools**: 5个同类别高评分工具
2. **Featured Matches**: 3个相关分类推荐工具
3. **Other Tools**: 4个同类别其他优质工具

## 📊 数据结构

### 完整工具对象字段 (50+ 字段)

#### 基础信息
- `id`, `title`, `slug`, `content`, `excerpt`, `url`
- `date_created`, `date_modified`

#### 产品信息
- `product_name`, `product_url`, `short_introduction`, `product_story`
- `author_company`, `primary_task`, `category`, `original_category_name`
- `initial_release_date`, `general_price_tag`

#### 媒体资源
- `logo_img_url`, `overview_img_url`, `demo_video_url`

#### 评分数据
- `average_rating`, `popularity_score`, `user_ratings_count`
- `is_verified_tool`, `number_of_tools_by_author`

#### UI文本 (15个字段)
- `message`, `copy_url_text`, `save_button_text`
- `vote_best_ai_tool_text`, `how_would_you_rate_text`
- `alternatives_count_text`, `view_more_alternatives_text`
- `if_you_liked_text`, 等等...

#### 功能特性
- `inputs`, `outputs`, `features`
- `pros_list`, `cons_list`, `related_tasks`
- `faq` (问答数组)

#### 智能推荐
- `alternative_tools` (对象数组)
- `featured_matches` (对象数组) 
- `other_tools` (对象数组)
- `alternatives` (兼容字段)

#### 复杂数据
- `pricing_details` (定价信息对象)
- `releases` (版本发布数组)
- `job_impacts` (职业影响数组)

#### 分类标签
- `categories`, `tags`

## 🚀 使用示例

### JavaScript/Fetch
```javascript
// 获取工具列表
const response = await fetch('https://your-domain.com/wp-json/ai-tools/v1/tools?per_page=5', {
  headers: {
    'X-API-Key': 'your_api_key_here'
  }
});
const data = await response.json();
console.log(data.data); // 工具列表

// 获取单个工具详情
const toolResponse = await fetch('https://your-domain.com/wp-json/ai-tools/v1/tools/100377', {
  headers: {
    'X-API-Key': 'your_api_key_here'
  }
});
const toolData = await toolResponse.json();
console.log(toolData.data.alternative_tools); // 推荐工具
```

### Python/requests
```python
import requests

headers = {'X-API-Key': 'your_api_key_here'}
base_url = 'https://your-domain.com/wp-json/ai-tools/v1'

# 获取热门工具
response = requests.get(f'{base_url}/tools/popular?count=3', headers=headers)
popular_tools = response.json()['data']

# 搜索工具
search_response = requests.get(
    f'{base_url}/tools?search=music&category=AI Music Generator', 
    headers=headers
)
search_results = search_response.json()
```

### cURL
```bash
# 获取工具详情
curl -H "X-API-Key: your_api_key_here" \
     "https://your-domain.com/wp-json/ai-tools/v1/tools/100377"

# 导入工具
curl -X POST \
     -H "X-API-Key: your_api_key_here" \
     -H "Content-Type: application/json" \
     -d '{"tool_data":{"product_name":"Test Tool","category":"AI ChatBots"}}' \
     "https://your-domain.com/wp-json/ai-tools/v1/import"
```

## ⚡ 性能与安全

### 性能优化
- WordPress对象缓存支持
- 数据库查询优化
- JSON字段高效解析
- 分页查询性能优化

### 安全特性
- API密钥认证机制
- 管理员权限验证
- 输入参数严格验证
- CORS跨域支持

### 错误处理
- `400`: 请求参数错误
- `401`: API密钥无效
- `403`: 权限不足
- `404`: 资源不存在
- `429`: 请求过于频繁
- `500`: 服务器内部错误

## 📈 版本信息

**当前版本**: v1  
**最后更新**: 2025年6月19日

---

## 📞 技术支持

如有问题或建议，请联系技术团队或查看项目文档。 