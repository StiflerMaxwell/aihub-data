"""
AI工具导入系统 - Firecrawl数据抓取器
"""

import requests
import json
import time
from config import config
from logger import logger

class FirecrawlScraper:
    """Firecrawl网站数据抓取器"""
    
    def __init__(self):
        self.api_key = config.FIRECRAWL_API_KEY
        self.timeout = config.FIRECRAWL_TIMEOUT
        self.request_count = 0
        self.last_request_time = 0
        self.min_delay = 6.5  # 免费计划: 60秒/10次 = 6秒间隔，加0.5秒缓冲
        
        if not self.api_key:
            raise ValueError("Firecrawl API密钥未配置")
        
    def load_schema(self):
        """加载抓取Schema"""
        try:
            with open(config.SCHEMA_FILE, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            logger.debug(f"成功加载Schema: {config.SCHEMA_FILE}")
            return schema
        except FileNotFoundError:
            logger.error(f"Schema文件不存在: {config.SCHEMA_FILE}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Schema文件格式错误: {config.SCHEMA_FILE}")
            return None
        
    def _rate_limit_delay(self):
        """实现速率限制延迟"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            logger.info(f"🕐 速率限制延迟 {sleep_time:.1f} 秒...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _check_credits(self):
        """检查剩余credits（如果API支持）"""
        try:
            # 这里可以添加credits检查的API调用
            # 目前先记录请求数
            if self.request_count > 0 and self.request_count % 10 == 0:
                logger.warning(f"⚠️  已使用 {self.request_count} 次API调用，请注意免费额度限制")
        except Exception as e:
            logger.debug(f"无法检查credits: {e}")
    
    def scrape_website(self, url, schema):
        """抓取单个网站数据"""
        try:
            # 实施速率限制
            self._rate_limit_delay()
            
            # 检查credits
            self._check_credits()
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'url': url,
                'formats': ['extract'],
                'extract': {
                    'schema': schema,
                    'systemPrompt': '请严格按照提供的schema格式提取网站信息，确保所有字段都有值。如果某个字段无法从网站获取，请提供合理的默认值。'
                }
            }
            
            logger.debug(f"正在抓取网站: {url}")
            
            response = requests.post(
                'https://api.firecrawl.dev/v1/scrape',
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('data', {}).get('extract'):
                    extract_data = result['data']['extract']
                    logger.success(f"✓ 抓取成功: {url}")
                    return extract_data
                else:
                    logger.warning(f"抓取返回空数据: {url}")
                    return None
            elif response.status_code == 402:
                logger.error(f"💳 Firecrawl API额度不足或超过速率限制: {url}")
                logger.error("📊 可能的原因:")
                logger.error("   • 免费计划500 credits已用完")
                logger.error("   • 超过每分钟10次抓取限制")
                logger.error("   • 需要升级付费计划")
                logger.error("💡 建议解决方案:")
                logger.error("   1. 等待下个月额度重置")
                logger.error("   2. 升级到付费计划")
                logger.error("   3. 使用 ENABLE_FIRECRAWL=false 禁用抓取")
                return None
            else:
                logger.error(f"抓取失败 {response.status_code}: {url}")
                if response.status_code == 429:
                    logger.warning("速率限制，建议增加延迟时间")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"⏱️  请求超时: {url}")
            return None
        except Exception as e:
            logger.error(f"抓取异常 {url}: {e}")
            return None
    
    def scrape_single(self, tool_data, schema, max_retries=3):
        """抓取单个网站数据，包含重试和错误处理"""
        url = tool_data.get('url', '').strip()
        
        if not url:
            return {
                'status': 'error',
                'message': 'URL为空',
                'data': tool_data
            }
        
        # 确保URL格式正确
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"尝试抓取 ({attempt + 1}/{max_retries}): {url}")
                
                # 抓取数据
                scraped_data = self.scrape_website(url, schema)
                
                if scraped_data:
                    # 确保基本字段存在
                    if not scraped_data.get('product_name'):
                        scraped_data['product_name'] = tool_data.get('product_name', 'Unknown')
                    
                    if not scraped_data.get('product_url'):
                        scraped_data['product_url'] = url
                    
                    if not scraped_data.get('category'):
                        scraped_data['category'] = tool_data.get('category', 'AI Tools')
                    
                    # 添加原始分类信息
                    scraped_data['original_category_name'] = tool_data.get('category', '')
                    
                    logger.success(f"✓ 抓取成功: {scraped_data.get('product_name', 'Unknown')}")
                    return {
                        'status': 'success',
                        'data': scraped_data
                    }
                else:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        logger.info(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ 抓取失败: {error_msg}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"💥 所有重试失败: {url}")
        
        # 所有重试都失败了，返回错误
        return {
            'status': 'error',
            'message': f'抓取失败: {url}',
            'data': tool_data
        }

    def scrape_batch(self, tool_list, schema):
        """批量抓取工具数据"""
        results = []
        total = len(tool_list)
        
        logger.info(f"开始批量抓取 {total} 个工具")
        
        for i, tool in enumerate(tool_list, 1):
            logger.info(f"[{i}/{total}] 抓取: {tool['product_name']}")
            
            # 使用单个抓取方法
            result = self.scrape_single(tool, schema)
            results.append(result)
            
            # 添加延迟
            if i < total:
                time.sleep(self.min_delay)
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        logger.info(f"批量抓取完成: {success_count}/{total} 成功")
        
        return results 