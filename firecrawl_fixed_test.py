#!/usr/bin/env python3
"""
修正的Firecrawl测试脚本
使用官方文档的正确API格式
"""

import requests
import json
import time
from typing import Dict, List, Optional

def test_corrected_firecrawl():
    """使用正确的API格式测试Firecrawl"""
    
    api_key = "fc-4a9ca9115114472d92ace77332cf0262"
    
    # 正确的端点 - 包含 v1
    url = "https://api.firecrawl.dev/v1/scrape"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 简单测试网站
    test_url = "https://example.com"
    
    print("🔧 使用修正的Firecrawl API格式测试...")
    print(f"🔗 测试网站: {test_url}")
    print(f"📍 API端点: {url}\n")
    
    # 测试1: 基础Markdown抓取
    print("📦 测试1: 基础Markdown抓取")
    
    basic_payload = {
        "url": test_url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "timeout": 30000
    }
    
    try:
        response = requests.post(url, json=basic_payload, headers=headers, timeout=30)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 基础抓取成功")
            print(f"🔍 Success: {data.get('success')}")
            
            if data.get('data') and data['data'].get('markdown'):
                markdown_content = data['data']['markdown']
                print(f"📄 Markdown内容长度: {len(markdown_content)}")
                print(f"📝 内容预览: {markdown_content[:200]}...")
            else:
                print("⚠️ 未获取到Markdown内容")
        else:
            print(f"❌ 基础抓取失败")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    print("-" * 60)
    time.sleep(2)
    
    # 测试2: 使用Schema进行结构化提取
    print("📦 测试2: 结构化数据提取（正确Schema位置）")
    
    # 简单的Schema
    test_schema = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "网页的主标题"
            },
            "description": {
                "type": "string",
                "description": "网页的描述或主要内容"
            },
            "main_heading": {
                "type": "string",
                "description": "页面的主要标题或H1标签"
            }
        }
    }
    
    # 正确的payload格式
    schema_payload = {
        "url": test_url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "timeout": 30000,
        "jsonOptions": {
            "schema": test_schema  # Schema放在jsonOptions中
        }
    }
    
    try:
        response = requests.post(url, json=schema_payload, headers=headers, timeout=30)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 结构化提取成功")
            print(f"🔍 Success: {data.get('success')}")
            
            # 检查提取的结构化数据
            if data.get('data'):
                if 'llm_extraction' in data['data']:
                    extraction = data['data']['llm_extraction']
                    print(f"🎯 LLM提取数据: {json.dumps(extraction, indent=2, ensure_ascii=False)}")
                elif 'extract' in data['data']:
                    extraction = data['data']['extract']
                    print(f"🎯 提取数据: {json.dumps(extraction, indent=2, ensure_ascii=False)}")
                else:
                    print(f"📋 可用字段: {list(data['data'].keys())}")
                    print(f"📄 完整响应: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
            else:
                print("⚠️ 未获取到数据")
        else:
            print(f"❌ 结构化提取失败")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")

def test_ai_tool_with_corrected_api():
    """使用修正的API测试AI工具抓取"""
    
    api_key = "fc-4a9ca9115114472d92ace77332cf0262"
    url = "https://api.firecrawl.dev/v1/scrape"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 测试AI工具
    test_tool = {
        "name": "Gamma",
        "url": "https://gamma.app"
    }
    
    print(f"\n🎯 使用修正API测试AI工具: {test_tool['name']}")
    print(f"🔗 URL: {test_tool['url']}\n")
    
    # AI工具专用Schema
    ai_schema = {
        "type": "object",
        "properties": {
            "product_name": {
                "type": "string",
                "description": "AI工具的产品名称"
            },
            "description": {
                "type": "string",
                "description": "产品的主要描述或介绍"
            },
            "company": {
                "type": "string",
                "description": "开发这个AI工具的公司名称"
            },
            "pricing": {
                "type": "string",
                "description": "价格信息，如免费、付费、订阅等"
            },
            "main_features": {
                "type": "string",
                "description": "主要功能特性"
            },
            "use_cases": {
                "type": "string",
                "description": "主要用途或使用场景"
            }
        }
    }
    
    # 正确的payload
    ai_payload = {
        "url": test_tool['url'],
        "formats": ["markdown"],
        "onlyMainContent": True,
        "timeout": 60000,  # AI网站可能需要更长时间
        "jsonOptions": {
            "schema": ai_schema,
            "systemPrompt": "请从网页中提取AI工具的相关信息，包括产品名称、描述、公司、价格等。",
            "prompt": "分析这个AI工具网站并提取关键信息。"
        },
        "waitFor": 3000,  # 等待页面完全加载
        "blockAds": True  # 屏蔽广告
    }
    
    try:
        print("🚀 开始抓取AI工具信息...")
        response = requests.post(url, json=ai_payload, headers=headers, timeout=90)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI工具抓取成功")
            print(f"🔍 Success: {data.get('success')}")
            
            # 显示抓取结果
            if data.get('data'):
                # 尝试不同的提取字段名
                extraction_keys = ['llm_extraction', 'extract', 'structured_data', 'json']
                extracted_data = None
                
                for key in extraction_keys:
                    if key in data['data'] and data['data'][key]:
                        extracted_data = data['data'][key]
                        print(f"🎯 找到提取数据 (字段: {key})")
                        break
                
                if extracted_data:
                    print(f"📄 AI工具信息:")
                    print(json.dumps(extracted_data, indent=2, ensure_ascii=False))
                    
                    # 保存结果
                    result = {
                        "tool_info": test_tool,
                        "extracted_data": extracted_data,
                        "extraction_method": "corrected_api",
                        "success": True
                    }
                    
                    with open(f"corrected_api_result_{test_tool['name'].lower()}.json", 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print(f"💾 结果已保存")
                    
                else:
                    print(f"⚠️ 未找到提取数据")
                    print(f"📋 可用字段: {list(data['data'].keys())}")
                    
                    # 显示markdown内容的一部分用于调试
                    if 'markdown' in data['data']:
                        markdown = data['data']['markdown']
                        print(f"📄 Markdown长度: {len(markdown)}")
                        print(f"📝 内容预览: {markdown[:500]}...")
            else:
                print("⚠️ 响应中无数据字段")
                
        elif response.status_code == 402:
            print("💳 API配额不足")
        else:
            print(f"❌ AI工具抓取失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")

def main():
    """主函数"""
    print("=== 修正的Firecrawl API测试 ===")
    print("使用官方文档的正确API格式\n")
    
    print("选择测试:")
    print("1. 基础API格式测试")
    print("2. AI工具抓取测试")
    print("3. 全部测试")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "1":
        test_corrected_firecrawl()
    elif choice == "2":
        test_ai_tool_with_corrected_api()
    elif choice == "3":
        test_corrected_firecrawl()
        test_ai_tool_with_corrected_api()
    else:
        print("❌ 无效选择，运行全部测试...")
        test_corrected_firecrawl()
        test_ai_tool_with_corrected_api()

if __name__ == "__main__":
    main() 