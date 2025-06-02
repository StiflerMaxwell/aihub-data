#!/usr/bin/env python3
"""
AI工具数据导入系统 - 简化版本
跳过WordPress连接，只处理数据并生成JSON文件
"""

import json
import sys
from config import config
from logger import logger
from csv_data_processor import parse_ai_tools_csv
from gemini_enhancer import gemini_enhancer
from favicon_logo_helper import favicon_helper
from screenshot_helper import screenshot_helper

def main():
    """主执行函数"""
    logger.info("=" * 60)
    logger.info("AI工具数据导入系统启动 (简化版本)")
    logger.info("=" * 60)
    
    # 1. 验证基础配置
    logger.info("配置摘要:")
    logger.info(f"Gemini增强: {'启用' if config.ENABLE_GEMINI_ENHANCEMENT else '禁用'}")
    logger.info(f"处理限制: {config.MAX_TOOLS_TO_PROCESS or '无限制'}")
    logger.info(f"调试模式: {'开启' if config.DEBUG_MODE else '关闭'}")
    logger.info("⚠️  注意: 跳过WordPress连接，仅生成数据文件")
    
    try:
        # 2. 解析CSV数据
        logger.info("\n步骤1: 解析CSV数据")
        tools_list = parse_ai_tools_csv(config.INPUT_CSV_FILE)
        
        if not tools_list:
            logger.error("没有找到有效的工具数据")
            return False
        
        # 限制处理数量（如果配置了）
        if config.MAX_TOOLS_TO_PROCESS:
            tools_list = tools_list[:config.MAX_TOOLS_TO_PROCESS]
            logger.info(f"限制处理数量为: {config.MAX_TOOLS_TO_PROCESS}")
        
        logger.success(f"成功解析 {len(tools_list)} 个工具")
        
        # 显示工具预览
        logger.info("\n工具预览:")
        for i, tool in enumerate(tools_list[:5], 1):
            logger.info(f"  {i}. {tool['product_name']} ({tool['category']})")
        if len(tools_list) > 5:
            logger.info(f"  ... 还有 {len(tools_list) - 5} 个工具")
        
        # 3. 数据处理
        logger.info("\n步骤2: 数据处理")
        enhanced_tools = []
        
        for i, tool_data in enumerate(tools_list, 1):
            logger.info(f"[{i}/{len(tools_list)}] 处理: {tool_data['product_name']}")
            
            # 直接从CSV数据创建基础工具信息
            enhanced_tool = {
                'product_name': tool_data['product_name'],
                'product_url': tool_data['url'],
                'category': tool_data['category'],
                'original_category_name': tool_data['category'],
                'short_introduction': f"This is an {tool_data['category']} AI tool.",
                'general_price_tag': 'Unknown',
                'inputs': ['Text'],  # 默认输入类型
                'outputs': ['Text'], # 默认输出类型
                'description': f"{tool_data['product_name']} is an {tool_data['category']} tool.",
                'features': [],
                'pricing_plans': []
            }
            
            # Gemini增强（如果启用）
            if config.ENABLE_GEMINI_ENHANCEMENT and gemini_enhancer.is_enabled():
                logger.debug(f"Gemini增强: {enhanced_tool['product_name']}")
                try:
                    enhanced_tool = gemini_enhancer.enhance_tool_data(enhanced_tool)
                except Exception as e:
                    logger.warning(f"Gemini增强失败: {e}")
            
            # Favicon增强
            try:
                enhanced_tool = favicon_helper.enhance_tool_with_favicon(enhanced_tool)
            except Exception as e:
                logger.warning(f"Favicon获取失败: {e}")
            
            # Screenshot增强
            try:
                enhanced_tool = screenshot_helper.enhance_tool_with_screenshot(enhanced_tool)
            except Exception as e:
                logger.warning(f"Screenshot获取失败: {e}")
            
            enhanced_tools.append(enhanced_tool)
            logger.success(f"✓ 处理完成: {enhanced_tool['product_name']}")
        
        logger.success(f"完成 {len(enhanced_tools)} 个工具的处理")
        
        # 4. 保存处理结果
        logger.info("\n步骤3: 保存处理结果")
        try:
            with open(config.OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(enhanced_tools, f, ensure_ascii=False, indent=2)
            logger.success(f"数据已保存到: {config.OUTPUT_JSON_FILE}")
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return False
        
        # 5. 生成分类法摘要
        logger.info("\n步骤4: 分类法摘要")
        _log_batch_taxonomy_summary(enhanced_tools)
        
        # 6. 生成统计报告
        logger.info("\n" + "=" * 60)
        logger.info("处理完成统计")
        logger.info("=" * 60)
        
        total_tools = len(tools_list)
        successful_processes = len(enhanced_tools)
        
        logger.info(f"总计工具数: {total_tools}")
        logger.info(f"成功处理: {successful_processes}")
        logger.info(f"处理成功率: {successful_processes/total_tools*100:.1f}%")
        
        if successful_processes > 0:
            logger.success(f"🎉 成功处理 {successful_processes} 个AI工具!")
            logger.info(f"数据文件: {config.OUTPUT_JSON_FILE}")
            logger.info("您可以手动导入这些数据到WordPress")
        
        logger.info("=" * 60)
        logger.info("AI工具数据处理完成")
        logger.info("=" * 60)
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("\n用户中断执行")
        return False
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
        return False

def _log_batch_taxonomy_summary(tools_data):
    """记录批量处理的分类法摘要"""
    try:
        categories = set()
        tags = set()
        pricing_models = set()
        input_types = set()
        output_types = set()
        
        for tool_data in tools_data:
            # 收集分类
            primary_category = tool_data.get('category') or tool_data.get('original_category_name') or tool_data.get('primary_task')
            if primary_category:
                categories.add(primary_category)
            
            # 收集标签
            if tool_data.get('primary_task'):
                tags.add(tool_data['primary_task'])
            if tool_data.get('inputs') and isinstance(tool_data['inputs'], list):
                tags.update(tool_data['inputs'])
            if tool_data.get('outputs') and isinstance(tool_data['outputs'], list):
                tags.update(tool_data['outputs'])
            if tool_data.get('general_price_tag'):
                tags.add(tool_data['general_price_tag'])
                pricing_models.add(tool_data['general_price_tag'])
            
            # 收集输入/输出类型
            if tool_data.get('inputs') and isinstance(tool_data['inputs'], list):
                input_types.update(tool_data['inputs'])
            if tool_data.get('outputs') and isinstance(tool_data['outputs'], list):
                output_types.update(tool_data['outputs'])
            
            # 收集定价模式
            pricing_detail = tool_data.get('pricing_details', {}).get('pricing_model') if tool_data.get('pricing_details') else None
            if pricing_detail:
                pricing_models.add(pricing_detail)
        
        logger.info("📊 分类法摘要:")
        logger.info(f"  🗂️  分类 ({len(categories)}): {', '.join(sorted(categories))}")
        logger.info(f"  🏷️  标签 ({len(tags)}): {', '.join(sorted(list(tags)[:10]))}{'...' if len(tags) > 10 else ''}")
        logger.info(f"  💰 定价模式 ({len(pricing_models)}): {', '.join(sorted(pricing_models))}")
        logger.info(f"  📥 输入类型 ({len(input_types)}): {', '.join(sorted(input_types))}")
        logger.info(f"  📤 输出类型 ({len(output_types)}): {', '.join(sorted(output_types))}")
        
    except Exception as e:
        logger.warning(f"生成分类法摘要失败: {e}")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 