#!/usr/bin/env python3
"""Simple import test"""

try:
    # Test basic imports without LLM dependencies
    from tg_analyzer.config.config_manager import ConfigManager
    from tg_analyzer.processors.telegram_parser import TelegramParser
    from tg_analyzer.processors.cleaners import get_cleaner
    from tg_analyzer.processors.formatters import get_formatter
    print("✅ Basic imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()

