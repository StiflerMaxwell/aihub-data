#!/usr/bin/env python3
"""
WordPress自定义API连接测试
"""

import requests
from requests.auth import HTTPBasicAuth

# 配置信息（请根据实际情况修改）
WORDPRESS_URL = "https://vertu.com"
USERNAME = "maxwell"
PASSWORD = input("请输入您的WordPress应用密码: ")

def test_api_connection():
    """测试API连接"""
    
    # API端点
    test_url = f"{WORDPRESS_URL}/wp-json/ai-tools/v1/test"
    
    # 认证信息
    auth = HTTPBasicAuth(USERNAME, PASSWORD)
    headers = {"Content-Type": "application/json"}
    
    print(f"🔍 正在测试API连接...")
    print(f"📍 URL: {test_url}")
    print(f"👤 用户名: {USERNAME}")
    
    try:
        response = requests.get(test_url, auth=auth, headers=headers, timeout=30)
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API连接成功！")
            print(f"📝 响应数据:")
            print(f"   用户: {data.get('user', {}).get('name', 'Unknown')}")
            print(f"   邮箱: {data.get('user', {}).get('email', 'Unknown')}")
            print(f"   时间: {data.get('timestamp', 'Unknown')}")
            return True
        else:
            print("❌ API连接失败")
            print(f"📝 错误响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 连接异常: {e}")
        return False

if __name__ == "__main__":
    test_api_connection() 