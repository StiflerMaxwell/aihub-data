"""
AI工具导入系统 - WordPress数据导入器
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import time
from config import config
from logger import logger

class WordPressImporter:
    """WordPress数据导入器"""
    
    def __init__(self):
        self.wp_username = config.WP_USERNAME
        self.wp_password = config.WP_APP_PASSWORD
        self.wp_api_url = config.WP_API_BASE_URL
        self.custom_api_url = config.WP_CUSTOM_API_BASE_URL
        self.custom_api_key = getattr(config, 'WP_CUSTOM_API_KEY', '')
        self.timeout = config.REQUEST_TIMEOUT
        self.delay = config.IMPORT_DELAY
        self.use_custom_api = False  # 直接使用WordPress原生API，更可靠
        
        if not all([self.wp_username, self.wp_password, self.wp_api_url]):
            raise ValueError("WordPress配置不完整")
    
    def test_connection(self):
        """测试WordPress连接"""
        try:
            # 测试基础API
            response = requests.get(f"{self.wp_api_url}/", timeout=self.timeout)
            if response.status_code != 200:
                logger.error("WordPress基础API连接失败")
                return False
            
            # 测试认证API
            auth = HTTPBasicAuth(self.wp_username, self.wp_password)
            response = requests.get(f"{self.wp_api_url}/users/me", auth=auth, timeout=self.timeout)
            if response.status_code != 200:
                logger.error("WordPress认证失败")
                return False
            
            user_data = response.json()
            logger.success(f"WordPress连接成功，用户: {user_data.get('name', 'Unknown')}")
            
            # 测试自定义API（更强的测试逻辑）
            logger.debug(f"测试自定义API: {self.custom_api_url}/test")
            try:
                # 准备自定义API的请求头
                custom_headers = {}
                if self.custom_api_key:
                    custom_headers['X-API-Key'] = self.custom_api_key
                    logger.debug(f"使用API Key: {self.custom_api_key[:12]}...")
                else:
                    logger.warning("未配置自定义API Key，将尝试无认证访问")
                
                response = requests.get(f"{self.custom_api_url}/test", headers=custom_headers, timeout=self.timeout)
                logger.debug(f"自定义API响应状态: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        logger.success("自定义API连接成功")
                        self.use_custom_api = True
                    else:
                        logger.warning(f"自定义API返回失败: {result}")
                        self.use_custom_api = False
                else:
                    logger.warning(f"自定义API HTTP错误 {response.status_code}:")
                    logger.warning(response.text[:200])
                    self.use_custom_api = False
            except requests.exceptions.Timeout:
                logger.warning("自定义API请求超时，将使用标准WordPress API")
                self.use_custom_api = False
            except requests.exceptions.ConnectionError:
                logger.warning("自定义API连接错误，将使用标准WordPress API")
                self.use_custom_api = False
            except Exception as e:
                logger.warning(f"自定义API测试失败，将使用标准WordPress API: {e}")
                self.use_custom_api = False
            
            logger.info(f"API模式: {'自定义API' if self.use_custom_api else '标准WordPress API'}")
            return True
            
        except Exception as e:
            logger.error(f"WordPress连接测试失败: {e}")
            return False
    
    def import_single_tool(self, tool_data):
        """导入单个工具"""
        try:
            tool_name = tool_data.get('product_name', 'Unknown')
            logger.debug(f"正在导入: {tool_name}")
            
            # 首先检查是否已存在同名产品
            existing_post = self._check_existing_product(tool_name)
            
            if existing_post:
                logger.info(f"🔄 检测到重复产品: {tool_name} (ID: {existing_post['id']})，将更新内容")
                return self._update_existing_product(existing_post, tool_data)
            else:
                logger.debug(f"✅ 产品不重复，开始创建: {tool_name}")
                
            if self.use_custom_api:
                # 使用自定义API
                return self._import_via_custom_api(tool_data)
            else:
                # 使用标准WordPress API
                return self._import_via_standard_api(tool_data)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"导入异常: {tool_name} - {error_msg}")
            return {
                'success': False,
                'tool_name': tool_name,
                'error': error_msg
            }
    
    def _check_existing_product(self, product_name):
        """检查是否已存在同名产品"""
        try:
            auth = HTTPBasicAuth(self.wp_username, self.wp_password)
            
            # 首先尝试在aihub CPT中搜索
            search_urls = [
                f"{self.wp_api_url}/aihub?search={requests.utils.quote(product_name)}&per_page=5",
                f"{self.wp_api_url}/posts?search={requests.utils.quote(product_name)}&per_page=5"
            ]
            
            for search_url in search_urls:
                try:
                    logger.debug(f"搜索URL: {search_url}")
                    response = requests.get(search_url, auth=auth, timeout=30)
                    if response.status_code == 200:
                        posts = response.json()
                        logger.debug(f"搜索到 {len(posts)} 个结果")
                        for post in posts:
                            # 精确匹配标题
                            post_title = post.get('title', {}).get('rendered', '').strip() if isinstance(post.get('title'), dict) else str(post.get('title', '')).strip()
                            if post_title == product_name.strip():
                                # 确保返回的post包含type信息
                                if 'type' not in post:
                                    # 如果搜索结果中没有type字段，根据搜索URL推断
                                    if '/aihub?' in search_url:
                                        post['type'] = 'aihub'
                                    else:
                                        post['type'] = 'post'
                                
                                logger.debug(f"找到重复产品: {product_name} (ID: {post['id']}, 类型: {post.get('type', 'unknown')})")
                                return post
                except Exception as e:
                    logger.debug(f"搜索失败 {search_url}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"检查重复产品失败: {e}")
            return None
    
    def _update_existing_product(self, existing_post, tool_data):
        """更新已存在的产品"""
        try:
            auth = HTTPBasicAuth(self.wp_username, self.wp_password)
            headers = {"Content-Type": "application/json"}
            
            tool_name = tool_data.get('product_name', 'Unknown')
            post_id = existing_post['id']
            post_type = existing_post.get('type', 'post')
            
            # 准备更新数据
            update_data = {
                'title': tool_name,
                'content': tool_data.get('description', f"{tool_name} is an {tool_data.get('category', 'AI')} tool."),
                'excerpt': tool_data.get('short_introduction', ''),
                'status': 'publish'
            }
            
            # 根据实际的文章类型选择正确的API端点
            if post_type == 'aihub':
                endpoint = f"{self.wp_api_url}/aihub/{post_id}"
                logger.debug(f"使用aihub端点更新: {endpoint}")
            else:
                endpoint = f"{self.wp_api_url}/posts/{post_id}"
                logger.debug(f"使用posts端点更新: {endpoint}")
            
            # 添加ACF字段到更新数据
            acf_fields = self._prepare_acf_fields(tool_data)
            if acf_fields:
                update_data['acf'] = acf_fields
            
            # 添加分类和标签
            update_data['categories'] = self._get_or_create_categories(tool_data)
            update_data['tags'] = self._get_or_create_tag_ids(tool_data)
            
            logger.debug(f"更新数据: {json.dumps(update_data, ensure_ascii=False)[:200]}...")
            
            response = requests.post(
                endpoint,
                headers=headers,
                auth=auth,
                json=update_data,
                timeout=60
            )
            
            logger.debug(f"更新响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.success(f"🔄 更新成功: {tool_name} (ID: {post_id}, 类型: {post_type})")
                
                # 强制保存ACF字段
                self._save_acf_fields_via_api(post_id, tool_data)
                
                # 再次确保ACF字段已保存（有时需要单独更新）
                self._update_acf_fields_separately(post_id, tool_data)
                
                return {
                    'success': True,
                    'post_id': post_id,
                    'tool_name': tool_name,
                    'message': f'更新现有产品成功 (类型: {post_type})',
                    'updated': True
                }
            else:
                error_msg = f"更新失败 {response.status_code}: {response.text[:200]}"
                logger.error(f"更新失败: {tool_name} - {error_msg}")
                
                # 如果aihub端点失败，尝试使用posts端点作为备用
                if post_type == 'aihub' and response.status_code == 404:
                    logger.warning(f"aihub端点失败，尝试使用posts端点作为备用...")
                    fallback_endpoint = f"{self.wp_api_url}/posts/{post_id}"
                    
                    fallback_response = requests.post(
                        fallback_endpoint,
                        headers=headers,
                        auth=auth,
                        json=update_data,
                        timeout=60
                    )
                    
                    if fallback_response.status_code == 200:
                        result = fallback_response.json()
                        logger.success(f"🔄 备用更新成功: {tool_name} (ID: {post_id})")
                        self._save_acf_fields_via_api(post_id, tool_data)
                        self._update_acf_fields_separately(post_id, tool_data)
                        return {
                            'success': True,
                            'post_id': post_id,
                            'tool_name': tool_name,
                            'message': '通过备用端点更新成功',
                            'updated': True
                        }
                    else:
                        logger.error(f"备用更新也失败: {fallback_response.status_code} - {fallback_response.text[:200]}")
                
                return {
                    'success': False,
                    'tool_name': tool_name,
                    'error': error_msg,
                    'updated': False
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"更新异常: {tool_name} - {error_msg}")
            return {
                'success': False,
                'tool_name': tool_name,
                'error': error_msg,
                'updated': False
            }
    
    def _import_via_custom_api(self, tool_data):
        """通过自定义API导入"""
        headers = {"Content-Type": "application/json"}
        
        # 添加API Key到请求头
        if self.custom_api_key:
            headers['X-API-Key'] = self.custom_api_key
        
        payload = {"tool_data": tool_data}
        
        tool_name = tool_data.get('product_name', 'Unknown')
        
        response = requests.post(
            f"{self.custom_api_url}/import",
            headers=headers,
            json=payload,
            timeout=60  # 导入可能需要更长时间
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.success(f"导入成功: {tool_name}")
                
                # 记录分类和标签创建信息
                self._log_taxonomy_info(tool_data, tool_name)
                
                return {
                    'success': True,
                    'post_id': result.get('post_id'),
                    'tool_name': tool_name,
                    'message': result.get('message', '导入成功')
                }
            else:
                error_msg = result.get('message', 'Unknown error')
                logger.error(f"导入失败: {tool_name} - {error_msg}")
                return {
                    'success': False,
                    'tool_name': tool_name,
                    'error': error_msg
                }
        else:
            error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            logger.error(f"导入失败: {tool_name} - {error_msg}")
            return {
                'success': False,
                'tool_name': tool_name,
                'error': error_msg
            }
    
    def _import_via_standard_api(self, tool_data):
        """通过标准WordPress API导入（降级模式）"""
        auth = HTTPBasicAuth(self.wp_username, self.wp_password)
        headers = {"Content-Type": "application/json"}
        
        tool_name = tool_data.get('product_name', 'Unknown')
        
        # 创建基础文章数据
        post_data = {
            'title': tool_name,
            'content': tool_data.get('product_story', tool_data.get('short_introduction', f"{tool_name} is an {tool_data.get('category', 'AI')} tool.")),
            'status': 'publish',
            'type': 'post',  # 如果aihub CPT不存在，使用标准post类型
            'excerpt': tool_data.get('short_introduction', ''),
        }
        
        # 添加ACF字段
        acf_fields = self._prepare_acf_fields(tool_data)
        if acf_fields:
            post_data['acf'] = acf_fields
        
        # 添加分类和标签
        post_data['categories'] = self._get_or_create_categories(tool_data)
        post_data['tags'] = self._get_or_create_tag_ids(tool_data)
        
        # 尝试使用aihub CPT，如果失败则使用post
        try:
            post_data['type'] = 'aihub'
            response = requests.post(
                f"{self.wp_api_url}/aihub",
                headers=headers,
                auth=auth,
                json=post_data,
                timeout=60
            )
            
            if response.status_code not in [200, 201]:
                # aihub CPT不存在，使用标准post
                post_data['type'] = 'post'
                response = requests.post(
                    f"{self.wp_api_url}/posts",
                    headers=headers,
                    auth=auth,
                    json=post_data,
                    timeout=60
                )
        except Exception:
            # 如果aihub失败，使用标准post
            post_data['type'] = 'post'
            response = requests.post(
                f"{self.wp_api_url}/posts",
                headers=headers,
                auth=auth,
                json=post_data,
                timeout=60
            )
        
        if response.status_code in [200, 201]:
            result = response.json()
            post_id = result.get('id')
            
            logger.success(f"导入成功: {tool_name} (ID: {post_id})")
            
            # 确保ACF字段已保存（有时需要单独更新）
            self._update_acf_fields_separately(post_id, tool_data)
            
            # 记录分类和标签创建信息
            self._log_taxonomy_info(tool_data, tool_name)
            
            return {
                'success': True,
                'post_id': post_id,
                'tool_name': tool_name,
                'message': f'通过原生WordPress API导入成功 (类型: {post_data["type"]})'
            }
        else:
            error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            logger.error(f"导入失败: {tool_name} - {error_msg}")
            return {
                'success': False,
                'tool_name': tool_name,
                'error': error_msg
            }
    
    def _prepare_acf_fields(self, tool_data):
        """为ACF字段准备数据 - MVP简化版本：6个大型JSON字段"""
        # 分组1：基础信息 (产品详情、公司、分类等)
        basic_info = {
            'product_name': tool_data.get('product_name', ''),
            'product_url': tool_data.get('product_url', ''),
            'short_introduction': tool_data.get('short_introduction', ''),
            'product_story': tool_data.get('product_story', ''),
            'author_company': tool_data.get('author_company', ''),
            'primary_task': tool_data.get('primary_task', ''),
            'category': tool_data.get('category', ''),
            'original_category_name': tool_data.get('original_category_name', ''),
            'initial_release_date': tool_data.get('initial_release_date', ''),
            'general_price_tag': tool_data.get('general_price_tag', ''),
        }
        
        # 分组2：媒体资源 (logo、图片、视频)
        media_data = {
            'logo_img_url': tool_data.get('logo_img_url', ''),
            'overview_img_url': tool_data.get('overview_img_url', ''),
            'demo_video_url': tool_data.get('demo_video_url', ''),
        }
        
        # 分组3：评分和数值数据 (评分、流行度、用户数等)
        ratings_data = {
            'average_rating': tool_data.get('average_rating', 0),
            'popularity_score': tool_data.get('popularity_score', 0),
            'user_ratings_count': tool_data.get('user_ratings_count', 0),
            'is_verified_tool': tool_data.get('is_verified_tool', False),
            'number_of_tools_by_author': tool_data.get('number_of_tools_by_author', 0),
        }
        
        # 分组4：UI文本数据 (所有界面显示的文本标签)
        ui_text_data = {
            'message': tool_data.get('message', ''),
            'copy_url_text': tool_data.get('copy_url_text', ''),
            'save_button_text': tool_data.get('save_button_text', ''),
            'vote_best_ai_tool_text': tool_data.get('vote_best_ai_tool_text', ''),
            'how_would_you_rate_text': tool_data.get('how_would_you_rate_text', ''),
            'help_other_people_text': tool_data.get('help_other_people_text', ''),
            'your_rating_text': tool_data.get('your_rating_text', ''),
            'post_review_button_text': tool_data.get('post_review_button_text', ''),
            'feature_requests_intro': tool_data.get('feature_requests_intro', ''),
            'request_feature_button_text': tool_data.get('request_feature_button_text', ''),
            'view_more_pros_text': tool_data.get('view_more_pros_text', ''),
            'view_more_cons_text': tool_data.get('view_more_cons_text', ''),
            'alternatives_count_text': tool_data.get('alternatives_count_text', ''),
            'view_more_alternatives_text': tool_data.get('view_more_alternatives_text', ''),
            'if_you_liked_text': tool_data.get('if_you_liked_text', ''),
        }
        
        # 分组5：功能特性数据 (输入输出、功能列表、优缺点等)
        features_data = {
            'inputs': tool_data.get('inputs', []),
            'outputs': tool_data.get('outputs', []),
            'features': tool_data.get('features', []),
            'pros_list': tool_data.get('pros_list', []),
            'cons_list': tool_data.get('cons_list', []),
            'related_tasks': tool_data.get('related_tasks', []),
            'alternative_tools': tool_data.get('alternative_tools', []),
            'featured_matches': tool_data.get('featured_matches', []),
            'other_tools': tool_data.get('other_tools', []),
        }
        
        # 分组6：复杂对象数据 (定价详情、发布信息、工作影响等)
        complex_data = {
            'pricing_details': tool_data.get('pricing_details', {}),
            'releases': tool_data.get('releases', []),
            'job_impacts': tool_data.get('job_impacts', []),
            'alternatives': tool_data.get('alternatives', []),
        }
        
        # 将所有分组数据序列化为JSON字符串
        acf_fields = {
            'basic_info': json.dumps(basic_info, ensure_ascii=False, indent=2),
            'media_data': json.dumps(media_data, ensure_ascii=False, indent=2),
            'ratings_data': json.dumps(ratings_data, ensure_ascii=False, indent=2),
            'ui_text_data': json.dumps(ui_text_data, ensure_ascii=False, indent=2),
            'features_data': json.dumps(features_data, ensure_ascii=False, indent=2),
            'complex_data': json.dumps(complex_data, ensure_ascii=False, indent=2),
        }
        
        return acf_fields
    
    def _get_or_create_categories(self, tool_data):
        """获取或创建分类"""
        categories = []
        if 'category' in tool_data and tool_data['category']:
            try:
                auth = HTTPBasicAuth(self.wp_username, self.wp_password)
                
                # 搜索现有分类
                search_url = f"{self.wp_api_url}/categories?search={requests.utils.quote(tool_data['category'])}"
                response = requests.get(search_url, auth=auth, timeout=30)
                
                if response.status_code == 200:
                    existing_cats = response.json()
                    for cat in existing_cats:
                        if cat['name'].lower() == tool_data['category'].lower():
                            categories.append(cat['id'])
                            return categories
                
                # 如果不存在，创建新分类
                create_url = f"{self.wp_api_url}/categories"
                create_data = {'name': tool_data['category']}
                response = requests.post(create_url, auth=auth, json=create_data, timeout=30)
                
                if response.status_code == 201:
                    new_cat = response.json()
                    categories.append(new_cat['id'])
                    
            except Exception as e:
                logger.debug(f"处理分类失败: {e}")
                
        return categories
    
    def _get_or_create_tags(self, tool_data):
        """获取或创建标签 - 返回tag names列表（用于自定义API）"""
        tags = []
        
        # 1. 如果数据中有明确的tags字段，优先使用
        if 'tags' in tool_data and isinstance(tool_data['tags'], list):
            for tag_name in tool_data['tags']:
                if isinstance(tag_name, str) and tag_name.strip():
                    tags.append(tag_name.strip())
        
        # 2. 如果没有明确的tags，自动生成
        if not tags:
            auto_tags = set()
            
            # 从主要任务生成标签
            if tool_data.get('primary_task'):
                auto_tags.add(tool_data['primary_task'])
            
            # 从输入类型生成标签
            if tool_data.get('inputs') and isinstance(tool_data['inputs'], list):
                for input_type in tool_data['inputs'][:3]:  # 限制数量
                    if isinstance(input_type, str) and input_type.strip():
                        auto_tags.add(input_type.strip())
            
            # 从输出类型生成标签
            if tool_data.get('outputs') and isinstance(tool_data['outputs'], list):
                for output_type in tool_data['outputs'][:3]:  # 限制数量
                    if isinstance(output_type, str) and output_type.strip():
                        auto_tags.add(output_type.strip())
            
            # 从定价类型生成标签
            if tool_data.get('general_price_tag'):
                auto_tags.add(tool_data['general_price_tag'])
            
            # 从公司名生成标签（如果有知名公司）
            company = tool_data.get('author_company', '')
            if company and len(company.split()) <= 2:  # 简短的公司名
                auto_tags.add(company)
            
            # 转换为列表并限制数量
            tags = list(auto_tags)[:8]  # 最多8个标签
            
            # 过滤掉空白和太长的标签
            tags = [tag for tag in tags if tag and len(tag) <= 30]
        
        return tags

    def _get_or_create_tag_ids(self, tool_data):
        """获取或创建标签IDs - 用于WordPress REST API"""
        tags = self._get_or_create_tags(tool_data)
        tag_ids = []
        
        if not tags:
            return tag_ids
        
        try:
            auth = HTTPBasicAuth(self.wp_username, self.wp_password)
            
            for tag_name in tags:
                # 搜索现有标签
                search_response = requests.get(
                    f"{self.wp_api_url}/tags",
                    auth=auth,
                    params={'search': tag_name, 'per_page': 10},
                    timeout=10
                )
                
                if search_response.status_code == 200:
                    existing_tags = search_response.json()
                    
                    # 查找完全匹配的标签
                    tag_id = None
                    for tag in existing_tags:
                        if tag.get('name', '').lower() == tag_name.lower():
                            tag_id = tag.get('id')
                            break
                    
                    # 如果没找到，创建新标签
                    if not tag_id:
                        create_response = requests.post(
                            f"{self.wp_api_url}/tags",
                            auth=auth,
                            json={'name': tag_name},
                            timeout=10
                        )
                        
                        if create_response.status_code in [200, 201]:
                            new_tag = create_response.json()
                            tag_id = new_tag.get('id')
                            logger.debug(f"创建新标签: {tag_name} (ID: {tag_id})")
                        else:
                            logger.warning(f"创建标签失败: {tag_name}")
                            continue
                    else:
                        logger.debug(f"使用现有标签: {tag_name} (ID: {tag_id})")
                    
                    if tag_id:
                        tag_ids.append(tag_id)
                
                # 避免请求过快
                time.sleep(0.1)
                
        except Exception as e:
            logger.warning(f"处理标签时发生错误: {e}")
        
        return tag_ids
    
    def _update_acf_fields_separately(self, post_id, tool_data):
        """单独更新ACF字段（备用方法）- MVP简化版本：6个JSON字段"""
        try:
            auth = HTTPBasicAuth(self.wp_username, self.wp_password)
            
            # 使用简化的6个JSON字段方法
            acf_fields = self._prepare_acf_fields(tool_data)
            
            # 逐个更新6个JSON字段
            success_count = 0
            for field_name, field_value in acf_fields.items():
                try:
                    # 使用meta字段更新
                    meta_url = f"{self.wp_api_url}/aihub/{post_id}"
                    meta_data = {'meta': {field_name: field_value}}
                    response = requests.post(meta_url, auth=auth, json=meta_data, timeout=30)
                    
                    if response.status_code in [200, 201]:
                        success_count += 1
                        logger.debug(f"✓ {field_name} 字段更新成功")
                    else:
                        logger.warning(f"✗ {field_name} 字段更新失败: {response.status_code}")
                    
                    time.sleep(0.2)  # 避免请求过快
                    
                except Exception as e:
                    logger.debug(f"字段 {field_name} 更新异常: {e}")
                        
            logger.info(f"ACF字段单独更新完成: {success_count}/6 成功")
            return success_count > 0
                        
        except Exception as e:
            logger.debug(f"单独更新ACF字段失败: {e}")
            return False

    def _log_taxonomy_info(self, tool_data, tool_name):
        """记录分类和标签信息"""
        try:
            # 记录将要创建/使用的分类法信息
            taxonomies_info = []
            
            # 主要分类
            primary_category = tool_data.get('category') or tool_data.get('original_category_name') or tool_data.get('primary_task')
            if primary_category:
                taxonomies_info.append(f"分类: {primary_category}")
            
            # AI标签
            ai_tags = []
            if tool_data.get('primary_task'):
                ai_tags.append(tool_data['primary_task'])
            if tool_data.get('inputs') and isinstance(tool_data['inputs'], list):
                ai_tags.extend(tool_data['inputs'])
            if tool_data.get('outputs') and isinstance(tool_data['outputs'], list):
                ai_tags.extend(tool_data['outputs'])
            if tool_data.get('general_price_tag'):
                ai_tags.append(tool_data['general_price_tag'])
            
            if ai_tags:
                unique_tags = list(set(ai_tags))
                taxonomies_info.append(f"标签: {', '.join(unique_tags[:5])}{'...' if len(unique_tags) > 5 else ''}")
            
            # 定价模式
            pricing_model = tool_data.get('general_price_tag') or (tool_data.get('pricing_details', {}).get('pricing_model') if tool_data.get('pricing_details') else None)
            if pricing_model:
                taxonomies_info.append(f"定价: {pricing_model}")
            
            if taxonomies_info:
                logger.debug(f"分类法信息 [{tool_name}]: {' | '.join(taxonomies_info)}")
                
        except Exception as e:
            logger.warning(f"记录分类法信息失败 [{tool_name}]: {e}")
    
    def import_batch(self, tools_data):
        """批量导入工具"""
        results = []
        total = len(tools_data)
        
        logger.info(f"开始批量导入 {total} 个工具")
        
        # 统计分类和标签信息
        self._log_batch_taxonomy_summary(tools_data)
        
        created_count = 0
        updated_count = 0
        
        for i, tool_data in enumerate(tools_data, 1):
            tool_name = tool_data.get('product_name', 'Unknown')
            logger.info(f"[{i}/{total}] 导入: {tool_name}")
            
            result = self.import_single_tool(tool_data)
            results.append(result)
            
            # 统计创建和更新数量
            if result.get('success'):
                if result.get('updated'):
                    updated_count += 1
                else:
                    created_count += 1
            
            # 添加延迟
            if i < total:
                time.sleep(self.delay)
        
        success_count = sum(1 for r in results if r.get('success', False))
        logger.info(f"批量导入完成: {success_count}/{total} 成功")
        logger.info(f"  📝 新创建: {created_count} 个")
        logger.info(f"  🔄 更新: {updated_count} 个")
        logger.info(f"  ❌ 失败: {total - success_count} 个")
        
        return results
    
    def _log_batch_taxonomy_summary(self, tools_data):
        """记录批量导入的分类法摘要"""
        try:
            categories = set()
            tags = set()
            pricing_models = set()
            input_types = set()
            output_types = set()
            
            for tool_data in tools_data:
                # 收集分类
                primary_category = tool_data.get('category') or tool_data.get('original_category_name') or tool_data.get('primary_task')
                if primary_category:
                    categories.add(primary_category)
                
                # 收集标签
                if tool_data.get('primary_task'):
                    tags.add(tool_data['primary_task'])
                if tool_data.get('inputs') and isinstance(tool_data['inputs'], list):
                    tags.update(tool_data['inputs'])
                if tool_data.get('outputs') and isinstance(tool_data['outputs'], list):
                    tags.update(tool_data['outputs'])
                if tool_data.get('general_price_tag'):
                    tags.add(tool_data['general_price_tag'])
                    pricing_models.add(tool_data['general_price_tag'])
                
                # 收集输入/输出类型
                if tool_data.get('inputs') and isinstance(tool_data['inputs'], list):
                    input_types.update(tool_data['inputs'])
                if tool_data.get('outputs') and isinstance(tool_data['outputs'], list):
                    output_types.update(tool_data['outputs'])
                
                # 收集定价模式
                pricing_detail = tool_data.get('pricing_details', {}).get('pricing_model') if tool_data.get('pricing_details') else None
                if pricing_detail:
                    pricing_models.add(pricing_detail)
            
            logger.info("\n📊 分类法摘要:")
            logger.info(f"  🗂️  将创建/使用的分类 ({len(categories)}): {', '.join(sorted(categories))}")
            logger.info(f"  🏷️  将创建/使用的标签 ({len(tags)}): {', '.join(sorted(list(tags)[:10]))}{'...' if len(tags) > 10 else ''}")
            logger.info(f"  💰 定价模式 ({len(pricing_models)}): {', '.join(sorted(pricing_models))}")
            logger.info(f"  📥 输入类型 ({len(input_types)}): {', '.join(sorted(input_types))}")
            logger.info(f"  📤 输出类型 ({len(output_types)}): {', '.join(sorted(output_types))}")
            
        except Exception as e:
            logger.warning(f"生成分类法摘要失败: {e}")
    
    def diagnose_post_status(self, post_id):
        """诊断特定文章ID的状态"""
        try:
            auth = HTTPBasicAuth(self.wp_username, self.wp_password)
            
            logger.info(f"诊断文章ID: {post_id}")
            
            # 尝试不同的端点
            endpoints = [
                f"{self.wp_api_url}/aihub/{post_id}",
                f"{self.wp_api_url}/posts/{post_id}",
                f"{self.wp_api_url}/aihub?include={post_id}",
                f"{self.wp_api_url}/posts?include={post_id}"
            ]
            
            for endpoint in endpoints:
                try:
                    logger.debug(f"测试端点: {endpoint}")
                    response = requests.get(endpoint, auth=auth, timeout=30)
                    logger.debug(f"响应状态: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            post = data[0]
                        else:
                            post = data
                        
                        logger.success(f"✓ 端点有效: {endpoint}")
                        logger.info(f"  文章类型: {post.get('type', 'unknown')}")
                        logger.info(f"  标题: {post.get('title', {}).get('rendered', 'N/A') if isinstance(post.get('title'), dict) else post.get('title', 'N/A')}")
                        logger.info(f"  状态: {post.get('status', 'unknown')}")
                        return True
                    else:
                        logger.warning(f"✗ 端点失败: {endpoint} - {response.status_code}")
                        
                except Exception as e:
                    logger.debug(f"端点测试异常: {endpoint} - {e}")
            
            logger.error(f"所有端点都无法访问文章ID: {post_id}")
            return False
            
        except Exception as e:
            logger.error(f"诊断失败: {e}")
            return False

    def _save_acf_fields_via_api(self, post_id, tool_data):
        """通过WordPress REST API保存ACF字段 - MVP简化版本：6个JSON字段"""
        try:
            auth = HTTPBasicAuth(self.wp_username, self.wp_password)
            
            # 准备6个JSON字段数据
            acf_fields = self._prepare_acf_fields(tool_data)
            
            logger.debug(f"准备保存6个JSON字段到文章 {post_id}")
            
            # 确定正确的端点
            endpoint = f"{self.wp_api_url}/aihub/{post_id}"
            
            # 批量更新6个meta字段
            update_data = {'meta': acf_fields}
            
            response = requests.post(endpoint, auth=auth, json=update_data, timeout=30)
            
            if response.status_code in [200, 201]:
                logger.success(f"✓ 6个JSON字段保存成功")
                return True
            else:
                logger.warning(f"JSON字段保存失败: {response.status_code}")
                logger.debug(f"响应: {response.text[:200]}")
                
                # 尝试逐个保存6个字段
                success_count = 0
                for field_name, field_value in acf_fields.items():
                    try:
                        single_data = {'meta': {field_name: field_value}}
                        single_response = requests.post(endpoint, auth=auth, json=single_data, timeout=15)
                        
                        if single_response.status_code in [200, 201]:
                            success_count += 1
                            logger.debug(f"✓ {field_name} 保存成功")
                        else:
                            logger.warning(f"✗ {field_name} 保存失败: {single_response.status_code}")
                        
                        time.sleep(0.2)  # 避免请求过快
                        
                    except Exception as e:
                        logger.debug(f"字段 {field_name} 保存异常: {e}")
                
                logger.info(f"逐个字段保存完成: {success_count}/6 成功")
                return success_count > 0
            
        except Exception as e:
            logger.error(f"ACF字段保存失败: {e}")
            return False 