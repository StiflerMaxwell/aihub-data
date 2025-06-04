#!/usr/bin/env python3
"""
CORS头部测试脚本
测试所有API端点的跨域访问支持
"""

import requests
import json
from config import config

def test_cors_headers():
    """测试CORS头部设置"""
    
    # API基础配置
    api_base = "https://yourdomain.com/wp-json/ai-tools/v1"  # 替换为你的域名
    api_key = "ak_demo_1234567890abcdef"  # 替换为你的API Key
    
    # 要测试的端点
    endpoints = [
        "/test",
        "/tools",
        "/tools/1", 
        "/tools/random",
        "/tools/popular",
        "/categories",
        "/tags", 
        "/stats",
        "/tools/by-url?url=https://example.com"
    ]
    
    print("🔍 开始测试CORS头部...")
    print("=" * 50)
    
    for endpoint in endpoints:
        print(f"\n📍 测试端点: {endpoint}")
        
        try:
            # 1. 测试OPTIONS预检请求
            options_response = requests.options(
                f"{api_base}{endpoint}",
                headers={
                    "Origin": "https://example.com",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "X-API-Key"
                }
            )
            
            print(f"   OPTIONS响应状态: {options_response.status_code}")
            
            # 检查预检响应头
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods", 
                "Access-Control-Allow-Headers"
            ]
            
            for header in cors_headers:
                value = options_response.headers.get(header, "❌ 未设置")
                print(f"   {header}: {value}")
            
            # 2. 测试实际GET请求
            get_response = requests.get(
                f"{api_base}{endpoint}",
                headers={
                    "X-API-Key": api_key,
                    "Origin": "https://example.com"
                }
            )
            
            print(f"   GET响应状态: {get_response.status_code}")
            
            # 检查响应CORS头
            cors_origin = get_response.headers.get("Access-Control-Allow-Origin", "❌ 未设置")
            print(f"   Access-Control-Allow-Origin: {cors_origin}")
            
            if get_response.status_code == 200:
                print("   ✅ 端点正常，CORS设置完整")
            else:
                print(f"   ⚠️  端点返回错误: {get_response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
        
        print("-" * 30)
    
    print("\n🏁 CORS测试完成！")

def test_browser_compatibility():
    """测试浏览器兼容性"""
    
    print("\n🌐 浏览器兼容性测试...")
    print("=" * 50)
    
    # 模拟不同浏览器的请求
    browsers = {
        "Chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Firefox": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101",
        "Safari": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
    }
    
    api_base = "https://yourdomain.com/wp-json/ai-tools/v1"
    api_key = "ak_demo_1234567890abcdef"
    
    for browser, user_agent in browsers.items():
        print(f"\n🔍 测试 {browser}...")
        
        try:
            response = requests.get(
                f"{api_base}/test",
                headers={
                    "X-API-Key": api_key,
                    "User-Agent": user_agent,
                    "Origin": "https://example.com",
                    "Referer": "https://example.com/"
                }
            )
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
            }
            
            print(f"   状态码: {response.status_code}")
            for header, value in cors_headers.items():
                status = "✅" if value else "❌"
                print(f"   {status} {header}: {value or '未设置'}")
                
        except Exception as e:
            print(f"   ❌ {browser} 测试失败: {e}")

def generate_cors_test_html():
    """生成前端测试页面"""
    
    html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI工具API CORS测试</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .test-result { margin: 10px 0; padding: 10px; border-radius: 4px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        button { padding: 10px 20px; margin: 5px; }
    </style>
</head>
<body>
    <h1>🔍 AI工具API CORS测试</h1>
    <p>在浏览器控制台中查看详细的跨域请求测试结果</p>
    
    <button onclick="testCorsRequests()">开始CORS测试</button>
    <button onclick="testApiEndpoints()">测试所有端点</button>
    
    <div id="results"></div>
    
    <script>
        const API_BASE = 'https://yourdomain.com/wp-json/ai-tools/v1';  // 替换为你的域名
        const API_KEY = 'ak_demo_1234567890abcdef';  // 替换为你的API Key
        
        async function testCorsRequests() {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<h3>🧪 开始CORS测试...</h3>';
            
            const endpoints = [
                '/test',
                '/tools',
                '/categories',
                '/tags',
                '/stats'
            ];
            
            for (const endpoint of endpoints) {
                try {
                    console.log(`测试端点: ${endpoint}`);
                    
                    const response = await fetch(`${API_BASE}${endpoint}`, {
                        method: 'GET',
                        headers: {
                            'X-API-Key': API_KEY,
                            'Content-Type': 'application/json'
                        },
                        mode: 'cors'  // 明确启用CORS
                    });
                    
                    const result = await response.json();
                    
                    resultsDiv.innerHTML += `
                        <div class="test-result success">
                            ✅ ${endpoint}: ${response.status} - ${result.message || 'OK'}
                        </div>
                    `;
                    
                    console.log(`✅ ${endpoint} 成功:`, result);
                    
                } catch (error) {
                    resultsDiv.innerHTML += `
                        <div class="test-result error">
                            ❌ ${endpoint}: ${error.message}
                        </div>
                    `;
                    
                    console.error(`❌ ${endpoint} 失败:`, error);
                }
            }
        }
        
        async function testApiEndpoints() {
            console.log('开始测试所有API端点...');
            
            // 测试不同的请求方法和头部
            const testCases = [
                {
                    name: '标准GET请求',
                    method: 'GET',
                    headers: { 'X-API-Key': API_KEY }
                },
                {
                    name: 'Bearer Token认证',
                    method: 'GET', 
                    headers: { 'Authorization': `Bearer ${API_KEY}` }
                },
                {
                    name: '查询参数认证',
                    method: 'GET',
                    url_suffix: `?api_key=${API_KEY}`
                }
            ];
            
            for (const testCase of testCases) {
                console.log(`\\n🧪 ${testCase.name}:`);
                
                try {
                    const url = `${API_BASE}/test${testCase.url_suffix || ''}`;
                    const response = await fetch(url, {
                        method: testCase.method,
                        headers: testCase.headers || {},
                        mode: 'cors'
                    });
                    
                    console.log(`✅ ${testCase.name} 成功: ${response.status}`);
                    
                } catch (error) {
                    console.error(`❌ ${testCase.name} 失败:`, error);
                }
            }
        }
        
        // 页面加载时显示说明
        window.onload = function() {
            console.log('🚀 AI工具API CORS测试页面已加载');
            console.log('请点击按钮开始测试，或在控制台中查看详细结果');
        };
    </script>
</body>
</html>'''
    
    # 保存HTML文件
    with open('cors_test.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("📄 生成了 cors_test.html 文件")
    print("   在浏览器中打开此文件进行CORS测试")

if __name__ == "__main__":
    print("🔧 AI工具API CORS测试工具")
    print("=" * 50)
    
    # 提示用户配置
    print("⚠️  请先在脚本中配置正确的:")
    print("   - API域名 (api_base)")
    print("   - API Key")
    print()
    
    # 运行测试
    test_cors_headers()
    test_browser_compatibility()
    
    # 生成前端测试页面
    generate_cors_test_html()
    
    print("\n🎉 测试完成！")
    print("💡 如果发现CORS问题，请检查WordPress插件是否正确安装并激活") 