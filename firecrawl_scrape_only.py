#!/usr/bin/env python3
"""
AI工具数据抓取器 - 使用Firecrawl抓取网站信息并合并CSV数据
仅抓取和合并，不进行WordPress导入
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional
from csv_data_processor import CSVDataProcessor
from config import Config

class FirecrawlScraper:
    """Firecrawl抓取器"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.firecrawl.dev"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('firecrawl_scrape.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_schema(self) -> Dict:
        """加载抓取Schema"""
        try:
            with open('ai_tool_firecrawl_schema.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"无法加载Schema: {e}")
            return {}
    
    def scrape_single_tool(self, url: str, schema: Dict) -> Optional[Dict]:
        """抓取单个工具的数据"""
        try:
            payload = {
                "url": url,
                "formats": ["extract"],
                "extract": {
                    "schema": schema
                }
            }
            
            self.logger.info(f"🔍 正在抓取: {url}")
            
            response = requests.post(
                f"{self.base_url}/v1/scrape",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "extract" in data:
                    extracted = data["extract"]
                    self.logger.info(f"✅ 抓取成功，获得 {len(extracted)} 个字段")
                    return extracted
                else:
                    self.logger.warning(f"⚠️ 抓取成功但无提取数据: {url}")
                    return None
            else:
                self.logger.error(f"❌ 抓取失败 {response.status_code}: {url}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 抓取异常 {url}: {e}")
            return None
    
    def merge_data(self, csv_data: Dict, scraped_data: Optional[Dict]) -> Dict:
        """合并CSV数据和抓取数据"""
        merged = csv_data.copy()
        
        if scraped_data:
            # 添加抓取标记
            merged['scraped_successfully'] = True
            merged['scraped_fields_count'] = len(scraped_data)
            
            # 合并抓取的字段
            for key, value in scraped_data.items():
                if value is not None and value != "":
                    merged[f"scraped_{key}"] = value
                    
            # 特殊处理图片URL
            if "logo_img_url" in scraped_data:
                merged["logo_img_url"] = scraped_data["logo_img_url"]
            if "overview_img_url" in scraped_data:
                merged["overview_img_url"] = scraped_data["overview_img_url"]
        else:
            merged['scraped_successfully'] = False
            merged['scraped_fields_count'] = 0
        
        return merged

def main():
    """主函数"""
    
    # 加载配置
    config = Config()
    
    print("\n=== AI工具数据抓取器 ===")
    print("仅进行Firecrawl抓取和数据合并，不进行WordPress导入\n")
    
    # 检查Firecrawl配置
    if not config.firecrawl_api_key:
        print("❌ 错误：未配置FIRECRAWL_API_KEY")
        print("请在.env文件中设置您的Firecrawl API密钥")
        return
    
    # 初始化抓取器
    scraper = FirecrawlScraper(config.firecrawl_api_key, config.firecrawl_base_url)
    schema = scraper.load_schema()
    
    if not schema:
        print("❌ 错误：无法加载Firecrawl Schema")
        return
    
    print(f"✅ Firecrawl配置正常，Schema包含 {len(schema.get('properties', {}))} 个字段")
    
    # 加载CSV数据
    print("\n📁 加载CSV数据...")
    processor = CSVDataProcessor(config.csv_file_path)
    tools_data = processor.get_tools_data()
    
    print(f"✅ 成功加载 {len(tools_data)} 个AI工具")
    
    # 处理数量限制
    if config.debug_mode and config.max_tools_to_process:
        tools_data = tools_data[:config.max_tools_to_process]
        print(f"🔧 调试模式：限制处理 {len(tools_data)} 个工具")
    
    # 开始抓取
    print(f"\n🚀 开始抓取 {len(tools_data)} 个工具的详细信息...\n")
    
    merged_results = []
    success_count = 0
    failed_count = 0
    
    for index, tool in enumerate(tools_data, 1):
        tool_name = tool.get('product_name', 'Unknown')
        tool_url = tool.get('product_url', '')
        
        print(f"📦 [{index}/{len(tools_data)}] 处理: {tool_name}")
        print(f"🔗 URL: {tool_url}")
        
        if not tool_url:
            print("⚠️ 跳过：无URL")
            merged = scraper.merge_data(tool, None)
            failed_count += 1
        else:
            # 抓取数据
            scraped_data = scraper.scrape_single_tool(tool_url, schema)
            
            # 合并数据
            merged = scraper.merge_data(tool, scraped_data)
            
            if scraped_data:
                success_count += 1
                print(f"✅ 成功抓取 {len(scraped_data)} 个字段")
            else:
                failed_count += 1
                print("❌ 抓取失败")
        
        merged_results.append(merged)
        
        # 添加延迟避免过快请求
        if index < len(tools_data):
            print("⏳ 等待2秒...\n")
            time.sleep(2)
    
    # 保存结果
    output_file = "merged_ai_tools_data.json"
    
    print(f"\n💾 保存合并结果到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_results, f, ensure_ascii=False, indent=2)
    
    # 统计报告
    print(f"\n📊 抓取完成统计:")
    print(f"✅ 总计工具: {len(tools_data)}")
    print(f"✅ 抓取成功: {success_count}")
    print(f"❌ 抓取失败: {failed_count}")
    print(f"📊 成功率: {success_count/len(tools_data)*100:.1f}%")
    
    # 显示样例数据
    if merged_results:
        print(f"\n🔍 第一个工具的合并数据样例:")
        sample = merged_results[0]
        print(f"产品名称: {sample.get('product_name', 'N/A')}")
        print(f"抓取成功: {sample.get('scraped_successfully', 'N/A')}")
        print(f"抓取字段数: {sample.get('scraped_fields_count', 'N/A')}")
        
        # 显示抓取到的字段
        scraped_fields = [k for k in sample.keys() if k.startswith('scraped_')]
        if scraped_fields:
            print(f"抓取字段: {', '.join(scraped_fields[:5])}{'...' if len(scraped_fields) > 5 else ''}")
    
    print(f"\n✨ 数据已保存到: {output_file}")
    print("您可以查看合并结果，确认后再进行WordPress导入。")

if __name__ == "__main__":
    main() 