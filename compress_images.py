#!/usr/bin/env python3
"""
压缩图片，将总大小控制在目标范围内
"""
import os
import subprocess
from pathlib import Path

# 图片目录
image_dir = Path("/Users/zhaoyang/WeChatProjects/miniprogram-1/sbti/sbti_images")
target_size_kb = 200  # 目标总大小 KB

# 获取所有 PNG 图片
images = list(image_dir.glob("*.png"))

# 计算当前总大小
current_size = sum(img.stat().st_size for img in images)
current_size_kb = current_size / 1024

print(f"当前图片数量: {len(images)}")
print(f"当前总大小: {current_size_kb:.2f} KB")
print(f"目标大小: {target_size_kb} KB")

# 计算需要的压缩比例
compression_ratio = target_size_kb / current_size_kb
print(f"需要压缩到: {compression_ratio * 100:.1f}%")

# 计算每张图片的目标大小
target_per_image_kb = target_size_kb / len(images)
print(f"每张图片目标大小: {target_per_image_kb:.2f} KB")

# 创建临时目录存放压缩后的图片
temp_dir = image_dir / "temp"
temp_dir.mkdir(exist_ok=True)

print("\n开始压缩...")

# 使用 sips 压缩每张图片
for i, img_path in enumerate(images, 1):
    temp_path = temp_dir / img_path.name
    
    # 获取原始文件大小
    original_size = img_path.stat().st_size / 1024
    
    # 使用 sips 转换为 JPEG 并设置质量
    # 先尝试转换为 JPEG 格式（比 PNG 更小）
    jpeg_path = temp_dir / (img_path.stem + ".jpg")
    
    try:
        # 使用 sips 转换格式并调整质量
        # 更激进的压缩：更低的质量和更小的尺寸
        result = subprocess.run([
            'sips',
            '-s', 'format', 'jpeg',
            '-s', 'formatOptions', '25',  # 降低质量到 25
            '--resampleWidth', '300',  # 限制宽度为 300px
            str(img_path),
            '--out', str(jpeg_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            # 检查压缩后的大小
            compressed_size = jpeg_path.stat().st_size / 1024
            print(f"[{i}/{len(images)}] {img_path.name}: {original_size:.1f}KB -> {compressed_size:.1f}KB (JPEG)")
        else:
            print(f"[{i}/{len(images)}] {img_path.name}: 压缩失败，保留原文件")
            jpeg_path = img_path
    except Exception as e:
        print(f"[{i}/{len(images)}] {img_path.name}: 错误 - {e}")
        jpeg_path = img_path

# 计算压缩后的总大小
final_images = list(temp_dir.glob("*.jpg"))
final_size = sum(img.stat().st_size for img in final_images)
final_size_kb = final_size / 1024

print(f"\n压缩后总大小: {final_size_kb:.2f} KB")

if final_size_kb <= target_size_kb:
    print("✓ 压缩成功！目标达成！")
else:
    print(f"✗ 压缩后仍超出目标 {final_size_kb - target_size_kb:.2f} KB，需要进一步压缩")

print(f"\n压缩后的图片保存在: {temp_dir}")
