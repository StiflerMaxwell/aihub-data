#!/usr/bin/env python3
"""
AI工具导入系统 - Favicon和Logo获取助手
"""

import requests
from urllib.parse import urlparse, urljoin
from config import config
from logger import logger

class FaviconHelper:
    """Favicon和Logo获取助手"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = config.REQUEST_TIMEOUT
    
    def get_favicon_url(self, website_url):
        """获取网站的favicon URL"""
        if not website_url:
            return None
            
        try:
            # 标准化URL
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
                
            parsed_url = urlparse(website_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            domain = parsed_url.netloc
            
            logger.debug(f"获取favicon: {website_url}")
            
            # 方法1: 尝试标准favicon路径
            standard_favicon = urljoin(base_url, '/favicon.ico')
            if self._check_url_exists(standard_favicon):
                logger.debug(f"找到标准favicon: {standard_favicon}")
                return standard_favicon
            
            # 方法2: 使用第三方服务
            fallback_services = [
                f"https://www.google.com/s2/favicons?domain={domain}&sz=64",
                f"https://favicon.yandex.net/favicon/{domain}",
                f"https://icons.duckduckgo.com/ip3/{domain}.ico"
            ]
            
            for service_url in fallback_services:
                if self._check_url_exists(service_url):
                    logger.debug(f"使用第三方服务: {service_url}")
                    return service_url
            
            logger.warning(f"未找到favicon: {website_url}")
            return None
            
        except Exception as e:
            logger.error(f"获取favicon失败: {e}")
            return None
    
    def _check_url_exists(self, url):
        """检查URL是否存在"""
        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except Exception:
            return False
    
    def enhance_tool_with_favicon(self, tool_data):
        """为工具数据添加favicon"""
        if not tool_data.get('logo_img_url'):
            favicon_url = self.get_favicon_url(tool_data.get('product_url'))
            if favicon_url:
                tool_data['logo_img_url'] = favicon_url
                logger.debug(f"添加favicon: {favicon_url}")
        
        return tool_data

# 全局实例
favicon_helper = FaviconHelper() 