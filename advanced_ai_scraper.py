#!/usr/bin/env python3
"""
高级AI工具抓取器
基于详细Schema抓取并为WordPress CPT+ACF格式化数据
"""

import requests
import json
import time
from typing import Dict, List, Optional

class AdvancedAIScraper:
    """高级AI工具抓取器，支持WordPress CPT+ACF结构"""
    
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
    
    def load_detailed_schema(self) -> Dict:
        """加载详细的抓取Schema"""
        try:
            with open('ai_tool_detailed_schema.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 无法加载详细Schema: {e}")
            # 如果详细Schema不可用，使用简化版本
            return self.get_fallback_schema()
    
    def get_fallback_schema(self) -> Dict:
        """备用简化Schema"""
        return {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "产品名称或网站标题"
                },
                "description": {
                    "type": "string", 
                    "description": "产品描述或网站主要描述"
                },
                "company": {
                    "type": "string",
                    "description": "公司或开发者名称"
                },
                "pricing": {
                    "type": "string",
                    "description": "价格信息，如Free、Paid、Freemium等"
                },
                "features": {
                    "type": "string",
                    "description": "主要功能特性"
                },
                "logo_url": {
                    "type": "string",
                    "description": "Logo图片URL"
                }
            }
        }
    
    def scrape_tool_with_retry(self, url: str, schema: Dict, max_retries: int = 2) -> Optional[Dict]:
        """带重试机制的抓取"""
        
        for attempt in range(max_retries + 1):
            try:
                # 先尝试详细Schema
                if attempt == 0:
                    current_schema = schema
                else:
                    # 如果第一次失败，使用简化Schema
                    current_schema = self.get_fallback_schema()
                    print(f"   🔄 重试 {attempt}/{max_retries} - 使用简化Schema")
                
                payload = {
                    "url": url,
                    "formats": ["extract"],
                    "extract": {"schema": current_schema}
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
                        extracted = data["extract"]
                        if extracted and any(v for v in extracted.values() if v):  # 确保有实际数据
                            return extracted
                        else:
                            print(f"   ⚠️ 尝试 {attempt + 1}: 抓取成功但数据为空")
                    else:
                        print(f"   ⚠️ 尝试 {attempt + 1}: 抓取响应无效")
                elif response.status_code == 402:
                    print(f"   💳 API配额不足，请检查Firecrawl账户")
                    break
                else:
                    print(f"   ❌ 尝试 {attempt + 1}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ 尝试 {attempt + 1}: 异常 {e}")
            
            # 在重试前等待
            if attempt < max_retries:
                time.sleep(2)
        
        return None
    
    def format_for_wordpress(self, csv_data: Dict, scraped_data: Optional[Dict]) -> Dict:
        """格式化数据为WordPress CPT+ACF结构"""
        
        # WordPress CPT基础字段
        wordpress_data = {
            "cpt_fields": {
                "post_title": csv_data.get('product_name', ''),
                "post_content": "",  # 将在下面填充
                "post_name": "",  # 将自动生成slug
                "post_status": "draft",  # 默认为草稿
                "post_type": "ai_tool"
            },
            "taxonomies": {
                "ai_tool_category": [csv_data.get('category', '')],
                "ai_tool_tag": []  # 将从抓取数据中提取
            },
            "acf_fields": {}
        }
        
        if scraped_data:
            # 基本信息字段组
            basic_info = {}
            if isinstance(scraped_data.get('basic_info'), dict):
                basic_info = scraped_data['basic_info']
            else:
                # 如果是扁平结构，映射到基本信息
                basic_info = {
                    'product_name': scraped_data.get('product_name', ''),
                    'product_introduction': scraped_data.get('description', ''),
                    'author_company': scraped_data.get('company', ''),
                    'logo_img_url': scraped_data.get('logo_url', ''),
                    'primary_task': csv_data.get('category', '')
                }
            
            # 设置post_content
            wordpress_data["cpt_fields"]["post_content"] = basic_info.get('product_introduction', basic_info.get('product_story', ''))
            
            # ACF字段组1：基本信息
            wordpress_data["acf_fields"]["basic_info"] = {
                "product_url": csv_data.get('url', ''),
                "logo_img_url": basic_info.get('logo_img_url', ''),
                "overview_img_url": basic_info.get('overview_img_url', ''),
                "product_story": basic_info.get('product_story', ''),
                "author_company": basic_info.get('author_company', ''),
                "popularity_score": basic_info.get('popularity_score', ''),
                "initial_release_date": basic_info.get('initial_release_date', ''),
                "number_of_tools_by_author": basic_info.get('number_of_tools_by_author', ''),
                "is_verified_tool": basic_info.get('is_verified_tool', False)
            }
            
            # ACF字段组2：定价
            pricing = scraped_data.get('pricing', {})
            if isinstance(pricing, str):
                pricing = {"general_price_tag": pricing}
            
            wordpress_data["acf_fields"]["pricing"] = {
                "general_price_tag": pricing.get('general_price_tag', scraped_data.get('pricing', '')),
                "pricing_model": pricing.get('pricing_model', ''),
                "paid_options_from": pricing.get('paid_options_from', ''),
                "billing_frequency": pricing.get('billing_frequency', ''),
                "currency": pricing.get('currency', '')
            }
            
            # ACF字段组3：功能特性
            features = scraped_data.get('features', {})
            if isinstance(features, str):
                features = {"description": features}
            
            wordpress_data["acf_fields"]["features"] = {
                "inputs": features.get('inputs', []),
                "outputs": features.get('outputs', []),
                "pros": features.get('pros', []),
                "cons": features.get('cons', []),
                "related_tasks": features.get('related_tasks', [])
            }
            
            # ACF字段组4：评分评论
            reviews = scraped_data.get('reviews', {})
            wordpress_data["acf_fields"]["reviews"] = {
                "user_ratings_count": reviews.get('user_ratings_count', ''),
                "average_rating": reviews.get('average_rating', ''),
                "how_would_you_rate_text": reviews.get('how_would_you_rate_text', '')
            }
            
            # ACF字段组5：工作影响
            wordpress_data["acf_fields"]["job_impacts"] = scraped_data.get('job_impacts', [])
            
            # ACF字段组6：替代方案
            wordpress_data["acf_fields"]["alternatives"] = scraped_data.get('alternatives', [])
            
            # ACF字段组7：版本发布
            wordpress_data["acf_fields"]["releases"] = scraped_data.get('releases', [])
            
            # ACF字段组8：相关推荐
            see_also = scraped_data.get('see_also', {})
            wordpress_data["acf_fields"]["see_also"] = {
                "featured_matches": see_also.get('featured_matches', []),
                "other_tools": see_also.get('other_tools', [])
            }
            
            # 提取标签
            if basic_info.get('tag'):
                tags = basic_info['tag'].split(',')
                wordpress_data["taxonomies"]["ai_tool_tag"] = [tag.strip() for tag in tags if tag.strip()]
        
        # 抓取元数据
        wordpress_data["scrape_metadata"] = {
            "scraped_successfully": scraped_data is not None,
            "scraped_fields_count": len(scraped_data) if scraped_data else 0,
            "scrape_timestamp": int(time.time()),
            "source_url": csv_data.get('url', '')
        }
        
        return wordpress_data

def main():
    """主函数"""
    
    print("\n=== 高级AI工具抓取器 ===")
    print("基于详细Schema，为WordPress CPT+ACF格式化数据\n")
    
    # 配置
    api_key = "fc-4a9ca9115114472d92ace77332cf0262"
    max_tools = 3  # 测试数量
    
    # 初始化抓取器
    scraper = AdvancedAIScraper(api_key)
    
    # 加载Schema
    schema = scraper.load_detailed_schema()
    schema_fields = len(schema.get('properties', {}))
    print(f"✅ Schema加载完成，包含 {schema_fields} 个主要字段组")
    
    # 加载工具数据
    print("📁 加载已处理的工具数据...")
    tools_data = scraper.load_tools_data()
    
    if not tools_data:
        print("❌ 未找到工具数据")
        return
    
    print(f"✅ 成功加载 {len(tools_data)} 个AI工具")
    
    # 限制处理数量
    if max_tools and len(tools_data) > max_tools:
        tools_data = tools_data[:max_tools]
        print(f"🔧 测试模式：限制处理前 {len(tools_data)} 个工具")
    
    # 显示将要抓取的工具
    print(f"\n📋 将要抓取的工具:")
    for i, tool in enumerate(tools_data, 1):
        print(f"  {i}. {tool['product_name']} ({tool['category']})")
        print(f"     🔗 {tool['url']}")
    
    # 确认继续
    print(f"\n准备开始高级抓取...")
    input("按回车键继续，或Ctrl+C取消...")
    
    # 开始抓取
    print(f"\n🚀 开始抓取...\n")
    
    wordpress_results = []
    success_count = 0
    
    for index, tool in enumerate(tools_data, 1):
        print(f"📦 [{index}/{len(tools_data)}] {tool['product_name']}")
        print(f"🔗 {tool['url']}")
        print(f"📂 类别: {tool['category']}")
        
        # 抓取数据（带重试）
        scraped_data = scraper.scrape_tool_with_retry(tool['url'], schema)
        
        # 格式化为WordPress结构
        wp_data = scraper.format_for_wordpress(tool, scraped_data)
        
        if scraped_data:
            success_count += 1
            fields_count = wp_data["scrape_metadata"]["scraped_fields_count"]
            print(f"   ✅ 抓取成功，获得 {fields_count} 个字段")
            
            # 显示关键抓取信息
            basic_info = wp_data["acf_fields"].get("basic_info", {})
            if basic_info.get("author_company"):
                print(f"   🏢 公司: {basic_info['author_company']}")
            
            pricing = wp_data["acf_fields"].get("pricing", {})
            if pricing.get("general_price_tag"):
                print(f"   💰 价格: {pricing['general_price_tag']}")
                
            if wp_data["cpt_fields"]["post_content"]:
                content_preview = wp_data["cpt_fields"]["post_content"][:100]
                print(f"   📝 内容: {content_preview}{'...' if len(wp_data['cpt_fields']['post_content']) > 100 else ''}")
        else:
            print("   ❌ 抓取失败")
        
        wordpress_results.append(wp_data)
        
        # 进度显示
        progress = (index / len(tools_data)) * 100
        print(f"   📊 进度: {progress:.1f}% ({success_count}/{index} 成功)")
        
        # 延迟
        if index < len(tools_data):
            print("   ⏳ 等待3秒...\n")
            time.sleep(3)
    
    # 保存WordPress格式的结果
    wp_output_file = "wordpress_ai_tools_data.json"
    print(f"\n💾 保存WordPress格式数据到: {wp_output_file}")
    
    with open(wp_output_file, 'w', encoding='utf-8') as f:
        json.dump(wordpress_results, f, ensure_ascii=False, indent=2)
    
    # 保存仅成功的数据
    successful_results = [r for r in wordpress_results if r["scrape_metadata"]["scraped_successfully"]]
    if successful_results:
        success_file = "wordpress_ai_tools_success.json"
        with open(success_file, 'w', encoding='utf-8') as f:
            json.dump(successful_results, f, ensure_ascii=False, indent=2)
        print(f"💾 保存成功数据到: {success_file}")
    
    # 统计报告
    print(f"\n📊 抓取完成统计:")
    print(f"✅ 总计工具: {len(tools_data)}")
    print(f"✅ 抓取成功: {success_count}")
    print(f"❌ 抓取失败: {len(tools_data) - success_count}")
    print(f"📈 成功率: {success_count/len(tools_data)*100:.1f}%")
    
    # WordPress字段统计
    if successful_results:
        print(f"\n📋 WordPress数据结构:")
        sample = successful_results[0]
        print(f"   📄 CPT字段: {len(sample['cpt_fields'])}")
        print(f"   🏷️ 分类法: {len(sample['taxonomies'])}")
        print(f"   🔧 ACF字段组: {len(sample['acf_fields'])}")
        
        # 显示ACF字段组
        for group_name in sample['acf_fields'].keys():
            print(f"      - {group_name}")
    
    print(f"\n✨ 抓取完成！")
    print(f"📄 WordPress数据: {wp_output_file}")
    if successful_results:
        print(f"📄 成功数据: {success_file}")
    print(f"\n🚀 下一步：可以使用WordPress自定义API导入这些数据。")

if __name__ == "__main__":
    main() 