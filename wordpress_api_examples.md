# WordPress REST API 调用示例

本文档展示了AI工具导入系统中使用的WordPress REST API调用方式。

## 认证设置

```python
from requests.auth import HTTPBasicAuth

# 使用应用密码进行认证
auth = HTTPBasicAuth('username', 'application_password')
headers = {"Content-Type": "application/json"}
```

## 1. 创建自定义文章类型 (CPT)

### 创建新的AI工具文章

```python
# API端点
url = "https://your-site.com/wp-json/wp/v2/ai_tool"

# 请求数据
payload = {
    "title": "ChatGPT",
    "content": "一个强大的AI聊天机器人...",
    "status": "publish",
    "excerpt": "AI聊天助手"
}

# 发送请求
response = requests.post(url, headers=headers, auth=auth, json=payload)
post_data = response.json()
post_id = post_data['id']  # 获取创建的文章ID
```

### 更新现有文章

```python
# API端点（包含文章ID）
url = f"https://your-site.com/wp-json/wp/v2/ai_tool/{post_id}"

# 发送更新请求
response = requests.post(url, headers=headers, auth=auth, json=payload)
```

## 2. 更新ACF字段

```python
# 准备ACF数据
acf_data = {
    "product_url": "https://chat.openai.com",
    "logo_img": 123,  # 媒体库图片ID
    "primary_task": "对话助手",
    "author_company": "OpenAI",
    "is_verified_tool": True,
    # Repeater字段示例
    "inputs": [
        {"input_type": "文本"},
        {"input_type": "音频"}
    ],
    "pros_list": [
        {"pro_item": "响应速度快"},
        {"pro_item": "理解能力强"}
    ]
}

# 更新ACF字段
acf_payload = {"acf": acf_data}
response = requests.post(
    f"https://your-site.com/wp-json/wp/v2/ai_tool/{post_id}",
    headers=headers, 
    auth=auth, 
    json=acf_payload
)
```

## 3. 上传图片到媒体库

```python
# 下载远程图片
image_response = requests.get("https://example.com/logo.png", stream=True)
image_content = image_response.content

# 准备上传
upload_headers = {
    'Content-Type': 'image/png',
    'Content-Disposition': 'attachment; filename="logo.png"'
}

# 上传到WordPress
upload_response = requests.post(
    "https://your-site.com/wp-json/wp/v2/media",
    headers=upload_headers,
    auth=auth,
    data=image_content
)

media_data = upload_response.json()
media_id = media_data['id']  # 媒体库ID，用于ACF图片字段
```

## 4. 创建/获取分类法术语

### 搜索现有分类

```python
# 搜索现有分类
search_url = "https://your-site.com/wp-json/wp/v2/ai_tool_category"
search_params = {"search": "AI聊天机器人"}

response = requests.get(search_url, params=search_params, auth=auth)
categories = response.json()

category_id = None
for cat in categories:
    if cat['name'].lower() == "ai聊天机器人".lower():
        category_id = cat['id']
        break
```

### 创建新分类

```python
if not category_id:
    # 创建新分类
    create_url = "https://your-site.com/wp-json/wp/v2/ai_tool_category"
    category_payload = {"name": "AI聊天机器人"}
    
    response = requests.post(create_url, headers=headers, auth=auth, json=category_payload)
    new_category = response.json()
    category_id = new_category['id']
```

### 设置文章分类

```python
# 为文章设置分类
taxonomy_payload = {"ai_tool_category": [category_id]}
response = requests.post(
    f"https://your-site.com/wp-json/wp/v2/ai_tool/{post_id}",
    headers=headers,
    auth=auth,
    json=taxonomy_payload
)
```

## 5. 验证连接

```python
# 测试API连接和权限
test_response = requests.get(
    "https://your-site.com/wp-json/wp/v2/users/me",
    auth=auth
)

if test_response.status_code == 200:
    user_data = test_response.json()
    print(f"连接成功，用户: {user_data['name']}")
else:
    print("连接失败")
```

## 6. 错误处理

```python
try:
    response = requests.post(url, headers=headers, auth=auth, json=payload, timeout=30)
    response.raise_for_status()  # 抛出HTTP错误
    
    data = response.json()
    print("操作成功")
    
except requests.exceptions.HTTPError as e:
    print(f"HTTP错误: {e}")
    print(f"响应内容: {response.text}")
    
except requests.exceptions.RequestException as e:
    print(f"请求错误: {e}")
    
except json.JSONDecodeError:
    print("响应不是有效的JSON格式")
```

## 7. 批量操作示例

```python
def bulk_import_tools(tools_data):
    """批量导入AI工具"""
    results = []
    
    for tool in tools_data:
        try:
            # 1. 创建CPT文章
            post_payload = {
                "title": tool['name'],
                "content": tool['description'],
                "status": "publish"
            }
            
            response = requests.post(
                f"{WP_API_BASE_URL}/ai_tool",
                headers=headers,
                auth=auth,
                json=post_payload
            )
            response.raise_for_status()
            
            post_data = response.json()
            post_id = post_data['id']
            
            # 2. 上传Logo
            if tool.get('logo_url'):
                media_id = upload_image_to_wp(tool['logo_url'])
            else:
                media_id = None
            
            # 3. 更新ACF字段
            acf_data = {
                "product_url": tool.get('url'),
                "logo_img": media_id,
                "primary_task": tool.get('category'),
            }
            
            acf_response = requests.post(
                f"{WP_API_BASE_URL}/ai_tool/{post_id}",
                headers=headers,
                auth=auth,
                json={"acf": acf_data}
            )
            acf_response.raise_for_status()
            
            results.append({
                "name": tool['name'],
                "post_id": post_id,
                "status": "success"
            })
            
            # 礼貌性延迟
            time.sleep(1)
            
        except Exception as e:
            results.append({
                "name": tool['name'],
                "status": "error",
                "error": str(e)
            })
    
    return results
```

## API端点总结

| 操作 | 方法 | 端点 | 说明 |
|------|------|------|------|
| 创建文章 | POST | `/wp-json/wp/v2/ai_tool` | 创建新的AI工具文章 |
| 更新文章 | POST | `/wp-json/wp/v2/ai_tool/{id}` | 更新现有文章和ACF字段 |
| 搜索文章 | GET | `/wp-json/wp/v2/ai_tool?search=关键词` | 搜索现有文章 |
| 上传媒体 | POST | `/wp-json/wp/v2/media` | 上传图片到媒体库 |
| 获取分类 | GET | `/wp-json/wp/v2/ai_tool_category` | 获取分类列表 |
| 创建分类 | POST | `/wp-json/wp/v2/ai_tool_category` | 创建新分类 |
| 验证用户 | GET | `/wp-json/wp/v2/users/me` | 验证认证和权限 |

## 注意事项

1. **认证**: 必须使用有效的WordPress用户名和应用密码
2. **权限**: 用户必须有创建/编辑文章和上传媒体的权限
3. **速率限制**: 建议在请求之间添加延迟，避免触发服务器限制
4. **错误处理**: 务必处理网络错误和API错误响应
5. **超时设置**: 设置合理的请求超时时间
6. **ACF字段**: 确保ACF字段名称与WordPress中设置的完全匹配 