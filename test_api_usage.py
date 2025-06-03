#!/usr/bin/env python3
"""
AI工具API使用示例脚本 - 增强版
支持所有新的API端点功能
"""

import requests
import json
from logger import logger

class AIToolsAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        # 设置默认头部
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get_tools(self, page=1, per_page=20, search=None, category=None, pricing=None, input_type=None, output_type=None):
        """获取AI工具列表（增强版）"""
        url = f"{self.base_url}/wp-json/ai-tools/v1/tools"
        
        params = {
            'page': page,
            'per_page': per_page
        }
        
        if search:
            params['search'] = search
        if category:
            params['category'] = category
        if pricing:
            params['pricing'] = pricing
        if input_type:
            params['input_type'] = input_type
        if output_type:
            params['output_type'] = output_type
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                return data
            else:
                logger.error(f"API错误: {data.get('message', '未知错误')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return None
    
    def get_tool_details(self, tool_id):
        """获取单个工具详情"""
        url = f"{self.base_url}/wp-json/ai-tools/v1/tools/{tool_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                return data
            else:
                logger.error(f"获取工具详情失败: {data.get('message', '未知错误')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
    
    def get_tool_by_url(self, product_url):
        """通过产品URL查找工具"""
        url = f"{self.base_url}/wp-json/ai-tools/v1/tools/by-url"
        
        params = {'url': product_url}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                return data
            else:
                logger.error(f"通过URL查找失败: {data.get('message', '未知错误')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
    
    def get_random_tools(self, count=5, category=None):
        """获取随机推荐工具"""
        url = f"{self.base_url}/wp-json/ai-tools/v1/tools/random"
        
        params = {'count': count}
        if category:
            params['category'] = category
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                return data
            else:
                logger.error(f"获取随机工具失败: {data.get('message', '未知错误')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
    
    def get_popular_tools(self, count=10):
        """获取热门工具"""
        url = f"{self.base_url}/wp-json/ai-tools/v1/tools/popular"
        
        params = {'count': count}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                return data
            else:
                logger.error(f"获取热门工具失败: {data.get('message', '未知错误')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
    
    def get_categories(self):
        """获取分类列表"""
        url = f"{self.base_url}/wp-json/ai-tools/v1/categories"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                return data
            else:
                logger.error(f"获取分类列表失败: {data.get('message', '未知错误')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
    
    def get_tags(self):
        """获取标签列表"""
        url = f"{self.base_url}/wp-json/ai-tools/v1/tags"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                return data
            else:
                logger.error(f"获取标签列表失败: {data.get('message', '未知错误')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
    
    def get_statistics(self):
        """获取统计信息"""
        url = f"{self.base_url}/wp-json/ai-tools/v1/stats"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                return data
            else:
                logger.error(f"获取统计信息失败: {data.get('message', '未知错误')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
    
    def search_tools(self, keyword, limit=10):
        """搜索AI工具"""
        logger.info(f"搜索关键词: {keyword}")
        
        result = self.get_tools(page=1, per_page=limit, search=keyword)
        if result:
            tools = result.get('data', [])
            logger.success(f"找到 {len(tools)} 个工具")
            
            for i, tool in enumerate(tools, 1):
                logger.info(f"{i}. {tool.get('title', '无标题')}")
                logger.info(f"   产品URL: {tool.get('product_url', '无链接')}")
                logger.info(f"   网站URL: {tool.get('url', '无链接')}")
                logger.info(f"   定价: {tool.get('general_price_tag', '未知')}")
                logger.info(f"   评分: {tool.get('average_rating', 0)}")
                logger.info(f"   流行度: {tool.get('popularity_score', 0)}")
                if tool.get('features'):
                    logger.info(f"   功能: {', '.join(tool['features'][:3])}")
                logger.info("   " + "-" * 50)
        
        return result

def test_enhanced_api_features():
    """测试增强版API功能"""
    
    # 这里需要替换为您的实际API Key
    API_KEY = input("请输入您的API Key: ").strip()
    
    if not API_KEY:
        logger.error("API Key不能为空！")
        return
    
    if not API_KEY.startswith('ak_'):
        logger.warning("API Key格式可能不正确，应该以'ak_'开头")
    
    BASE_URL = "https://vertu.com"
    
    logger.info("=" * 60)
    logger.info("AI工具API增强功能测试")
    logger.info("=" * 60)
    
    # 初始化API客户端
    api = AIToolsAPI(BASE_URL, API_KEY)
    
    # 测试1: 获取统计信息
    logger.info("\n📊 测试1: 获取数据库统计")
    stats = api.get_statistics()
    if stats:
        data = stats.get('data', {})
        logger.success(f"总工具数: {data.get('total_tools', 0)}")
        logger.info("分类统计:")
        for cat in data.get('categories', [])[:5]:
            logger.info(f"  - {cat['name']}: {cat['count']} 个")
        logger.info("定价统计:")
        for price in data.get('pricing', [])[:5]:
            logger.info(f"  - {price['pricing']}: {price['count']} 个")
    
    # 测试2: 获取分类列表
    logger.info("\n📋 测试2: 获取分类列表")
    categories = api.get_categories()
    if categories:
        cat_list = categories.get('data', [])
        logger.success(f"找到 {len(cat_list)} 个分类")
        for cat in cat_list[:5]:
            logger.info(f"  - {cat['name']} ({cat['count']} 个工具)")
    
    # 测试3: 获取热门工具
    logger.info("\n🔥 测试3: 获取热门工具")
    popular = api.get_popular_tools(count=5)
    if popular:
        tools = popular.get('data', [])
        logger.success(f"获取 {len(tools)} 个热门工具")
        for i, tool in enumerate(tools, 1):
            logger.info(f"{i}. {tool['title']} (流行度: {tool['popularity_score']})")
    
    # 测试4: 获取随机推荐
    logger.info("\n🎲 测试4: 获取随机推荐")
    random_tools = api.get_random_tools(count=3)
    if random_tools:
        tools = random_tools.get('data', [])
        logger.success(f"获取 {len(tools)} 个随机工具")
        for i, tool in enumerate(tools, 1):
            logger.info(f"{i}. {tool['title']} - {tool.get('general_price_tag', 'Unknown')}")
    
    # 测试5: 高级搜索功能
    logger.info("\n🔍 测试5: 高级搜索功能")
    
    # 按定价筛选
    logger.info("5.1 按定价筛选 (Free)")
    free_tools = api.get_tools(per_page=3, pricing="Free")
    if free_tools:
        tools = free_tools.get('data', [])
        logger.info(f"找到 {len(tools)} 个免费工具")
    
    # 按输入类型筛选
    logger.info("5.2 按输入类型筛选 (Text)")
    text_tools = api.get_tools(per_page=3, input_type="Text")
    if text_tools:
        tools = text_tools.get('data', [])
        logger.info(f"找到 {len(tools)} 个文本输入工具")
    
    # 测试6: 工具详情获取
    logger.info("\n📖 测试6: 获取工具详情")
    first_tool = api.get_tools(per_page=1)
    if first_tool and first_tool.get('data'):
        tool_id = first_tool['data'][0]['id']
        details = api.get_tool_details(tool_id)
        if details:
            tool_data = details.get('data', {})
            logger.success(f"获取工具详情: {tool_data.get('title', 'Unknown')}")
            logger.info(f"公司: {tool_data.get('author_company', 'Unknown')}")
            logger.info(f"优点数量: {len(tool_data.get('pros_list', []))}")
            logger.info(f"缺点数量: {len(tool_data.get('cons_list', []))}")
            logger.info(f"相关任务: {len(tool_data.get('related_tasks', []))}")
            logger.info(f"替代工具: {len(tool_data.get('alternatives', []))}")
    
    # 测试7: 通过URL查找工具
    logger.info("\n🔗 测试7: 通过URL查找工具")
    test_url = "https://chat.openai.com"
    url_result = api.get_tool_by_url(test_url)
    if url_result:
        tool_data = url_result.get('data', {})
        logger.success(f"通过URL找到工具: {tool_data.get('title', 'Unknown')}")
    else:
        logger.info(f"未找到URL对应的工具: {test_url}")
    
    # 测试8: 获取标签列表
    logger.info("\n🏷️ 测试8: 获取标签列表")
    tags = api.get_tags()
    if tags:
        tag_list = tags.get('data', [])
        logger.success(f"找到 {len(tag_list)} 个标签")
        popular_tags = tag_list[:10]  # 显示前10个最受欢迎的标签
        for tag in popular_tags:
            logger.info(f"  - {tag['name']} ({tag['count']} 次使用)")

def demo_different_auth_methods():
    """演示不同的认证方式"""
    
    API_KEY = input("请输入您的API Key用于认证演示: ").strip()
    BASE_URL = "https://vertu.com"
    
    if not API_KEY:
        logger.error("需要API Key进行演示")
        return
    
    logger.info("\n🔐 演示不同的API认证方式")
    logger.info("-" * 40)
    
    # 方式1: X-API-Key头部
    logger.info("方式1: X-API-Key 头部认证")
    try:
        response = requests.get(
            f"{BASE_URL}/wp-json/ai-tools/v1/tools",
            headers={'X-API-Key': API_KEY},
            params={'per_page': 1},
            timeout=10
        )
        logger.info(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                logger.success("✅ X-API-Key 认证成功")
                logger.info(f"返回 {len(data.get('data', []))} 条数据")
            else:
                logger.error(f"❌ API返回错误: {data.get('message')}")
        else:
            logger.error(f"❌ 认证失败: {response.text}")
    except Exception as e:
        logger.error(f"请求失败: {e}")
    
    # 方式2: Authorization Bearer头部
    logger.info("\n方式2: Authorization Bearer 头部认证")
    try:
        response = requests.get(
            f"{BASE_URL}/wp-json/ai-tools/v1/tools",
            headers={'Authorization': f'Bearer {API_KEY}'},
            params={'per_page': 1},
            timeout=10
        )
        logger.info(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                logger.success("✅ Bearer Token 认证成功")
            else:
                logger.error(f"❌ API返回错误: {data.get('message')}")
        else:
            logger.error(f"❌ 认证失败: {response.text}")
    except Exception as e:
        logger.error(f"请求失败: {e}")
    
    # 方式3: URL参数
    logger.info("\n方式3: URL参数认证")
    try:
        response = requests.get(
            f"{BASE_URL}/wp-json/ai-tools/v1/tools",
            params={'api_key': API_KEY, 'per_page': 1},
            timeout=10
        )
        logger.info(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                logger.success("✅ URL参数 认证成功")
            else:
                logger.error(f"❌ API返回错误: {data.get('message')}")
        else:
            logger.error(f"❌ 认证失败: {response.text}")
    except Exception as e:
        logger.error(f"请求失败: {e}")

if __name__ == "__main__":
    try:
        # 主要API功能测试
        test_enhanced_api_features()
        
        print("\n" + "="*60)
        
        # 认证方式演示
        demo_different_auth_methods()
        
        print("\n🎉 所有测试完成！")
        print("\n📈 API功能总结:")
        print("✅ 工具列表查询 (支持搜索、筛选、排序)")
        print("✅ 工具详情获取")
        print("✅ 随机推荐工具")
        print("✅ 热门工具排行")
        print("✅ 分类和标签管理") 
        print("✅ 数据统计分析")
        print("✅ URL反向查找")
        print("✅ 多种认证方式")
        
        print("\n💡 新增功能亮点:")
        print("1. 🎯 丰富的字段信息 - 产品URL、公司、评分等")
        print("2. 🔍 高级筛选功能 - 按定价、输入输出类型等")
        print("3. 📊 详细统计数据 - 分类、定价分布等")
        print("4. 🎲 随机推荐算法 - 发现新工具")
        print("5. 🔥 人气排序功能 - 找到最受欢迎的工具")
        print("6. 🏷️ 标签系统完善 - 更好的分类管理")
        
        print("\n⚠️ 使用建议:")
        print("1. 推荐使用 X-API-Key 头部认证方式")
        print("2. 注意API速率限制（默认每小时1000次请求）")
        print("3. 妥善保管您的API Key，不要在代码中硬编码")
        print("4. 生产环境建议使用环境变量存储API Key")
        print("5. 合理使用分页，避免一次请求过多数据")
        
    except KeyboardInterrupt:
        print("\n\n👋 测试被用户中断")
    except Exception as e:
        logger.error(f"测试过程中发生未知错误: {e}") 