#!/usr/bin/env python3
"""
下载 SBTI 人格图鉴的所有图片
"""
import os
import urllib.request
import urllib.error
from urllib.parse import urlparse
import time

# 创建保存目录
save_dir = "/Users/zhaoyang/iFlow/aiteacher-2/sbti_images"
os.makedirs(save_dir, exist_ok=True)

# 所有图片链接
images = [
    {"src": "https://luoluo.help/sbti/CTRL.webp", "alt": "CTRL（拿捏者）"},
    {"src": "https://luoluo.help/sbti/ATM-er.webp", "alt": "ATM-er（送钱者）"},
    {"src": "https://luoluo.help/sbti/Dior-s.webp", "alt": "Dior-s（屌丝）"},
    {"src": "https://luoluo.help/sbti/BOSS.webp", "alt": "BOSS（领导者）"},
    {"src": "https://luoluo.help/sbti/THAN-K.webp", "alt": "THAN-K（感恩者）"},
    {"src": "https://luoluo.help/sbti/OH-NO.webp", "alt": "OH-NO（哦不人）"},
    {"src": "https://luoluo.help/sbti/GOGO.webp", "alt": "GOGO（行者）"},
    {"src": "https://luoluo.help/sbti/SEXY.webp", "alt": "SEXY（尤物）"},
    {"src": "https://luoluo.help/sbti/LOVE-R.webp", "alt": "LOVE-R（多情者）"},
    {"src": "https://luoluo.help/sbti/MUM.webp", "alt": "MUM（妈妈）"},
    {"src": "https://luoluo.help/sbti/FAKE.webp", "alt": "FAKE（伪人）"},
    {"src": "https://luoluo.help/sbti/OJBK.webp", "alt": "OJBK（无所谓人）"},
    {"src": "https://luoluo.help/sbti/MALO.webp", "alt": "MALO（吗喽）"},
    {"src": "https://luoluo.help/sbti/JOKE-R.webp", "alt": "JOKE-R（小丑）"},
    {"src": "https://luoluo.help/sbti/WOC.webp", "alt": "WOC!（握草人）"},
    {"src": "https://luoluo.help/sbti/THIN-K.webp", "alt": "THIN-K（思考者）"},
    {"src": "https://luoluo.help/sbti/SHIT.webp", "alt": "SHIT（愤世者）"},
    {"src": "https://luoluo.help/sbti/ZZZZ.webp", "alt": "ZZZZ（装死者）"},
    {"src": "https://luoluo.help/sbti/POOR.webp", "alt": "POOR（贫困者）"},
    {"src": "https://luoluo.help/sbti/MONK.webp", "alt": "MONK（僧人）"},
    {"src": "https://luoluo.help/sbti/IMSB.webp", "alt": "IMSB（傻者）"},
    {"src": "https://luoluo.help/sbti/SOLO.webp", "alt": "SOLO（孤儿）"},
    {"src": "https://luoluo.help/sbti/FUCK.webp", "alt": "FUCK（草者）"},
    {"src": "https://luoluo.help/sbti/DEAD.webp", "alt": "DEAD（死者）"},
    {"src": "https://luoluo.help/sbti/IMFW.webp", "alt": "IMFW（废物）"},
    {"src": "https://luoluo.help/sbti/HHHH.webp", "alt": "HHHH（傻乐者）"},
    {"src": "https://luoluo.help/sbti/DRUNK.webp", "alt": "DRUNK（酒鬼）"},
]

# 请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://luoluo.help/sbti'
}

print(f"开始下载 SBTI 人格图鉴，共 {len(images)} 张图片...")
print(f"保存目录: {save_dir}\n")

success_count = 0
fail_count = 0

for i, img_info in enumerate(images, 1):
    url = img_info['src']
    alt = img_info['alt']
    
    # 从 URL 中提取文件名
    filename = os.path.basename(urlparse(url).path)
    filepath = os.path.join(save_dir, filename)
    
    try:
        print(f"[{i}/{len(images)}] 正在下载: {alt} ({filename})...")
        
        # 创建请求对象
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req, timeout=30)
        
        # 读取图片内容
        image_data = response.read()
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        file_size = len(image_data)
        print(f"    ✓ 下载成功! 大小: {file_size / 1024:.2f} KB")
        success_count += 1
        
        # 添加延迟，避免请求过快
        time.sleep(0.5)
        
    except Exception as e:
        print(f"    ✗ 下载失败: {e}")
        fail_count += 1

print(f"\n下载完成!")
print(f"成功: {success_count} 张")
print(f"失败: {fail_count} 张")
print(f"图片保存在: {save_dir}")
