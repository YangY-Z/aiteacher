#!/usr/bin/env python3
"""
OpenHuman Voice Demo - STT & TTS
基于 whisper.cpp 和 Piper 的本地语音转文本和文本转语音示例

依赖安装:
  pip install sounddevice numpy wave subprocess asyncio

环境要求:
  - whisper-cli: brew install whisper-cpp (macOS) 或从源码编译
  - piper: 从 https://github.com/rhasspy/piper/releases 下载
  - Whisper 模型: 从 https://huggingface.co/ggerganov/whisper.cpp 下载 GGML 模型

使用方法:
  python voice_demo.py           # 交互式语音对话
  python voice_demo.py --stt     # 仅测试 STT
  python voice_demo.py --tts     # 仅测试 TTS
"""

import argparse
import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd
import wave

import os
# Use huggingface mirror to avoid SSL issues
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"


class SherpaTTS:
    """
    使用 sherpa-onnx 进行离线文本转语音
    优点：完全离线、支持中文、音质好
    缺点：首次需要下载模型
    """

    def __init__(self, model_name: str = "vits-melo-tts-zh_en"):
        self.model_name = model_name
        self.model_dir = None
        self.tts = None
        
        try:
            import sherpa_onnx
            self._sherpa_onnx = sherpa_onnx
            # 自动下载并加载模型
            self._download_and_load_model()
            print(f"✓ 使用 sherpa-onnx (模型: {model_name})")
        except ImportError:
            print(f"⚠️ sherpa-onnx 未安装")
            print(f"   安装: pip install sherpa-onnx")

    def _download_and_load_model(self):
        """下载并加载模型"""
        import requests
        import tarfile
        import io
        
        # 模型目录
        model_base_dir = Path("~/.openhuman/models").expanduser()
        model_base_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_dir = model_base_dir / self.model_name
        
        # 如果模型不存在，下载
        if not self.model_dir.exists():
            print(f"📥 正在下载 sherpa-onnx 模型: {self.model_name}...")
            
            # 构建下载 URL（GitHub Release 直连）
            if self.model_name == "vits-melo-tts-zh_en":
                tarball_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-melo-tts-zh_en.tar.bz2"
            elif self.model_name == "vits-zh-hf-fanchen-C":
                tarball_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-zh-hf-fanchen-C.tar.bz2"
            elif self.model_name == "vits-zh-hf-theresa":
                tarball_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-zh-hf-theresa.tar.bz2"
            elif self.model_name == "matcha-icefall-zh-baker":
                tarball_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/matcha-icefall-zh-baker.tar.bz2"
            else:
                raise ValueError(f"不支持的模型: {self.model_name}")
            
            # 使用 requests 下载（禁用 SSL 验证）
            print(f"🌐 下载链接: {tarball_url}")
            response = requests.get(tarball_url, verify=False, stream=True, timeout=300)
            response.raise_for_status()
            
            # 显示下载进度
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            # 下载完整内容
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = downloaded / total_size * 100
                        print(f"\r  下载进度: {progress:.1f}% ({downloaded/1024/1024:.1f}MB/{total_size/1024/1024:.1f}MB)", end="", flush=True)
            
            print()  # 换行
            
            # 直接解压到目标目录
            with tarfile.open(fileobj=io.BytesIO(content), mode='r:bz2') as tar:
                tar.extractall(path=model_base_dir)
            
            print(f"✓ 模型下载完成: {self.model_dir}")
        
        # 加载模型
        print(f"🔄 正在加载模型...")
        model_config = self._create_model_config()
        self.tts = self._sherpa_onnx.OfflineTts(model_config)
        print(f"✓ 模型加载完成")

    def _create_model_config(self):
        """创建模型配置"""
        # 根据模型类型创建不同的配置
        if self.model_name == "vits-melo-tts-zh_en":
            return self._sherpa_onnx.OfflineTtsModelConfig(
                vits=self._sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=str(self.model_dir / "model.onnx"),
                    lexicon=str(self.model_dir / "lexicon.txt"),
                    data_dir=str(self.model_dir / "espeak-ng-data"),
                ),
            )
        elif self.model_name == "vits-zh-hf-fanchen-C":
            return self._sherpa_onnx.OfflineTtsModelConfig(
                vits=self._sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=str(self.model_dir / "model.onnx"),
                    lexicon=str(self.model_dir / "lexicon.txt"),
                    data_dir=str(self.model_dir / "espeak-ng-data"),
                    tokens=str(self.model_dir / "tokens.txt"),
                ),
            )
        else:
            raise ValueError(f"不支持的模型: {self.model_name}")

    def synthesize(self, text: str, output_file: Optional[str] = None, speaker_id: int = 0, speed: float = 1.0) -> str:
        """
        合成语音
        返回输出文件路径
        """
        if self.tts is None:
            raise RuntimeError("sherpa-onnx TTS 未初始化")

        if output_file is None:
            output_file = tempfile.mktemp(suffix=".wav", prefix="tts_")

        # 合成语音
        audio = self.tts.generate(text, speaker_id=speaker_id, speed=speed)
        
        # 保存为 WAV 文件
        import wave
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(audio.sample_rate)
            wf.writeframes(audio.samples.astype(np.int16).tobytes())
        
        print(f"✓ TTS 完成: {output_file}")
        return output_file


class AudioRecorder:
    """麦克风录音 - 类似 Rust 的 audio_capture.rs"""

    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels

    def record(self, duration: Optional[float] = None, silence_threshold: float = 0.01, silence_duration: float = 1.0) -> bytes:
        """
        录音直到指定时长或检测到静音
        支持静音门控，类似 Rust 版的 500ms 静音阈值
        """
        print("🎤 开始录音... (按 Ctrl+C 停止)")

        audio_data = []
        silence_start = None
        recording_started = False

        def callback(indata, frames, time_info, status):
            nonlocal silence_start, recording_started

            if status:
                print(f"⚠️ 录音状态: {status}")

            audio_chunk = indata.copy()
            audio_data.append(audio_chunk)

            # 静音检测 - 计算 RMS 能量
            rms = np.sqrt(np.mean(audio_chunk ** 2))

            if rms > silence_threshold:
                recording_started = True
                silence_start = None
            elif recording_started:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > silence_duration:
                    raise sd.CallbackStop()

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32',
                callback=callback
            ):
                if duration:
                    sd.sleep(int(duration * 1000))
                else:
                    while True:
                        sd.sleep(100)
        except sd.CallbackStop:
            print("\n✓ 检测到静音，停止录音")
        except KeyboardInterrupt:
            print("\n✓ 手动停止录音")

        if not audio_data:
            raise ValueError("未录制到任何音频")

        # 拼接所有音频块
        audio = np.concatenate(audio_data, axis=0)

        # 转换为 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)

        return audio_int16.tobytes(), len(audio_int16)

    def save_wav(self, audio_bytes: bytes, num_samples: int, filepath: str):
        """保存为 WAV 文件 - 16kHz 单声道"""
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_bytes)
        print(f"💾 音频已保存: {filepath}")


class WhisperSTT:
    """
    本地语音转文本 - 类似 Rust 的 local_transcribe.rs
    支持两种模式:
    1. whisper-cli 子进程
    2. 使用 faster-whisper (Python 库)
    """

    def __init__(self, whisper_bin: Optional[str] = None, model: str = "base"):
        self.whisper_bin = whisper_bin or os.environ.get("WHISPER_BIN", "whisper-cli")
        self.model = model
        self._use_faster_whisper = False

        # 尝试导入 faster-whisper (更快的 Python 实现)
        try:
            from faster_whisper import WhisperModel
            self.faster_model = WhisperModel(model, device="cpu", compute_type="int8")
            self._use_faster_whisper = True
            print(f"✓ 使用 faster-whisper (模型: {model})")
        except ImportError:
            print(f"⚠️ faster-whisper 未安装，将使用 whisper-cli 子进程")
            print(f"   安装: pip install faster-whisper")

    def transcribe(self, audio_file: str) -> str:
        """转录音频文件"""
        if self._use_faster_whisper:
            return self._transcribe_faster(audio_file)
        else:
            return self._transcribe_cli(audio_file)

    def _transcribe_faster(self, audio_file: str) -> str:
        """使用 faster-whisper 转录"""
        segments, info = self.faster_model.transcribe(
            audio_file,
            beam_size=5,
            language="zh"  # 可改为 auto 自动检测
        )

        print(f"📊 检测语言: {info.language} (置信度: {info.language_probability:.2f})")

        text = " ".join([segment.text for segment in segments])
        return text.strip()

    def _transcribe_cli(self, audio_file: str) -> str:
        """使用 whisper-cli 子进程转录"""
        if not os.path.exists(self.whisper_bin):
            raise FileNotFoundError(
                f"whisper-cli 未找到: {self.whisper_bin}\n"
                "请设置 WHISPER_BIN 环境变量或安装 whisper.cpp:\n"
                "  macOS: brew install whisper-cpp\n"
                "  其他: https://github.com/ggerganov/whisper.cpp"
            )

        model_path = self._resolve_model_path()

        import subprocess
        cmd = [
            self.whisper_bin,
            "-m", model_path,
            "-f", audio_file,
            "-l", "zh",  # 中文
            "--output-txt"
        ]

        print(f"🔄 执行: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"whisper-cli 失败: {result.stderr}")

        # 读取输出文本
        output_file = audio_file.replace('.wav', '.txt')
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        else:
            return result.stdout.strip()

    def _resolve_model_path(self) -> str:
        """解析 Whisper 模型路径"""
        model_variants = [
            f"ggml-{self.model}.bin",
            f"ggml-{self.model}.gguf",
        ]

        search_paths = [
            Path(os.environ.get("WHISPER_MODEL_DIR", "~/.openhuman/models/whisper")).expanduser(),
            Path("/usr/local/share/whisper.cpp/models"),
        ]

        for search_path in search_paths:
            for variant in model_variants:
                model_path = search_path / variant
                if model_path.exists():
                    return str(model_path)

        raise FileNotFoundError(
            f"Whisper 模型未找到: {self.model}\n"
            "请下载模型到 ~/.openhuman/models/whisper/\n"
            "下载: https://huggingface.co/ggerganov/whisper.cpp/tree/main"
        )


class PiperTTS:
    """
    本地文本转语音 - 类似 Rust 的 local_speech.rs
    使用 Piper TTS 子进程
    """

    def __init__(self, piper_bin: Optional[str] = None, voice: Optional[str] = None):
        self.piper_bin = piper_bin or os.environ.get("PIPER_BIN", "piper")
        self.voice = voice or os.environ.get("PIPER_VOICE", "en_US-lessac-medium")
        self.voice_model = None

        # 尝试使用 piper-python (Python 库)
        try:
            from piper import PiperVoice
            self._use_piper_python = True
            print(f"✓ 使用 piper-python (声音: {self.voice})")
        except ImportError:
            self._use_piper_python = False
            print(f"⚠️ piper-python 未安装，将使用 piper 子进程")
            print(f"   安装: pip install piper-tts")

    def synthesize(self, text: str, output_file: Optional[str] = None) -> str:
        """
        合成语音
        返回输出文件路径
        """
        if output_file is None:
            output_file = tempfile.mktemp(suffix=".wav", prefix="tts_")

        if self._use_piper_python:
            return self._synthesize_python(text, output_file)
        else:
            return self._synthesize_cli(text, output_file)

    def _synthesize_python(self, text: str, output_file: str) -> str:
        """使用 piper-python 合成"""
        from piper import PiperVoice

        # 首次调用时加载模型
        if self.voice_model is None:
            print(f"📥 正在下载并加载 Piper 模型: {self.voice}...")
            try:
                # 使用 PiperVoice.load 自动下载模型
                import huggingface_hub
                model_dir = Path("~/.openhuman/models/piper").expanduser()
                model_dir.mkdir(parents=True, exist_ok=True)
                
                # 下载模型文件
                model_file = huggingface_hub.hf_hub_download(
                    repo_id=f"rhasspy/piper-voices",
                    filename=f"{self.voice}/{self.voice}.onnx",
                    cache_dir=str(model_dir)
                )
                config_file = huggingface_hub.hf_hub_download(
                    repo_id=f"rhasspy/piper-voices",
                    filename=f"{self.voice}/{self.voice}.onnx.json",
                    cache_dir=str(model_dir)
                )
                
                self.voice_model = PiperVoice.load(model_file, config_file)
                print(f"✓ Piper 模型加载成功: {self.voice}")
            except Exception as e:
                raise RuntimeError(f"Piper 模型加载失败: {e}")

        # 合成语音并写入 WAV 文件
        import wave
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.voice_model.config.sample_rate)
            
            for audio_chunk in self.voice_model.synthesize(text):
                wf.writeframes(audio_chunk)
        
        print(f"✓ TTS 完成: {output_file}")
        return output_file

    def _synthesize_cli(self, text: str, output_file: str) -> str:
        """使用 piper 子进程合成"""
        if not os.path.exists(self.piper_bin):
            raise FileNotFoundError(
                f"piper 未找到: {self.piper_bin}\n"
                "请设置 PIPER_BIN 环境变量或安装 piper:\n"
                "  下载: https://github.com/rhasspy/piper/releases"
            )

        voice_model = self._resolve_voice_path()

        import subprocess
        cmd = [
            self.piper_bin,
            "--model", voice_model,
            "--output_file", output_file
        ]

        print(f"🔄 执行: {' '.join(cmd[:3])} ...")
        process = subprocess.run(
            cmd,
            input=text,
            capture_output=True,
            text=True
        )

        if process.returncode != 0:
            raise RuntimeError(f"piper 失败: {process.stderr}")

        if not os.path.exists(output_file):
            raise RuntimeError("piper 未生成输出文件")

        print(f"✓ TTS 完成: {output_file}")
        return output_file

    def _resolve_voice_path(self) -> str:
        """解析 Piper 声音模型路径"""
        search_paths = [
            Path(os.environ.get("PIPER_VOICE_DIR", "~/.openhuman/models/piper")).expanduser(),
            Path("/usr/local/share/piper/voices"),
        ]

        for search_path in search_paths:
            model_path = search_path / f"{self.voice}.onnx"
            if model_path.exists():
                return str(model_path)

        raise FileNotFoundError(
            f"Piper 声音模型未找到: {self.voice}\n"
            "请下载模型到 ~/.openhuman/models/piper/\n"
            "下载: https://huggingface.co/rhasspy/piper-voices/tree/main"
        )


class VoiceDemo:
    """语音对话演示 - 整合 STT 和 TTS"""

    def __init__(self, use_local: bool = True):
        self.recorder = AudioRecorder(sample_rate=16000)

        if use_local:
            self.stt = WhisperSTT(model="base")
            # 使用 sherpa-onnx（支持中文，完全离线）
            self.tts = SherpaTTS(model_name="vits-melo-tts-zh_en")
        else:
            # 云端模式需要 API key
            raise NotImplementedError("云端模式需要配置 API key")

    def interactive_conversation(self, max_turns: int = 5):
        """交互式语音对话"""
        print("\n" + "="*60)
        print("🎙️  OpenHuman Voice Demo - 交互式语音对话")
        print("="*60)
        print(f"STT: {'faster-whisper' if self.stt._use_faster_whisper else 'whisper-cli'}")
        print(f"TTS: sherpa-onnx ({self.tts.model_name})")
        print(f"最多对话数: {max_turns}")
        print("提示: 说话后停顿 1 秒自动停止录音")
        print("="*60 + "\n")

        for turn in range(1, max_turns + 1):
            print(f"\n--- 第 {turn}/{max_turns} 轮对话 ---")

            # 1. 录音
            try:
                audio_bytes, num_samples = self.recorder.record(
                    silence_threshold=0.01,
                    silence_duration=1.0
                )
            except ValueError as e:
                print(f"❌ 录音失败: {e}")
                continue

            # 2. 保存 WAV
            wav_file = tempfile.mktemp(suffix=".wav", prefix="voice_")
            self.recorder.save_wav(audio_bytes, num_samples, wav_file)

            # 3. STT 转录
            print("\n🔄 正在转录...")
            start_time = time.time()
            try:
                text = self.stt.transcribe(wav_file)
                elapsed = time.time() - start_time
                print(f"✓ 转录完成 ({elapsed:.2f}s): {text}")
            except Exception as e:
                print(f"❌ 转录失败: {e}")
                continue

            if not text:
                print("⚠️ 未识别到文本")
                continue

            # 4. TTS 合成回复
            reply = f"你说的是: {text}"
            print(f"\n🔄 正在合成回复...")
            start_time = time.time()
            try:
                output_file = self.tts.synthesize(reply)
                elapsed = time.time() - start_time
                print(f"✓ 合成完成 ({elapsed:.2f}s): {output_file}")

                # 播放音频 (需要系统播放器)
                self._play_audio(output_file)
            except Exception as e:
                print(f"❌ TTS 失败: {e}")

    def test_stt_only(self, audio_file: Optional[str] = None):
        """仅测试 STT"""
        print("\n" + "="*60)
        print("🎤 STT 测试")
        print("="*60)

        if audio_file:
            print(f"📂 使用文件: {audio_file}")
            text = self.stt.transcribe(audio_file)
            print(f"✓ 转录结果: {text}")
        else:
            # 录音后转录
            audio_bytes, num_samples = self.recorder.record()
            wav_file = tempfile.mktemp(suffix=".wav", prefix="stt_test_")
            self.recorder.save_wav(audio_bytes, num_samples, wav_file)

            print("\n🔄 正在转录...")
            start_time = time.time()
            text = self.stt.transcribe(wav_file)
            elapsed = time.time() - start_time

            print(f"✓ 转录完成 ({elapsed:.2f}s): {text}")

    def test_tts_only(self, text: str = "你好，这是 OpenHuman Voice Demo 的文本转语音测试"):
        """仅测试 TTS"""
        print("\n" + "="*60)
        print("🔊 TTS 测试")
        print("="*60)

        print(f"📝 文本: {text}")
        print("\n🔄 正在合成...")
        start_time = time.time()

        output_file = self.tts.synthesize(text)
        elapsed = time.time() - start_time

        print(f"✓ 合成完成 ({elapsed:.2f}s): {output_file}")

        # 播放音频
        self._play_audio(output_file)

    def _play_audio(self, audio_file: str):
        """播放音频文件"""
        import platform

        system = platform.system()
        print(f"\n🔊 播放音频: {audio_file}")

        try:
            if system == "Darwin":  # macOS
                os.system(f"afplay '{audio_file}'")
            elif system == "Linux":
                os.system(f"aplay '{audio_file}' 2>/dev/null || paplay '{audio_file}' 2>/dev/null")
            elif system == "Windows":
                os.system(f'start /min wmplayer "{audio_file}"')
            else:
                print(f"⚠️ 不支持的操作系统，请手动播放: {audio_file}")
        except Exception as e:
            print(f"⚠️ 播放失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="OpenHuman Voice Demo - STT & TTS")
    parser.add_argument("--stt", action="store_true", help="仅测试 STT")
    parser.add_argument("--tts", action="store_true", help="仅测试 TTS")
    parser.add_argument("--tts-text", type=str, help="TTS 测试文本")
    parser.add_argument("--stt-file", type=str, help="STT 测试音频文件路径")
    parser.add_argument("--max-turns", type=int, default=5, help="最大对话轮数")
    parser.add_argument("--whisper-model", type=str, default="base", help="Whisper 模型名称")
    parser.add_argument("--piper-voice", type=str, default="en_US-lessac-medium", help="Piper 声音名称")

    args = parser.parse_args()

    try:
        demo = VoiceDemo(use_local=True)

        if args.stt:
            demo.test_stt_only(args.stt_file)
        elif args.tts:
            text = args.tts_text or "你好，这是 OpenHuman Voice Demo 的文本转语音测试"
            demo.test_tts_only(text)
        else:
            demo.interactive_conversation(max_turns=args.max_turns)

    except FileNotFoundError as e:
        print(f"\n❌ 文件未找到: {e}")
        print("\n📖 安装指南:")
        print("="*60)
        print("\n1. STT (Whisper):")
        print("   pip install faster-whisper")
        print("   # 或安装 whisper-cli:")
        print("   macOS: brew install whisper-cpp")
        print("   下载模型: https://huggingface.co/ggerganov/whisper.cpp")
        print("\n2. TTS (Piper):")
        print("   pip install piper-tts")
        print("   # 或下载二进制:")
        print("   https://github.com/rhasspy/piper/releases")
        print("   下载声音: https://huggingface.co/rhasspy/piper-voices")
        print("\n3. 环境变量 (可选):")
        print("   export WHISPER_BIN=/path/to/whisper-cli")
        print("   export PIPER_BIN=/path/to/piper")
        print("   export WHISPER_MODEL_DIR=~/.openhuman/models/whisper")
        print("   export PIPER_VOICE_DIR=~/.openhuman/models/piper")
        print("="*60)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
