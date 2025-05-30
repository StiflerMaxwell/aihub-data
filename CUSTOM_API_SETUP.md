# WordPress自定义API安装和使用指南

本指南将帮助您安装和使用自定义WordPress API来导入AI工具数据。

## 🎯 优势

使用自定义API相比标准WordPress REST API的优势：

- **简化导入流程**: 一个API调用完成所有操作（CPT创建、ACF更新、图片上传、分类设置）
- **更好的错误处理**: 集中式错误处理和日志记录
- **批量优化**: 专门优化的批量导入功能
- **数据验证**: WordPress端进行完整的数据验证
- **性能优化**: 减少API调用次数，提高导入速度
- **重复检测**: 自动检测和更新现有工具

## 📋 前置条件

1. WordPress网站（5.0+）
2. ACF Pro插件已安装并配置
3. 自定义文章类型 `ai_tool` 已创建
4. 自定义分类法 `ai_tool_category` 已创建
5. WordPress用户具有 `edit_posts` 和 `upload_files` 权限

## 🛠️ 步骤1: 安装WordPress插件

### 方法一：通过插件文件安装

1. 将 `wordpress_custom_api.php` 文件上传到您的WordPress插件目录：
   ```
   /wp-content/plugins/ai-tool-import-api/wordpress_custom_api.php
   ```

2. 在WordPress管理后台启用插件：
   - 进入 `插件` → `已安装的插件`
   - 找到 "AI工具导入API" 插件
   - 点击 "启用"

### 方法二：作为主题函数添加

如果不想创建插件，可以将代码添加到主题的 `functions.php` 文件中：

```php
// 在 functions.php 文件末尾添加（去掉PHP开始标签）
// 将 wordpress_custom_api.php 的内容复制过来，但要去掉 <?php 开始标签
```

## 🔧 步骤2: 验证API端点

安装后，以下API端点将可用：

- **测试连接**: `GET /wp-json/ai-tools/v1/test`
- **单个导入**: `POST /wp-json/ai-tools/v1/import`  
- **批量导入**: `POST /wp-json/ai-tools/v1/batch-import`

您可以通过浏览器访问测试端点来验证安装：
```
https://your-site.com/wp-json/ai-tools/v1/test
```

## 🔑 步骤3: 配置Python环境

### 3.1 更新.env文件

确保您的 `.env` 文件包含WordPress配置：

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

### 3.2 安装Python依赖

```bash
pip install -r requirements.txt
```

## 🚀 步骤4: 使用自定义API

您现在有两个Python客户端可选择：

### 选项1: 基础客户端（无Firecrawl）

```bash
python ai_tools_custom_api_client.py
```

特点：
- 使用CSV数据直接导入
- 快速简单
- 适合基础数据导入

### 选项2: 高级客户端（集成Firecrawl）

```bash
python ai_tools_custom_api_advanced.py
```

特点：
- 自动抓取网站数据
- 结合CSV数据和抓取数据
- 更完整的工具信息
- 自动下载和上传图片

## 📊 API使用示例

### 测试连接

```bash
curl -X GET "https://your-site.com/wp-json/ai-tools/v1/test" \
  -u "username:application_password"
```

### 导入单个工具

```bash
curl -X POST "https://your-site.com/wp-json/ai-tools/v1/import" \
  -H "Content-Type: application/json" \
  -u "username:application_password" \
  -d '{
    "tool_data": {
      "product_name": "ChatGPT",
      "product_url": "https://chat.openai.com",
      "original_category_name": "AI ChatBots",
      "short_introduction": "AI聊天助手",
      "logo_img_url": "https://example.com/logo.png"
    }
  }'
```

### 批量导入工具

```bash
curl -X POST "https://your-site.com/wp-json/ai-tools/v1/batch-import" \
  -H "Content-Type: application/json" \
  -u "username:application_password" \
  -d '{
    "tools": [
      {
        "product_name": "ChatGPT",
        "product_url": "https://chat.openai.com",
        "original_category_name": "AI ChatBots"
      },
      {
        "product_name": "DALL-E",
        "product_url": "https://openai.com/dall-e-2",
        "original_category_name": "AI Image Generator"
      }
    ]
  }'
```

## 🔍 API响应格式

### 成功响应

```json
{
  "success": true,
  "message": "AI工具 'ChatGPT' created成功",
  "post_id": 123,
  "action": "created",
  "warnings": []
}
```

### 错误响应

```json
{
  "success": false,
  "message": "产品名称是必需的",
  "errors": {
    "product_name": "产品名称不能为空"
  }
}
```

### 批量导入响应

```json
{
  "success": true,
  "summary": {
    "total": 10,
    "success": 8,
    "errors": 2
  },
  "results": [
    {
      "index": 0,
      "tool_name": "ChatGPT",
      "success": true,
      "message": "AI工具 'ChatGPT' created成功",
      "post_id": 123
    }
  ]
}
```

## 🛡️ 安全考虑

1. **认证**: 始终使用WordPress应用密码，不要使用实际密码
2. **权限**: 确保API用户只有必要的权限（edit_posts, upload_files）
3. **速率限制**: API内置了延迟机制，避免服务器过载
4. **数据验证**: 所有输入数据都会进行验证和清理

## 🔧 故障排除

### 常见问题

#### 1. API端点404错误
- 检查插件是否已启用
- 确认permalink设置正确
- 尝试刷新permalink（设置 → 固定链接 → 保存更改）

#### 2. 认证失败
- 确认使用WordPress应用密码而非实际密码
- 检查用户权限是否足够

#### 3. ACF字段未更新
- 确认ACF Pro已安装
- 检查字段名称是否与代码中一致
- 确认字段组已分配给 `ai_tool` 文章类型

#### 4. 图片上传失败
- 检查WordPress上传目录权限
- 确认图片URL可访问
- 检查服务器内存和上传大小限制

### 调试方法

1. **启用WordPress调试**:
   ```php
   define('WP_DEBUG', true);
   define('WP_DEBUG_LOG', true);
   ```

2. **查看错误日志**:
   - WordPress: `/wp-content/debug.log`
   - Python: `custom_api_import.log` 或 `advanced_api_import.log`

3. **使用调试模式**:
   - 在 `.env` 文件中设置 `DEBUG_MODE=true`
   - 限制处理数量: `MAX_TOOLS_TO_PROCESS=1`

## 📈 性能优化

1. **批量大小**: 根据服务器性能调整批量大小
   - 无Firecrawl: 5-10个/批次
   - 有Firecrawl: 3-5个/批次

2. **缓存**: 如果重复导入，考虑启用对象缓存

3. **服务器资源**: 确保足够的内存和执行时间限制

4. **延迟设置**: 根据服务器负载调整请求间延迟

## 📚 进阶使用

### 扩展ACF字段支持

要添加新的ACF字段支持，编辑 `wordpress_custom_api.php` 中的 `update_acf_fields` 方法：

```php
// 添加新的基本字段
$fields['new_field'] = $tool_data['new_field'] ?? '';

// 添加新的Repeater字段
if (!empty($tool_data['new_repeater']) && is_array($tool_data['new_repeater'])) {
    $repeater_data = array();
    foreach ($tool_data['new_repeater'] as $item) {
        $repeater_data[] = array('sub_field' => $item);
    }
    $fields['new_repeater'] = $repeater_data;
}
```

### 自定义数据处理

您可以修改 `prepare_complete_tool_data` 方法来自定义数据处理逻辑：

```python
def prepare_complete_tool_data(self, scraped_data: Dict, original_data: Dict) -> Dict:
    # 自定义数据处理逻辑
    tool_data = original_data.copy()
    
    # 添加您的自定义逻辑
    if scraped_data:
        # 处理抓取的数据
        pass
    
    return tool_data
```

## 🆘 获取帮助

如果遇到问题：

1. 检查本文档的故障排除部分
2. 查看生成的日志文件
3. 确认所有前置条件都已满足
4. 测试单个工具导入是否正常工作 