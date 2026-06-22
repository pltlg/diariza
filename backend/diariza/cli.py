"""Command-line interface for the headless engine: ``diariza run|devices|backends``."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from . import __version__
from .hardware import list_devices, resolve_device
from .pipeline import run_pipeline
from .registry import diarization_backends, transcription_backends

app = typer.Typer(add_completion=False, help="diariza engine CLI")


def _parse_names(path: Optional[str]) -> dict[str, str]:
    names: dict[str, str] = {}
    if path:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                names[k.strip()] = v.strip()
    return names


@app.command()
def run(
    media: str = typer.Argument(..., help="Video or audio file"),
    transcript: Optional[str] = typer.Option(None, "--transcript", "-t",
                                             help="Existing VTT/SRT (Mode B). Omit to transcribe."),
    transcribe: bool = typer.Option(False, "--transcribe", help="Force ASR even if --transcript set"),
    num_speakers: Optional[int] = typer.Option(None, "--num-speakers", "-n"),
    min_speakers: Optional[int] = typer.Option(None, "--min-speakers"),
    max_speakers: Optional[int] = typer.Option(None, "--max-speakers"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="ASR language (e.g. hu)"),
    asr_model: Optional[str] = typer.Option(None, "--asr-model", help="Whisper model size"),
    device: str = typer.Option("auto", "--device", "-d", help="auto | gpu | cpu"),
    diar_backend: str = typer.Option("pyannote-local", "--diar-backend"),
    asr_backend: str = typer.Option("faster-whisper-local", "--asr-backend"),
    names: Optional[str] = typer.Option(None, "--names", help="SPEAKER_NN=Name file"),
    out: str = typer.Option("out", "--out", "-o", help="Output directory"),
):
    """Transcribe (or import) + diarize + merge a media file into labeled transcripts."""
    dev = resolve_device(device)
    typer.echo(f"Device: {dev.name} ({'usable' if dev.usable else 'NOT usable — ' + dev.detail})")

    def progress(frac: float, msg: str) -> None:
        bar = "" if frac < 0 else f"[{frac*100:5.1f}%] "
        typer.echo(f"{bar}{msg}")

    result = run_pipeline(
        media,
        transcript_path=None if transcribe else transcript,
        diarization_backend=diar_backend,
        transcription_backend=asr_backend,
        num_speakers=num_speakers, min_speakers=min_speakers, max_speakers=max_speakers,
        language=language, asr_model=asr_model, device=device,
        names=_parse_names(names), output_dir=out, progress=progress,
    )
    typer.echo("\nSpeakers (by speaking time):")
    for s in result.speakers:
        typer.echo(f"  {s['speaker']:20s} {s['minutes']:7.1f} min  ({s['cues']} cues)")
    typer.echo("\nOutputs:")
    for k, v in result.outputs.items():
        typer.echo(f"  {k:9s} {v}")


@app.command()
def devices():
    """List detected compute devices and whether they're usable."""
    for d in list_devices():
        mark = "ok" if d.usable else "UNUSABLE"
        typer.echo(f"  {d.kind:5s} {mark:9s} {d.name}  {d.detail}")


@app.command()
def backends():
    """List available transcription and diarization backends."""
    typer.echo("Transcription backends:")
    for name in sorted(transcription_backends()):
        typer.echo(f"  {name}")
    typer.echo("Diarization backends:")
    for name in sorted(diarization_backends()):
        typer.echo(f"  {name}")


@app.command()
def version():
    typer.echo(__version__)


if __name__ == "__main__":
    app()
