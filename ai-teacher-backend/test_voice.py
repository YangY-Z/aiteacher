import os
# Use huggingface mirror to avoid SSL issues
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from supertonic import TTS

# First run downloads the model from Hugging Face automatically.
tts = TTS(auto_download=True)

style = tts.get_voice_style(voice_name="M1")

text = "赵阳阳，你说得对！坐标的两个数确实分别控制不同方向的移动。第一个数（x坐标）控制左右移动，第二个数（y坐标）控制上下移动。就像导航一样：先左右，再上下，就能精确找到目标点。"

wav, duration = tts.synthesize(
    text=text,
    lang="zh",                      # Language code (e.g., "en", "ko", "na" for language-agnostic)
    voice_style=style,              # Voice style object
    total_steps=8,                  # Quality: 5 (low) to 12 (high), default 8 (medium)
    speed=1.05,                     # Speed: 0.7 (slow) to 2.0 (fast)
)
# wav: numpy array of shape (1, num_samples,) with dtype=np.float32, sampled at 44100 Hz
# duration: numpy array of shape (1,) containing the duration of the generated audio in seconds

tts.save_audio(wav, "output.wav")
# import soundfile as sf
# sf.write("output.wav", wav.squeeze(), 44100)

print(f"Generated {duration[0]:.2f}s of audio")