import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    import uvicorn
    # Flush output immediately
    sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, "reconfigure") else None
    sys.stderr.reconfigure(line_buffering=True) if hasattr(sys.stderr, "reconfigure") else None
    print("[BACKEND-RUN] Starting DocuIntellect FastAPI server on http://127.0.0.1:8000", flush=True)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")

