#!/usr/bin/env python3
"""
Headless TUI testing with Textual's testing framework
This is like Playwright but for TUI!
"""

import asyncio
from textual.pilot import Pilot
from textual.testing import AppTest
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_tui_basic():
    """Test basic TUI functionality"""
    from lbrxchat.lbrx_ultimate_tui import LbrxUltimateTUI
    
    # Create app tester
    async with AppTest(LbrxUltimateTUI()) as pilot:
        # Take screenshot of initial state
        print("Initial state:")
        print(pilot.app.screen)
        
        # Press F2 to switch to RAG tab
        await pilot.press("f2")
        await pilot.pause()
        
        print("\nAfter F2 (RAG tab):")
        print(pilot.app.screen)
        
        # Press F3 for Files tab
        await pilot.press("f3")
        await pilot.pause()
        
        print("\nAfter F3 (Files tab):")
        print(pilot.app.screen)
        
        # Try to interact with a button
        # await pilot.click("#add-files")
        
        return "Test completed!"


async def test_tui_automated():
    """Automated TUI interaction test"""
    from lbrxchat.lbrx_ultimate_tui import LbrxUltimateTUI
    
    app = LbrxUltimateTUI()
    
    async with app.run_test() as pilot:
        # Log initial state
        with open("tui_test.log", "w") as f:
            f.write("=== TUI Automated Test ===\n\n")
            f.write("Initial screen:\n")
            f.write(str(pilot.app.screen))
            f.write("\n\n")
            
            # Navigate through tabs
            for tab_key, tab_name in [
                ("f1", "Chat"),
                ("f2", "RAG"),
                ("f3", "Files"),
                ("f4", "Voice"),
                ("f5", "TTS"),
                ("f6", "VoiceAI")
            ]:
                await pilot.press(tab_key)
                await pilot.pause()
                
                f.write(f"--- Tab: {tab_name} ---\n")
                f.write(str(pilot.app.screen))
                f.write("\n\n")
        
        print("Test log saved to tui_test.log")


def main():
    """Run headless TUI tests"""
    print("🤖 Running headless TUI tests (like Playwright for terminal!)")
    
    try:
        # Run basic test
        result = asyncio.run(test_tui_basic())
        print(f"\n✅ {result}")
        
        # Run automated test
        asyncio.run(test_tui_automated())
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()