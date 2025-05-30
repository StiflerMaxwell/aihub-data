#!/usr/bin/env python3
"""
AI工具导入 - 自定义WordPress API客户端（高级版）
集成Firecrawl数据抓取和自定义WordPress API导入
"""

import requests
import json
import time
import logging
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Optional
from csv_data_processor import CSVDataProcessor
from config import Config

class FirecrawlService:
    """Firecrawl服务客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.firecrawl.dev"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def scrape_with_schema(self, url: str, schema: Dict) -> Optional[Dict]:
        """使用Schema进行结构化抓取"""
        try:
            payload = {
                "url": url,
                "formats": ["extract"],
                "extract": {
                    "schema": schema
                }
            }
            
            response = requests.post(
                f"{self.base_url}/v1/scrape",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "extract" in data:
                    return data["extract"]
            
            return None
            
        except Exception as e:
            logging.error(f"Firecrawl抓取失败: {e}")
            return None

class AdvancedCustomAPIClient:
    """高级WordPress自定义API客户端"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = f"{config.wordpress_url.rstrip('/')}/wp-json/ai-tools/v1"
        self.auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_password)
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "AI-Tools-Importer-Advanced/1.0"
        }
        
        # 初始化Firecrawl
        if config.firecrawl_api_key:
            self.firecrawl = FirecrawlService(config.firecrawl_api_key, config.firecrawl_base_url)
            self.schema = self.load_firecrawl_schema()
        else:
            self.firecrawl = None
            self.schema = None
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('advanced_api_import.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_firecrawl_schema(self) -> Dict:
        """加载Firecrawl抓取Schema"""
        try:
            with open('ai_tool_firecrawl_schema.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"无法加载Firecrawl Schema: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            response = requests.get(
                f"{self.base_url}/test",
                auth=self.auth,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ WordPress API连接成功！用户: {data['user']['name']}")
                return True
            else:
                self.logger.error(f"❌ WordPress API连接失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 连接测试异常: {e}")
            return False
    
    def scrape_tool_data(self, url: str) -> Optional[Dict]:
        """抓取AI工具数据"""
        if not self.firecrawl or not self.schema:
            return None
        
        try:
            self.logger.info(f"🔍 正在抓取: {url}")
            data = self.firecrawl.scrape_with_schema(url, self.schema)
            
            if data:
                self.logger.info(f"✅ 抓取成功，获得 {len(data)} 个字段")
                return data
            else:
                self.logger.warning(f"⚠️ 抓取失败或无数据: {url}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 抓取异常: {e}")
            return None
    
    def import_single_tool_with_scraping(self, tool_info: Dict) -> Dict:
        """使用抓取功能导入单个AI工具"""
        tool_name = tool_info.get('product_name', 'Unknown')
        tool_url = tool_info.get('product_url', '')
        
        # 1. 抓取数据（如果可用）
        scraped_data = {}
        if tool_url and self.firecrawl:
            scraped_data = self.scrape_tool_data(tool_url) or {}
        
        # 2. 准备完整数据
        tool_data = self.prepare_complete_tool_data(scraped_data, tool_info)
        
        # 3. 调用API导入
        try:
            payload = {"tool_data": tool_data}
            
            response = requests.post(
                f"{self.base_url}/import",
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code in [200, 500]:
                result = response.json()
                result['scraped_fields'] = len(scraped_data)
                return result
            else:
                return {
                    "success": False,
                    "message": f"HTTP错误: {response.status_code}",
                    "errors": {"http": response.text},
                    "scraped_fields": len(scraped_data)
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"请求异常: {e}",
                "errors": {"exception": str(e)},
                "scraped_fields": len(scraped_data)
            }
    
    def batch_import_with_scraping(self, tools_list: List[Dict], batch_size: int = 5) -> Dict:
        """批量导入（带抓取功能）"""
        total_tools = len(tools_list)
        all_results = []
        success_count = 0
        error_count = 0
        
        self.logger.info(f"🚀 开始批量导入 {total_tools} 个AI工具（批次大小: {batch_size}）")
        
        # 分批处理
        for batch_start in range(0, total_tools, batch_size):
            batch_end = min(batch_start + batch_size, total_tools)
            batch_tools = tools_list[batch_start:batch_end]
            
            self.logger.info(f"📦 处理批次 {batch_start+1}-{batch_end}/{total_tools}")
            
            # 为当前批次准备数据
            prepared_batch = []
            for tool_info in batch_tools:
                tool_url = tool_info.get('product_url', '')
                
                # 抓取数据
                scraped_data = {}
                if tool_url and self.firecrawl:
                    scraped_data = self.scrape_tool_data(tool_url) or {}
                    time.sleep(1)  # 避免抓取过快
                
                # 准备完整数据
                tool_data = self.prepare_complete_tool_data(scraped_data, tool_info)
                prepared_batch.append(tool_data)
            
            # 发送批次请求
            try:
                payload = {"tools": prepared_batch}
                
                response = requests.post(
                    f"{self.base_url}/batch-import",
                    auth=self.auth,
                    headers=self.headers,
                    json=payload,
                    timeout=600
                )
                
                if response.status_code == 200:
                    batch_result = response.json()
                    batch_results = batch_result.get("results", [])
                    
                    for result in batch_results:
                        if result.get("success"):
                            success_count += 1
                        else:
                            error_count += 1
                    
                    all_results.extend(batch_results)
                else:
                    # 批次失败，标记所有工具为失败
                    for tool_info in batch_tools:
                        all_results.append({
                            "tool_name": tool_info.get('product_name', 'Unknown'),
                            "success": False,
                            "message": f"批次请求失败: {response.status_code}",
                            "errors": {"batch_http": response.text}
                        })
                        error_count += 1
                
            except Exception as e:
                # 批次异常，标记所有工具为失败
                for tool_info in batch_tools:
                    all_results.append({
                        "tool_name": tool_info.get('product_name', 'Unknown'),
                        "success": False,
                        "message": f"批次请求异常: {e}",
                        "errors": {"batch_exception": str(e)}
                    })
                    error_count += 1
            
            # 批次间延迟
            if batch_end < total_tools:
                time.sleep(2)
        
        return {
            "success": True,
            "summary": {
                "total": total_tools,
                "success": success_count,
                "errors": error_count
            },
            "results": all_results
        }
    
    def prepare_complete_tool_data(self, scraped_data: Dict, original_data: Dict) -> Dict:
        """准备完整的工具数据"""
        # 开始基本数据
        tool_data = {
            "product_name": original_data.get('product_name', ''),
            "product_url": original_data.get('product_url', ''),
            "original_category_name": original_data.get('original_category_name', ''),
        }
        
        # 合并抓取的数据
        if scraped_data:
            # 基本字段
            basic_fields = [
                "short_introduction", "product_story", "primary_task", 
                "author_company", "general_price_tag", "initial_release_date"
            ]
            for field in basic_fields:
                if field in scraped_data and scraped_data[field]:
                    tool_data[field] = scraped_data[field]
            
            # 布尔字段
            if "is_verified_tool" in scraped_data:
                tool_data["is_verified_tool"] = scraped_data["is_verified_tool"]
            
            # 图片URL
            for img_field in ["logo_img_url", "overview_img_url"]:
                if img_field in scraped_data and scraped_data[img_field]:
                    tool_data[img_field] = scraped_data[img_field]
            
            # 数值字段
            numeric_fields = [
                "popularity_score", "number_of_tools_by_author", 
                "average_rating", "rating_count"
            ]
            for field in numeric_fields:
                if field in scraped_data and scraped_data[field] is not None:
                    try:
                        tool_data[field] = float(scraped_data[field])
                    except (ValueError, TypeError):
                        pass
            
            # 复杂字段
            if "pricing_details" in scraped_data and isinstance(scraped_data["pricing_details"], dict):
                tool_data["pricing_details"] = scraped_data["pricing_details"]
            
            # 列表字段
            list_fields = [
                "inputs", "outputs", "pros_list", "cons_list", 
                "related_tasks", "releases", "job_impacts"
            ]
            for field in list_fields:
                if field in scraped_data and isinstance(scraped_data[field], list):
                    tool_data[field] = scraped_data[field]
        
        return tool_data

def main():
    """主函数"""
    # 加载配置
    config = Config()
    
    print("\n=== AI工具导入 - 高级自定义WordPress API客户端 ===")
    config.display_summary()
    
    # 初始化客户端
    client = AdvancedCustomAPIClient(config)
    
    # 测试连接
    print("\n📡 测试WordPress API连接...")
    if not client.test_connection():
        print("❌ WordPress API连接失败，请检查配置！")
        return
    
    # 检查Firecrawl可用性
    if client.firecrawl:
        print("✅ Firecrawl服务已启用")
    else:
        print("⚠️ Firecrawl服务未配置，将只使用CSV数据")
    
    # 加载CSV数据
    print("\n📁 加载CSV数据...")
    processor = CSVDataProcessor(config.csv_file_path)
    tools_data = processor.get_tools_data()
    
    print(f"✅ 成功加载 {len(tools_data)} 个AI工具")
    
    # 处理数量限制
    if config.debug_mode and config.max_tools_to_process:
        tools_data = tools_data[:config.max_tools_to_process]
        print(f"🔧 调试模式：限制处理 {len(tools_data)} 个工具")
    
    # 选择导入方式
    print("\n请选择导入方式:")
    print("1. 批量导入（推荐）")
    print("2. 逐个导入")
    
    choice = input("输入选择 (1/2): ").strip()
    
    if choice == "1":
        # 批量导入
        batch_size = 5
        if client.firecrawl:
            batch_size = 3  # 抓取模式使用较小批次
        
        result = client.batch_import_with_scraping(tools_data, batch_size)
        
        summary = result.get("summary", {})
        print(f"\n✅ 批量导入完成！")
        print(f"📊 总计: {summary.get('total', 0)}")
        print(f"✅ 成功: {summary.get('success', 0)}")
        print(f"❌ 失败: {summary.get('errors', 0)}")
        
        # 显示详细结果
        if config.debug_mode:
            results = result.get("results", [])
            for res in results:
                status = "✅" if res.get("success") else "❌"
                print(f"{status} {res.get('tool_name', 'Unknown')}: {res.get('message', 'No message')}")
    
    elif choice == "2":
        # 逐个导入
        success_count = 0
        error_count = 0
        
        for index, tool in enumerate(tools_data, 1):
            print(f"\n📦 处理第 {index}/{len(tools_data)} 个工具: {tool['product_name']}")
            
            result = client.import_single_tool_with_scraping(tool)
            
            if result.get("success"):
                success_count += 1
                action = result.get("action", "processed")
                scraped_fields = result.get("scraped_fields", 0)
                print(f"✅ {tool['product_name']} {action}成功 (抓取字段: {scraped_fields})")
                
                if result.get("warnings"):
                    print(f"⚠️ 警告: {len(result['warnings'])} 个非致命错误")
            else:
                error_count += 1
                scraped_fields = result.get("scraped_fields", 0)
                print(f"❌ {tool['product_name']} 处理失败 (抓取字段: {scraped_fields})")
                print(f"   错误: {result.get('message', 'Unknown error')}")
                
                if config.debug_mode and result.get("errors"):
                    for error_type, error_msg in result["errors"].items():
                        print(f"   - {error_type}: {error_msg}")
            
            # 添加延迟
            if index < len(tools_data):
                time.sleep(2 if client.firecrawl else 1)
        
        print(f"\n📊 导入完成！成功: {success_count}, 失败: {error_count}")
    
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main() 