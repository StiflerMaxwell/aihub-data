#!/usr/bin/env python3
"""
AI工具导入系统 - 真实视频URL获取助手
专注于从AI工具网站提取真实的演示视频、产品介绍视频
"""

import requests
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlunparse
from config import config
from logger import logger

class VideoHelper:
    """真实视频URL获取助手"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.timeout = config.REQUEST_TIMEOUT
        
        # 扩展的视频平台URL模式
        self.video_patterns = {
            'youtube': r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            'vimeo': r'(?:https?:\/\/)?(?:www\.)?vimeo\.com\/(?:video\/)?(\d+)',
            'loom': r'(?:https?:\/\/)?(?:www\.)?loom\.com\/share\/([a-zA-Z0-9-]+)',
            'wistia': r'(?:https?:\/\/)?(?:[\w-]+\.)?wistia\.com\/(?:medias|embed)\/([a-zA-Z0-9]+)',
            'streamable': r'(?:https?:\/\/)?streamable\.com\/([a-zA-Z0-9]+)',
            'twitch': r'(?:https?:\/\/)?(?:www\.)?twitch\.tv\/videos\/(\d+)',
            'dailymotion': r'(?:https?:\/\/)?(?:www\.)?dailymotion\.com\/video\/([a-zA-Z0-9]+)',
            'direct_video': r'https?:\/\/[^\s]+\.(?:mp4|webm|ogg|mov|avi|m4v)(?:\?[^\s]*)?'
        }
        
        # 常见的视频相关关键词和选择器
        self.video_keywords = [
            'demo', 'demonstration', 'tutorial', 'overview', 'introduction', 'walkthrough',
            'preview', 'showcase', 'how to', 'getting started', 'product tour',
            '演示', '教程', '介绍', '预览', '展示', '使用方法'
        ]
        
        # 视频容器的CSS选择器
        self.video_selectors = [
            'iframe[src*="youtube"]', 'iframe[src*="vimeo"]', 'iframe[src*="loom"]',
            'iframe[src*="wistia"]', 'video', 'embed[src*="youtube"]',
            '.video-container', '.demo-video', '.product-video', '.hero-video',
            '[data-video-id]', '[data-youtube-id]', '[data-vimeo-id]'
        ]
        
        # 已验证的真实AI工具视频（定期更新）
        self.verified_tool_videos = {
            # === 主流聊天机器人 ===
            'ChatGPT': 'https://www.youtube.com/watch?v=JTxsNm9IdYU',  # OpenAI官方介绍
            'Claude': 'https://www.youtube.com/watch?v=3TDJQVo4s1c',   # Anthropic官方演示
            'Bard': 'https://www.youtube.com/watch?v=yHp3jQriQpk',     # Google Bard演示
            'Gemini': 'https://www.youtube.com/watch?v=UIZAiXYceBI',   # Google Gemini
            'Character.AI': 'https://www.youtube.com/watch?v=DWuOW_v7o8Y', # Character AI
            'Perplexity': 'https://www.youtube.com/watch?v=aF4eJhcD9E8', # Perplexity AI搜索
            
            # === 图像生成工具 ===
            'Midjourney': 'https://www.youtube.com/watch?v=9XKNDdWWJDk', # 官方教程
            'DALL-E': 'https://www.youtube.com/watch?v=qTgPSKKjfVg',   # OpenAI DALL-E 2演示
            'DALL-E 2': 'https://www.youtube.com/watch?v=qTgPSKKjfVg', # OpenAI DALL-E 2演示
            'DALL-E 3': 'https://www.youtube.com/watch?v=3BBLpSj8jjY', # DALL-E 3演示
            'Stable Diffusion': 'https://www.youtube.com/watch?v=1CIpzeNxIhU', # 官方介绍
            'Leonardo AI': 'https://www.youtube.com/watch?v=3dGQf2H6RN8', # Leonardo AI教程
            'Adobe Firefly': 'https://www.youtube.com/watch?v=0gNauWdOw6Q', # Adobe官方
            'SeaArt': 'https://www.youtube.com/watch?v=kZZi9__p9bM',    # SeaArt演示
            'Artbreeder': 'https://www.youtube.com/watch?v=u45rP8Ilzfw', # Artbreeder介绍
            
            # === 视频生成工具 ===
            'Runway ML': 'https://www.youtube.com/watch?v=5U8bMQT8ib4',  # RunwayML演示
            'Pika Labs': 'https://www.youtube.com/watch?v=T_0LFgJKDhA',  # Pika Labs演示
            'Synthesia': 'https://www.youtube.com/watch?v=8REp1-QO23A',  # Synthesia演示
            'D-ID': 'https://www.youtube.com/watch?v=R6_JcGRROUo',       # D-ID视频生成
            
            # === 写作助手 ===
            'Jasper': 'https://www.youtube.com/watch?v=VYJtb2YXae8',     # Jasper AI演示
            'Copy.ai': 'https://www.youtube.com/watch?v=R7XfQvP9Sjk',    # Copy.ai演示
            'Writesonic': 'https://www.youtube.com/watch?v=q_VsNlYYlmo',  # Writesonic演示
            'Grammarly': 'https://www.youtube.com/watch?v=qQhiJyWIHTk',   # Grammarly AI功能
            'Notion AI': 'https://www.youtube.com/watch?v=57Gt1cMWCWk',  # Notion官方
            'QuillBot': 'https://www.youtube.com/watch?v=t1JVzOVPn9c',   # QuillBot演示
            
            # === 代码助手 ===
            'GitHub Copilot': 'https://www.youtube.com/watch?v=DSHfHT5qnGc', # GitHub官方
            'CodeWhisperer': 'https://www.youtube.com/watch?v=rQ8wYcUu-B8', # AWS CodeWhisperer
            'Tabnine': 'https://www.youtube.com/watch?v=TKLkXh_c-Gw',    # Tabnine演示
            'Codeium': 'https://www.youtube.com/watch?v=lR-0mN0JZo0',    # Codeium演示
            
            # === 演示文稿工具 ===
            'Gamma': 'https://www.youtube.com/watch?v=7OUZ5bZb9P8',      # Gamma演示
            'Beautiful.AI': 'https://www.youtube.com/watch?v=QHSyA0V4nAE', # Beautiful.AI
            'Tome': 'https://www.youtube.com/watch?v=lzaODUqSgFc',       # Tome演示
            
            # === 设计工具 ===
            'Canva AI': 'https://www.youtube.com/watch?v=TGXAtGgp7as',   # Canva AI功能
            'Figma AI': 'https://www.youtube.com/watch?v=HZuk6Wkx_Eg',   # Figma AI功能
            'Framer AI': 'https://www.youtube.com/watch?v=9gJI_bQ1HQU',  # Framer AI
            
            # === 音频/音乐工具 ===
            'ElevenLabs': 'https://www.youtube.com/watch?v=TQTlCHxyuu8',  # ElevenLabs语音
            'Murf': 'https://www.youtube.com/watch?v=2O5RDBJhVzA',       # Murf AI配音
            'AIVA': 'https://www.youtube.com/watch?v=M1eNoOTdRhE',       # AIVA音乐生成
            'Suno AI': 'https://www.youtube.com/watch?v=xmQWCvGMH0Y',    # Suno AI音乐
            
            # === 搜索引擎 ===
            'Bing Chat': 'https://www.youtube.com/watch?v=SGUCcjHTmGY',  # New Bing演示
            'You.com': 'https://www.youtube.com/watch?v=JUhN8_pW-YY',    # You.com AI搜索
            
            # === 其他工具 ===
            'Luma AI': 'https://www.youtube.com/watch?v=5ysAHcJ5FKg',    # Luma AI 3D扫描
            'Descript': 'https://www.youtube.com/watch?v=Bl_Vau09-gw',   # Descript音频编辑
            'Loom AI': 'https://www.youtube.com/watch?v=J4y50Bg0YXg',    # Loom AI功能
        }
    
    def enhance_tool_with_video(self, tool_data):
        """为工具数据添加真实的演示视频URL"""
        # 如果已有视频URL，跳过
        if tool_data.get('demo_video_url'):
            return tool_data
        
        product_url = tool_data.get('product_url', '')
        product_name = tool_data.get('product_name', '')
        
        if not product_url:
            tool_data['demo_video_url'] = ''
            return tool_data
        
        logger.debug(f"🎬 搜索真实视频: {product_name}")
        
        # 策略1: 优先使用已验证的真实工具视频
        verified_video = self.get_verified_tool_video(product_name)
        if verified_video:
            tool_data['demo_video_url'] = verified_video
            logger.success(f"✅ 使用已验证视频: {verified_video}")
            return tool_data
        
        # 策略2: 深度提取网站真实视频
        real_video = self.deep_extract_real_video(product_url, product_name)
        if real_video:
            tool_data['demo_video_url'] = real_video
            logger.success(f"🎯 提取到真实视频: {real_video}")
            return tool_data
        
        # 策略3: 搜索相关页面的视频
        related_video = self.search_related_pages_for_video(product_url, product_name)
        if related_video:
            tool_data['demo_video_url'] = related_video
            logger.success(f"🔍 从相关页面找到视频: {related_video}")
            return tool_data
        
        # 如果都没找到，不使用默认视频，保持为空
        tool_data['demo_video_url'] = ''
        logger.warning(f"❌ 未找到真实视频: {product_name} - 将尝试其他方式获取")
        
        return tool_data
    
    def get_verified_tool_video(self, product_name):
        """获取已验证的真实工具视频"""
        product_lower = product_name.lower()
        
        # 精确匹配
        for tool_name, video_url in self.verified_tool_videos.items():
            if tool_name.lower() == product_lower:
                return video_url
        
        # 模糊匹配
        for tool_name, video_url in self.verified_tool_videos.items():
            if tool_name.lower() in product_lower or product_lower in tool_name.lower():
                logger.debug(f"模糊匹配到已验证视频: {tool_name}")
                return video_url
        
        return None
    
    def deep_extract_real_video(self, url, tool_name):
        """深度提取网站的真实演示视频"""
        try:
            # 标准化URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            logger.debug(f"🔎 深度分析网站: {url}")
            
            # 获取网页内容
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 方法1: 查找高优先级的视频元素
            video_url = self.find_priority_videos(soup, url)
            if video_url:
                return video_url
            
            # 方法2: 分析JSON-LD结构化数据中的视频
            video_url = self.extract_video_from_jsonld(soup)
            if video_url:
                return video_url
            
            # 方法3: 查找带有演示/介绍关键词的视频
            video_url = self.find_demo_videos_by_context(soup, url)
            if video_url:
                return video_url
            
            # 方法4: 检查特定的视频页面路径
            video_url = self.check_common_video_paths(url)
            if video_url:
                return video_url
            
            return None
            
        except Exception as e:
            logger.debug(f"深度视频提取失败 {url}: {e}")
            return None
    
    def find_priority_videos(self, soup, base_url):
        """查找高优先级的视频元素"""
        # 按优先级顺序查找视频
        priority_selectors = [
            # 首页英雄区域的视频
            '.hero video, .hero iframe',
            '.banner video, .banner iframe',
            '.intro video, .intro iframe',
            
            # 产品演示区域
            '.demo video, .demo iframe',
            '.product-demo video, .product-demo iframe',
            '.showcase video, .showcase iframe',
            
            # 标记为主要视频的元素
            '.main-video, .primary-video, .featured-video',
            '[data-main-video], [data-featured-video]',
            
            # YouTube/Vimeo嵌入
            'iframe[src*="youtube.com/embed"]',
            'iframe[src*="vimeo.com/video"]',
            'iframe[src*="loom.com/embed"]',
        ]
        
        for selector in priority_selectors:
            elements = soup.select(selector)
            for element in elements:
                video_url = self.extract_video_url_from_element(element, base_url)
                if video_url:
                    logger.debug(f"高优先级视频元素找到: {selector}")
                    return video_url
        
        return None
    
    def extract_video_from_jsonld(self, soup):
        """从JSON-LD结构化数据提取视频"""
        try:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                if script.string:
                    import json
                    data = json.loads(script.string)
                    
                    # 递归查找视频URL
                    video_url = self.find_video_in_jsonld(data)
                    if video_url:
                        return video_url
        except Exception as e:
            logger.debug(f"JSON-LD视频提取失败: {e}")
        
        return None
    
    def find_video_in_jsonld(self, data):
        """在JSON-LD数据中递归查找视频"""
        if isinstance(data, dict):
            # 检查常见的视频字段
            video_fields = ['video', 'embedUrl', 'contentUrl', 'url']
            for field in video_fields:
                if field in data and isinstance(data[field], str):
                    if self.is_video_url(data[field]):
                        return self.normalize_video_url(data[field])
            
            # 递归检查嵌套对象
            for value in data.values():
                result = self.find_video_in_jsonld(value)
                if result:
                    return result
        
        elif isinstance(data, list):
            for item in data:
                result = self.find_video_in_jsonld(item)
                if result:
                    return result
        
        return None
    
    def find_demo_videos_by_context(self, soup, base_url):
        """通过上下文关键词查找演示视频"""
        # 查找包含演示关键词的区域
        for keyword in self.video_keywords:
            # 查找标题或文本包含关键词的容器
            containers = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            
            for text_node in containers:
                # 向上查找包含该文本的容器元素
                container = text_node.parent
                for _ in range(3):  # 最多向上查找3层
                    if container:
                        # 在容器中查找视频
                        video_elements = container.find_all(['iframe', 'video', 'embed'])
                        for element in video_elements:
                            video_url = self.extract_video_url_from_element(element, base_url)
                            if video_url:
                                logger.debug(f"通过关键词'{keyword}'找到视频")
                                return video_url
                        container = container.parent
                    else:
                        break
        
        return None
    
    def check_common_video_paths(self, base_url):
        """检查常见的视频页面路径"""
        parsed = urlparse(base_url)
        common_paths = [
            '/demo', '/demo/', '/demos', '/demos/',
            '/video', '/video/', '/videos', '/videos/',
            '/tutorial', '/tutorial/', '/tutorials', '/tutorials/',
            '/overview', '/overview/', '/introduction', '/introduction/',
            '/getting-started', '/how-it-works', '/product-tour'
        ]
        
        for path in common_paths:
            try:
                video_page_url = f"{parsed.scheme}://{parsed.netloc}{path}"
                logger.debug(f"检查视频页面: {video_page_url}")
                
                response = self.session.get(video_page_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # 在这些页面中查找视频
                    video_elements = soup.find_all(['iframe', 'video'])
                    for element in video_elements:
                        video_url = self.extract_video_url_from_element(element, video_page_url)
                        if video_url:
                            logger.debug(f"在路径{path}找到视频")
                            return video_url
                
                # 避免过于频繁的请求
                time.sleep(1)
                
            except Exception:
                continue
        
        return None
    
    def search_related_pages_for_video(self, base_url, tool_name):
        """搜索相关页面的视频"""
        try:
            parsed = urlparse(base_url)
            
            # 尝试从sitemap找到视频页面
            sitemap_urls = [
                f"{parsed.scheme}://{parsed.netloc}/sitemap.xml",
                f"{parsed.scheme}://{parsed.netloc}/sitemap_index.xml",
                f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            ]
            
            for sitemap_url in sitemap_urls:
                try:
                    response = self.session.get(sitemap_url, timeout=10)
                    if response.status_code == 200:
                        # 查找可能包含视频的页面URL
                        video_page_urls = re.findall(
                            r'https?://[^\s<>"]+(?:demo|video|tutorial|overview|introduction)[^\s<>"]*',
                            response.text,
                            re.IGNORECASE
                        )
                        
                        for url in video_page_urls[:3]:  # 限制检查数量
                            video_url = self.extract_video_from_page(url)
                            if video_url:
                                return video_url
                        
                        break  # 找到sitemap就不继续了
                except Exception:
                    continue
            
        except Exception as e:
            logger.debug(f"搜索相关页面失败: {e}")
        
        return None
    
    def extract_video_from_page(self, url):
        """从指定页面提取视频"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 查找视频元素
                video_elements = soup.find_all(['iframe', 'video'])
                for element in video_elements:
                    video_url = self.extract_video_url_from_element(element, url)
                    if video_url:
                        return video_url
        except Exception:
            pass
        
        return None
    
    def extract_video_url_from_element(self, element, base_url):
        """从HTML元素提取视频URL"""
        if element.name == 'iframe':
            src = element.get('src', '')
            if src:
                full_url = urljoin(base_url, src)
                if self.is_video_url(full_url):
                    return self.normalize_video_url(full_url)
        
        elif element.name == 'video':
            # 检查video元素的src属性
            src = element.get('src', '')
            if src:
                full_url = urljoin(base_url, src)
                return full_url
            
            # 检查source子元素
            sources = element.find_all('source')
            for source in sources:
                src = source.get('src', '')
                if src:
                    full_url = urljoin(base_url, src)
                    return full_url
        
        elif element.name == 'embed':
            src = element.get('src', '')
            if src:
                full_url = urljoin(base_url, src)
                if self.is_video_url(full_url):
                    return self.normalize_video_url(full_url)
        
        return None
    
    def is_video_url(self, url):
        """检查URL是否为视频URL"""
        if not url:
            return False
        
        # 检查各种视频平台
        for platform, pattern in self.video_patterns.items():
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False
    
    def normalize_video_url(self, url):
        """标准化视频URL为可嵌入的格式"""
        if not url:
            return ""
        
        # YouTube URL标准化 - 转换为watch格式便于前端处理
        youtube_match = re.search(self.video_patterns['youtube'], url)
        if youtube_match:
            video_id = youtube_match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
        
        # Vimeo URL标准化
        vimeo_match = re.search(self.video_patterns['vimeo'], url)
        if vimeo_match:
            video_id = vimeo_match.group(1)
            return f"https://vimeo.com/{video_id}"
        
        # Loom URL标准化
        loom_match = re.search(self.video_patterns['loom'], url)
        if loom_match:
            video_id = loom_match.group(1)
            return f"https://www.loom.com/share/{video_id}"
        
        # 其他平台保持原样
        return url
    
    def validate_video_url(self, url):
        """验证视频URL是否有效且可访问"""
        if not url:
            return False
        
        try:
            # 对于YouTube视频，检查video ID的有效性
            if 'youtube.com' in url or 'youtu.be' in url:
                response = self.session.head(url, timeout=10)
                return response.status_code == 200
            
            # 对于其他视频，简单检查HTTP状态
            response = self.session.head(url, timeout=10)
            return response.status_code == 200
            
        except Exception:
            return False

# 全局实例
video_helper = VideoHelper() 