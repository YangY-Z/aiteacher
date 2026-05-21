import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { API_BASE_URL } from '../api/client';

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognition extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

interface SpeechRecognitionConstructor {
  new (): SpeechRecognition;
}

declare global {
  interface Window {
    SpeechRecognition: SpeechRecognitionConstructor;
    webkitSpeechRecognition: SpeechRecognitionConstructor;
  }
}

interface ListenOptions {
  initialText?: string;
  onTranscript: (text: string) => void;
}

interface SpeechQueueItem {
  id: number;
  text: string;
}

const VOICE_AUTO_READ_KEY = 'voice:autoRead';
const MAX_SPEAKING_CHARS = 220;

const normalizeForSpeech = (text: string): string => {
  return text
    .replace(/```[\s\S]*?```/g, '')
    .replace(/!\[[^\]]*]\([^)]*\)/g, '')
    .replace(/\[[^\]]*]\([^)]*\)/g, '')
    .replace(/[#*_>`~$\\]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
};

const trimForCostControl = (text: string): string => {
  const normalized = normalizeForSpeech(text);
  if (normalized.length <= MAX_SPEAKING_CHARS) return normalized;
  const firstSentence = normalized.match(/^.*?[。！？!?]/)?.[0];
  if (firstSentence && firstSentence.length <= MAX_SPEAKING_CHARS) return firstSentence;
  return `${normalized.slice(0, MAX_SPEAKING_CHARS)}。`;
};

export const useBrowserVoice = () => {
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const speakGenerationRef = useRef(0);
  const speechQueueRef = useRef<SpeechQueueItem[]>([]);
  const isProcessingSpeechQueueRef = useRef(false);
  const speechItemIdRef = useRef(0);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRead, setAutoReadState] = useState(() => localStorage.getItem(VOICE_AUTO_READ_KEY) === 'true');

  const speechRecognitionSupported = useMemo(
    () => typeof window !== 'undefined' && Boolean(window.SpeechRecognition || window.webkitSpeechRecognition),
    [],
  );
  const speechSynthesisSupported = useMemo(
    () => typeof window !== 'undefined' && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window,
    [],
  );

  const setAutoRead = useCallback((enabled: boolean) => {
    localStorage.setItem(VOICE_AUTO_READ_KEY, String(enabled));
    setAutoReadState(enabled);
  }, []);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  const startListening = useCallback(({ initialText = '', onTranscript }: ListenOptions) => {
    if (!speechRecognitionSupported) {
      setError('当前浏览器不支持语音输入');
      return;
    }

    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) return;

    recognitionRef.current?.abort();
    const recognition = new Recognition();
    let finalText = initialText.trim();

    recognition.lang = 'zh-CN';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      let interimText = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) {
          finalText = `${finalText}${finalText ? ' ' : ''}${result[0].transcript}`.trim();
        } else {
          interimText += result[0].transcript;
        }
      }
      onTranscript(`${finalText}${interimText ? ` ${interimText}` : ''}`.trim());
    };

    recognition.onerror = (event) => {
      setError(event.error || '语音识别失败');
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    setError(null);
    setIsListening(true);
    recognition.start();
  }, [speechRecognitionSupported]);

  const stopSpeaking = useCallback((clearQueue = true) => {
    speakGenerationRef.current += 1;
    if (clearQueue) {
      speechQueueRef.current = [];
    }
    isProcessingSpeechQueueRef.current = false;
    audioRef.current?.pause();
    if (audioRef.current) {
      audioRef.current.src = '';
      audioRef.current.load();
    }
    audioRef.current = null;
    if (speechSynthesisSupported) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
    setIsPaused(false);
  }, [speechSynthesisSupported]);

  const pauseSpeaking = useCallback(() => {
    if (!isSpeaking || isPaused) return;
    audioRef.current?.pause();
    if (speechSynthesisSupported && window.speechSynthesis.speaking) {
      window.speechSynthesis.pause();
    }
    setIsPaused(true);
  }, [isPaused, isSpeaking, speechSynthesisSupported]);

  const resumeSpeaking = useCallback(() => {
    if (!isPaused) return;
    setIsPaused(false);
    if (audioRef.current) {
      void audioRef.current.play().catch(() => {
        setIsSpeaking(false);
        setIsPaused(false);
      });
      return;
    }
    if (speechSynthesisSupported && window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
  }, [isPaused, speechSynthesisSupported]);

  const speakWithBrowser = useCallback((text: string, generation: number): Promise<void> => {
    if (!speechSynthesisSupported) {
      setError('当前浏览器不支持语音朗读');
      return Promise.resolve();
    }

    const speechText = trimForCostControl(text);
    if (!speechText) return Promise.resolve();

    return new Promise((resolve) => {
      if (generation !== speakGenerationRef.current) {
        resolve();
        return;
      }

      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(speechText);
      utterance.lang = 'zh-CN';
      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => {
        setIsSpeaking(false);
        setIsPaused(false);
        resolve();
      };
      utterance.onerror = () => {
        setIsSpeaking(false);
        setIsPaused(false);
        resolve();
      };
      window.speechSynthesis.speak(utterance);
    });
  }, [speechSynthesisSupported]);

  const resolveAudioUrl = useCallback((audioUrl: string) => {
    if (audioUrl.startsWith('http')) return audioUrl;
    return `${new URL(API_BASE_URL).origin}${audioUrl}`;
  }, []);

  const playSpeechText = useCallback(async (speechText: string, generation: number) => {
      try {
        const response = await fetch(`${API_BASE_URL}/voice/synthesize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: speechText,
            voice: 'zh-CN-XiaoxiaoNeural',
            speed: 1,
          }),
        });

        if (!response.ok) {
          throw new Error(`TTS request failed: ${response.status}`);
        }

        const data = await response.json();
        if (data.audio_url && !data.should_use_browser_tts) {
          if (generation !== speakGenerationRef.current) return;
          const audio = new Audio(resolveAudioUrl(data.audio_url));
          audioRef.current = audio;
          await new Promise<void>((resolve) => {
            audio.onplay = () => setIsSpeaking(true);
            audio.onended = () => {
              setIsSpeaking(false);
              setIsPaused(false);
              resolve();
            };
            audio.onerror = () => {
              setIsSpeaking(false);
              setIsPaused(false);
              resolve();
              if (generation === speakGenerationRef.current) {
                void speakWithBrowser(speechText, generation);
              }
            };
            void audio.play().catch(() => {
              setIsSpeaking(false);
              setIsPaused(false);
              resolve();
              if (generation === speakGenerationRef.current) {
                void speakWithBrowser(speechText, generation);
              }
            });
          });
          return;
        }
      } catch (err) {
        console.warn('Cloud TTS failed, falling back to browser TTS:', err);
      }

      if (generation !== speakGenerationRef.current) return;
      await speakWithBrowser(speechText, generation);
  }, [resolveAudioUrl, speakWithBrowser]);

  const processSpeechQueue = useCallback(() => {
    if (isProcessingSpeechQueueRef.current) return;
    isProcessingSpeechQueueRef.current = true;
    const generation = speakGenerationRef.current;

    void (async () => {
      try {
        while (speechQueueRef.current.length > 0 && generation === speakGenerationRef.current) {
          const item = speechQueueRef.current.shift();
          if (!item) continue;
          await playSpeechText(item.text, generation);
        }
      } finally {
        isProcessingSpeechQueueRef.current = false;
        setIsSpeaking(false);
        if (speechQueueRef.current.length > 0 && generation === speakGenerationRef.current) {
          processSpeechQueue();
        }
      }
    })();
  }, [playSpeechText]);

  const speak = useCallback((text: string, options?: { interrupt?: boolean }) => {
    const speechText = trimForCostControl(text);
    if (!speechText) return;

    if (options?.interrupt) {
      stopSpeaking(true);
    }

    speechQueueRef.current.push({
      id: speechItemIdRef.current += 1,
      text: speechText,
    });
    processSpeechQueue();
  }, [processSpeechQueue, stopSpeaking]);

  useEffect(() => {
    return () => {
      speakGenerationRef.current += 1;
      recognitionRef.current?.abort();
      audioRef.current?.pause();
      if (speechSynthesisSupported) window.speechSynthesis.cancel();
    };
  }, [speechSynthesisSupported]);

  return {
    speechRecognitionSupported,
    speechSynthesisSupported,
    isListening,
    isSpeaking,
    isPaused,
    error,
    autoRead,
    setAutoRead,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    pauseSpeaking,
    resumeSpeaking,
  };
};
