# Instrukcja Instalacji dla Zwykłych Ludzi 👨‍🦳

Witaj! Ta instrukcja jest napisana tak, żeby każdy - nawet 70-letni wujek - mógł zainstalować i używać lbrxVoice.

## 🍎 Dla użytkowników Mac (Apple)

### Krok 1: Otwórz Terminal
1. Naciśnij `Cmd + Spacja` (lub kliknij lupkę w prawym górnym rogu)
2. Wpisz: `terminal`
3. Naciśnij Enter

### Krok 2: Skopiuj i wklej tę komendę
```bash
curl -fsSL https://raw.githubusercontent.com/LibraxisAI/lbrxVoice/main/install.sh | sh
```

**Jak to zrobić:**
1. Zaznacz całą komendę powyżej (od `curl` do `sh`)
2. Skopiuj: `Cmd + C`
3. Wklej w terminalu: `Cmd + V`
4. Naciśnij Enter
5. Poczekaj 2-5 minut

### Krok 3: Uruchom program
Po instalacji wpisz:
```bash
lbrxvoice
```

I naciśnij Enter. Program się uruchomi!

## 🎯 Jak używać

Program ma **6 zakładek** - przełączasz je klawiszami **F1, F2, F3, F4, F5, F6**:

1. **F1 - Chat**: Rozmowa z AI
2. **F2 - RAG**: Baza wiedzy  
3. **F3 - Files**: Transkrypcja plików
4. **F4 - Voice**: Transkrypcja na żywo
5. **F5 - TTS**: Synteza mowy
6. **F6 - VoiceAI**: Kompleksowy asystent głosowy

### Podstawowe klawisze:
- **Tab**: Przejście do następnego elementu
- **Enter**: Potwierdź/Wyślij
- **Ctrl + C**: Wyjście z programu

## 🎤 Jak nagrywać głos

1. Naciśnij **F4** (zakładka Voice)
2. Kliknij "Start Recording" 
3. Mów do mikrofonu
4. Kliknij "Stop Recording"
5. Tekst pojawi się automatycznie!

## 🗣️ Jak słuchać syntezowanej mowy

1. Naciśnij **F5** (zakładka TTS)
2. Wpisz tekst który chcesz usłyszeć
3. Wybierz głos (np. "Marek" dla polskiego)
4. Kliknij "Synthesize"
5. Poczekaj i słuchaj!

## 💬 Jak rozmawiać z AI

1. Naciśnij **F1** (zakładka Chat)
2. Wpisz pytanie w polu na dole
3. Naciśnij Enter
4. AI odpowie w czasie rzeczywistym!

## 🆘 Jeśli coś nie działa

### Problem: "command not found: lbrxvoice"
**Rozwiązanie:**
```bash
source ~/.zshrc
lbrxvoice
```

### Problem: "Permission denied"
**Rozwiązanie:**
```bash
chmod +x ~/.local/bin/lbrxvoice
```

### Problem: Terminal pokazuje dziwne znaki po zamknięciu
**Rozwiązanie:**
```bash
reset
```

### Problem: Mikrofon nie działa
**Rozwiązanie:**
1. Sprawdź czy Mac pyta o pozwolenie na mikrofon
2. Idź do: System Preferences → Privacy → Microphone
3. Dodaj Terminal do listy dozwolonych aplikacji

## 🔧 Wymagania

- **Mac z procesorem Apple Silicon** (M1, M2, M3)
- **macOS 12.0 lub nowszy**
- **Połączenie internetowe** (do instalacji)

## 📞 Pomoc

Jeśli nic nie działa:
1. Zamknij terminal: `Cmd + Q`
2. Otwórz nowy terminal
3. Spróbuj ponownie od początku

---

**Pamiętaj:** Komputer to tylko narzędzie. Jeśli coś nie działa, to nie Twoja wina! 

**No i zajebiście!** 🚀

---

*Utworzone przez Macieja i Klaudiusza z ❤️ dla wszystkich, niezależnie od wieku!*