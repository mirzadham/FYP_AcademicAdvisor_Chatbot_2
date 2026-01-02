"""
Windows Launcher for Rasa Pro CALM
===================================
This script fixes the Windows asyncio event loop issue that causes
LLM calls to hang when running inside Rasa's Sanic server.

Usage:
    python run_windows.py shell    # Instead of 'rasa shell'
    python run_windows.py train    # Instead of 'rasa train'
    python run_windows.py run      # Instead of 'rasa run'
"""

import sys
import os
import asyncio

# =============================================================================
# FIX: Apply Windows-specific event loop policy BEFORE importing Rasa
# =============================================================================
if sys.platform == 'win32':
    # Use the Selector event loop which is more compatible with async HTTP libraries
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("[Windows Fix] Applied WindowsSelectorEventLoopPolicy")

# Load environment variables from .env file
def load_dotenv():
    """Load environment variables from .env file"""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print(f"[Env] Loaded environment variables from .env")
    else:
        print(f"[Env] Warning: .env file not found at {env_file}")

# Load .env before running Rasa
load_dotenv()

# =============================================================================
# Main entry point
# =============================================================================
if __name__ == "__main__":
    # Import rasa CLI after applying the fix
    from rasa.__main__ import main as rasa_main
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python run_windows.py shell    # Start interactive shell")
        print("  python run_windows.py train    # Train the model")
        print("  python run_windows.py run      # Run the server")
        print("  python run_windows.py <any>    # Any rasa command")
        sys.exit(1)
    
    # Pass all arguments to rasa
    print(f"[Rasa] Running: rasa {' '.join(sys.argv[1:])}")
    print("-" * 50)
    
    # Run rasa with the provided arguments
    sys.argv = ['rasa'] + sys.argv[1:]
    rasa_main()
