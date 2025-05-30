#!/usr/bin/env python3
"""
测试抓取脚本 - 使用更容易抓取的网站
"""

import requests
import json
import time
from typing import Dict, List, Optional

def test_firecrawl_basic():
    """测试基础的Firecrawl功能"""
    
    api_key = "fc-4a9ca9115114472d92ace77332cf0262"
    base_url = "https://api.firecrawl.dev"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 使用一些更简单的网站进行测试
    test_sites = [
        {
            "name": "Example.com",
            "url": "https://example.com",
            "expected": "Example Domain"
        },
        {
            "name": "GitHub",
            "url": "https://github.com",
            "expected": "GitHub"
        },
        {
            "name": "Wikipedia首页",
            "url": "https://en.wikipedia.org/wiki/Main_Page",
            "expected": "Wikipedia"
        }
    ]
    
    # 简单的Schema
    simple_schema = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "网页标题"
            },
            "description": {
                "type": "string", 
                "description": "网页描述或主要内容"
            },
            "main_heading": {
                "type": "string",
                "description": "主要标题或heading"
            }
        }
    }
    
    print("🧪 测试Firecrawl基础功能...\n")
    
    for i, site in enumerate(test_sites, 1):
        print(f"📦 [{i}/{len(test_sites)}] 测试: {site['name']}")
        print(f"🔗 URL: {site['url']}")
        
        try:
            payload = {
                "url": site['url'],
                "formats": ["extract"],
                "extract": {"schema": simple_schema}
            }
            
            response = requests.post(
                f"{base_url}/v1/scrape",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API调用成功")
                print(f"🔍 Success: {data.get('success')}")
                
                if data.get("success") and "extract" in data:
                    extracted = data["extract"]
                    print(f"📄 提取字段数: {len(extracted)}")
                    
                    # 显示提取的数据
                    for key, value in extracted.items():
                        if value:
                            print(f"   {key}: {value[:100]}{'...' if len(str(value)) > 100 else ''}")
                    
                    if any(v for v in extracted.values() if v):
                        print("✅ 数据提取成功")
                    else:
                        print("⚠️ 提取成功但数据为空")
                else:
                    print("❌ 数据提取失败")
                    print(f"响应: {json.dumps(data, indent=2)[:500]}")
                    
            elif response.status_code == 402:
                print("💳 API配额不足")
                break
            else:
                print(f"❌ API调用失败: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"错误信息: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"响应文本: {response.text[:200]}")
                    
        except Exception as e:
            print(f"❌ 异常: {e}")
        
        print("-" * 50)
        if i < len(test_sites):
            time.sleep(2)
    
    print("\n🏁 基础测试完成!")

def test_ai_tools_from_list():
    """从我们的列表中选择一些可能更容易抓取的AI工具"""
    
    api_key = "fc-4a9ca9115114472d92ace77332cf0262"
    base_url = "https://api.firecrawl.dev"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 选择一些相对简单的AI工具网站
    test_tools = [
        {
            "name": "SeaArt",
            "url": "https://www.seaart.ai",
            "category": "AI Image Generator"
        },
        {
            "name": "Gamma",
            "url": "https://gamma.app", 
            "category": "AI Presentation Maker"
        }
    ]
    
    # AI工具特定的Schema
    ai_schema = {
        "type": "object", 
        "properties": {
            "product_name": {
                "type": "string",
                "description": "AI工具的产品名称"
            },
            "description": {
                "type": "string",
                "description": "产品描述或主要功能介绍"
            },
            "company": {
                "type": "string", 
                "description": "开发公司名称"
            },
            "pricing": {
                "type": "string",
                "description": "价格信息，如Free、Paid等"
            },
            "main_feature": {
                "type": "string",
                "description": "主要功能或特色"
            }
        }
    }
    
    print("\n🎯 测试AI工具抓取...\n")
    
    for i, tool in enumerate(test_tools, 1):
        print(f"🤖 [{i}/{len(test_tools)}] 测试: {tool['name']}")
        print(f"🔗 URL: {tool['url']}")
        print(f"📂 类别: {tool['category']}")
        
        try:
            payload = {
                "url": tool['url'],
                "formats": ["extract"],
                "extract": {"schema": ai_schema}
            }
            
            response = requests.post(
                f"{base_url}/v1/scrape",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "extract" in data:
                    extracted = data["extract"]
                    print(f"✅ 抓取成功，获得 {len(extracted)} 个字段")
                    
                    # 显示关键信息
                    for key, value in extracted.items():
                        if value and str(value).strip():
                            print(f"   📝 {key}: {str(value)[:80]}{'...' if len(str(value)) > 80 else ''}")
                    
                    # 保存单个测试结果
                    test_result = {
                        "tool_info": tool,
                        "scraped_data": extracted,
                        "success": True
                    }
                    
                    filename = f"test_result_{tool['name'].lower().replace(' ', '_')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(test_result, f, ensure_ascii=False, indent=2)
                    print(f"💾 结果保存到: {filename}")
                    
                else:
                    print("⚠️ 抓取成功但无数据提取")
            else:
                print(f"❌ 抓取失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")
        
        print("-" * 50)
        if i < len(test_tools):
            time.sleep(3)
    
    print("\n🏁 AI工具测试完成!")

def main():
    """主函数"""
    print("=== Firecrawl抓取测试 ===")
    print("测试不同类型的网站以验证抓取功能\n")
    
    # 选择测试类型
    print("选择测试类型:")
    print("1. 基础网站测试（简单网站）")
    print("2. AI工具测试（从我们的列表中）")
    print("3. 全部测试")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "1":
        test_firecrawl_basic()
    elif choice == "2":
        test_ai_tools_from_list()
    elif choice == "3":
        test_firecrawl_basic()
        test_ai_tools_from_list()
    else:
        print("❌ 无效选择，运行全部测试...")
        test_firecrawl_basic()
        test_ai_tools_from_list()

if __name__ == "__main__":
    main() 