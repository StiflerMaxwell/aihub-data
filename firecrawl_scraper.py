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
        self.delay = config.SCRAPE_DELAY
        
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
    
    def scrape_website(self, url, schema):
        """抓取单个网站数据"""
        try:
            # 增加延迟确保不超过API速率限制
            logger.debug(f"等待 {self.delay} 秒以避免API限制...")
            time.sleep(self.delay)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'url': url,
                'formats': ['extract'],
                'extract': {
                    'schema': schema
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
            else:
                logger.error(f"抓取失败 {response.status_code}: {url}")
                return None
                
        except Exception as e:
            logger.error(f"抓取异常 {url}: {e}")
            return None
    
    def scrape_single(self, tool, schema):
        """抓取单个工具数据"""
        # 抓取数据
        scraped_data = self.scrape_website(tool['url'], schema)
        
        if scraped_data:
            # 补充基本信息
            scraped_data['product_name'] = scraped_data.get('product_name', tool['product_name'])
            scraped_data['product_url'] = scraped_data.get('product_url', tool['url'])
            scraped_data['category'] = tool['category']
            scraped_data['original_category_name'] = tool['category']
            
            return {
                'status': 'success',
                'tool': tool,
                'data': scraped_data
            }
        else:
            # 抓取失败，保存基本信息
            return {
                'status': 'failed',
                'tool': tool,
                'data': {
                    'product_name': tool['product_name'],
                    'product_url': tool['url'],
                    'category': tool['category'],
                    'original_category_name': tool['category'],
                    'short_introduction': f"这是一个{tool['category']}类型的AI工具。"
                }
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
                time.sleep(self.delay)
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        logger.info(f"批量抓取完成: {success_count}/{total} 成功")
        
        return results 