import csv
import json
from urllib.parse import urlparse

def parse_ai_tools_csv(csv_file_path):
    """
    解析多列格式的AI工具CSV文件
    CSV格式：每个类别占两列（产品名称，网址），从第3列开始
    """
    tools_data = []
    
    # 定义类别映射（根据CSV文件头部）
    categories = [
        "AI Search Engine",
        "AI ChatBots", 
        "AI Character Generator",
        "AI Presentation Maker",
        "AI Image Generator",
        "AI Image Editor",
        "AI Image Enhancer", 
        "AI Video Generator",
        "AI Video Editing",
        "AI Music Generator"
    ]
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)
        
        # 跳过前两行标题
        data_rows = rows[2:]
        
        for row in data_rows:
            if len(row) < 2:  # 跳过空行或不完整行
                continue
                
            # 处理每个类别的数据
            for i, category in enumerate(categories):
                name_col = 1 + i * 2  # 产品名称列索引
                url_col = 2 + i * 2   # 网址列索引
                
                if len(row) > url_col and row[name_col].strip() and row[url_col].strip():
                    product_name = row[name_col].strip()
                    product_url = row[url_col].strip()
                    
                    # 验证和清理URL
                    clean_url = sanitize_url(product_url)
                    
                    if clean_url:
                        tools_data.append({
                            "category": category,
                            "product_name": product_name,
                            "url": clean_url
                        })
    
    return tools_data

def sanitize_url(url_str):
    """清理和验证URL"""
    if not url_str:
        return None
        
    url_str = url_str.strip()
    
    # 添加协议前缀
    if not url_str.startswith(("http://", "https://")):
        url_str = "https://" + url_str
    
    # 基本URL验证
    try:
        parsed = urlparse(url_str)
        if parsed.netloc:
            return url_str
    except:
        pass
    
    return None

def export_to_standard_csv(tools_data, output_file):
    """导出为标准的三列CSV格式"""
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Category', 'Product Name', 'URL'])
        
        for tool in tools_data:
            writer.writerow([tool['category'], tool['product_name'], tool['url']])

def main():
    # 解析原始CSV文件
    print("正在解析CSV文件...")
    tools_data = parse_ai_tools_csv("AI工具汇总-工作表2.csv")
    
    print(f"解析完成，共找到 {len(tools_data)} 个AI工具")
    
    # 按类别统计
    category_count = {}
    for tool in tools_data:
        category = tool['category']
        category_count[category] = category_count.get(category, 0) + 1
    
    print("\n按类别统计：")
    for category, count in category_count.items():
        print(f"  {category}: {count} 个工具")
    
    # 导出为标准CSV格式
    export_to_standard_csv(tools_data, "ai_tools_processed.csv")
    print("\n已导出为标准CSV格式: ai_tools_processed.csv")
    
    # 保存为JSON格式
    with open("ai_tools_data.json", 'w', encoding='utf-8') as f:
        json.dump(tools_data, f, ensure_ascii=False, indent=2)
    print("已保存为JSON格式: ai_tools_data.json")
    
    return tools_data

if __name__ == "__main__":
    main() 