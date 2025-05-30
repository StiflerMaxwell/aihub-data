#!/usr/bin/env python3
"""
AI工具导入 - 自定义WordPress API客户端
使用自定义WordPress API端点进行AI工具数据导入
"""

import requests
import json
import time
import logging
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Optional
from csv_data_processor import CSVDataProcessor
from config import Config

class CustomAPIClient:
    """WordPress自定义API客户端"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = f"{config.wordpress_url.rstrip('/')}/wp-json/ai-tools/v1"
        self.auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_password)
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "AI-Tools-Importer/1.0"
        }
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('custom_api_import.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            response = requests.get(
                f"{self.base_url}/test",
                auth=self.auth,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ API连接成功！用户: {data['user']['name']}")
                return True
            else:
                self.logger.error(f"❌ API连接失败: {response.status_code}")
                self.logger.error(f"响应: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 连接测试异常: {e}")
            return False
    
    def import_single_tool(self, tool_data: Dict) -> Dict:
        """导入单个AI工具"""
        try:
            payload = {"tool_data": tool_data}
            
            response = requests.post(
                f"{self.base_url}/import",
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code in [200, 500]:  # 500也可能包含部分成功信息
                return response.json()
            else:
                return {
                    "success": False,
                    "message": f"HTTP错误: {response.status_code}",
                    "errors": {"http": response.text}
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"请求异常: {e}",
                "errors": {"exception": str(e)}
            }
    
    def batch_import_tools(self, tools_data: List[Dict]) -> Dict:
        """批量导入AI工具"""
        try:
            payload = {"tools": tools_data}
            
            self.logger.info(f"🚀 开始批量导入 {len(tools_data)} 个AI工具...")
            
            response = requests.post(
                f"{self.base_url}/batch-import",
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=600  # 10分钟超时
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "message": f"批量导入失败: {response.status_code}",
                    "errors": {"http": response.text}
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"批量导入异常: {e}",
                "errors": {"exception": str(e)}
            }

def prepare_tool_data_for_api(firecrawl_data: Dict, original_data: Dict) -> Dict:
    """为自定义API准备工具数据"""
    tool_data = {
        "product_name": original_data.get('product_name', ''),
        "product_url": original_data.get('product_url', ''),
        "original_category_name": original_data.get('original_category_name', ''),
    }
    
    # 从Firecrawl数据中提取字段
    if firecrawl_data:
        # 基本信息
        tool_data.update({
            "short_introduction": firecrawl_data.get("short_introduction", ""),
            "product_story": firecrawl_data.get("product_story", ""),
            "primary_task": firecrawl_data.get("primary_task", ""),
            "author_company": firecrawl_data.get("author_company", ""),
            "general_price_tag": firecrawl_data.get("general_price_tag", ""),
            "initial_release_date": firecrawl_data.get("initial_release_date", ""),
            "is_verified_tool": firecrawl_data.get("is_verified_tool", False),
        })
        
        # 图片URL
        tool_data.update({
            "logo_img_url": firecrawl_data.get("logo_img_url", ""),
            "overview_img_url": firecrawl_data.get("overview_img_url", ""),
        })
        
        # 数值字段
        numeric_fields = [
            "popularity_score", "number_of_tools_by_author", 
            "average_rating", "rating_count"
        ]
        for field in numeric_fields:
            if field in firecrawl_data and firecrawl_data[field] is not None:
                tool_data[field] = firecrawl_data[field]
        
        # 价格信息
        if "pricing_details" in firecrawl_data:
            tool_data["pricing_details"] = firecrawl_data["pricing_details"]
        
        # 列表字段
        list_fields = [
            "inputs", "outputs", "pros_list", "cons_list", 
            "related_tasks", "releases", "job_impacts"
        ]
        for field in list_fields:
            if field in firecrawl_data and isinstance(firecrawl_data[field], list):
                tool_data[field] = firecrawl_data[field]
    
    return tool_data

def main():
    """主函数"""
    # 加载配置
    config = Config()
    
    print("\n=== AI工具导入 - 自定义WordPress API客户端 ===")
    config.display_summary()
    
    # 初始化客户端
    client = CustomAPIClient(config)
    
    # 测试连接
    print("\n📡 测试API连接...")
    if not client.test_connection():
        print("❌ API连接失败，请检查配置！")
        return
    
    # 加载CSV数据
    print("\n📁 加载CSV数据...")
    processor = CSVDataProcessor(config.csv_file_path)
    tools_data = processor.get_tools_data()
    
    print(f"✅ 成功加载 {len(tools_data)} 个AI工具")
    
    # 处理数量限制
    if config.debug_mode and config.max_tools_to_process:
        tools_data = tools_data[:config.max_tools_to_process]
        print(f"🔧 调试模式：限制处理 {len(tools_data)} 个工具")
    
    # 选择导入方式
    print("\n请选择导入方式:")
    print("1. 批量导入（推荐）")
    print("2. 逐个导入")
    
    choice = input("输入选择 (1/2): ").strip()
    
    if choice == "1":
        # 批量导入
        prepared_data = []
        for tool in tools_data:
            # 这里简化处理，直接使用CSV数据，如果需要Firecrawl可以集成
            tool_data = prepare_tool_data_for_api({}, tool)
            prepared_data.append(tool_data)
        
        result = client.batch_import_tools(prepared_data)
        
        if result.get("success"):
            summary = result.get("summary", {})
            print(f"\n✅ 批量导入完成！")
            print(f"📊 总计: {summary.get('total', 0)}")
            print(f"✅ 成功: {summary.get('success', 0)}")
            print(f"❌ 失败: {summary.get('errors', 0)}")
            
            # 显示详细结果
            if config.debug_mode:
                results = result.get("results", [])
                for res in results:
                    status = "✅" if res["success"] else "❌"
                    print(f"{status} {res['tool_name']}: {res['message']}")
        else:
            print(f"❌ 批量导入失败: {result.get('message', 'Unknown error')}")
    
    elif choice == "2":
        # 逐个导入
        success_count = 0
        error_count = 0
        
        for index, tool in enumerate(tools_data, 1):
            print(f"\n📦 处理第 {index}/{len(tools_data)} 个工具: {tool['product_name']}")
            
            tool_data = prepare_tool_data_for_api({}, tool)
            result = client.import_single_tool(tool_data)
            
            if result.get("success"):
                success_count += 1
                action = result.get("action", "processed")
                print(f"✅ {tool['product_name']} {action}成功")
                
                if result.get("warnings"):
                    print(f"⚠️ 警告: {len(result['warnings'])} 个非致命错误")
            else:
                error_count += 1
                print(f"❌ {tool['product_name']} 处理失败: {result.get('message', 'Unknown error')}")
                
                if config.debug_mode and result.get("errors"):
                    for error_type, error_msg in result["errors"].items():
                        print(f"   - {error_type}: {error_msg}")
            
            # 添加延迟
            if index < len(tools_data):
                time.sleep(1)
        
        print(f"\n📊 导入完成！成功: {success_count}, 失败: {error_count}")
    
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main() 