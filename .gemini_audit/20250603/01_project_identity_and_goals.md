# Audit Report: Project Identity and Goals

**Date of Audit:** 2025-06-03
**Auditor:** Gemini AI Assistant

## 1. Project Name and Purpose

Based on user input and the `pro/INTERNAL_ANALYSIS.mdx` document, the project is identified as **lbrxVoice**. 

Its primary purpose is to be a comprehensive system for:
*   **Multivoice Speech-to-Text (STT):** Transcribing audio from various voices.
*   **Text-to-Speech (TTS):** Generating speech from text, with a focus on Polish language capabilities.
*   **AI-Finetuning for CSM-MLX and DIA models:** Adapting and optimizing specific AI models for speech tasks.

The project appears to be evolving from an experimental phase ("lbrxWhisper") into a more polished, production-focused system ("lbrxVoicePro").

## 2. Stated Goals (derived from `pro/INTERNAL_ANALYSIS.mdx`)

The transition to "lbrxVoicePro" outlines the following key goals:

*   **Achieve Production Readiness:** Move beyond a "dev playground" to a stable, reliable system suitable for real-world application and investor demonstration (e.g., "Sesame AI Labs").
*   **Showcase Working Functionality:** Focus on demonstrating end-to-end working flows rather than a multitude of experimental or partially implemented features.
*   **Modularity and Clean Architecture:** Implement a clear, modular structure with distinct components:
    *   `core/`: Essential, working functionalities.
    *   `dataset/`: Data handling, particularly in MOSHI/MIMI format.
    *   `models/`: Integrations with AI models.
    *   `api/`: A single, unified point of entry for services.
    *   `ui/`: Separated user interface components.
    *   `docs/`: Professional and comprehensive documentation.
*   **Efficiency and Performance:** Significantly reduce resource consumption (startup time, memory) and improve performance (e.g., "10x realtime on M1 Pro").
*   **Specific Technical Achievements to Showcase:**
    *   End-to-end dataset collection pipeline.
    *   Realtime STT performance.
    *   Pluggable knowledge base (RAG system).
    *   Effective Polish TTS.
*   **Improved Development Practices:**
    *   Adoption of `uv` for package management.
    *   Native support for MOSHI/MIMI dataset formats.
    *   Strict separation of concerns between modules.
*   **Language Focus:** Prioritize Polish language support ("Polish-first") while being adaptable for English ("English-ready").

## 3. Implied Goals from Project Structure and Components

The presence of directories and files related to various servers (`whisper_servers/`, `tts_servers/`, `dia/`, `csm/`), models (`models/`), and tools suggests a history of exploration and integration of different speech technologies. The long-term goal seems to be a flexible platform capable of incorporating various STT/TTS engines and supporting research and development in voice AI, particularly with MLX and related frameworks for Apple Silicon.

The project also aims to support dataset collection and management, crucial for finetuning and improving AI models for speech.