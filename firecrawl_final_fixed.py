#!/usr/bin/env python3
"""
最终修正的Firecrawl脚本
解决API格式问题，使用正确的formats和jsonOptions配合
"""

import requests
import json
import time
from typing import Dict, List, Optional

def test_final_corrected_api():
    """最终修正的API测试"""
    
    api_key = "fc-4a9ca9115114472d92ace77332cf0262"
    url = "https://api.firecrawl.dev/v1/scrape"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    test_url = "https://example.com"
    
    print("🔧 最终修正的Firecrawl API测试...")
    print(f"🔗 测试网站: {test_url}")
    print(f"📍 API端点: {url}\n")
    
    # 测试1: 纯Markdown抓取（无Schema）
    print("📦 测试1: 纯Markdown抓取")
    
    markdown_payload = {
        "url": test_url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "timeout": 30000
    }
    
    try:
        response = requests.post(url, json=markdown_payload, headers=headers, timeout=45)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Markdown抓取成功")
            print(f"🔍 Success: {data.get('success')}")
            
            if data.get('data') and data['data'].get('markdown'):
                markdown_content = data['data']['markdown']
                print(f"📄 Markdown长度: {len(markdown_content)}")
                print(f"📝 内容预览:\n{markdown_content[:300]}...")
            else:
                print("⚠️ 未获取到Markdown内容")
                print(f"Data结构: {list(data.get('data', {}).keys())}")
        else:
            print(f"❌ Markdown抓取失败")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    print("-" * 60)
    time.sleep(3)
    
    # 测试2: 结构化提取（formats包含extract）
    print("📦 测试2: 结构化数据提取")
    
    extraction_schema = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "网页标题"
            },
            "main_content": {
                "type": "string",
                "description": "主要内容"
            }
        }
    }
    
    # 关键：formats必须包含extract，并且提供jsonOptions
    extract_payload = {
        "url": test_url,
        "formats": ["markdown", "extract"],  # 包含extract格式
        "onlyMainContent": True,
        "timeout": 30000,
        "jsonOptions": {
            "schema": extraction_schema
        }
    }
    
    try:
        response = requests.post(url, json=extract_payload, headers=headers, timeout=45)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 结构化提取成功")
            print(f"🔍 Success: {data.get('success')}")
            
            if data.get('data'):
                print(f"📋 数据字段: {list(data['data'].keys())}")
                
                # 检查提取结果
                if 'extract' in data['data']:
                    extract_data = data['data']['extract']
                    print(f"🎯 提取结果: {json.dumps(extract_data, indent=2, ensure_ascii=False)}")
                
                # 显示markdown（如果有）
                if 'markdown' in data['data']:
                    markdown = data['data']['markdown']
                    print(f"📄 同时获得Markdown (长度: {len(markdown)})")
            else:
                print("⚠️ 未获取到数据")
        else:
            print(f"❌ 结构化提取失败")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")

def test_ai_tool_corrected():
    """测试AI工具抓取（使用修正的格式）"""
    
    api_key = "fc-4a9ca9115114472d92ace77332cf0262"
    url = "https://api.firecrawl.dev/v1/scrape"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 选择一个相对简单的AI工具进行测试
    test_tools = [
        {
            "name": "Gamma", 
            "url": "https://gamma.app"
        },
        {
            "name": "SeaArt",
            "url": "https://www.seaart.ai"
        }
    ]
    
    # AI工具Schema
    ai_schema = {
        "type": "object",
        "properties": {
            "product_name": {
                "type": "string",
                "description": "AI工具的产品名称"
            },
            "description": {
                "type": "string",
                "description": "产品描述"
            },
            "company": {
                "type": "string",
                "description": "开发公司"
            },
            "pricing": {
                "type": "string",
                "description": "价格信息"
            },
            "features": {
                "type": "string",
                "description": "主要功能"
            }
        }
    }
    
    print(f"\n🎯 测试AI工具抓取（修正格式）\n")
    
    for i, tool in enumerate(test_tools, 1):
        print(f"🤖 [{i}/{len(test_tools)}] 测试: {tool['name']}")
        print(f"🔗 URL: {tool['url']}")
        
        # 正确的payload格式
        payload = {
            "url": tool['url'],
            "formats": ["markdown", "extract"],  # 同时获取markdown和extract
            "onlyMainContent": True,
            "timeout": 60000,
            "jsonOptions": {
                "schema": ai_schema,
                "systemPrompt": "提取AI工具的基本信息",
                "prompt": "从网页中提取产品名称、描述、公司、价格和主要功能"
            },
            "waitFor": 5000,  # 等待5秒让页面完全加载
            "blockAds": True
        }
        
        try:
            print("🚀 开始抓取...")
            response = requests.post(url, json=payload, headers=headers, timeout=90)
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 抓取成功")
                
                if data.get('data'):
                    # 显示提取的结构化数据
                    if 'extract' in data['data'] and data['data']['extract']:
                        extract_result = data['data']['extract']
                        print(f"🎯 AI工具信息:")
                        for key, value in extract_result.items():
                            if value:
                                print(f"   📝 {key}: {value}")
                        
                        # 保存结果
                        filename = f"final_corrected_{tool['name'].lower()}.json"
                        result = {
                            "tool": tool,
                            "extracted_data": extract_result,
                            "success": True,
                            "method": "final_corrected_api"
                        }
                        
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)
                        print(f"💾 结果保存到: {filename}")
                    else:
                        print("⚠️ 未获取到提取数据")
                        
                    # 显示markdown信息
                    if 'markdown' in data['data']:
                        markdown = data['data']['markdown']
                        print(f"📄 Markdown长度: {len(markdown)}")
                        if len(markdown) > 100:
                            print(f"📝 内容样例: {markdown[:200]}...")
                else:
                    print("⚠️ 无数据返回")
                    
            elif response.status_code == 402:
                print("💳 API配额不足")
                break
            else:
                print(f"❌ 抓取失败: {response.status_code}")
                print(f"错误: {response.text}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")
        
        print("-" * 50)
        if i < len(test_tools):
            print("⏳ 等待5秒继续下一个...\n")
            time.sleep(5)

def main():
    """主函数"""
    print("=== 最终修正的Firecrawl API测试 ===")
    print("解决formats和jsonOptions匹配问题\n")
    
    print("选择测试:")
    print("1. 基础API测试")
    print("2. AI工具抓取测试")
    print("3. 全部测试")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "1":
        test_final_corrected_api()
    elif choice == "2":
        test_ai_tool_corrected()
    elif choice == "3":
        test_final_corrected_api()
        test_ai_tool_corrected()
    else:
        print("❌ 无效选择，运行全部测试...")
        test_final_corrected_api()
        test_ai_tool_corrected()

if __name__ == "__main__":
    main() 