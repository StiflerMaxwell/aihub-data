#!/usr/bin/env python3
"""
修复已导入WordPress的AI工具产品名称
将WordPress中错误的产品名称更新为CSV中的正确名称
"""

import requests
import json
from requests.auth import HTTPBasicAuth
from config import config
from logger import logger
from csv_data_processor import parse_ai_tools_csv

class ProductNameFixer:
    """产品名称修复器"""
    
    def __init__(self):
        self.wp_username = config.WP_USERNAME
        self.wp_password = config.WP_APP_PASSWORD
        self.wp_api_url = config.WP_API_BASE_URL
        self.wp_custom_api_url = config.WP_CUSTOM_API_BASE_URL
        
    def get_existing_tools(self):
        """获取现有的AI工具"""
        try:
            auth = HTTPBasicAuth(self.wp_username, self.wp_password)
            
            # 尝试通过aihub CPT获取
            response = requests.get(
                f"{self.wp_api_url}/aihub",
                auth=auth,
                params={'per_page': 100},
                timeout=30
            )
            
            if response.status_code == 200:
                tools = response.json()
                logger.info(f"获取到 {len(tools)} 个现有工具")
                return tools
            else:
                logger.error(f"获取工具失败: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"获取现有工具出错: {e}")
            return []
    
    def find_tool_by_url(self, tools, target_url):
        """根据URL查找工具"""
        for tool in tools:
            # 从工具数据中提取URL
            tool_url = None
            
            # 尝试从不同字段获取URL
            if hasattr(tool, 'acf') and tool.acf:
                tool_url = tool.acf.get('product_url')
            elif hasattr(tool, 'meta') and tool.meta:
                tool_url = tool.meta.get('product_url')
            elif 'acf' in tool:
                tool_url = tool['acf'].get('product_url')
            elif 'meta' in tool:
                tool_url = tool['meta'].get('product_url')
            
            # 清理URL进行比较
            if tool_url:
                tool_url = tool_url.strip().rstrip('/')
                target_url_clean = target_url.strip().rstrip('/')
                
                if tool_url == target_url_clean:
                    return tool
        
        return None
    
    def update_tool_title(self, tool_id, new_title):
        """更新工具标题"""
        try:
            auth = HTTPBasicAuth(self.wp_username, self.wp_password)
            headers = {"Content-Type": "application/json"}
            
            update_data = {
                'title': new_title
            }
            
            response = requests.post(
                f"{self.wp_api_url}/aihub/{tool_id}",
                headers=headers,
                auth=auth,
                json=update_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.success(f"✅ 更新成功: {new_title} (ID: {tool_id})")
                return True
            else:
                logger.error(f"更新失败: {response.status_code} - {response.text[:200]}")
                return False
                
        except Exception as e:
            logger.error(f"更新工具标题出错: {e}")
            return False
    
    def fix_product_names(self):
        """修复产品名称"""
        logger.info("=" * 60)
        logger.info("开始修复WordPress中的产品名称")
        logger.info("=" * 60)
        
        # 1. 获取CSV中的正确名称
        logger.info("步骤1: 读取CSV中的正确产品名称")
        tools_list = parse_ai_tools_csv(config.INPUT_CSV_FILE)
        
        if not tools_list:
            logger.error("无法读取CSV数据")
            return False
        
        logger.info(f"CSV中找到 {len(tools_list)} 个工具")
        
        # 2. 获取WordPress中现有的工具
        logger.info("步骤2: 获取WordPress中现有的工具")
        existing_tools = self.get_existing_tools()
        
        if not existing_tools:
            logger.error("无法获取WordPress中的工具")
            return False
        
        # 3. 匹配和更新
        logger.info("步骤3: 匹配并更新产品名称")
        updated_count = 0
        
        for csv_tool in tools_list:
            csv_name = csv_tool['product_name']
            csv_url = csv_tool['url']
            
            # 查找对应的WordPress工具
            wp_tool = self.find_tool_by_url(existing_tools, csv_url)
            
            if wp_tool:
                wp_title = wp_tool.get('title', {}).get('rendered', '') if isinstance(wp_tool.get('title'), dict) else str(wp_tool.get('title', ''))
                wp_id = wp_tool.get('id')
                
                logger.debug(f"匹配: {csv_name} <-> {wp_title}")
                
                # 检查是否需要更新
                if wp_title != csv_name:
                    logger.info(f"需要更新: '{wp_title}' -> '{csv_name}'")
                    
                    if self.update_tool_title(wp_id, csv_name):
                        updated_count += 1
                else:
                    logger.debug(f"名称已正确: {csv_name}")
            else:
                logger.warning(f"未找到匹配的WordPress工具: {csv_name} ({csv_url})")
        
        # 4. 总结
        logger.info("=" * 60)
        logger.info("修复完成总结")
        logger.info("=" * 60)
        logger.info(f"CSV工具总数: {len(tools_list)}")
        logger.info(f"WordPress工具总数: {len(existing_tools)}")
        logger.info(f"成功更新: {updated_count}")
        
        if updated_count > 0:
            logger.success(f"🎉 成功修复 {updated_count} 个工具的名称！")
        else:
            logger.info("没有需要修复的工具名称")
        
        return True

def main():
    """主函数"""
    # 验证配置
    if not all([config.WP_USERNAME, config.WP_APP_PASSWORD, config.WP_API_BASE_URL]):
        logger.error("WordPress配置不完整，请检查.env文件")
        return False
    
    fixer = ProductNameFixer()
    return fixer.fix_product_names()

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1) 