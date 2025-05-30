#!/usr/bin/env python3
"""
简化版AI工具数据抓取器
直接抓取网站信息，不依赖外部模块
"""

import requests
import json
import time
import csv
import os
from typing import Dict, List, Optional

class SimpleFirecrawlScraper:
    """简化的Firecrawl抓取器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.firecrawl.dev"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def load_csv_data(self, file_path: str) -> List[Dict]:
        """加载CSV数据"""
        tools_data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    # 找到产品名称和URL列
                    product_name = None
                    product_url = None
                    category = None
                    
                    for key, value in row.items():
                        if value and value.strip():
                            # 判断是否为URL
                            if value.startswith('http'):
                                product_url = value.strip()
                                # 从列名推断类别
                                if '产品名称' in key or 'product' in key.lower():
                                    continue
                                # 从列名推断类别
                                for cat in ['AI Search Engine', 'AI ChatBots', 'AI Character Generator', 
                                          'AI Presentation Maker', 'AI Image Generator', 'AI Image Editor',
                                          'AI Image Enhancer', 'AI Video Generator', 'AI Video Editing', 
                                          'AI Music Generator']:
                                    if cat in key:
                                        category = cat
                                        break
                            else:
                                # 可能是产品名称
                                if not product_name:
                                    product_name = value.strip()
                    
                    if product_name and product_url:
                        tools_data.append({
                            'product_name': product_name,
                            'product_url': product_url,
                            'original_category_name': category or 'Unknown'
                        })
            
            return tools_data
            
        except Exception as e:
            print(f"❌ 读取CSV文件失败: {e}")
            return []
    
    def load_schema(self) -> Dict:
        """加载抓取Schema"""
        try:
            with open('ai_tool_firecrawl_schema.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 无法加载Schema，使用默认Schema: {e}")
            # 返回简化的默认Schema
            return {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "产品名称"},
                    "short_introduction": {"type": "string", "description": "简短介绍"},
                    "logo_img_url": {"type": "string", "description": "Logo图片URL"},
                    "overview_img_url": {"type": "string", "description": "概览图片URL"},
                    "primary_task": {"type": "string", "description": "主要功能"},
                    "author_company": {"type": "string", "description": "开发公司"},
                    "general_price_tag": {"type": "string", "description": "价格标签"}
                }
            }
    
    def scrape_tool(self, url: str, schema: Dict) -> Optional[Dict]:
        """抓取单个工具"""
        try:
            payload = {
                "url": url,
                "formats": ["extract"],
                "extract": {"schema": schema}
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
            
            print(f"⚠️ 抓取失败 {response.status_code}: {url}")
            return None
            
        except Exception as e:
            print(f"❌ 抓取异常: {e}")
            return None

def main():
    """主函数"""
    
    print("\n=== 简化版AI工具数据抓取器 ===")
    
    # 配置
    api_key = "fc-4a9ca9115114472d92ace77332cf0262"  # 您的Firecrawl API密钥
    csv_file = "AI工具汇总-工作表2.csv"
    max_tools = 3  # 测试限制
    
    # 初始化抓取器
    scraper = SimpleFirecrawlScraper(api_key)
    
    # 加载Schema
    schema = scraper.load_schema()
    print(f"✅ Schema加载完成，包含 {len(schema.get('properties', {}))} 个字段")
    
    # 加载CSV数据
    print(f"\n📁 加载CSV文件: {csv_file}")
    tools_data = scraper.load_csv_data(csv_file)
    
    if not tools_data:
        print("❌ 未找到有效的工具数据")
        return
    
    print(f"✅ 成功加载 {len(tools_data)} 个AI工具")
    
    # 限制处理数量（测试）
    if max_tools and len(tools_data) > max_tools:
        tools_data = tools_data[:max_tools]
        print(f"🔧 测试模式：限制处理 {len(tools_data)} 个工具")
    
    # 显示将要处理的工具
    print(f"\n📋 将要抓取的工具:")
    for i, tool in enumerate(tools_data, 1):
        print(f"  {i}. {tool['product_name']} - {tool['product_url']}")
    
    # 开始抓取
    print(f"\n🚀 开始抓取...\n")
    
    results = []
    success_count = 0
    
    for index, tool in enumerate(tools_data, 1):
        print(f"📦 [{index}/{len(tools_data)}] {tool['product_name']}")
        print(f"🔗 {tool['product_url']}")
        
        # 抓取数据
        scraped_data = scraper.scrape_tool(tool['product_url'], schema)
        
        # 合并数据
        merged = tool.copy()
        if scraped_data:
            success_count += 1
            merged['scraped_successfully'] = True
            merged['scraped_data'] = scraped_data
            print(f"✅ 抓取成功，获得 {len(scraped_data)} 个字段")
            
            # 显示抓取到的关键字段
            key_fields = ['product_name', 'short_introduction', 'primary_task', 'author_company']
            for field in key_fields:
                if field in scraped_data and scraped_data[field]:
                    print(f"   {field}: {scraped_data[field][:50]}{'...' if len(str(scraped_data[field])) > 50 else ''}")
        else:
            merged['scraped_successfully'] = False
            merged['scraped_data'] = None
            print("❌ 抓取失败")
        
        results.append(merged)
        
        # 延迟
        if index < len(tools_data):
            print("⏳ 等待2秒...\n")
            time.sleep(2)
    
    # 保存结果
    output_file = "scraped_results.json"
    print(f"\n💾 保存结果到: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 统计
    print(f"\n📊 抓取统计:")
    print(f"✅ 总计: {len(tools_data)}")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {len(tools_data) - success_count}")
    print(f"📈 成功率: {success_count/len(tools_data)*100:.1f}%")
    
    print(f"\n✨ 完成！结果已保存到 {output_file}")
    print("您可以查看抓取结果，确认后再进行WordPress导入。")

if __name__ == "__main__":
    main() 