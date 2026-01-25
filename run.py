import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(__file__))

from app.bot.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped.")