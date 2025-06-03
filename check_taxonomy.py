#!/usr/bin/env python3
"""
检查WordPress中分类法设置的脚本
"""

import requests
from requests.auth import HTTPBasicAuth
from config import config
from logger import logger

def check_taxonomies():
    """检查最新工具的分类法设置"""
    try:
        auth = HTTPBasicAuth(config.WP_USERNAME, config.WP_APP_PASSWORD)
        
        # 获取最新的两个工具
        response = requests.get(
            f"{config.WP_API_BASE_URL}/aihub?per_page=5&orderby=date&order=desc", 
            auth=auth,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"获取工具失败: {response.status_code}")
            return False
        
        tools = response.json()
        logger.info(f"找到 {len(tools)} 个工具")
        
        for tool in tools:
            tool_id = tool['id']
            title = tool['title']['rendered']
            
            logger.info(f"\n检查工具: {title} (ID: {tool_id})")
            
            # 获取详细信息包含分类法
            detail_response = requests.get(
                f"{config.WP_API_BASE_URL}/aihub/{tool_id}?_embed", 
                auth=auth,
                timeout=30
            )
            
            if detail_response.status_code == 200:
                detail = detail_response.json()
                
                # 检查嵌入的分类法数据
                if '_embedded' in detail and 'wp:term' in detail['_embedded']:
                    terms = detail['_embedded']['wp:term']
                    logger.info(f"  分类法组数: {len(terms)}")
                    
                    for i, term_group in enumerate(terms):
                        if term_group:
                            term_names = [t['name'] for t in term_group]
                            taxonomy = term_group[0]['taxonomy'] if term_group else 'unknown'
                            logger.info(f"    组 {i} ({taxonomy}): {term_names}")
                        else:
                            logger.info(f"    组 {i}: 空")
                else:
                    logger.warning(f"  没有找到分类法数据")
                
                # 直接检查分类和标签
                categories_response = requests.get(
                    f"{config.WP_API_BASE_URL}/categories?post={tool_id}",
                    auth=auth
                )
                if categories_response.status_code == 200:
                    categories = categories_response.json()
                    if categories:
                        logger.info(f"  标准分类: {[c['name'] for c in categories]}")
                    else:
                        logger.warning(f"  没有标准分类")
                
                tags_response = requests.get(
                    f"{config.WP_API_BASE_URL}/tags?post={tool_id}",
                    auth=auth
                )
                if tags_response.status_code == 200:
                    tags = tags_response.json()
                    if tags:
                        logger.info(f"  标准标签: {[t['name'] for t in tags]}")
                    else:
                        logger.warning(f"  没有标准标签")
            else:
                logger.error(f"获取工具详情失败: {detail_response.status_code}")
        
        # 检查可用的分类法
        logger.info("\n检查可用的分类法:")
        taxonomies_response = requests.get(
            f"{config.WP_API_BASE_URL}/taxonomies",
            auth=auth
        )
        
        if taxonomies_response.status_code == 200:
            taxonomies = taxonomies_response.json()
            for tax_name, tax_info in taxonomies.items():
                if 'aihub' in tax_info.get('object_type', []):
                    logger.info(f"  - {tax_name}: {tax_info.get('name', 'Unknown')}")
        
        return True
        
    except Exception as e:
        logger.error(f"检查过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    check_taxonomies() 