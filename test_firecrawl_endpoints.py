#!/usr/bin/env python3
"""
测试Firecrawl不同端点的脚本
基于官方文档验证正确的API使用方式
"""

import requests
import json
import time
from typing import Dict, List, Optional

def test_firecrawl_endpoints():
    """测试Firecrawl的不同API端点"""
    
    api_key = "fc-4a9ca9115114472d92ace77332cf0262"
    base_url = "https://api.firecrawl.dev"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    test_url = "https://example.com"  # 简单的测试网站
    
    print("🧪 测试Firecrawl不同API端点...\n")
    
    # 测试1: 基础Scrape端点
    print("📦 测试1: 基础Scrape端点")
    print(f"端点: POST {base_url}/scrape")
    
    try:
        scrape_payload = {
            "url": test_url,
            "formats": ["markdown", "html"]
        }
        
        response = requests.post(
            f"{base_url}/scrape",
            headers=headers,
            json=scrape_payload,
            timeout=30
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Scrape成功")
            print(f"🔍 Success: {data.get('success')}")
            if data.get('data'):
                print(f"📄 Markdown长度: {len(data['data'].get('markdown', ''))}")
                print(f"📄 HTML长度: {len(data['data'].get('html', ''))}")
        else:
            print(f"❌ Scrape失败")
            try:
                error_data = response.json()
                print(f"错误: {json.dumps(error_data, indent=2)}")
            except:
                print(f"响应文本: {response.text}")
                
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    print("-" * 60)
    time.sleep(2)
    
    # 测试2: Extract端点（结构化提取）
    print("📦 测试2: Extract端点（结构化提取）")
    print(f"端点: POST {base_url}/extract")
    
    try:
        extract_schema = {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "网页标题"
                },
                "description": {
                    "type": "string",
                    "description": "网页描述"
                }
            }
        }
        
        extract_payload = {
            "url": test_url,
            "schema": extract_schema
        }
        
        response = requests.post(
            f"{base_url}/extract",
            headers=headers,
            json=extract_payload,
            timeout=30
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Extract成功")
            print(f"🔍 Success: {data.get('success')}")
            if data.get('data'):
                extracted = data['data']
                print(f"📄 提取数据: {json.dumps(extracted, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Extract失败")
            try:
                error_data = response.json()
                print(f"错误: {json.dumps(error_data, indent=2)}")
            except:
                print(f"响应文本: {response.text}")
                
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    print("-" * 60)
    time.sleep(2)
    
    # 测试3: Scrape with Extract（组合方式）
    print("📦 测试3: Scrape with Extract（组合方式）")
    print(f"端点: POST {base_url}/scrape")
    
    try:
        combined_schema = {
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
        
        combined_payload = {
            "url": test_url,
            "formats": ["extract"],
            "extract": {
                "schema": combined_schema
            }
        }
        
        response = requests.post(
            f"{base_url}/scrape",
            headers=headers,
            json=combined_payload,
            timeout=30
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Scrape+Extract成功")
            print(f"🔍 Success: {data.get('success')}")
            if data.get('data') and data['data'].get('extract'):
                extracted = data['data']['extract']
                print(f"📄 提取数据: {json.dumps(extracted, indent=2, ensure_ascii=False)}")
            else:
                print(f"⚠️ 无提取数据")
                print(f"响应结构: {list(data.keys())}")
                if data.get('data'):
                    print(f"Data结构: {list(data['data'].keys())}")
        else:
            print(f"❌ Scrape+Extract失败")
            try:
                error_data = response.json()
                print(f"错误: {json.dumps(error_data, indent=2)}")
            except:
                print(f"响应文本: {response.text}")
                
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    print("-" * 60)
    
    # 测试4: 检查账户使用情况
    print("📦 测试4: 检查账户使用情况")
    print(f"端点: GET {base_url}/credit-usage")
    
    try:
        response = requests.get(
            f"{base_url}/credit-usage",
            headers=headers,
            timeout=30
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 账户信息获取成功")
            print(f"💳 账户数据: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ 账户信息获取失败")
            
    except Exception as e:
        print(f"❌ 异常: {e}")

def test_ai_tool_with_correct_endpoint():
    """使用正确的端点测试AI工具抓取"""
    
    api_key = "fc-4a9ca9115114472d92ace77332cf0262"
    base_url = "https://api.firecrawl.dev"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 测试一个相对简单的AI工具
    test_tool = {
        "name": "Gamma",
        "url": "https://gamma.app"
    }
    
    print(f"\n🎯 使用正确端点测试AI工具: {test_tool['name']}")
    print(f"🔗 URL: {test_tool['url']}\n")
    
    # AI工具Schema
    ai_schema = {
        "type": "object",
        "properties": {
            "product_name": {
                "type": "string",
                "description": "产品名称"
            },
            "description": {
                "type": "string",
                "description": "产品描述"
            },
            "company": {
                "type": "string",
                "description": "公司名称"
            },
            "pricing": {
                "type": "string",
                "description": "价格信息"
            }
        }
    }
    
    # 方法1: 使用Extract端点
    print("📋 方法1: 使用Extract端点")
    try:
        extract_payload = {
            "url": test_tool['url'],
            "schema": ai_schema
        }
        
        response = requests.post(
            f"{base_url}/extract",
            headers=headers,
            json=extract_payload,
            timeout=60
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                print(f"✅ Extract成功")
                print(f"📄 提取数据: {json.dumps(data['data'], indent=2, ensure_ascii=False)}")
            else:
                print(f"⚠️ Extract无数据")
        else:
            print(f"❌ Extract失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Extract异常: {e}")
    
    print("-" * 40)
    
    # 方法2: 使用Scrape+Extract组合
    print("📋 方法2: 使用Scrape+Extract组合")
    try:
        scrape_payload = {
            "url": test_tool['url'],
            "formats": ["extract"],
            "extract": {
                "schema": ai_schema
            }
        }
        
        response = requests.post(
            f"{base_url}/scrape",
            headers=headers,
            json=scrape_payload,
            timeout=60
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Scrape+Extract成功")
                if data.get('data') and data['data'].get('extract'):
                    print(f"📄 提取数据: {json.dumps(data['data']['extract'], indent=2, ensure_ascii=False)}")
                else:
                    print(f"⚠️ 无提取数据")
                    print(f"可用字段: {list(data.get('data', {}).keys())}")
            else:
                print(f"⚠️ Scrape+Extract未成功")
        else:
            print(f"❌ Scrape+Extract失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Scrape+Extract异常: {e}")

def main():
    """主函数"""
    print("=== Firecrawl API端点测试 ===")
    print("基于官方文档测试正确的API使用方式\n")
    
    print("选择测试:")
    print("1. 测试所有端点")
    print("2. 测试AI工具抓取")
    print("3. 全部测试")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "1":
        test_firecrawl_endpoints()
    elif choice == "2":
        test_ai_tool_with_correct_endpoint()
    elif choice == "3":
        test_firecrawl_endpoints()
        test_ai_tool_with_correct_endpoint()
    else:
        print("❌ 无效选择，运行全部测试...")
        test_firecrawl_endpoints()
        test_ai_tool_with_correct_endpoint()

if __name__ == "__main__":
    main() 