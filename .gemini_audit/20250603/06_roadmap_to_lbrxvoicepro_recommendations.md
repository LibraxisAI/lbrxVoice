# Audit Report: Roadmap to `lbrxVoicePro` - Recommendations

**Date of Audit:** 2025-06-03
**Auditor:** Gemini AI Assistant

This section provides actionable recommendations to transition the project from its current state ("lbrxWhisper") to the desired "lbrxVoicePro" architecture, as outlined in `pro/INTERNAL_ANALYSIS.mdx`.

## 1. Embrace the New Philosophy: "Pokażmy że to faktycznie działa"

*   **Instruction:** Shift focus from feature quantity to quality and reliability. Prioritize end-to-end working flows with the components confirmed to be stable.
*   **Action:** Before adding new features, ensure the core functionality defined in `lbrxVoicePro` is robust and well-tested.

## 2. Implement the `lbrxVoicePro` Modular Architecture

*   **Instruction:** Create the defined 6 top-level module directories and migrate existing code accordingly. Enforce strict separation of concerns.
*   **Actions:**
    1.  **Create Directories:**
        *   `core/`
        *   `dataset/`
        *   `models/`
        *   `api/`
        *   `ui/`
        *   `docs/`
    2.  **Migrate `core/` components:**
        *   Relocate the working `VoicePipeline`, `VoiceActivityDetector` (Silero VAD), and `RAGEngine` (ChromaDB RAG) implementations here.
        *   Refactor to ensure they are self-contained and expose clear interfaces.
    3.  **Populate `dataset/`:**
        *   Move any data collection scripts (like `dataset/collector.py` mentioned for batch processing) here.
        *   Implement/centralize MOSHI/MIMI formatting logic here (`formatter = MoshiMimiFormatter()`).
    4.  **Organize `models/`:**
        *   Place integrations for working models like MLX Whisper and Edge TTS here.
        *   If the Veterinary RAG (`veterinary_pl_v2.json`, `VeterinaryRAG` class) is to be included, its model-specific logic would reside here, building upon the `core/RAGEngine`.
    5.  **Develop `api/`:**
        *   Design and implement a single, unified API entry point for all project services.
        *   Initially, this should expose the confirmed working functionalities: transcription (MLX Whisper), VAD, RAG queries, and Polish TTS (Edge TTS).
        *   Ensure this API does not have direct knowledge of UI or specific model storage details.
    6.  **Structure `ui/`:**
        *   If a UI is necessary, relocate TUI components here (e.g., parts of `lbrx_ultimate_tui.py`, `mlx_vet_rag_tui.py`).
        *   Simplify the TUI based on the critique (e.g., remove empty tabs, focus on useful features).
        *   Ensure UI components interact with the system strictly through the `api/`.
    7.  **Build `docs/`:**
        *   Start creating professional documentation for the new architecture, modules, API endpoints, and setup procedures.
        *   Migrate any relevant existing documentation (e.g., from root `.md` files or `docs/` subdirectories after vetting).

## 3. Codebase Cleanup and Refinement

*   **Instruction:** Systematically remove or archive components and files identified as non-functional, redundant, or clutter.
*   **Actions:**
    *   **Remove Non-Working Servers:** Delete code related to DIA TTS servers and CSM servers (unless voice cloning part of CSM can be salvaged and re-integrated with a working model via `models/`).
    *   **Consolidate Configurations:** Identify and merge the "3 różne konfiguracje tego samego" (duplicate Whisper configs) into a single, authoritative configuration, likely within `core/` or `models/` as appropriate.
    *   **Eliminate Unused Scripts:** Review and remove the "50+ nieużywanych skryptów."
    *   **Address Root File Clutter:**
        *   Move essential scripts (e.g., `main.py` for the new API) to `api/` or a root-level script that initializes the `api/`.
        *   Relocate other scripts to `tools/` (for dev utilities) or `scripts/` (for operational tasks) if they are still needed, otherwise delete.
        *   Organize test files (see next point).
    *   **Refactor/Simplify Overengineered Components:**
        *   Re-evaluate the TUI. If kept, simplify based on usage.
        *   Standardize on one working voice pipeline within `core/`.
        *   Stick to a primary API style (e.g., REST through the `api/` module) and avoid premature introduction of others like GraphQL unless a clear, immediate need arises.

## 4. Testing Strategy

*   **Instruction:** Consolidate scattered test files into a structured testing hierarchy, ideally within each new module (`core/tests/`, `api/tests/`, etc.) or a top-level `tests/` directory mirroring the module structure.
*   **Action:** Adopt a testing framework (e.g., `pytest`) and write tests for all core components and API endpoints.

## 5. Dependency Management and Build System

*   **Instruction:** Adopt `uv` as the primary package manager and `hatchling` for builds, as stated in `INTERNAL_ANALYSIS.mdx` (`[build-system] requires = ["hatchling"]`).
*   **Action:**
    *   Create/update `pyproject.toml` to reflect `hatchling` usage.
    *   Transition from any existing `requirements.txt`, `poetry.lock`, or `conda` environments to `uv` for dependency management.
    *   Aim to reduce the number of dependencies from "50+" to the "15" targeted for `lbrxVoicePro` by removing unused or problematic libraries.

## 6. Language Focus

*   **Instruction:** Ensure new developments are "Polish-first, English-ready."
*   **Action:** Default configurations and examples should favor Polish, but code should be structured to easily accommodate English and other languages where feasible (e.g., language parameters in API calls, model selection).

## 7. Iterative Verification

*   **Instruction:** After each major refactoring step, verify that the system achieves the targeted improvements mentioned in `INTERNAL_ANALYSIS.mdx` (reduced files, LOC, dependencies, faster startup, lower memory usage, 100% working features for the defined scope).

By following these recommendations, the project can systematically transform into the lean, functional, and maintainable `lbrxVoicePro` system envisioned in the internal analysis.