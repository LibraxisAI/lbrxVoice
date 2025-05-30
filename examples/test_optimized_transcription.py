#!/usr/bin/env python3
"""
Test transkrypcji z optymalnymi parametrami dla języka polskiego
zapobiegającymi powtórzeniom i poprawiającymi jakość
"""
import mlx_whisper
import sys
from pathlib import Path

def transcribe_polish_optimized(audio_path: str, model_name: str = "mlx-community/whisper-large-v3-mlx"):
    """
    Transkrybuj audio po polsku z optymalnymi ustawieniami
    """
    print(f"Transcribing: {audio_path}")
    print(f"Model: {model_name}")
    print("-" * 60)
    
    # Konfiguracja zapobiegająca powtórzeniom
    result = mlx_whisper.transcribe(
        audio_path,
        path_or_hf_repo=model_name,
        verbose=True,  # pokazuj postęp
        
        # Parametry językowe
        language="pl",  # wymuszenie polskiego
        
        # Parametry jakości - zapobieganie powtórzeniom
        temperature=0.0,  # deterministyczne (można też (0.0, 0.2) dla fallback)
        compression_ratio_threshold=2.4,  # wykrywa powtórzenia
        logprob_threshold=-1.0,  # próg prawdopodobieństwa
        no_speech_threshold=0.6,  # próg ciszy
        
        # KLUCZOWE! Wyłącz warunkowanie na poprzednim tekście
        # aby przerwać pętle powtórzeń
        condition_on_previous_text=False,
        
        # Timestampy słów dla lepszej segmentacji
        word_timestamps=True,
        prepend_punctuations="\"'"¿([{-„",  # dodano polskie cudzysłowy
        append_punctuations="\"'.。,，!！?？:：")]}、"",
        
        # Prompt kontekstowy - pomaga w rozpoznaniu języka i kontekstu
        initial_prompt="Transkrypcja rozmowy po polsku.",
        
        # Opcje dekodowania
        decode_options={
            "language": "pl",
            "task": "transcribe",  # nie translate!
            "beam_size": 5,  # beam search
            "best_of": 5,    # liczba prób
            "patience": 1.0,  # cierpliwość w beam search
            "length_penalty": 1.0,  # kara za długość
            # można dodać:
            # "suppress_tokens": [-1],  # lista tokenów do pominięcia
            # "suppress_blank": True,   # pomija puste tokeny
        }
    )
    
    return result

def test_with_different_settings(audio_path: str):
    """
    Testuj różne konfiguracje i porównaj wyniki
    """
    configs = [
        {
            "name": "Domyślna (auto-detect)",
            "params": {
                "verbose": False,
            }
        },
        {
            "name": "Polski z condition_on_previous_text=True",
            "params": {
                "language": "pl",
                "condition_on_previous_text": True,
                "verbose": False,
            }
        },
        {
            "name": "Polski zoptymalizowany (bez warunkowania)",
            "params": {
                "language": "pl",
                "condition_on_previous_text": False,
                "compression_ratio_threshold": 2.4,
                "initial_prompt": "Transkrypcja po polsku.",
                "verbose": False,
                "decode_options": {
                    "language": "pl",
                    "beam_size": 5,
                    "best_of": 5,
                }
            }
        },
        {
            "name": "Polski z wyższym progiem kompresji",
            "params": {
                "language": "pl",
                "condition_on_previous_text": False,
                "compression_ratio_threshold": 3.0,  # wyższy próg
                "verbose": False,
            }
        },
    ]
    
    results = []
    for config in configs:
        print(f"\n{'='*60}")
        print(f"Testowanie: {config['name']}")
        print(f"{'='*60}")
        
        try:
            result = mlx_whisper.transcribe(
                audio_path,
                path_or_hf_repo="mlx-community/whisper-large-v3-mlx",
                **config['params']
            )
            
            text = result.get('text', '').strip()
            lang = result.get('language', 'unknown')
            
            # Sprawdź powtórzenia
            words = text.split()
            repetitions = 0
            if len(words) > 1:
                for i in range(1, len(words)):
                    if words[i] == words[i-1]:
                        repetitions += 1
            
            results.append({
                'config': config['name'],
                'language': lang,
                'text_length': len(text),
                'word_count': len(words),
                'repetitions': repetitions,
                'text_preview': text[:200] + '...' if len(text) > 200 else text
            })
            
            print(f"Język: {lang}")
            print(f"Długość: {len(text)} znaków, {len(words)} słów")
            print(f"Powtórzenia: {repetitions}")
            print(f"Początek: {text[:200]}...")
            
        except Exception as e:
            print(f"Błąd: {e}")
            results.append({
                'config': config['name'],
                'error': str(e)
            })
    
    # Podsumowanie
    print(f"\n{'='*60}")
    print("PODSUMOWANIE")
    print(f"{'='*60}")
    
    for r in results:
        print(f"\n{r['config']}:")
        if 'error' in r:
            print(f"  Błąd: {r['error']}")
        else:
            print(f"  Język: {r['language']}")
            print(f"  Słowa: {r['word_count']}")
            print(f"  Powtórzenia: {r['repetitions']}")

def main():
    if len(sys.argv) < 2:
        print("Użycie: python test_optimized_transcription.py <plik_audio>")
        print("\nOpcje:")
        print("  --test    Testuj różne konfiguracje")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    if not Path(audio_path).exists():
        print(f"Błąd: Plik {audio_path} nie istnieje!")
        sys.exit(1)
    
    if len(sys.argv) > 2 and sys.argv[2] == "--test":
        test_with_different_settings(audio_path)
    else:
        result = transcribe_polish_optimized(audio_path)
        
        print("\n=== WYNIK ===")
        print(f"Język: {result.get('language', 'unknown')}")
        print(f"Tekst:\n{result.get('text', '')}")
        
        if 'segments' in result:
            print(f"\nSegmenty: {len(result['segments'])}")
            for i, seg in enumerate(result['segments'][:3]):  # pierwsze 3
                print(f"  [{seg['start']:.2f}s - {seg['end']:.2f}s]: {seg['text']}")

if __name__ == "__main__":
    main()