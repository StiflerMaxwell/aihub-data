#!/usr/bin/env python3
"""
AI工具Firecrawl抓取器 - 最终版本
使用已处理的JSON数据进行抓取
"""

import requests
import json
import time
from typing import Dict, List, Optional

class FinalFirecrawlScraper:
    """最终版Firecrawl抓取器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.firecrawl.dev"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def load_tools_data(self) -> List[Dict]:
        """加载已处理的工具数据"""
        try:
            with open('ai_tools_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载工具数据失败: {e}")
            return []
    
    def load_schema(self) -> Dict:
        """加载抓取Schema"""
        try:
            with open('ai_tool_firecrawl_schema.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 无法加载完整Schema，使用简化版本: {e}")
            # 简化的Schema
            return {
                "type": "object",
                "properties": {
                    "short_introduction": {
                        "type": "string",
                        "description": "产品的简短介绍或描述"
                    },
                    "logo_img_url": {
                        "type": "string", 
                        "description": "产品Logo图片的URL地址"
                    },
                    "overview_img_url": {
                        "type": "string",
                        "description": "产品概览图片或截图的URL地址"
                    },
                    "primary_task": {
                        "type": "string",
                        "description": "产品的主要功能或用途"
                    },
                    "author_company": {
                        "type": "string",
                        "description": "开发这个产品的公司或作者名称"
                    },
                    "general_price_tag": {
                        "type": "string",
                        "description": "产品的价格信息，如免费、付费、订阅等"
                    }
                }
            }
    
    def scrape_tool(self, url: str, schema: Dict) -> Optional[Dict]:
        """抓取单个工具的详细信息"""
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
                else:
                    print(f"   ⚠️ 抓取成功但未提取到数据")
                    return None
            else:
                print(f"   ❌ 抓取失败 {response.status_code}")
                if response.status_code == 402:
                    print("   💳 API配额不足，请检查您的Firecrawl账户")
                return None
                
        except Exception as e:
            print(f"   ❌ 抓取异常: {e}")
            return None

def main():
    """主函数"""
    
    print("\n=== AI工具Firecrawl抓取器 - 最终版本 ===")
    print("使用已处理的JSON数据进行网站内容抓取\n")
    
    # 配置
    api_key = "fc-4a9ca9115114472d92ace77332cf0262"
    max_tools = 5  # 限制测试数量
    
    # 初始化抓取器
    scraper = FinalFirecrawlScraper(api_key)
    
    # 加载Schema
    schema = scraper.load_schema()
    print(f"✅ Schema加载完成，包含 {len(schema.get('properties', {}))} 个抓取字段")
    
    # 加载工具数据
    print("📁 加载已处理的工具数据...")
    tools_data = scraper.load_tools_data()
    
    if not tools_data:
        print("❌ 未找到工具数据，请先运行 csv_data_processor.py")
        return
    
    print(f"✅ 成功加载 {len(tools_data)} 个AI工具")
    
    # 限制处理数量（测试）
    if max_tools and len(tools_data) > max_tools:
        tools_data = tools_data[:max_tools]
        print(f"🔧 测试模式：限制处理前 {len(tools_data)} 个工具")
    
    # 显示将要抓取的工具
    print(f"\n📋 将要抓取的工具:")
    for i, tool in enumerate(tools_data, 1):
        print(f"  {i}. {tool['product_name']} ({tool['category']})")
        print(f"     🔗 {tool['url']}")
    
    # 确认继续
    print(f"\n准备开始抓取，每个工具间隔2秒...")
    input("按回车键继续，或Ctrl+C取消...")
    
    # 开始抓取
    print(f"\n🚀 开始抓取...\n")
    
    results = []
    success_count = 0
    total_fields_scraped = 0
    
    for index, tool in enumerate(tools_data, 1):
        print(f"📦 [{index}/{len(tools_data)}] {tool['product_name']}")
        print(f"🔗 {tool['url']}")
        print(f"📂 类别: {tool['category']}")
        
        # 抓取数据
        scraped_data = scraper.scrape_tool(tool['url'], schema)
        
        # 合并数据
        merged = tool.copy()
        
        if scraped_data:
            success_count += 1
            fields_count = len([v for v in scraped_data.values() if v])
            total_fields_scraped += fields_count
            
            merged['scraped_successfully'] = True
            merged['scraped_data'] = scraped_data
            merged['scraped_fields_count'] = fields_count
            
            print(f"   ✅ 抓取成功，获得 {fields_count} 个有效字段")
            
            # 显示抓取到的关键信息
            if scraped_data.get('short_introduction'):
                intro = scraped_data['short_introduction'][:80]
                print(f"   📝 简介: {intro}{'...' if len(scraped_data['short_introduction']) > 80 else ''}")
            
            if scraped_data.get('primary_task'):
                print(f"   🎯 功能: {scraped_data['primary_task']}")
            
            if scraped_data.get('author_company'):
                print(f"   🏢 公司: {scraped_data['author_company']}")
            
            if scraped_data.get('logo_img_url'):
                print(f"   🖼️ Logo: {scraped_data['logo_img_url']}")
        else:
            merged['scraped_successfully'] = False
            merged['scraped_data'] = None
            merged['scraped_fields_count'] = 0
            print("   ❌ 抓取失败或无数据")
        
        results.append(merged)
        
        # 进度显示
        progress = (index / len(tools_data)) * 100
        print(f"   📊 进度: {progress:.1f}% ({success_count}/{index} 成功)")
        
        # 延迟
        if index < len(tools_data):
            print("   ⏳ 等待2秒...\n")
            time.sleep(2)
    
    # 保存结果
    output_file = "scraped_ai_tools_complete.json"
    print(f"\n💾 保存完整结果到: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 保存仅抓取成功的数据
    successful_results = [r for r in results if r.get('scraped_successfully')]
    if successful_results:
        success_file = "scraped_ai_tools_success_only.json"
        with open(success_file, 'w', encoding='utf-8') as f:
            json.dump(successful_results, f, ensure_ascii=False, indent=2)
        print(f"💾 保存成功数据到: {success_file}")
    
    # 详细统计
    print(f"\n📊 抓取完成统计:")
    print(f"✅ 总计工具: {len(tools_data)}")
    print(f"✅ 抓取成功: {success_count}")
    print(f"❌ 抓取失败: {len(tools_data) - success_count}")
    print(f"📈 成功率: {success_count/len(tools_data)*100:.1f}%")
    print(f"📋 平均每个工具抓取字段: {total_fields_scraped/success_count:.1f}" if success_count > 0 else "📋 平均字段: 0")
    
    # 按类别统计
    category_stats = {}
    for result in results:
        category = result['category']
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'success': 0}
        category_stats[category]['total'] += 1
        if result.get('scraped_successfully'):
            category_stats[category]['success'] += 1
    
    print(f"\n📂 按类别统计:")
    for category, stats in category_stats.items():
        success_rate = (stats['success'] / stats['total']) * 100
        print(f"  {category}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
    
    print(f"\n✨ 抓取完成！")
    print(f"📄 完整数据: {output_file}")
    if successful_results:
        print(f"📄 成功数据: {success_file}")
    print(f"\n下一步：您可以查看抓取结果，然后使用WordPress自定义API进行导入。")

if __name__ == "__main__":
    main() 