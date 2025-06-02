"""
AI工具导入系统 - 网站截图辅助器
"""

import requests
import time
from urllib.parse import urlparse, quote
from config import config
from logger import logger

class ScreenshotHelper:
    """网站截图辅助器"""
    
    def __init__(self):
        self.timeout = config.REQUEST_TIMEOUT
    
    def get_website_screenshot(self, url: str, tool_name: str = "") -> str:
        """获取网站截图URL"""
        if not url:
            return ""
        
        try:
            # 标准化URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed_url = urlparse(url)
            if not parsed_url.netloc:
                logger.warning(f"无效的URL: {url}")
                return ""
            
            # 方法1: 使用Screenshot Machine API (免费服务)
            screenshot_url = self._try_screenshot_machine(url)
            if screenshot_url:
                logger.debug(f"使用Screenshot Machine获取截图: {screenshot_url}")
                return screenshot_url
            
            # 方法2: 使用Website Screenshot API
            screenshot_url = self._try_website_screenshot_api(url)
            if screenshot_url:
                logger.debug(f"使用Website Screenshot API获取截图: {screenshot_url}")
                return screenshot_url
            
            # 方法3: 使用HTMLCSStoImage API
            screenshot_url = self._try_htmlcsstoimage(url)
            if screenshot_url:
                logger.debug(f"使用HTMLCSStoImage获取截图: {screenshot_url}")
                return screenshot_url
            
            # 方法4: 使用Webpage Screenshot API
            screenshot_url = self._try_webpage_screenshot(url)
            if screenshot_url:
                logger.debug(f"使用Webpage Screenshot获取截图: {screenshot_url}")
                return screenshot_url
            
            logger.warning(f"无法获取网站截图: {url}")
            return ""
            
        except Exception as e:
            logger.error(f"获取截图异常 {url}: {e}")
            return ""
    
    def _try_screenshot_machine(self, url: str) -> str:
        """尝试使用Screenshot Machine服务"""
        try:
            # Screenshot Machine - 使用用户提供的API密钥
            api_key = config.SCREENSHOT_API_KEY or 'demo'
            encoded_url = quote(url, safe='')
            screenshot_url = f"https://api.screenshotmachine.com/?key={api_key}&url={encoded_url}&dimension=1920x1080&device=desktop&cacheLimit=0"
            
            # 验证截图是否可访问
            if self._verify_image_url(screenshot_url):
                return screenshot_url
            
            return ""
        except Exception:
            return ""
    
    def _try_website_screenshot_api(self, url: str) -> str:
        """尝试使用Website Screenshot API"""
        try:
            # Website Screenshot API - 免费服务
            encoded_url = quote(url, safe='')
            screenshot_url = f"https://api.website-screenshot.net/screenshot?url={encoded_url}&width=1920&height=1080&format=png"
            
            if self._verify_image_url(screenshot_url):
                return screenshot_url
            
            return ""
        except Exception:
            return ""
    
    def _try_htmlcsstoimage(self, url: str) -> str:
        """尝试使用HTMLCSStoImage服务"""
        try:
            # HTMLCSStoImage - 有免费额度
            encoded_url = quote(url, safe='')
            screenshot_url = f"https://hcti.io/v1/image?url={encoded_url}&viewport_width=1920&viewport_height=1080"
            
            if self._verify_image_url(screenshot_url):
                return screenshot_url
            
            return ""
        except Exception:
            return ""
    
    def _try_webpage_screenshot(self, url: str) -> str:
        """尝试使用简单的截图服务"""
        try:
            # 简单的截图服务
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # 方法1: 使用thumbnail服务
            screenshot_url = f"https://image.thum.io/get/width/1200/crop/800/noanimate/{url}"
            if self._verify_image_url(screenshot_url):
                return screenshot_url
            
            # 方法2: 使用另一个截图服务
            screenshot_url = f"https://mini.s-shot.ru/1920x1080/JPEG/1024/Z100/?{url}"
            if self._verify_image_url(screenshot_url):
                return screenshot_url
            
            return ""
        except Exception:
            return ""
    
    def _verify_image_url(self, url: str, timeout: int = 10) -> bool:
        """验证图片URL是否有效"""
        try:
            response = requests.head(url, timeout=timeout, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                return content_type.startswith('image/') or 'image' in content_type.lower()
            
            return False
        except Exception:
            return False
    
    def enhance_tool_with_screenshot(self, tool_data: dict) -> dict:
        """为工具数据添加截图"""
        if tool_data.get('overview_img_url'):
            return tool_data  # 已有截图，跳过
        
        product_url = tool_data.get('product_url', '')
        product_name = tool_data.get('product_name', '')
        
        if not product_url:
            return tool_data
        
        logger.debug(f"获取截图: {product_name}")
        screenshot_url = self.get_website_screenshot(product_url, product_name)
        
        if screenshot_url:
            tool_data['overview_img_url'] = screenshot_url
            logger.success(f"✓ 添加截图: {screenshot_url}")
        else:
            logger.warning(f"未能获取截图: {product_name}")
        
        return tool_data

# 全局实例
screenshot_helper = ScreenshotHelper() 