# AI工具API文档

## 🔗 **基础信息**

**基础URL**: `https://vertu.com/wp-json/ai-tools/v1`

**认证方式**: API Key（三种认证方法）

**数据格式**: JSON

**字符编码**: UTF-8

---

## 🔐 **认证**

### **获取API Key**
1. 登录WordPress后台
2. 进入 `工具 → AI工具API`
3. 填写表单生成新的API Key
4. 复制并保存API Key

### **认证方法**

您可以使用以下三种方式中的任意一种进行认证：

#### **方法1: X-API-Key 头部（推荐）**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
     "https://vertu.com/wp-json/ai-tools/v1/tools"
```

#### **方法2: Authorization Bearer 头部**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://vertu.com/wp-json/ai-tools/v1/tools"
```

#### **方法3: URL参数**
```bash
curl "https://vertu.com/wp-json/ai-tools/v1/tools?api_key=YOUR_API_KEY"
```

---

## 📋 **API端点**

### **1. 获取AI工具列表**

```
GET /tools
```

获取AI工具的分页列表，支持搜索和筛选。

#### **参数**
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `page` | integer | 1 | 页码 |
| `per_page` | integer | 20 | 每页条数（1-100） |
| `search` | string | - | 搜索关键词 |
| `category` | string | - | 按分类筛选 |
| `pricing` | string | - | 按定价筛选（Free, Freemium, Paid等） |
| `input_type` | string | - | 按输入类型筛选 |
| `output_type` | string | - | 按输出类型筛选 |

#### **响应示例**
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "title": "ChatGPT",
      "slug": "chatgpt",
      "url": "https://vertu.com/aihub/chatgpt",
      "excerpt": "强大的AI对话工具...",
      "date_created": "2024-01-15T10:30:00",
      "date_modified": "2024-01-20T15:45:00",
      "product_name": "ChatGPT",
      "product_url": "https://chat.openai.com",
      "short_introduction": "基于GPT技术的智能对话助手",
      "general_price_tag": "Freemium",
      "category": "AI聊天工具",
      "logo_img_url": "https://example.com/logo.png",
      "overview_img_url": "https://example.com/overview.png",
      "average_rating": 4.8,
      "popularity_score": 95.6,
      "is_verified_tool": true,
      "inputs": ["Text", "Voice"],
      "outputs": ["Text", "Code"],
      "categories": ["AI聊天工具", "文本生成"],
      "tags": ["对话", "GPT", "OpenAI", "免费增值"],
      "pricing_details": {
        "pricing_model": "Freemium",
        "currency": "USD",
        "paid_options_from": 20.00
      },
      "features": [
        "多语言支持",
        "代码生成",
        "文档写作"
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 122,
    "total_pages": 7
  },
  "timestamp": "2024-01-20T16:00:00+00:00"
}
```

### **2. 获取单个AI工具详情**

```
GET /tools/{id}
```

获取指定AI工具的完整详细信息。

#### **参数**
| 参数 | 类型 | 描述 |
|------|------|------|
| `id` | integer | 工具ID |

#### **响应示例**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "title": "ChatGPT",
    "content": "完整的工具描述内容...",
    "product_story": "产品发展历程...",
    "author_company": "OpenAI",
    "initial_release_date": "2022-11-30",
    "user_ratings_count": 1500,
    "average_rating": 4.8,
    "pros_list": [
      {"pro_item": "响应速度快"},
      {"pro_item": "支持多语言"}
    ],
    "cons_list": [
      {"con_item": "免费版有限制"}
    ],
    "related_tasks": [
      {"task_item": "文档写作"},
      {"task_item": "代码生成"}
    ],
    "alternatives": [
      {
        "alternative_tool_name": "Claude",
        "alternative_tool_url": "https://claude.ai",
        "relationship_type": "Alternative"
      }
    ],
    "releases": [
      {
        "release_product_name": "ChatGPT 4.0",
        "release_date": "2023-03-14",
        "release_notes": "新增多模态支持",
        "release_author": "OpenAI"
      }
    ]
  },
  "timestamp": "2024-01-20T16:00:00+00:00"
}
```

### **3. 按URL查找工具**

```
GET /tools/by-url?url={tool_url}
```

通过产品URL查找对应的AI工具。

#### **参数**
| 参数 | 类型 | 描述 |
|------|------|------|
| `url` | string | 工具的产品URL |

### **4. 获取分类列表**

```
GET /categories
```

获取所有可用的AI工具分类。

#### **响应示例**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "AI聊天工具",
      "slug": "ai-chat-tools",
      "count": 25,
      "description": "智能对话和聊天机器人"
    }
  ],
  "count": 10,
  "timestamp": "2024-01-20T16:00:00+00:00"
}
```

### **5. 获取标签列表**

```
GET /tags
```

获取所有可用的AI工具标签。

### **6. 获取统计信息**

```
GET /stats
```

获取整体数据统计信息。

#### **响应示例**
```json
{
  "success": true,
  "data": {
    "total_tools": 122,
    "categories": [
      {"name": "AI聊天工具", "count": 25},
      {"name": "图像生成", "count": 18}
    ],
    "pricing": [
      {"pricing": "Free", "count": 45},
      {"pricing": "Freemium", "count": 52},
      {"pricing": "Paid", "count": 25}
    ],
    "last_updated": "2024-01-20T15:30:00"
  }
}
```

### **7. 随机推荐工具**

```
GET /tools/random
```

获取随机推荐的AI工具。

#### **参数**
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `count` | integer | 5 | 返回工具数量（1-20） |
| `category` | string | - | 限制分类 |

### **8. 热门工具**

```
GET /tools/popular
```

获取按受欢迎程度排序的工具。

#### **参数**
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `count` | integer | 10 | 返回工具数量（1-50） |

---

## ⚠️ **错误处理**

### **错误响应格式**
```json
{
  "success": false,
  "message": "错误描述",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-20T16:00:00+00:00"
}
```

### **常见错误码**
| HTTP状态码 | 错误码 | 描述 |
|------------|--------|------|
| 401 | `missing_api_key` | 缺少API Key |
| 401 | `invalid_api_key` | API Key无效或已过期 |
| 429 | `rate_limit_exceeded` | 超过速率限制 |
| 404 | `not_found` | 资源不存在 |
| 400 | `invalid_parameters` | 参数无效 |

---

## 🚀 **使用示例**

### **Python示例**
```python
import requests

# 设置API Key
API_KEY = "ak_your_api_key_here"
BASE_URL = "https://vertu.com/wp-json/ai-tools/v1"

# 设置请求头
headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

# 获取AI工具列表
response = requests.get(f"{BASE_URL}/tools", headers=headers)
data = response.json()

if data['success']:
    tools = data['data']
    print(f"找到 {len(tools)} 个AI工具")
    for tool in tools:
        print(f"- {tool['title']}: {tool['product_url']}")
```

### **JavaScript示例**
```javascript
const API_KEY = 'ak_your_api_key_here';
const BASE_URL = 'https://vertu.com/wp-json/ai-tools/v1';

// 使用fetch获取工具列表
fetch(`${BASE_URL}/tools?per_page=10`, {
    headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log(`找到 ${data.data.length} 个AI工具`);
        data.data.forEach(tool => {
            console.log(`${tool.title}: ${tool.product_url}`);
        });
    }
})
.catch(error => console.error('Error:', error));
```

### **cURL示例**
```bash
# 获取前10个工具
curl -H "X-API-Key: ak_your_api_key_here" \
     "https://vertu.com/wp-json/ai-tools/v1/tools?per_page=10"

# 搜索包含"ChatGPT"的工具
curl -H "X-API-Key: ak_your_api_key_here" \
     "https://vertu.com/wp-json/ai-tools/v1/tools?search=ChatGPT"

# 获取免费工具
curl -H "X-API-Key: ak_your_api_key_here" \
     "https://vertu.com/wp-json/ai-tools/v1/tools?pricing=Free"
```

---

## �� **最佳实践**

### **1. 速率限制**
- 默认每小时1000次请求
- 超过限制将返回429错误
- 建议添加重试机制和指数退避

### **2. 错误处理**
- 始终检查`success`字段
- 实现适当的错误处理和用户反馈
- 记录API调用日志便于调试

### **3. 数据缓存**
- 对不经常变化的数据（如分类列表）进行缓存
- 设置合理的缓存过期时间

### **4. 安全性**
- 不要在前端代码中暴露API Key
- 使用环境变量存储API Key
- 定期轮换API Key

### **5. 分页处理**
- 使用分页避免一次获取过多数据
- 实现分页导航和加载更多功能

---

## 📞 **支持与反馈**

如有任何问题或建议，请联系：
- **邮箱**: support@vertu.com
- **文档版本**: v2.0
- **最后更新**: 2025-06-03 