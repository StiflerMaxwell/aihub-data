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
        self.timeout = config.REQUEST_TIMEOUT
        self.delay = config.IMPORT_DELAY
        self.use_custom_api = True  # 默认尝试使用自定义API
        
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
            
            # 测试自定义API（可选）
            try:
                response = requests.get(f"{self.custom_api_url}/test", auth=auth, timeout=self.timeout)
                if response.status_code == 200:
                    logger.success("自定义API连接成功")
                    self.use_custom_api = True
                else:
                    logger.warning("自定义API不可用，将使用标准WordPress API")
                    self.use_custom_api = False
            except Exception as e:
                logger.warning(f"自定义API测试失败，将使用标准WordPress API: {e}")
                self.use_custom_api = False
            
            return True
            
        except Exception as e:
            logger.error(f"WordPress连接测试失败: {e}")
            return False
    
    def import_single_tool(self, tool_data):
        """导入单个工具"""
        try:
            tool_name = tool_data.get('product_name', 'Unknown')
            logger.debug(f"正在导入: {tool_name}")
            
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
    
    def _import_via_custom_api(self, tool_data):
        """通过自定义API导入"""
        auth = HTTPBasicAuth(self.wp_username, self.wp_password)
        headers = {"Content-Type": "application/json"}
        
        payload = {"tool_data": tool_data}
        
        tool_name = tool_data.get('product_name', 'Unknown')
        
        response = requests.post(
            f"{self.custom_api_url}/import",
            headers=headers,
            auth=auth,
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
            'content': tool_data.get('description', f"{tool_name} is an {tool_data.get('category', 'AI')} tool."),
            'status': 'publish',
            'type': 'post',  # 如果aihub CPT不存在，使用标准post类型
            'excerpt': tool_data.get('short_introduction', ''),
        }
        
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
            
            # 记录分类和标签创建信息
            self._log_taxonomy_info(tool_data, tool_name)
            
            return {
                'success': True,
                'post_id': post_id,
                'tool_name': tool_name,
                'message': f'通过标准API导入成功 (类型: {post_data["type"]})'
            }
        else:
            error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            logger.error(f"导入失败: {tool_name} - {error_msg}")
            return {
                'success': False,
                'tool_name': tool_name,
                'error': error_msg
            }
    
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
        
        for i, tool_data in enumerate(tools_data, 1):
            tool_name = tool_data.get('product_name', 'Unknown')
            logger.info(f"[{i}/{total}] 导入: {tool_name}")
            
            result = self.import_single_tool(tool_data)
            results.append(result)
            
            # 添加延迟
            if i < total:
                time.sleep(self.delay)
        
        success_count = sum(1 for r in results if r.get('success', False))
        logger.info(f"批量导入完成: {success_count}/{total} 成功")
        
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