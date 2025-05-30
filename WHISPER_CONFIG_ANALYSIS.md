# Analiza konfiguracji Whisper - porównanie whisper.cpp vs MLX Whisper

## Parametry w whisper.cpp (z twojego przykładu):

### Parametry jakości transkrypcji:
- **`-bs` (beam_size)**: 5 - wielkość beam search
- **`-bo` (best_of)**: 5 - liczba prób beam search
- **`-et` (entropy_threshold)**: 2.2 - próg entropii (zapobiega powtórzeniom)
- **`-wt` (word_threshold)**: 0.01 - próg dla word timestamps
- **`-ml` (max_len)**: 120 - maksymalna długość segmentu (zapobiega zapętleniom)

### Parametry językowe:
- **`-l` (language)**: 'pl' - wymuszenie języka
- **`--translate`**: opcja tłumaczenia na angielski

### Parametry wydajności:
- **`-t` (threads)**: liczba wątków
- **`-fa` (flash_attn)**: Flash Attention

### Parametry wyjścia:
- **`--output-txt`**, **`--output-srt`**, **`--output-vtt`**: format wyjścia
- **`--no-timestamps`**: wyłączenie timestamps
- **`-sow` (split_on_word)**: podział na słowa

## Parametry w MLX Whisper:

### DecodingOptions (decoding.py):
```python
@dataclass(frozen=True)
class DecodingOptions:
    task: str = "transcribe"              # "transcribe" lub "translate"
    language: Optional[str] = None        # np. "pl" - wymuszenie języka
    temperature: float = 0.0              # 0.0 = deterministyczne, >0 = losowe
    sample_len: Optional[int] = None      # max liczba tokenów
    best_of: Optional[int] = None         # liczba niezależnych próbek (gdy temp > 0)
    beam_size: Optional[int] = None       # liczba beams (gdy temp == 0)
    patience: Optional[float] = None      # patience w beam search
    length_penalty: Optional[float] = None # kara za długość
```

### Parametry funkcji transcribe():
```python
def transcribe(
    audio: Union[str, np.ndarray, mx.array],
    *,
    path_or_hf_repo: str,
    verbose: Optional[bool] = None,
    temperature: Union[float, Tuple[float, ...]] = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
    compression_ratio_threshold: Optional[float] = 2.4,
    logprob_threshold: Optional[float] = -1.0,
    no_speech_threshold: Optional[float] = 0.6,
    condition_on_previous_text: bool = True,  # WAŻNE! dla zapobiegania powtórzeniom
    word_timestamps: bool = False,
    prepend_punctuations: str = "\"'"¿([{-",
    append_punctuations: str = "\"'.。,，!！?？:：")]}、",
    initial_prompt: Optional[str] = None,  # WAŻNE! prompt kontekstowy
    decode_options: Optional[Dict[str, any]] = None,
    clip_timestamps: Union[str, List[float]] = "0",
    hallucination_silence_threshold: Optional[float] = None,
):
```

## Kluczowe różnice i jak je wykorzystać:

### 1. **Zapobieganie powtórzeniom**:
- whisper.cpp: `-et 2.2` (entropy_threshold), `-ml 120` (max_len)
- MLX Whisper: 
  - `compression_ratio_threshold=2.4` - wykrywa skompresowane (powtarzające się) teksty
  - `condition_on_previous_text=False` - WAŻNE! wyłącz to, aby przerwać pętle powtórzeń
  - `logprob_threshold=-1.0` - próg prawdopodobieństwa

### 2. **Język polski**:
```python
decode_options = {
    "language": "pl",  # wymuszenie polskiego
    "task": "transcribe",  # nie translate
    "beam_size": 5,  # jak -bs w whisper.cpp
    "best_of": 5,  # jak -bo w whisper.cpp
    "temperature": 0.0  # deterministyczne
}
```

### 3. **Prompt kontekstowy** (unikalny dla MLX):
```python
initial_prompt = "Transkrypcja rozmowy po polsku o technologii AI w weterynarii."
```

### 4. **Word timestamps**:
- whisper.cpp: `-wt 0.01`
- MLX: `word_timestamps=True`

## Rekomendowana konfiguracja dla polskiego audio:

```python
result = mlx_whisper.transcribe(
    audio_file,
    path_or_hf_repo="mlx-community/whisper-large-v3-mlx",
    language="pl",  # wymuszenie polskiego
    temperature=0.0,  # deterministyczne
    compression_ratio_threshold=2.4,
    logprob_threshold=-1.0,
    no_speech_threshold=0.6,
    condition_on_previous_text=False,  # WAŻNE! zapobiega powtórzeniom
    word_timestamps=True,
    initial_prompt="Transkrypcja po polsku.",  # pomaga w rozpoznaniu języka
    decode_options={
        "language": "pl",
        "task": "transcribe",
        "beam_size": 5,
        "best_of": 5,
        "patience": 1.0,
        "length_penalty": 1.0
    }
)
```

## Dodatkowe porady:

1. **Gdy są powtórzenia**:
   - Ustaw `condition_on_previous_text=False`
   - Zwiększ `compression_ratio_threshold` do 2.8 lub 3.0
   - Zmniejsz `beam_size` do 3

2. **Dla słabej jakości audio**:
   - Użyj `temperature=(0.0, 0.2, 0.4)` - da modelu kilka prób
   - Zwiększ `no_speech_threshold` do 0.7 lub 0.8

3. **Prompt engineering**:
   - Użyj `initial_prompt` z przykładowymi słowami kluczowymi z domeny
   - Np. dla weterynarii: "Rozmowa o diagnostyce weterynaryjnej, AI, personalizacja"

4. **Segmentacja**:
   - Użyj `clip_timestamps` do przetwarzania długich plików w częściach
   - Np. `clip_timestamps="0,300,300,600"` - przetwarza 5-minutowe fragmenty