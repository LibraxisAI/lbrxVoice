"""
Centralna konfiguracja MLX Whisper dla projektu lbrxWhisper
==========================================================

Ten plik zawiera wszystkie możliwe parametry konfiguracyjne dla MLX Whisper
z dokładnymi opisami i rekomendowanymi wartościami dla języka polskiego.

Autor: Maciej Gad & Claude
Data: 2025-05-30
"""

from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WhisperConfig:
    """
    Kompletna konfiguracja dla MLX Whisper z wszystkimi parametrami
    """
    
    # ==========================================================================
    # PODSTAWOWE USTAWIENIA
    # ==========================================================================
    
    # Model do użycia - możliwe wartości:
    # - "mlx-community/whisper-tiny-mlx" (~39M parametrów, najszybszy)
    # - "mlx-community/whisper-base-mlx" (~74M parametrów)
    # - "mlx-community/whisper-small-mlx" (~244M parametrów)
    # - "mlx-community/whisper-medium-mlx" (~769M parametrów)
    # - "mlx-community/whisper-large-v3-mlx" (~1550M parametrów, najdokładniejszy)
    model_name: str = "mlx-community/whisper-large-v3-mlx"
    
    # Język audio - None = auto-detect, "pl" = polski, "en" = angielski, itd.
    # Lista języków: https://github.com/openai/whisper/blob/main/whisper/tokenizer.py#L10
    language: Optional[str] = "pl"
    
    # Zadanie: "transcribe" = transkrypcja, "translate" = tłumaczenie na angielski
    task: str = "transcribe"
    
    # ==========================================================================
    # PARAMETRY JAKOŚCI I ZAPOBIEGANIA POWTÓRZENIOM
    # ==========================================================================
    
    # KLUCZOWY PARAMETR! Czy warunkować na poprzednim tekście?
    # True = model pamięta poprzedni kontekst (może powodować pętle powtórzeń)
    # False = każdy segment niezależny (zalecane dla problemów z powtórzeniami)
    condition_on_previous_text: bool = False
    
    # Próg współczynnika kompresji - wykrywa powtarzające się teksty
    # Wyższa wartość = bardziej restrykcyjna detekcja powtórzeń
    # Zakres: 1.5-3.0, domyślnie 2.4
    compression_ratio_threshold: float = 2.4
    
    # Próg logarytmu prawdopodobieństwa - minimalna pewność transkrypcji
    # Niższa wartość = bardziej restrykcyjna, odrzuca niepewne segmenty
    # Zakres: -2.0 do 0.0, domyślnie -1.0
    logprob_threshold: float = -1.0
    
    # Próg prawdopodobieństwa braku mowy
    # Wyższa wartość = łatwiej uznaje segment za ciszę
    # Zakres: 0.0-1.0, domyślnie 0.6
    no_speech_threshold: float = 0.6
    
    # ==========================================================================
    # PARAMETRY DEKODOWANIA (BEAM SEARCH)
    # ==========================================================================
    
    # Temperatura - kontroluje losowość generowania
    # 0.0 = deterministyczne (zawsze ten sam wynik)
    # >0.0 = losowe (różne wyniki przy każdym uruchomieniu)
    # Może być też krotką dla fallback: (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
    temperature: Union[float, Tuple[float, ...]] = 0.0
    
    # Wielkość beam search - ile ścieżek rozważa jednocześnie
    # Wyższa = lepsza jakość ale wolniej
    # Zakres: 1-10, domyślnie 5 (używane gdy temperature=0.0)
    beam_size: Optional[int] = 5
    
    # Liczba niezależnych prób - ile razy próbować transkrypcji
    # Wyższa = większa szansa na dobry wynik
    # Zakres: 1-10, domyślnie 5 (używane gdy temperature>0.0)
    best_of: Optional[int] = 5
    
    # Cierpliwość w beam search - jak długo czekać na poprawę
    # Wyższa = dłużej szuka optymalnego wyniku
    # Zakres: 0.0-2.0, domyślnie 1.0
    patience: Optional[float] = 1.0
    
    # Kara za długość - kontroluje długość generowanych segmentów
    # <1.0 = preferuje krótsze, >1.0 = preferuje dłuższe
    # Zakres: 0.5-2.0, domyślnie 1.0
    length_penalty: Optional[float] = 1.0
    
    # Maksymalna liczba tokenów do wygenerowania
    # None = bez limitu
    sample_len: Optional[int] = None
    
    # ==========================================================================
    # TIMESTAMPY I SEGMENTACJA
    # ==========================================================================
    
    # Czy generować timestampy dla słów?
    # True = dokładne czasy każdego słowa (wolniej)
    # False = tylko timestampy segmentów (szybciej)
    word_timestamps: bool = True
    
    # Znaki interpunkcyjne do łączenia z następnym słowem
    # Używane gdy word_timestamps=True
    prepend_punctuations: str = "\"'\"¿([{-„"
    
    # Znaki interpunkcyjne do łączenia z poprzednim słowem
    # Używane gdy word_timestamps=True
    append_punctuations: str = "\"'.。,，!！?？:：\")]}、\""
    
    # Próg ciszy dla detekcji halucynacji (w sekundach)
    # Używane gdy word_timestamps=True
    # None = wyłączone, >0 = pomija ciszę dłuższą niż X sekund
    hallucination_silence_threshold: Optional[float] = None
    
    # ==========================================================================
    # PROMPT I KONTEKST
    # ==========================================================================
    
    # Początkowy prompt - podpowiedź dla modelu
    # Może zawierać:
    # - Informację o języku: "Transkrypcja po polsku."
    # - Słownictwo domenowe: "Rozmowa o AI, weterynarii, diagnostyce"
    # - Styl: "Rozmowa formalna/nieformalna"
    # - Nazwy własne: "Firma LIBRAXIS, produkt VistaCoreMLX"
    initial_prompt: Optional[str] = "Transkrypcja rozmowy po polsku."
    
    # ==========================================================================
    # PRZETWARZANIE FRAGMENTÓW
    # ==========================================================================
    
    # Timestampy klipów do przetworzenia (w sekundach)
    # Format: "start1,end1,start2,end2,..."
    # Przykład: "0,300,300,600" = dwa 5-minutowe fragmenty
    # Przydatne dla bardzo długich plików
    clip_timestamps: Union[str, List[float]] = "0"
    
    # ==========================================================================
    # OPCJE TECHNICZNE
    # ==========================================================================
    
    # Czy używać float16 (szybsze) czy float32 (dokładniejsze)?
    fp16: bool = True
    
    # Poziom szczegółowości logów
    # None = automatyczny, True = szczegółowe, False = ciche
    verbose: Optional[bool] = True
    
    # ==========================================================================
    # PRESETY DLA RÓŻNYCH SCENARIUSZY
    # ==========================================================================
    
    @classmethod
    def polish_optimized(cls) -> 'WhisperConfig':
        """Optymalny preset dla języka polskiego"""
        return cls(
            language="pl",
            condition_on_previous_text=False,  # Zapobiega powtórzeniom
            compression_ratio_threshold=2.4,
            initial_prompt="Transkrypcja rozmowy po polsku.",
            word_timestamps=True,
            beam_size=5,
            best_of=5
        )
    
    @classmethod
    def polish_high_quality(cls) -> 'WhisperConfig':
        """Maksymalna jakość dla polskiego (wolniejsze)"""
        return cls(
            model_name="mlx-community/whisper-large-v3-mlx",
            language="pl",
            condition_on_previous_text=False,
            compression_ratio_threshold=2.8,  # Bardziej restrykcyjne
            temperature=(0.0, 0.2),  # Fallback dla trudnych fragmentów
            beam_size=8,  # Większy beam
            best_of=8,
            patience=1.5,
            word_timestamps=True,
            initial_prompt="Dokładna transkrypcja rozmowy po polsku."
        )
    
    @classmethod
    def polish_fast(cls) -> 'WhisperConfig':
        """Szybka transkrypcja polska (mniejszy model)"""
        return cls(
            model_name="mlx-community/whisper-medium-mlx",
            language="pl",
            condition_on_previous_text=False,
            beam_size=3,  # Mniejszy beam
            best_of=3,
            word_timestamps=False,  # Bez timestampów słów
            fp16=True
        )
    
    @classmethod
    def noisy_audio(cls) -> 'WhisperConfig':
        """Dla nagrań z szumami/słabej jakości"""
        return cls(
            language="pl",
            condition_on_previous_text=False,
            compression_ratio_threshold=3.0,  # Bardzo restrykcyjne
            no_speech_threshold=0.8,  # Łatwiej uznaje za ciszę
            temperature=(0.0, 0.2, 0.4),  # Więcej prób
            logprob_threshold=-1.5,  # Bardziej restrykcyjne
            initial_prompt="Transkrypcja nagrania ze znacznymi szumami."
        )
    
    @classmethod
    def domain_specific(cls, domain: str, keywords: List[str]) -> 'WhisperConfig':
        """Konfiguracja dla konkretnej domeny z kluczowymi słowami"""
        prompt = f"Transkrypcja rozmowy o {domain}. "
        if keywords:
            prompt += f"Słowa kluczowe: {', '.join(keywords)}."
        
        return cls(
            language="pl",
            condition_on_previous_text=False,
            initial_prompt=prompt,
            word_timestamps=True
        )
    
    def to_transcribe_kwargs(self) -> Dict:
        """Konwertuje konfigurację na argumenty dla mlx_whisper.transcribe()"""
        return {
            'language': self.language,
            'task': self.task,
            'temperature': self.temperature,
            'compression_ratio_threshold': self.compression_ratio_threshold,
            'logprob_threshold': self.logprob_threshold,
            'no_speech_threshold': self.no_speech_threshold,
            'condition_on_previous_text': self.condition_on_previous_text,
            'word_timestamps': self.word_timestamps,
            'prepend_punctuations': self.prepend_punctuations,
            'append_punctuations': self.append_punctuations,
            'initial_prompt': self.initial_prompt,
            'clip_timestamps': self.clip_timestamps,
            'hallucination_silence_threshold': self.hallucination_silence_threshold,
            'verbose': self.verbose,
            'decode_options': {
                'language': self.language,
                'task': self.task,
                'beam_size': self.beam_size,
                'best_of': self.best_of,
                'patience': self.patience,
                'length_penalty': self.length_penalty,
                'sample_len': self.sample_len,
                'fp16': self.fp16
            }
        }


# =============================================================================
# PRZYKŁADY UŻYCIA
# =============================================================================

if __name__ == "__main__":
    # Przykład 1: Domyślna konfiguracja
    config = WhisperConfig()
    print("Domyślna konfiguracja:")
    print(f"  Model: {config.model_name}")
    print(f"  Język: {config.language}")
    print(f"  Condition on previous: {config.condition_on_previous_text}")
    print()
    
    # Przykład 2: Preset dla polskiego
    config_pl = WhisperConfig.polish_optimized()
    print("Preset polski zoptymalizowany:")
    print(f"  Initial prompt: {config_pl.initial_prompt}")
    print(f"  Compression ratio: {config_pl.compression_ratio_threshold}")
    print()
    
    # Przykład 3: Konfiguracja dla konkretnej domeny
    config_vet = WhisperConfig.domain_specific(
        domain="weterynaria",
        keywords=["AI", "diagnostyka", "RTG", "USG", "personalizacja"]
    )
    print("Konfiguracja dla weterynarii:")
    print(f"  Initial prompt: {config_vet.initial_prompt}")
    print()
    
    # Przykład 4: Użycie w kodzie
    print("Użycie z mlx_whisper:")
    print("```python")
    print("import mlx_whisper")
    print("from whisper_config import WhisperConfig")
    print()
    print("config = WhisperConfig.polish_optimized()")
    print("result = mlx_whisper.transcribe(")
    print("    'audio.m4a',")
    print("    path_or_hf_repo=config.model_name,")
    print("    **config.to_transcribe_kwargs()")
    print(")")
    print("```")