#!/bin/bash
# UV-native log runner for lbrxWhisper

# Ścieżka do projektu
PROJECT_DIR="/Users/maciejgad/LIBRAXIS/Repos/VoiceProcessing/lbrxWhisper"
LOG_DIR="$PROJECT_DIR/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Tworzenie katalogu na logi
mkdir -p "$LOG_DIR"

# Przejście do katalogu projektu
cd "$PROJECT_DIR" || exit 1

echo "🚀 Uruchamiam lbrxWhisper Ultimate TUI"
echo "📁 Logi zapisywane do: $LOG_DIR"
echo "📝 Sesja: $TIMESTAMP"
echo ""

# Uruchomienie przez UV z pełnym logowaniem
# UV automatycznie użyje właściwego Pythona i środowiska
uv run python run_ultimate_tui.py \
    2>&1 | tee "$LOG_DIR/session_${TIMESTAMP}.log"

# Zapisz kod wyjścia
EXIT_CODE=$?

# Jeśli był błąd, zapisz dodatkowe informacje
if [ $EXIT_CODE -ne 0 ]; then
    echo "" >> "$LOG_DIR/session_${TIMESTAMP}.log"
    echo "=== ERROR DETAILS ===" >> "$LOG_DIR/session_${TIMESTAMP}.log"
    echo "Exit code: $EXIT_CODE" >> "$LOG_DIR/session_${TIMESTAMP}.log"
    echo "Python version:" >> "$LOG_DIR/session_${TIMESTAMP}.log"
    python --version >> "$LOG_DIR/session_${TIMESTAMP}.log" 2>&1
    echo "Installed packages:" >> "$LOG_DIR/session_${TIMESTAMP}.log"
    pip list >> "$LOG_DIR/session_${TIMESTAMP}.log" 2>&1
fi

echo ""
echo "✅ Zakończono. Logi zapisane w:"
echo "   $LOG_DIR/session_${TIMESTAMP}.log"