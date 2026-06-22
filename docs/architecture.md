# diariza — architecture

## System component diagram

```mermaid
flowchart LR
  subgraph Desktop["Electron desktop app"]
    UI["React renderer<br/>Import · Configure · Run<br/>Speakers · Export · Settings"]
    PRE["Preload<br/>(contextBridge)"]
    MAIN["Electron main<br/>window · spawns/supervises sidecar"]
  end

  subgraph Engine["Python engine — FastAPI sidecar"]
    API["server.py<br/>REST + WebSocket"]
    JOBS["jobs.py<br/>queue · progress · cancel"]
    PIPE["pipeline.py<br/>orchestration"]
    REG["registry.py<br/>entry-point plugin discovery"]
    IO["merge.py + vtt.py<br/>assign speakers · export"]
    HW["hardware.py<br/>device detect + probe"]
    MEDIA["media.py<br/>ffmpeg ingest"]
    CFG["config.py<br/>settings · keyring"]
    subgraph DIA["DiarizationBackend (plugin)"]
      PYA["pyannote-local"]
      NEMO["nemo-local"]
      DCLOUD["pyannoteAI / AssemblyAI / Deepgram"]
    end
    subgraph ASR["TranscriptionBackend (plugin)"]
      FW["faster-whisper-local"]
      ACLOUD["OpenAI / AssemblyAI / Deepgram"]
    end
  end

  subgraph Ext["External resources"]
    FFMPEG["ffmpeg binary"]
    HF["Hugging Face Hub<br/>(gated models)"]
    CLOUDAPI["Cloud ASR / diarization APIs"]
    KEY["OS keychain"]
    HWDEV["GPU / CPU"]
  end

  UI --> PRE --> MAIN
  MAIN -->|spawn process| API
  UI <-->|"HTTP + WS (localhost)"| API
  API --> JOBS --> PIPE
  PIPE --> MEDIA
  PIPE --> REG
  PIPE --> IO
  PIPE --> HW
  REG --> DIA
  REG --> ASR
  CFG --> KEY
  API --> CFG
  MEDIA --> FFMPEG
  PYA --> HF
  DCLOUD --> CLOUDAPI
  ACLOUD --> CLOUDAPI
  HW --> HWDEV
  PYA --> HWDEV
  FW --> HWDEV
```

## How it works (process flow)

```mermaid
flowchart TD
  A["Import media<br/>(video / audio) + optional transcript"] --> B["Configure<br/>diarization + transcription backend ·<br/>language · #speakers · device Auto/GPU/CPU"]
  B --> C["Run job"]
  C --> P["Resolve device<br/>Auto → CUDA → MPS → CPU"]
  P --> Q{"GPU usable?<br/>(tiny matmul probe)"}
  Q -->|No| R["Fall back to CPU<br/>+ notice in UI"]
  Q -->|Yes| D
  R --> D
  D["Ingest: ffmpeg → 16 kHz mono WAV"] --> E{"Existing transcript<br/>provided?"}
  E -->|"Yes — Mode B"| F["Parse VTT / SRT → Cues"]
  E -->|"No — Mode A"| G["Transcribe with Whisper → Cues<br/>(progress over WebSocket)"]
  F --> H["Diarize with selected backend → Segments<br/>(progress over WebSocket)"]
  G --> H
  H --> I["Merge: assign a speaker to each cue<br/>max overlap · nearest-gap fallback"]
  I --> J["Speaker stats<br/>speaking time · sample timestamps"]
  J --> K["Labeling UI<br/>play samples · rename · merge speakers"]
  K --> L["Export: labeled VTT · SRT · TXT · JSON"]
```

> Component status: the Python engine (orchestration, plugin registry, hardware probe, media,
> merge/export, pyannote-local + faster-whisper-local, CLI) is implemented (M1). The FastAPI server
> (M2), Electron shell (M3), labeling UI (M4), extra backends (M5), and installers (M6) are planned.
