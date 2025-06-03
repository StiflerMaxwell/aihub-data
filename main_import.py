#!/usr/bin/env python3
"""
AI工具数据导入系统 - 主导入脚本
完整的数据处理流程：CSV解析 → Firecrawl抓取 → Gemini增强 → Favicon获取 → WordPress导入
支持异步处理：每个工具抓取完成后立即进行增强
"""

import json
import sys
import asyncio
import concurrent.futures
from threading import Lock
from config import config
from logger import logger
from csv_data_processor import parse_ai_tools_csv
from firecrawl_scraper import FirecrawlScraper
from gemini_enhancer import gemini_enhancer
from favicon_logo_helper import favicon_helper
from screenshot_helper import screenshot_helper
from wordpress_importer import WordPressImporter

class AsyncToolProcessor:
    """异步工具处理器"""
    
    def __init__(self):
        self.enhanced_tools = []
        self.lock = Lock()
        self.processed_count = 0
        
    def process_single_tool(self, tool_data, firecrawl_scraper, schema):
        """处理单个工具：抓取 + 增强"""
        try:
            # 步骤1: Firecrawl抓取
            logger.info(f"[{self.processed_count + 1}] 开始处理: {tool_data.get('product_name', 'Unknown')}")
            
            # 抓取网站数据
            scrape_result = firecrawl_scraper.scrape_single(tool_data, schema)
            
            if scrape_result['status'] != 'success':
                logger.error(f"抓取失败: {tool_data.get('product_name', 'Unknown')}")
                return None
                
            enhanced_data = scrape_result['data']
            
            # 步骤2: Gemini增强（立即进行）
            if config.ENABLE_GEMINI_ENHANCEMENT and gemini_enhancer.is_enabled():
                logger.debug(f"Gemini增强: {enhanced_data.get('product_name', 'Unknown')}")
                enhanced_data = gemini_enhancer.enhance_tool_data(enhanced_data)
            
            # 步骤3: Favicon增强
            enhanced_data = favicon_helper.enhance_tool_with_favicon(enhanced_data)
            
            # 步骤4: Screenshot增强
            enhanced_data = screenshot_helper.enhance_tool_with_screenshot(enhanced_data)
            
            # 线程安全地添加到结果列表
            with self.lock:
                self.enhanced_tools.append(enhanced_data)
                self.processed_count += 1
                logger.success(f"✓ 完成处理 [{self.processed_count}]: {enhanced_data.get('product_name', 'Unknown')}")
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"处理工具失败 {tool_data.get('product_name', 'Unknown')}: {e}")
            return None

def main():
    """主执行函数"""
    logger.info("=" * 60)
    logger.info("AI工具数据导入系统启动 (异步增强版)")
    logger.info("=" * 60)
    
    # 1. 验证配置
    config.print_summary()
    errors = config.validate()
    if errors:
        logger.error("配置验证失败:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("请检查.env文件配置")
        return False
    
    logger.success("配置验证通过")
    
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
        
        # 3. 初始化组件
        logger.info("\n步骤2: 初始化组件")
        
        # WordPress导入器
        wp_importer = WordPressImporter()
        if not wp_importer.test_connection():
            logger.error("WordPress连接失败")
            return False
        
        # Firecrawl抓取器
        enable_firecrawl = config.ENABLE_FIRECRAWL if hasattr(config, 'ENABLE_FIRECRAWL') else True
        firecrawl_failed = False
        
        if enable_firecrawl:
            try:
                firecrawl_scraper = FirecrawlScraper()
                schema = firecrawl_scraper.load_schema()
                if not schema:
                    logger.error("无法加载Firecrawl Schema")
                    return False
                logger.success("Firecrawl抓取器初始化成功")
            except Exception as e:
                logger.error(f"Firecrawl抓取器初始化失败: {e}")
                return False
        else:
            logger.warning("⚠️  Firecrawl抓取已禁用，将使用CSV基础数据")
            firecrawl_scraper = None
            schema = None
        
        # Gemini增强器
        if config.ENABLE_GEMINI_ENHANCEMENT:
            if gemini_enhancer.is_enabled():
                logger.success("Gemini增强器已启用")
            else:
                logger.warning("Gemini增强器配置有误，将跳过增强")
        else:
            logger.info("Gemini增强器已禁用")
        
        # 4. 处理阶段：抓取 + 增强 或 直接处理CSV数据
        logger.info("\n步骤3: 数据处理")
        
        if enable_firecrawl and firecrawl_scraper and not firecrawl_failed:
            logger.info(f"开始处理 {len(tools_list)} 个工具 (使用Firecrawl抓取)...")
            logger.warning("💡 免费计划限制: 每分钟最多10次抓取，建议耐心等待")
            
            processor = AsyncToolProcessor()
            
            # 使用串行处理以避免Firecrawl API并发限制
            max_workers = 1  # 串行处理，避免并发限制导致的402错误
            logger.info("使用串行处理以遵守API速率限制...")
            
            enhanced_tools = []
            api_failed_count = 0
            
            for i, tool_data in enumerate(tools_list, 1):
                try:
                    logger.info(f"[{i}/{len(tools_list)}] 开始处理: {tool_data.get('product_name', 'Unknown')}")
                    
                    # 抓取网站数据
                    scrape_result = firecrawl_scraper.scrape_single(tool_data, schema)
                    
                    if scrape_result['status'] == 'success':
                        enhanced_data = scrape_result['data']
                        
                        # Gemini增强（如果启用）
                        if config.ENABLE_GEMINI_ENHANCEMENT and gemini_enhancer.is_enabled():
                            logger.debug(f"Gemini增强: {enhanced_data.get('product_name', 'Unknown')}")
                            enhanced_data = gemini_enhancer.enhance_tool_data(enhanced_data)
                        
                        # Favicon增强
                        enhanced_data = favicon_helper.enhance_tool_with_favicon(enhanced_data)
                        
                        # Screenshot增强
                        enhanced_data = screenshot_helper.enhance_tool_with_screenshot(enhanced_data)
                        
                        enhanced_tools.append(enhanced_data)
                        logger.success(f"✓ 完成处理 [{i}]: {enhanced_data.get('product_name', 'Unknown')}")
                        
                    elif "402" in scrape_result.get('message', ''):
                        # API额度不足，询问用户是否继续
                        api_failed_count += 1
                        logger.error(f"💳 API额度不足，已失败 {api_failed_count} 次")
                        
                        if api_failed_count >= 3:  # 连续失败3次，建议切换模式
                            logger.error("\n" + "="*50)
                            logger.error("🚫 Firecrawl API连续失败，建议切换处理模式")
                            logger.error("="*50)
                            logger.info("💡 解决方案:")
                            logger.info("  1. 稍后再试 (等待额度重置)")
                            logger.info("  2. 升级Firecrawl付费计划")
                            logger.info("  3. 自动切换到基础模式继续处理")
                            
                            # 自动切换到基础模式
                            logger.warning("⚠️  自动切换到基础模式，使用CSV数据继续处理...")
                            firecrawl_failed = True
                            break
                        else:
                            # 创建基础数据继续处理
                            basic_data = create_basic_tool_data(tool_data)
                            basic_data = enhance_basic_tool(basic_data)
                            enhanced_tools.append(basic_data)
                            logger.info(f"📋 使用基础数据继续: {basic_data.get('product_name', 'Unknown')}")
                    else:
                        # 其他错误，使用基础数据
                        basic_data = create_basic_tool_data(tool_data)
                        basic_data = enhance_basic_tool(basic_data)
                        enhanced_tools.append(basic_data)
                        logger.warning(f"⚠️  抓取失败，使用基础数据: {basic_data.get('product_name', 'Unknown')}")
                        
                except Exception as e:
                    logger.error(f"处理工具失败 {tool_data.get('product_name', 'Unknown')}: {e}")
                    # 创建基础数据
                    basic_data = create_basic_tool_data(tool_data)
                    basic_data = enhance_basic_tool(basic_data)
                    enhanced_tools.append(basic_data)
            
            # 如果切换到基础模式，处理剩余工具
            if firecrawl_failed and i < len(tools_list):
                logger.info(f"\n切换到基础模式，处理剩余 {len(tools_list) - i} 个工具...")
                for remaining_tool in tools_list[i:]:
                    basic_data = create_basic_tool_data(remaining_tool)
                    basic_data = enhance_basic_tool(basic_data)
                    enhanced_tools.append(basic_data)
                    logger.success(f"✓ 基础处理完成: {basic_data.get('product_name', 'Unknown')}")
            
            logger.success(f"完成 {len(enhanced_tools)} 个工具的处理")
        else:
            # 使用基础模式
            logger.info("使用CSV基础数据进行处理...")
            enhanced_tools = []
            
            for tool_data in tools_list:
                basic_data = create_basic_tool_data(tool_data)
                basic_data = enhance_basic_tool(basic_data)
                enhanced_tools.append(basic_data)
                logger.success(f"✓ 处理完成: {basic_data['product_name']}")
            
            logger.success(f"完成 {len(enhanced_tools)} 个工具的基础处理")
        
        # 5. 保存处理结果
        logger.info("\n步骤4: 保存处理结果")
        try:
            with open(config.OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(enhanced_tools, f, ensure_ascii=False, indent=2)
            logger.success(f"数据已保存到: {config.OUTPUT_JSON_FILE}")
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
        
        # 6. WordPress导入阶段
        logger.info("\n步骤5: WordPress批量导入")
        logger.info(f"开始导入 {len(enhanced_tools)} 个工具到WordPress...")
        import_results = wp_importer.import_batch(enhanced_tools)
        
        # 7. 生成统计报告
        logger.info("\n" + "=" * 60)
        logger.info("处理完成统计")
        logger.info("=" * 60)
        
        total_tools = len(tools_list)
        successful_processes = len(enhanced_tools)
        successful_imports = sum(1 for r in import_results if r['success'])
        
        logger.info(f"总计工具数: {total_tools}")
        logger.info(f"成功处理: {successful_processes}")
        logger.info(f"成功导入: {successful_imports}")
        logger.info(f"处理成功率: {successful_processes/total_tools*100:.1f}%")
        logger.info(f"导入成功率: {successful_imports/total_tools*100:.1f}%")
        
        if successful_imports > 0:
            logger.success(f"🎉 成功导入 {successful_imports} 个AI工具!")
            logger.info("请登录WordPress后台查看aihub文章类型")
        
        # 使用建议
        if firecrawl_failed or not enable_firecrawl:
            logger.info("\n💡 使用建议:")
            logger.info("  • 如需更丰富的数据，建议升级Firecrawl付费计划")
            logger.info("  • 当前使用基础模式，数据来源于CSV和Gemini增强")
            logger.info("  • 已自动获取favicon和截图来增强工具信息")
        
        logger.info("=" * 60)
        logger.info("AI工具数据导入系统完成")
        logger.info("=" * 60)
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("\n用户中断执行")
        return False
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
        return False

def create_basic_tool_data(tool_data):
    """从CSV数据创建基础工具信息"""
    return {
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

def enhance_basic_tool(tool_data):
    """增强基础工具数据"""
    # Gemini增强（如果启用）
    if config.ENABLE_GEMINI_ENHANCEMENT and gemini_enhancer.is_enabled():
        logger.debug(f"Gemini增强: {tool_data['product_name']}")
        tool_data = gemini_enhancer.enhance_tool_data(tool_data)
    
    # Favicon增强
    tool_data = favicon_helper.enhance_tool_with_favicon(tool_data)
    
    # Screenshot增强
    tool_data = screenshot_helper.enhance_tool_with_screenshot(tool_data)
    
    return tool_data

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 