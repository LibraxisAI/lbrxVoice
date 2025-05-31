# UV Installation - The Right Way™

## Instalacja UV (jeśli nie masz)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Instalacja projektu lbrxWhisper

```bash
# 1. Klonuj repo (jeśli jeszcze nie masz)
git clone https://github.com/yourusername/lbrxWhisper.git
cd lbrxWhisper

# 2. UV sync - to wszystko czego potrzebujesz!
uv sync

# 3. Uruchom z UV
uv run python run_ultimate_tui.py
```

## Dodawanie nowych pakietów

```bash
# Zamiast pip install
uv add nazwa-pakietu

# Zamiast pip install -r requirements.txt  
uv add -r requirements.txt

# Sync po zmianach
uv sync
```

## Uruchamianie

```bash
# Zawsze przez UV run - nie musisz aktywować żadnych venv!
uv run python run_ultimate_tui.py

# Lub z logami
uv run ./run_with_logs.sh
```

## Co robi UV za Ciebie?

- ✅ Zarządza wersjami Pythona (automatycznie pobierze 3.11)
- ✅ Tworzy i zarządza środowiskiem wirtualnym
- ✅ Instaluje zależności z pyproject.toml
- ✅ Lockuje wersje w uv.lock
- ✅ Nie musisz myśleć o venv, pip, poetry czy conda

## TL;DR

```bash
cd lbrxWhisper
uv sync
uv run python run_ultimate_tui.py
```

That's it. UV handles everything else.