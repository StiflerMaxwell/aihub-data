import csv
import json
import requests
from requests.auth import HTTPBasicAuth
import os
import time
import datetime
from urllib.parse import urlparse, urljoin
from csv_data_processor import parse_ai_tools_csv
import config

# === 从配置文件加载设置 ===
FIRECRAWL_API_KEY = config.FIRECRAWL_API_KEY
WP_USERNAME = config.WP_USERNAME
WP_APP_PASSWORD = config.WP_APP_PASSWORD
WP_API_BASE_URL = config.WP_API_BASE_URL

INPUT_CSV_FILE = config.INPUT_CSV_FILE
SCHEMA_FILE = config.SCHEMA_FILE
OUTPUT_RAW_FIRECRAWL_DATA = config.OUTPUT_RAW_FIRECRAWL_DATA
LOG_FILE = config.LOG_FILE

SCRAPE_DELAY = config.SCRAPE_DELAY
IMPORT_DELAY = config.IMPORT_DELAY
REQUEST_TIMEOUT = config.REQUEST_TIMEOUT
FIRECRAWL_TIMEOUT = config.FIRECRAWL_TIMEOUT

CATEGORY_TAXONOMY = config.CATEGORY_TAXONOMY
TAG_TAXONOMY = config.TAG_TAXONOMY
FIRECRAWL_ACTIONS = config.FIRECRAWL_ACTIONS

DEBUG_MODE = config.DEBUG_MODE
MAX_TOOLS_TO_PROCESS = config.MAX_TOOLS_TO_PROCESS

# === 工具函数 ===
def log_message(message, level="INFO"):
    """记录日志消息"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    # 输出到控制台
    print(log_entry)
    
    # 写入日志文件
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"写入日志文件失败: {e}")

def sanitize_url(url_str):
    """确保URL格式正确"""
    if not url_str:
        return None
    
    url_str = url_str.strip()
    if not url_str.startswith("http://") and not url_str.startswith("https://"):
        return "https://" + url_str
    return url_str

def test_wordpress_connection():
    """测试WordPress连接"""
    try:
        auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)
        response = requests.get(f"{WP_API_BASE_URL}/users/me", auth=auth, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        user_data = response.json()
        log_message(f"WordPress连接成功，用户: {user_data.get('name', 'Unknown')}")
        return True
        
    except requests.exceptions.RequestException as e:
        log_message(f"WordPress连接失败: {e}", "ERROR")
        return False

def get_or_create_wp_term(term_name, taxonomy_slug):
    """获取或创建WordPress分类法术语的ID"""
    if not term_name:
        return None
        
    headers = {"Content-Type": "application/json"}
    auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)
    
    try:
        # 1. 尝试查找现有术语
        search_url = f"{WP_API_BASE_URL}/{taxonomy_slug}?search={term_name}"
        response = requests.get(search_url, auth=auth, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        terms = response.json()
        
        for term in terms:
            if term['name'].lower() == term_name.lower():
                if DEBUG_MODE:
                    log_message(f"找到现有术语 '{term_name}' ID: {term['id']}")
                return term['id']
        
        # 2. 创建新术语
        create_url = f"{WP_API_BASE_URL}/{taxonomy_slug}"
        payload = {"name": term_name}
        response = requests.post(create_url, headers=headers, auth=auth, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        new_term = response.json()
        log_message(f"创建新术语 '{term_name}' ID: {new_term['id']}")
        return new_term['id']
        
    except requests.exceptions.RequestException as e:
        log_message(f"处理术语 '{term_name}' 时出错: {e}", "ERROR")
        return None

def upload_image_to_wp(image_url, post_id=None):
    """下载图片并上传到WordPress媒体库"""
    if not image_url:
        return None
    
    try:
        # 下载图片
        if DEBUG_MODE:
            log_message(f"正在下载图片: {image_url}")
        
        response = requests.get(image_url, stream=True, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        # 检查内容类型
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            log_message(f"警告: URL可能不是有效图片: {image_url}", "WARNING")
            return None

        # 获取文件信息
        file_name = os.path.basename(urlparse(image_url).path) or "image.jpg"
        if '.' not in file_name:
            # 根据content-type添加扩展名
            if 'jpeg' in content_type or 'jpg' in content_type:
                file_name += '.jpg'
            elif 'png' in content_type:
                file_name += '.png'
            elif 'gif' in content_type:
                file_name += '.gif'
            elif 'webp' in content_type:
                file_name += '.webp'
            else:
                file_name += '.jpg'
        
        # 上传到WordPress
        headers = {
            'Content-Type': content_type,
            'Content-Disposition': f'attachment; filename="{file_name}"'
        }
        auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)

        upload_url = f"{WP_API_BASE_URL}/media"
        upload_response = requests.post(
            upload_url, 
            headers=headers, 
            auth=auth, 
            data=response.content,
            timeout=60
        )
        upload_response.raise_for_status()
        
        media_data = upload_response.json()
        log_message(f"图片上传成功，媒体ID: {media_data['id']}")
        return media_data['id']
        
    except requests.exceptions.RequestException as e:
        log_message(f"上传图片 {image_url} 失败: {e}", "WARNING")
        return None
    except Exception as e:
        log_message(f"上传图片时发生未知错误: {e}", "ERROR")
        return None

def scrape_with_firecrawl(url, schema):
    """使用Firecrawl抓取网站数据"""
    try:
        headers = {
            'Authorization': f'Bearer {FIRECRAWL_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'url': url,
            'formats': ['json'],
            'actions': FIRECRAWL_ACTIONS,
            'jsonSchema': schema
        }
        
        if DEBUG_MODE:
            log_message(f"正在使用Firecrawl抓取: {url}")
        
        response = requests.post(
            'https://api.firecrawl.dev/v1/scrape',
            headers=headers,
            json=payload,
            timeout=FIRECRAWL_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data', {}).get('json'):
                return result['data']['json']
            else:
                log_message(f"Firecrawl返回成功但无JSON数据，URL: {url}", "WARNING")
                if DEBUG_MODE:
                    log_message(f"Firecrawl原始响应: {result}")
                return None
        else:
            log_message(f"Firecrawl API调用失败: {response.status_code} - {response.text}", "ERROR")
            return None
            
    except Exception as e:
        log_message(f"Firecrawl抓取出错 ({url}): {e}", "ERROR")
        return None

def clean_text_field(text):
    """清理文本字段"""
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = ' '.join(text.split())
    
    # 限制长度
    if len(text) > 5000:  # WordPress文章内容的合理限制
        text = text[:5000] + "..."
    
    return text

def import_tool_to_wordpress(scraped_data, original_category_name):
    """将抓取到的数据导入WordPress"""
    headers = {"Content-Type": "application/json"}
    auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)

    # 准备文章基本信息
    post_title = clean_text_field(scraped_data.get('product_name', 'Untitled AI Tool'))
    post_content = clean_text_field(scraped_data.get('short_introduction', ''))
    
    if scraped_data.get('product_story'):
        product_story = clean_text_field(scraped_data['product_story'])
        if post_content:
            post_content += "\n\n" + product_story
        else:
            post_content = product_story

    # 检查是否已存在相同工具
    try:
        search_url = f"{WP_API_BASE_URL}/ai_tool"
        search_params = {
            'search': post_title,
            'per_page': 10
        }
        search_res = requests.get(search_url, params=search_params, auth=auth, timeout=REQUEST_TIMEOUT)
        search_res.raise_for_status()
        existing_tools = search_res.json()
        
        wp_post_id = None
        if existing_tools:
            for tool in existing_tools:
                if tool['title']['rendered'].lower() == post_title.lower():
                    wp_post_id = tool['id']
                    log_message(f"找到现有工具 '{post_title}'，ID: {wp_post_id}，将进行更新")
                    break
        
        # 创建或更新CPT文章
        cpt_payload = {
            "title": post_title,
            "content": post_content,
            "status": "publish",
            "excerpt": clean_text_field(scraped_data.get('short_introduction', ''))[:200]  # 摘要限制200字符
        }
        
        if wp_post_id:
            # 更新现有文章
            update_url = f"{WP_API_BASE_URL}/ai_tool/{wp_post_id}"
            response = requests.post(update_url, headers=headers, auth=auth, json=cpt_payload, timeout=REQUEST_TIMEOUT)
        else:
            # 创建新文章
            create_url = f"{WP_API_BASE_URL}/ai_tool"
            response = requests.post(create_url, headers=headers, auth=auth, json=cpt_payload, timeout=REQUEST_TIMEOUT)
            
        response.raise_for_status()
        wp_tool_data = response.json()
        wp_post_id = wp_tool_data['id']
        
        log_message(f"成功{'更新' if wp_post_id else '创建'}工具 '{post_title}'，ID: {wp_post_id}")
        
    except requests.exceptions.RequestException as e:
        log_message(f"创建/更新工具 '{post_title}' 失败: {e}", "ERROR")
        return None

    # 上传图片
    logo_media_id = upload_image_to_wp(scraped_data.get('logo_img_url'), wp_post_id)
    overview_media_id = upload_image_to_wp(scraped_data.get('overview_img_url'), wp_post_id)

    # 准备ACF字段数据
    acf_data = {
        "product_url": scraped_data.get('product_url'),
        "product_story": clean_text_field(scraped_data.get('product_story')),
        "primary_task": clean_text_field(scraped_data.get('primary_task')),
        "author_company": clean_text_field(scraped_data.get('author_company')),
        "general_price_tag": clean_text_field(scraped_data.get('general_price_tag')),
        "initial_release_date": scraped_data.get('initial_release_date'),
        "is_verified_tool": scraped_data.get('is_verified_tool', False)
    }

    # 添加图片字段
    if logo_media_id:
        acf_data["logo_img"] = logo_media_id
    if overview_media_id:
        acf_data["overview_img"] = overview_media_id

    # 添加数值字段（确保类型正确）
    if scraped_data.get('popularity_score') is not None:
        try:
            acf_data["popularity_score"] = float(scraped_data['popularity_score'])
        except (ValueError, TypeError):
            pass

    if scraped_data.get('number_of_tools_by_author') is not None:
        try:
            acf_data["number_of_tools_by_author"] = int(scraped_data['number_of_tools_by_author'])
        except (ValueError, TypeError):
            pass

    if scraped_data.get('average_rating') is not None:
        try:
            acf_data["average_rating"] = float(scraped_data['average_rating'])
        except (ValueError, TypeError):
            pass

    if scraped_data.get('rating_count') is not None:
        try:
            acf_data["rating_count"] = int(scraped_data['rating_count'])
        except (ValueError, TypeError):
            pass

    # 处理数组字段
    if scraped_data.get('inputs') and isinstance(scraped_data['inputs'], list):
        acf_data["inputs"] = [{"input_type": clean_text_field(item)} for item in scraped_data['inputs'] if item]
    
    if scraped_data.get('outputs') and isinstance(scraped_data['outputs'], list):
        acf_data["outputs"] = [{"output_type": clean_text_field(item)} for item in scraped_data['outputs'] if item]
    
    if scraped_data.get('pros_list') and isinstance(scraped_data['pros_list'], list):
        acf_data["pros_list"] = [{"pro_item": clean_text_field(item)} for item in scraped_data['pros_list'] if item]
    
    if scraped_data.get('cons_list') and isinstance(scraped_data['cons_list'], list):
        acf_data["cons_list"] = [{"con_item": clean_text_field(item)} for item in scraped_data['cons_list'] if item]
    
    if scraped_data.get('related_tasks') and isinstance(scraped_data['related_tasks'], list):
        acf_data["related_tasks"] = [{"task_item": clean_text_field(item)} for item in scraped_data['related_tasks'] if item]

    # 处理价格信息
    pricing_details = scraped_data.get('pricing_details', {})
    if pricing_details and isinstance(pricing_details, dict):
        if pricing_details.get('pricing_model'):
            acf_data["pricing_model"] = clean_text_field(pricing_details['pricing_model'])
        if pricing_details.get('currency'):
            acf_data["currency"] = clean_text_field(pricing_details['currency'])
        if pricing_details.get('billing_frequency'):
            acf_data["billing_frequency"] = clean_text_field(pricing_details['billing_frequency'])
        
        if pricing_details.get('paid_options_from') is not None:
            try:
                acf_data["paid_options_from"] = float(pricing_details['paid_options_from'])
            except (ValueError, TypeError):
                pass

    # 处理Releases Repeater
    if scraped_data.get('releases') and isinstance(scraped_data['releases'], list):
        acf_data["releases"] = []
        for release in scraped_data['releases']:
            if isinstance(release, dict):
                release_data = {}
                if release.get('release_date'):
                    release_data["release_date"] = release['release_date']
                if release.get('release_notes'):
                    release_data["release_notes"] = clean_text_field(release['release_notes'])
                if release.get('release_author'):
                    release_data["release_author"] = clean_text_field(release['release_author'])
                
                if release_data:  # 只添加非空的发布信息
                    acf_data["releases"].append(release_data)

    # 处理Job Impacts Repeater
    if scraped_data.get('job_impacts') and isinstance(scraped_data['job_impacts'], list):
        acf_data["job_impacts"] = []
        for job in scraped_data['job_impacts']:
            if isinstance(job, dict):
                job_data = {}
                if job.get('job_type'):
                    job_data["job_type"] = clean_text_field(job['job_type'])
                if job.get('impact_description'):
                    job_data["impact_description"] = clean_text_field(job['impact_description'])
                if job.get('tasks_affected'):
                    job_data["tasks_affected"] = clean_text_field(job['tasks_affected'])
                if job.get('ai_skills_required'):
                    job_data["ai_skills_required"] = clean_text_field(job['ai_skills_required'])
                
                if job_data:  # 只添加非空的工作影响信息
                    acf_data["job_impacts"].append(job_data)

    # 更新ACF字段
    try:
        update_acf_payload = {"acf": acf_data}
        acf_update_url = f"{WP_API_BASE_URL}/ai_tool/{wp_post_id}"
        acf_response = requests.post(
            acf_update_url, 
            headers=headers, 
            auth=auth, 
            json=update_acf_payload,
            timeout=REQUEST_TIMEOUT
        )
        acf_response.raise_for_status()
        if DEBUG_MODE:
            log_message(f"成功更新ACF字段，工具ID: {wp_post_id}")
        
    except requests.exceptions.RequestException as e:
        log_message(f"更新ACF字段失败，工具ID {wp_post_id}: {e}", "ERROR")

    # 设置分类法
    category_name = scraped_data.get('primary_task') or original_category_name
    if category_name:
        category_id = get_or_create_wp_term(category_name, CATEGORY_TAXONOMY)
        
        if category_id:
            try:
                taxonomy_payload = {CATEGORY_TAXONOMY: [category_id]}
                taxonomy_response = requests.post(
                    acf_update_url, 
                    headers=headers, 
                    auth=auth, 
                    json=taxonomy_payload,
                    timeout=REQUEST_TIMEOUT
                )
                taxonomy_response.raise_for_status()
                if DEBUG_MODE:
                    log_message(f"成功设置分类法，工具ID: {wp_post_id}")
                
            except requests.exceptions.RequestException as e:
                log_message(f"设置分类法失败，工具ID {wp_post_id}: {e}", "WARNING")

    return wp_post_id

def main():
    """主执行函数"""
    log_message("开始AI工具抓取和导入流程")
    
    # 显示配置摘要
    if DEBUG_MODE:
        config.print_config_summary()
    
    # 验证配置
    config_errors = config.validate_config()
    if config_errors:
        log_message("配置验证失败:", "ERROR")
        for error in config_errors:
            log_message(f"  - {error}", "ERROR")
        log_message("请创建.env文件并设置正确的配置。参考env.example文件。", "ERROR")
        return False
    
    # 测试WordPress连接
    if not test_wordpress_connection():
        log_message("WordPress连接测试失败，请检查配置", "ERROR")
        return False
    
    # 加载Firecrawl Schema
    try:
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            firecrawl_schema = json.load(f)
        log_message("成功加载Firecrawl Schema")
    except FileNotFoundError:
        log_message(f"错误: Schema文件 '{SCHEMA_FILE}' 不存在", "ERROR")
        return False
    except json.JSONDecodeError:
        log_message(f"错误: Schema文件 '{SCHEMA_FILE}' 格式无效", "ERROR")
        return False

    # 解析CSV数据
    try:
        log_message("正在解析CSV文件...")
        initial_tools_data = parse_ai_tools_csv(INPUT_CSV_FILE)
        
        # 如果设置了处理限制
        if MAX_TOOLS_TO_PROCESS and MAX_TOOLS_TO_PROCESS > 0:
            initial_tools_data = initial_tools_data[:MAX_TOOLS_TO_PROCESS]
            log_message(f"限制处理数量为: {MAX_TOOLS_TO_PROCESS}")
        
        log_message(f"成功解析 {len(initial_tools_data)} 个AI工具")
    except Exception as e:
        log_message(f"解析CSV文件失败: {e}", "ERROR")
        return False

    if not initial_tools_data:
        log_message("没有找到要处理的AI工具数据", "WARNING")
        return False

    all_scraped_data = []

    # 阶段1: 使用Firecrawl抓取数据
    log_message("开始阶段1: 数据抓取")
    successful_scrapes = 0
    
    for i, tool_info in enumerate(initial_tools_data):
        product_name = tool_info['product_name']
        tool_url = tool_info['url']
        category_name = tool_info['category']

        log_message(f"[{i+1}/{len(initial_tools_data)}] 抓取 {product_name}")

        scraped_data = scrape_with_firecrawl(tool_url, firecrawl_schema)
        
        if scraped_data:
            # 补充基本信息
            scraped_data['product_name'] = scraped_data.get('product_name', product_name)
            scraped_data['product_url'] = scraped_data.get('product_url', tool_url)
            scraped_data['original_category_name'] = category_name
            all_scraped_data.append(scraped_data)
            successful_scrapes += 1
            log_message(f"✓ 成功抓取 {product_name} 的结构化数据")
        else:
            # 添加基本信息，即使抓取失败
            all_scraped_data.append({
                "product_name": product_name,
                "product_url": tool_url,
                "original_category_name": category_name,
                "short_introduction": "无法抓取详细信息",
                "error": "Firecrawl抓取失败"
            })
            log_message(f"✗ {product_name} 抓取失败，使用基本信息", "WARNING")

        # 礼貌性延迟
        time.sleep(SCRAPE_DELAY)

    log_message(f"阶段1完成: {successful_scrapes}/{len(initial_tools_data)} 成功抓取")

    # 保存原始抓取数据
    try:
        with open(OUTPUT_RAW_FIRECRAWL_DATA, 'w', encoding='utf-8') as f:
            json.dump(all_scraped_data, f, ensure_ascii=False, indent=2)
        log_message(f"原始抓取数据已保存到 {OUTPUT_RAW_FIRECRAWL_DATA}")
    except Exception as e:
        log_message(f"保存原始数据失败: {e}", "ERROR")

    # 阶段2: 导入WordPress
    log_message("开始阶段2: WordPress导入")
    processed_count = 0
    error_count = 0
    
    for scraped_tool in all_scraped_data:
        product_name = scraped_tool.get('product_name', 'Unknown')
        
        if 'error' in scraped_tool:
            log_message(f"跳过导入 '{product_name}'，因为抓取失败", "WARNING")
            error_count += 1
            continue
        
        wp_post_id = import_tool_to_wordpress(
            scraped_tool, 
            scraped_tool.get('original_category_name')
        )
        
        if wp_post_id:
            processed_count += 1
            log_message(f"✓ 成功导入 {product_name}")
        else:
            error_count += 1
            log_message(f"✗ 导入 {product_name} 失败", "ERROR")
        
        # 导入间隔
        time.sleep(IMPORT_DELAY)

    # 最终统计
    log_message("=" * 50)
    log_message("流程完成统计:")
    log_message(f"  总计工具数: {len(initial_tools_data)}")
    log_message(f"  成功抓取: {successful_scrapes}")
    log_message(f"  成功导入: {processed_count}")
    log_message(f"  失败/跳过: {error_count}")
    log_message("=" * 50)
    log_message("全部流程完成！")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1) 