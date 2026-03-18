// VIO 83 AI ORCHESTRA — Voice Mode (STT + TTS)
// Copyright (c) 2026 Viorica Porcu. AGPL-3.0 / Proprietaria
// Usa Web Speech API nativa del browser — ZERO librerie esterne, ZERO install
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';

interface VoiceModeProps {
  onTranscript: (text: string) => void;
  textToSpeak?: string;
  disabled?: boolean;
}

// Feature detection
const hasSpeechRecognition =
  typeof window !== 'undefined' &&
  ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

const hasSpeechSynthesis =
  typeof window !== 'undefined' && 'speechSynthesis' in window;

export default function VoiceMode({ onTranscript, textToSpeak, disabled }: VoiceModeProps) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Init Speech Recognition
  useEffect(() => {
    if (!hasSpeechRecognition) return;
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SR() as SpeechRecognition;
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    // Auto-detect lang from browser
    recognition.lang = navigator.language || 'it-IT';

    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
      setTranscript('');
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = '';
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          final += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }
      setTranscript(final || interim);
      if (final) {
        onTranscript(final.trim());
        setTranscript('');
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      setError(event.error === 'no-speech' ? 'Nessun audio rilevato' :
               event.error === 'not-allowed' ? 'Microfono non autorizzato' :
               `Errore: ${event.error}`);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.abort();
    };
  }, [onTranscript]);

  // TTS: speak when textToSpeak changes
  useEffect(() => {
    if (!hasSpeechSynthesis || !ttsEnabled || !textToSpeak) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = navigator.language || 'it-IT';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Try to use an Italian/English voice if available
    const voices = window.speechSynthesis.getVoices();
    const preferredLang = navigator.language?.split('-')[0] || 'it';
    const matchingVoice = voices.find(v => v.lang.startsWith(preferredLang)) || voices[0];
    if (matchingVoice) utterance.voice = matchingVoice;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);

    return () => {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    };
  }, [textToSpeak, ttsEnabled]);

  const toggleListening = useCallback(() => {
    if (!hasSpeechRecognition) return;
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      recognitionRef.current?.start();
    }
  }, [isListening]);

  const toggleTts = useCallback(() => {
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
    setTtsEnabled(prev => !prev);
  }, [isSpeaking]);

  const btnBase: React.CSSProperties = {
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    border: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s',
    flexShrink: 0,
    position: 'relative',
  };

  if (!hasSpeechRecognition && !hasSpeechSynthesis) return null;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
      {/* STT button */}
      {hasSpeechRecognition && (
        <button
          onClick={toggleListening}
          disabled={disabled}
          title={isListening ? 'Ferma registrazione' : 'Parla (STT)'}
          style={{
            ...btnBase,
            backgroundColor: isListening ? '#ef4444' : 'var(--vio-bg-tertiary)',
            color: isListening ? '#fff' : 'var(--vio-text-secondary)',
            boxShadow: isListening ? '0 0 0 3px rgba(239,68,68,0.3)' : 'none',
            animation: isListening ? 'pulse 1.2s infinite' : 'none',
          }}
        >
          {isListening ? <MicOff size={16} /> : <Mic size={16} />}
          {isListening && (
            <span style={{
              position: 'absolute',
              top: -2,
              right: -2,
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: '#ef4444',
              animation: 'pulse 1s infinite',
            }} />
          )}
        </button>
      )}

      {/* TTS toggle */}
      {hasSpeechSynthesis && (
        <button
          onClick={toggleTts}
          title={ttsEnabled ? 'Disattiva lettura risposte' : 'Attiva lettura risposte (TTS)'}
          style={{
            ...btnBase,
            backgroundColor: ttsEnabled ? 'rgba(0,255,0,0.15)' : 'var(--vio-bg-tertiary)',
            color: ttsEnabled ? 'var(--vio-green)' : 'var(--vio-text-dim)',
            border: ttsEnabled ? '1px solid var(--vio-green)' : '1px solid var(--vio-border)',
          }}
        >
          {isSpeaking ? <Volume2 size={14} /> : ttsEnabled ? <Volume2 size={14} /> : <VolumeX size={14} />}
        </button>
      )}

      {/* Live transcript display */}
      {transcript && (
        <span style={{
          fontSize: '11px',
          color: 'var(--vio-text-dim)',
          fontStyle: 'italic',
          maxWidth: '140px',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}>
          {transcript}...
        </span>
      )}

      {/* Error */}
      {error && (
        <span style={{ fontSize: '10px', color: '#ef4444', maxWidth: '120px' }}>
          {error}
        </span>
      )}
    </div>
  );
}
