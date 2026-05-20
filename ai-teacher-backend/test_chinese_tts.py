"""
中文 TTS 测试脚本
使用 Edge TTS（微软免费语音合成）生成中文语音

特点：
- 支持中文（简体/繁体）
- 多种音色可选
- 音质好，接近真人
- 需要网络连接
"""

import asyncio
import edge_tts
import os

# 输出文件
OUTPUT_FILE = "chinese_output.mp3"

# 测试文本
TEXT = "你好，这是一个中文语音合成测试。Edge TTS 支持高质量的中文语音生成，非常适合用于教育、播客、有声阅读等场景。"

# 中文语音列表（常用）
CHINESE_VOICES = [
    "zh-CN-XiaoxiaoNeural",     # 女声，温柔
    "zh-CN-YunxiNeural",        # 男声，年轻
    "zh-CN-YunjianNeural",      # 男声，成熟
    "zh-CN-XiaoyiNeural",       # 女声，活泼
]

async def list_chinese_voices():
    """列出所有可用的中文语音"""
    voices = await edge_tts.list_voices()
    chinese_voices = [v for v in voices if v['Locale'].startswith('zh-')]
    
    print("可用的中文语音:")
    print("-" * 60)
    for voice in chinese_voices:
        print(f"  {voice['ShortName']:30s} - {voice['Gender']:8s} - {voice.get('VoiceTag', {}).get('VoicePersonalName', '')}")
    print("-" * 60)
    print(f"共找到 {len(chinese_voices)} 种中文语音")
    return chinese_voices

async def synthesize_chinese(text, voice="zh-CN-XiaoxiaoNeural", output_file=OUTPUT_FILE):
    """
    合成中文语音
    
    参数:
        text: 要合成的文本
        voice: 语音名称
        output_file: 输出文件路径
    """
    print(f"\n开始合成语音...")
    print(f"  语音: {voice}")
    print(f"  文本: {text}")
    print(f"  输出: {output_file}")
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file) / 1024  # KB
        print(f"\n✓ 合成成功！")
        print(f"  文件大小: {file_size:.1f} KB")
        return True
    else:
        print("\n✗ 合成失败！")
        return False

async def main():
    print("=" * 60)
    print("中文 TTS 测试 (Edge TTS)")
    print("=" * 60)
    
    # 1. 列出可用语音
    await list_chinese_voices()
    
    # 2. 使用默认语音合成
    print("\n" + "=" * 60)
    print("使用默认语音 (Xiaoxiao) 合成")
    print("=" * 60)
    await synthesize_chinese(TEXT, voice="zh-CN-XiaoxiaoNeural", output_file="output_xiaoxiao.mp3")
    
    # 3. 使用不同语音合成
    print("\n" + "=" * 60)
    print("使用男声 (Yunxi) 合成")
    print("=" * 60)
    await synthesize_chinese(TEXT, voice="zh-CN-YunxiNeural", output_file="output_yunxi.mp3")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
