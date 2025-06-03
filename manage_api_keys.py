#!/usr/bin/env python3
"""
API Key管理工具
用于管理AI工具API的API Key
需要WordPress管理员权限
"""

import requests
import json
import getpass
from logger import logger
from config import config

class APIKeyManager:
    """API Key管理器"""
    
    def __init__(self):
        if config.WP_API_BASE_URL:
            self.base_url = config.WP_API_BASE_URL.replace('/wp/v2', '/ai-tools/v1')
        else:
            self.base_url = "https://vertu.com/wp-json/ai-tools/v1"
        
        self.session = requests.Session()
        self.authenticated = False
        
        logger.info(f"API基础URL: {self.base_url}")
    
    def login(self):
        """WordPress管理员登录"""
        logger.info("请输入WordPress管理员凭据：")
        username = input("用户名: ")
        password = getpass.getpass("密码: ")
        
        # 尝试获取nonce（这里简化处理）
        # 在实际应用中，你可能需要使用Application Passwords或其他认证方式
        logger.info("登录功能需要进一步实现...")
        logger.info("请使用以下方式之一：")
        logger.info("1. 在WordPress后台直接生成API Key")
        logger.info("2. 使用Application Passwords进行认证")
        logger.info("3. 通过Cookie认证（需要先在浏览器中登录）")
        
        return False
    
    def generate_api_key(self, name, description="", rate_limit=1000):
        """生成新的API Key"""
        logger.info(f"生成API Key: {name}")
        
        data = {
            "name": name,
            "description": description,
            "rate_limit": rate_limit
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/generate-api-key",
                json=data,
                timeout=30
            )
            
            if response.status_code == 401:
                logger.error("未认证，请先登录WordPress管理后台")
                return None
            elif response.status_code == 403:
                logger.error("权限不足，需要管理员权限")
                return None
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                api_key = result['data']['api_key']
                logger.success(f"API Key生成成功: {api_key}")
                logger.info(f"名称: {name}")
                logger.info(f"速率限制: {rate_limit}/小时")
                return api_key
            else:
                logger.error(f"生成失败: {result.get('message', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
    
    def list_api_keys(self):
        """列出所有API Key"""
        logger.info("获取API Key列表...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api-keys",
                timeout=30
            )
            
            if response.status_code == 401:
                logger.error("未认证，请先登录WordPress管理后台")
                return []
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                keys = result.get('data', [])
                
                if not keys:
                    logger.info("没有找到API Key")
                    return []
                
                logger.info(f"\n找到 {len(keys)} 个API Key:")
                logger.info("-" * 80)
                logger.info(f"{'ID':<5} {'名称':<20} {'预览':<15} {'速率限制':<10} {'状态':<8} {'创建时间'}")
                logger.info("-" * 80)
                
                for key in keys:
                    logger.info(f"{key['id']:<5} {key['name']:<20} {key['api_key_preview']:<15} "
                              f"{key['rate_limit']:<10} {key['status']:<8} {key['created_at']}")
                
                return keys
            else:
                logger.error(f"获取失败: {result.get('message', 'Unknown error')}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            return []
    
    def delete_api_key(self, key_id):
        """删除API Key"""
        logger.info(f"删除API Key ID: {key_id}")
        
        try:
            response = self.session.delete(
                f"{self.base_url}/api-keys/{key_id}",
                timeout=30
            )
            
            if response.status_code == 401:
                logger.error("未认证，请先登录WordPress管理后台")
                return False
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                logger.success("API Key删除成功")
                return True
            else:
                logger.error(f"删除失败: {result.get('message', 'Unknown error')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            return False
    
    def interactive_menu(self):
        """交互式菜单"""
        while True:
            print("\n" + "=" * 50)
            print("AI工具API Key管理")
            print("=" * 50)
            print("1. 列出所有API Key")
            print("2. 生成新的API Key")
            print("3. 删除API Key")
            print("4. 退出")
            print("-" * 50)
            
            choice = input("请选择操作 (1-4): ").strip()
            
            if choice == '1':
                self.list_api_keys()
            
            elif choice == '2':
                name = input("API Key名称: ").strip()
                if not name:
                    logger.error("名称不能为空")
                    continue
                
                description = input("描述（可选）: ").strip()
                
                try:
                    rate_limit = input("速率限制（默认1000/小时）: ").strip()
                    rate_limit = int(rate_limit) if rate_limit else 1000
                except ValueError:
                    rate_limit = 1000
                
                self.generate_api_key(name, description, rate_limit)
            
            elif choice == '3':
                # 先列出现有的keys
                keys = self.list_api_keys()
                if not keys:
                    continue
                
                try:
                    key_id = int(input("请输入要删除的API Key ID: ").strip())
                    confirm = input(f"确认删除API Key ID {key_id}? (y/N): ").strip().lower()
                    if confirm == 'y':
                        self.delete_api_key(key_id)
                except ValueError:
                    logger.error("请输入有效的ID")
            
            elif choice == '4':
                print("再见！")
                break
            
            else:
                logger.error("无效选择，请输入1-4")

def main():
    """主函数"""
    manager = APIKeyManager()
    
    logger.info("欢迎使用API Key管理工具")
    logger.warning("注意：此工具需要WordPress管理员权限")
    logger.info("请确保您已经在浏览器中登录WordPress管理后台")
    
    # 可以尝试登录（目前未实现完整的认证）
    # manager.login()
    
    manager.interactive_menu()

if __name__ == "__main__":
    main() 