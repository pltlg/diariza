"""PyInstaller entry point: launch the diariza FastAPI engine.

The packaged binary is invoked by the Electron main process with --host/--port (see
apps/desktop/src/main/sidecar.ts).
"""

from diariza.server import main

if __name__ == "__main__":
    main()
