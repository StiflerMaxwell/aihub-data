"""
AI工具导入系统 - Gemini AI数据增强器
"""

import json
import time
from typing import Dict, List, Optional
from config import config
from logger import logger

class GeminiEnhancer:
    """Gemini AI数据增强器"""
    
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.enabled = config.ENABLE_GEMINI_ENHANCEMENT
        self.client = None
        
        if self.is_enabled():
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.success("Gemini 2.5 Flash client initialized successfully")
            except ImportError:
                logger.error("Google GenAI SDK not installed. Please run: pip install google-genai")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.enabled = False
        
    def is_enabled(self) -> bool:
        """检查Gemini增强是否启用且配置正确"""
        return self.enabled and self.api_key and self.api_key != 'your_gemini_api_key'
    
    def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """调用Gemini API"""
        if not self.is_enabled() or not self.client:
            return None
            
        try:
            # 添加延迟避免配额限制 (每分钟10次请求，安全起见每次等待8秒)
            time.sleep(8)
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-preview-05-20",
                contents=prompt
            )
            
            if response and response.text:
                return response.text.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            # 如果遇到配额限制错误，等待更长时间
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning("API quota exceeded, waiting 60 seconds...")
                time.sleep(60)
            return None
    
    def enhance_tool_data(self, tool_data: Dict) -> Dict:
        """增强工具数据 - 确保所有字段都有内容"""
        if not self.is_enabled():
            logger.info("Gemini enhancement feature not enabled")
            return tool_data
            
        logger.info(f"Starting Gemini enhancement for: {tool_data.get('product_name', 'Unknown')}")
        
        enhanced_data = tool_data.copy()
        
        try:
            # 0. 首先处理关键空字段
            enhanced_data = self._enhance_critical_empty_fields(enhanced_data)
            
            # 1. 基础信息增强
            enhanced_data = self._enhance_basic_info(enhanced_data)
            
            # 2. 优缺点增强
            enhanced_data = self._enhance_pros_cons(enhanced_data)
            
            # 3. 相关任务增强
            enhanced_data = self._enhance_related_tasks(enhanced_data)
            
            # 4. 工作影响增强
            enhanced_data = self._enhance_job_impacts(enhanced_data)
            
            # 5. 替代工具增强
            enhanced_data = self._enhance_alternatives(enhanced_data)
            
            # 6. 评分和评论增强
            enhanced_data = self._enhance_ratings(enhanced_data)
            
            # 7. 定价信息增强
            enhanced_data = self._enhance_pricing(enhanced_data)
            
            # 8. 增强FAQ字段
            enhanced_data = self._enhance_faq(enhanced_data)
            
            # 9. 增强功能特性
            enhanced_data = self._enhance_features(enhanced_data)
            
            # 10. 填充所有必需的默认字段
            enhanced_data = self._fill_required_fields(enhanced_data)
            
            logger.success(f"Completed Gemini enhancement: {enhanced_data.get('product_name', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Gemini enhancement failed: {e}")
        
        return enhanced_data
    
    def _enhance_critical_empty_fields(self, tool_data: Dict) -> Dict:
        """专门处理关键的空字段"""
        product_name = tool_data.get('product_name', '')
        category = tool_data.get('category', '')
        
        # 增强短介绍
        if not tool_data.get('short_introduction') or tool_data.get('short_introduction').strip() == '':
            prompt = f"""Write a concise 1-sentence description for the AI tool "{product_name}" in the {category} category.
Keep it under 100 characters. Focus on what it does. Return only the description."""
            
            response = self._call_gemini_api(prompt)
            if response:
                tool_data['short_introduction'] = response.strip()
                logger.debug(f"Enhanced short_introduction for {product_name}")
        
        # 增强定价标签
        if not tool_data.get('general_price_tag') or tool_data.get('general_price_tag').strip() == '':
            prompt = f"""What is the pricing model for the AI tool "{product_name}"? 
Return one word: "Free", "Freemium", "Paid", or "Enterprise"."""
            
            response = self._call_gemini_api(prompt)
            if response:
                tool_data['general_price_tag'] = response.strip()
                logger.debug(f"Enhanced general_price_tag for {product_name}")
        
        # 增强输入类型
        if not tool_data.get('inputs') or len(tool_data.get('inputs', [])) == 0:
            prompt = f"""What types of input does the AI tool "{product_name}" accept? 
Return format: ["Input1", "Input2", "Input3"]
Common types: Text, Image, Audio, Video, Code, URL, File
Return only valid JSON array."""
            
            response = self._call_gemini_api(prompt)
            if response:
                try:
                    cleaned_response = self._clean_json_response(response)
                    inputs = json.loads(cleaned_response)
                    if isinstance(inputs, list) and len(inputs) > 0:
                        tool_data['inputs'] = inputs
                        logger.debug(f"Enhanced inputs for {product_name}")
                except json.JSONDecodeError:
                    tool_data['inputs'] = ['Text']  # 默认值
        
        # 增强输出类型
        if not tool_data.get('outputs') or len(tool_data.get('outputs', [])) == 0:
            prompt = f"""What types of output does the AI tool "{product_name}" generate? 
Return format: ["Output1", "Output2", "Output3"]
Common types: Text, Image, Audio, Video, Code, Data, Report
Return only valid JSON array."""
            
            response = self._call_gemini_api(prompt)
            if response:
                try:
                    cleaned_response = self._clean_json_response(response)
                    outputs = json.loads(cleaned_response)
                    if isinstance(outputs, list) and len(outputs) > 0:
                        tool_data['outputs'] = outputs
                        logger.debug(f"Enhanced outputs for {product_name}")
                except json.JSONDecodeError:
                    tool_data['outputs'] = ['Text']  # 默认值
        
        # 增强UI文本字段
        ui_text_defaults = {
            'how_would_you_rate_text': 'How would you rate this tool?',
            'help_other_people_text': 'Help others by rating this tool.',
            'your_rating_text': 'Your rating',
            'post_review_button_text': 'Post Review',
            'feature_requests_intro': 'Have a feature request?',
            'request_feature_button_text': 'Request Feature'
        }
        
        for field, default_value in ui_text_defaults.items():
            if not tool_data.get(field) or tool_data.get(field).strip() == '':
                tool_data[field] = default_value
                logger.debug(f"Enhanced {field} for {product_name}")
        
        # 增强定价详情
        if not tool_data.get('pricing_details') or not tool_data.get('pricing_details', {}).get('pricing_model'):
            pricing_model = tool_data.get('general_price_tag', 'Free')
            tool_data['pricing_details'] = {
                'pricing_model': pricing_model,
                'paid_options_from': 0 if pricing_model == 'Free' else 10,
                'currency': 'USD',
                'billing_frequency': 'monthly' if pricing_model != 'Free' else ''
            }
            logger.debug(f"Enhanced pricing_details for {product_name}")
        
        return tool_data
    
    def _enhance_basic_info(self, tool_data: Dict) -> Dict:
        """增强基础信息"""
        product_name = tool_data.get('product_name', '')
        category = tool_data.get('category', '')
        
        # 增强产品描述
        if not tool_data.get('product_story') or len(tool_data.get('product_story', '')) < 50:
            prompt = f"""Write a detailed 2-3 sentence product description for the AI tool "{product_name}" in the {category} category.
Focus on what it does, key features, and benefits. Use professional language.
Return only the description text."""
            
            response = self._call_gemini_api(prompt)
            if response:
                tool_data['product_story'] = response
                logger.debug(f"Enhanced product_story for {product_name}")
        
        # 增强作者公司
        if not tool_data.get('author_company'):
            prompt = f"""What company or organization created the AI tool "{product_name}"? 
Return only the company name, no explanations."""
            
            response = self._call_gemini_api(prompt)
            if response:
                tool_data['author_company'] = response
                logger.debug(f"Enhanced author_company for {product_name}")
        
        # 增强发布日期
        if not tool_data.get('initial_release_date'):
            prompt = f"""When was the AI tool "{product_name}" first released? 
Return in format YYYY-MM-DD or YYYY if only year is known. If unknown, return "2023"."""
            
            response = self._call_gemini_api(prompt)
            if response:
                tool_data['initial_release_date'] = response
                logger.debug(f"Enhanced initial_release_date for {product_name}")
        
        # 增强主要任务
        if not tool_data.get('primary_task'):
            prompt = f"""What is the primary task or main function of the AI tool "{product_name}"? 
Return a short 2-3 word description (e.g., "Text Generation", "Image Creation", "Code Assistant")."""
            
            response = self._call_gemini_api(prompt)
            if response:
                tool_data['primary_task'] = response
                logger.debug(f"Enhanced primary_task for {product_name}")
        
        # 增强欢迎消息
        if not tool_data.get('message') or tool_data.get('message') == 'What can I help with?':
            prompt = f"""Create a welcoming message that the AI tool "{product_name}" might show to users. 
Keep it short and friendly (under 10 words)."""
            
            response = self._call_gemini_api(prompt)
            if response:
                tool_data['message'] = response
                logger.debug(f"Enhanced message for {product_name}")
        
        return tool_data
    
    def _enhance_pros_cons(self, tool_data: Dict) -> Dict:
        """增强优缺点列表"""
        if tool_data.get('pros_list') and tool_data.get('cons_list'):
            return tool_data
            
        product_name = tool_data.get('product_name', '')
        category = tool_data.get('category', '')
        
        prompt = f"""Analyze the pros and cons of the AI tool "{product_name}" in the {category} category.

Return format (valid JSON only):
{{
  "pros_list": ["Pro 1", "Pro 2", "Pro 3"],
  "cons_list": ["Con 1", "Con 2"]
}}

Requirements:
1. At least 3 detailed pros and 2 specific cons
2. Be realistic and specific to this tool
3. Return only valid JSON, no explanations"""
        
        response = self._call_gemini_api(prompt)
        if response:
            try:
                # 清理响应
                cleaned_response = self._clean_json_response(response)
                pros_cons = json.loads(cleaned_response)
                
                if isinstance(pros_cons, dict):
                    if 'pros_list' in pros_cons:
                        tool_data['pros_list'] = pros_cons['pros_list']
                    if 'cons_list' in pros_cons:
                        tool_data['cons_list'] = pros_cons['cons_list']
                    logger.debug(f"Enhanced pros/cons for {product_name}")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid pros/cons JSON format: {e}")
        
        return tool_data
    
    def _enhance_related_tasks(self, tool_data: Dict) -> Dict:
        """增强相关任务列表"""
        if tool_data.get('related_tasks'):
            return tool_data
            
        product_name = tool_data.get('product_name', '')
        category = tool_data.get('category', '')
        
        prompt = f"""List 7 specific tasks that can be accomplished using the AI tool "{product_name}" in the {category} category.

Return format (valid JSON array only):
["Task 1", "Task 2", "Task 3", "Task 4", "Task 5", "Task 6", "Task 7"]

Requirements:
1. Be specific and actionable
2. Start with action verbs
3. Return only valid JSON array"""
        
        response = self._call_gemini_api(prompt)
        if response:
            try:
                cleaned_response = self._clean_json_response(response)
                tasks = json.loads(cleaned_response)
                if isinstance(tasks, list):
                    tool_data['related_tasks'] = tasks
                    logger.debug(f"Enhanced related_tasks for {product_name}")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid tasks JSON format: {e}")
        
        return tool_data
    
    def _enhance_job_impacts(self, tool_data: Dict) -> Dict:
        """增强工作影响 - 新的UI卡片格式"""
        if tool_data.get('job_impacts'):
            return tool_data
            
        product_name = tool_data.get('product_name', '')
        category = tool_data.get('category', '')
        
        prompt = f"""Analyze which jobs are most impacted by the AI tool "{product_name}" in the {category} category.

Return format (valid JSON only):
{{
  "job_impacts": [
    {{
      "job_type": "Content Creator",
      "impact": "95%",
      "tasks": 1245,
      "ais": 8567,
      "avatar_url": "https://api.dicebear.com/7.x/personas/svg?seed=content"
    }},
    {{
      "job_type": "Software Developer", 
      "impact": "87%",
      "tasks": 892,
      "ais": 6234,
      "avatar_url": "https://api.dicebear.com/7.x/personas/svg?seed=developer"
    }},
    {{
      "job_type": "Data Analyst",
      "impact": "83%", 
      "tasks": 756,
      "ais": 5123,
      "avatar_url": "https://api.dicebear.com/7.x/personas/svg?seed=analyst"
    }}
  ]
}}

Requirements:
1. Include 3-4 job types most impacted by this specific tool
2. Impact: percentage (80%-95% for high impact jobs)
3. Tasks: realistic number of affected tasks (700-1500)
4. AIs: number of related AI tools in this space (3000-15000)
5. Avatar URLs: use dicebear API with job-related seeds
6. Job types should be specific and realistic (avoid generic titles)
7. Return only valid JSON, no explanations"""
        
        response = self._call_gemini_api(prompt)
        if response:
            try:
                cleaned_response = self._clean_json_response(response)
                job_data = json.loads(cleaned_response)
                if isinstance(job_data, dict) and 'job_impacts' in job_data:
                    tool_data['job_impacts'] = job_data['job_impacts']
                    logger.debug(f"Enhanced job_impacts for {product_name}")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid job_impacts JSON format: {e}")
        
        return tool_data
    
    def _enhance_alternatives(self, tool_data: Dict) -> Dict:
        """增强替代工具"""
        if tool_data.get('alternative_tools'):
            return tool_data
            
        product_name = tool_data.get('product_name', '')
        category = tool_data.get('category', '')
        
        prompt = f"""List 5 alternative AI tools to "{product_name}" in the {category} category.

Return format (valid JSON array only):
["Alternative 1", "Alternative 2", "Alternative 3", "Alternative 4", "Alternative 5"]

Requirements:
1. Include well-known alternatives
2. Tools should be in the same or similar category
3. Return only valid JSON array"""
        
        response = self._call_gemini_api(prompt)
        if response:
            try:
                cleaned_response = self._clean_json_response(response)
                alternatives = json.loads(cleaned_response)
                if isinstance(alternatives, list):
                    tool_data['alternative_tools'] = alternatives
                    tool_data['alternatives_count_text'] = f"See {len(alternatives)} alternatives"
                    logger.debug(f"Enhanced alternatives for {product_name}")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid alternatives JSON format: {e}")
        
        return tool_data
    
    def _enhance_ratings(self, tool_data: Dict) -> Dict:
        """增强评分信息"""
        # 生成合理的评分数据
        import random
        
        if not tool_data.get('user_ratings_count'):
            tool_data['user_ratings_count'] = random.randint(50, 1000)
        
        if not tool_data.get('average_rating'):
            tool_data['average_rating'] = round(random.uniform(3.8, 4.8), 1)
        
        # 确保评分相关的文本存在
        tool_data['how_would_you_rate_text'] = tool_data.get('how_would_you_rate_text', 'How would you rate this tool?')
        tool_data['help_other_people_text'] = tool_data.get('help_other_people_text', 'Help others by rating this tool.')
        tool_data['your_rating_text'] = tool_data.get('your_rating_text', 'Your rating')
        tool_data['post_review_button_text'] = tool_data.get('post_review_button_text', 'Post Review')
        tool_data['feature_requests_intro'] = tool_data.get('feature_requests_intro', 'Have a feature request?')
        tool_data['request_feature_button_text'] = tool_data.get('request_feature_button_text', 'Request Feature')
        
        logger.debug(f"Enhanced ratings for {tool_data.get('product_name', 'Unknown')}")
        return tool_data
    
    def _enhance_pricing(self, tool_data: Dict) -> Dict:
        """增强定价信息"""
        if not tool_data.get('pricing_details'):
            tool_data['pricing_details'] = {}
        
        pricing = tool_data['pricing_details']
        
        # 确保基本定价字段存在
        if not pricing.get('pricing_model'):
            pricing['pricing_model'] = tool_data.get('general_price_tag', 'Free')
        
        if not pricing.get('currency'):
            pricing['currency'] = 'USD'
        
        if not pricing.get('paid_options_from'):
            if pricing.get('pricing_model', '').lower() in ['paid', 'premium', 'subscription']:
                pricing['paid_options_from'] = 9.99
            else:
                pricing['paid_options_from'] = 0
        
        if not pricing.get('billing_frequency'):
            if pricing.get('paid_options_from', 0) > 0:
                pricing['billing_frequency'] = 'monthly'
            else:
                pricing['billing_frequency'] = ''
        
        logger.debug(f"Enhanced pricing for {tool_data.get('product_name', 'Unknown')}")
        return tool_data
    
    def _enhance_faq(self, tool_data: Dict) -> Dict:
        """增强FAQ字段"""
        if tool_data.get('faq') and len(tool_data.get('faq', [])) >= 3:
            return tool_data
            
        product_name = tool_data.get('product_name', '')
        category = tool_data.get('category', '')
        
        prompt = f"""Generate 5 frequently asked questions and answers for the AI tool "{product_name}" in the {category} category.

Return format (valid JSON only):
{{
  "faq": [
    {{
      "question": "What is {product_name}?",
      "answer": "Detailed answer..."
    }},
    {{
      "question": "How do I use {product_name}?",
      "answer": "Step-by-step answer..."
    }},
    {{
      "question": "Is {product_name} free?",
      "answer": "Pricing information..."
    }},
    {{
      "question": "What are the main features?",
      "answer": "Feature overview..."
    }},
    {{
      "question": "Who should use {product_name}?",
      "answer": "Target audience..."
    }}
  ]
}}

Requirements:
1. Questions should be realistic and commonly asked
2. Answers should be informative and specific
3. Return only valid JSON, no explanations"""
        
        response = self._call_gemini_api(prompt)
        if response:
            try:
                cleaned_response = self._clean_json_response(response)
                faq_data = json.loads(cleaned_response)
                
                if isinstance(faq_data, dict) and 'faq' in faq_data:
                    tool_data['faq'] = faq_data['faq']
                    logger.debug(f"Enhanced FAQ for {product_name}")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid FAQ JSON format: {e}")
        
        return tool_data
    
    def _enhance_features(self, tool_data: Dict) -> Dict:
        """增强功能特性字段"""
        product_name = tool_data.get('product_name', '')
        category = tool_data.get('category', '')
        
        # 增强features列表
        if not tool_data.get('features') or len(tool_data.get('features', [])) < 3:
            prompt = f"""List 5-7 key features of the AI tool "{product_name}" in the {category} category.

Return format (valid JSON only):
{{
  "features": ["Feature 1", "Feature 2", "Feature 3", "Feature 4", "Feature 5"]
}}

Requirements:
1. Features should be specific and technical
2. Focus on what makes this tool unique
3. Return only valid JSON, no explanations"""
            
            response = self._call_gemini_api(prompt)
            if response:
                try:
                    cleaned_response = self._clean_json_response(response)
                    features_data = json.loads(cleaned_response)
                    
                    if isinstance(features_data, dict) and 'features' in features_data:
                        tool_data['features'] = features_data['features']
                        logger.debug(f"Enhanced features for {product_name}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid features JSON format: {e}")
        
        # 增强featured_matches
        if not tool_data.get('featured_matches') or len(tool_data.get('featured_matches', [])) < 2:
            prompt = f"""Suggest 3-4 tools that work well together with "{product_name}" for enhanced productivity.

Return format (valid JSON only):
{{
  "featured_matches": ["Tool 1", "Tool 2", "Tool 3"]
}}

Requirements:
1. Tools should complement {product_name}
2. Focus on workflow integration
3. Return only valid JSON, no explanations"""
            
            response = self._call_gemini_api(prompt)
            if response:
                try:
                    cleaned_response = self._clean_json_response(response)
                    matches_data = json.loads(cleaned_response)
                    
                    if isinstance(matches_data, dict) and 'featured_matches' in matches_data:
                        tool_data['featured_matches'] = matches_data['featured_matches']
                        logger.debug(f"Enhanced featured_matches for {product_name}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid featured_matches JSON format: {e}")
        
        # 增强other_tools
        if not tool_data.get('other_tools') or len(tool_data.get('other_tools', [])) < 3:
            prompt = f"""List 4-5 other AI tools in the same category as "{product_name}" ({category}).

Return format (valid JSON only):
{{
  "other_tools": ["Tool 1", "Tool 2", "Tool 3", "Tool 4"]
}}

Requirements:
1. Tools should be in the same category
2. Include both popular and emerging tools
3. Return only valid JSON, no explanations"""
            
            response = self._call_gemini_api(prompt)
            if response:
                try:
                    cleaned_response = self._clean_json_response(response)
                    other_tools_data = json.loads(cleaned_response)
                    
                    if isinstance(other_tools_data, dict) and 'other_tools' in other_tools_data:
                        tool_data['other_tools'] = other_tools_data['other_tools']
                        logger.debug(f"Enhanced other_tools for {product_name}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid other_tools JSON format: {e}")
        
        return tool_data

    def _fill_required_fields(self, tool_data: Dict) -> Dict:
        """填充所有必需的默认字段"""
        # 基础信息字段
        defaults = {
            'popularity_score': 0,
            'number_of_tools_by_author': 1,
            'is_verified_tool': False,
            'copy_url_text': 'Copy URL',
            'save_button_text': 'Save',
            'vote_best_ai_tool_text': f"Vote for {tool_data.get('product_name', 'this tool')}",
            
            # I/O字段 - 如果为空数组也需要填充
            'inputs': tool_data.get('inputs') if tool_data.get('inputs') else ['Text'],
            'outputs': tool_data.get('outputs') if tool_data.get('outputs') else ['Text'],
            
            # 版本发布
            'releases': [],
            
            # 优缺点视图文本
            'view_more_pros_text': 'View more pros',
            'view_more_cons_text': 'View more cons',
            
            # 替代方案
            'view_more_alternatives_text': 'View more alternatives',
            
            # 推荐工具
            'if_you_liked_text': f"If you liked {tool_data.get('product_name', 'this tool')}, you might also like:",
            'featured_matches': [],
            'other_tools': [],
        }
        
        # 填充缺失字段
        for key, default_value in defaults.items():
            if not tool_data.get(key):
                tool_data[key] = default_value
        
        # 智能生成版本发布历史
        if not tool_data.get('releases') or len(tool_data.get('releases', [])) == 0:
            tool_data = self._enhance_releases(tool_data)
        
        logger.debug(f"Filled required fields for {tool_data.get('product_name', 'Unknown')}")
        return tool_data
    
    def _enhance_releases(self, tool_data: Dict) -> Dict:
        """增强版本发布历史"""
        product_name = tool_data.get('product_name', '')
        category = tool_data.get('category', '')
        initial_release_date = tool_data.get('initial_release_date', '2023')
        
        prompt = f"""Generate a realistic version release history for the AI tool "{product_name}" in the {category} category.

Return format (valid JSON only):
{{
  "releases": [
    {{
      "product_name": "{product_name} v2.1",
      "release_date": "2024-01-15",
      "release_notes": "Added new features including improved accuracy and faster processing. Enhanced user interface with better accessibility options.",
      "release_author": "Product Team"
    }},
    {{
      "product_name": "{product_name} v2.0",
      "release_date": "2023-10-20",
      "release_notes": "Major update with redesigned interface, new AI capabilities, and improved performance. Added mobile support.",
      "release_author": "Development Team"
    }}
  ]
}}

Requirements:
1. Generate 2-4 realistic releases
2. Start from recent dates and go backwards
3. Include version numbers (v1.0, v2.0, etc.)
4. Make release notes specific to the tool's category
5. Use realistic dates after {initial_release_date}
6. Return only valid JSON"""
        
        response = self._call_gemini_api(prompt)
        if response:
            try:
                cleaned_response = self._clean_json_response(response)
                release_data = json.loads(cleaned_response)
                if isinstance(release_data, dict) and 'releases' in release_data:
                    tool_data['releases'] = release_data['releases']
                    logger.debug(f"Enhanced releases for {product_name}")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid releases JSON format: {e}")
        
        return tool_data
    
    def _clean_json_response(self, response: str) -> str:
        """清理Gemini响应为有效JSON"""
        cleaned = response.strip()
        
        # 移除markdown代码块
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]
        
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        
        return cleaned.strip()

# 全局实例
gemini_enhancer = GeminiEnhancer() 