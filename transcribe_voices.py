"""Resume local Russian speech transcription, saving each recording atomically."""

import argparse
import json
import os
import sqlite3
import sys
import time
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parent
os.environ["HF_HOME"] = str(ROOT / ".asr-models")
sys.path.insert(0, str(ROOT / ".asr-deps"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="small")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--cpu-threads", type=int, default=8)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--ids", nargs="*", type=int)
    args = parser.parse_args()

    from faster_whisper import WhisperModel

    output = args.root / "knowledge" / "transcripts"
    output.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.root / "knowledge" / "chat.sqlite") as connection:
        rows = connection.execute(
            "SELECT id, voice_file FROM messages WHERE voice_file IS NOT NULL ORDER BY id"
        ).fetchall()
    if args.ids:
        chosen = set(args.ids)
        rows = [row for row in rows if row[0] in chosen]
    distinct = list(dict((file, id) for id, file in rows).items())
    pending = [(file, id) for file, id in distinct if not (output / f"{Path(file).stem}.json").exists()]
    if args.limit:
        pending = pending[: args.limit]
    print(f"Pending {len(pending)} of {len(distinct)} unique recordings", flush=True)
    if not pending:
        return

    compute_type = "float16" if args.device == "cuda" else "int8"
    model = WhisperModel(
        args.model, device=args.device, compute_type=compute_type,
        cpu_threads=args.cpu_threads, local_files_only=args.local_files_only,
    )
    failures = 0
    for index, (voice_file, message_id) in enumerate(pending, 1):
        start = time.monotonic()
        try:
            segments, info = model.transcribe(
                str(args.root / voice_file),
                language="ru",
                beam_size=5,
                vad_filter=True,
                condition_on_previous_text=False,
                initial_prompt="Трейдинг, фьючерсы, акции, золото, нефть, газ, сезонность, Ларри Вильямс, COT, индикатор, таймфрейм, лонг, шорт, стоп-лосс.",
            )
            parts = [
                {"start": round(segment.start, 2), "end": round(segment.end, 2), "text": segment.text.strip()}
                for segment in segments
            ]
            result = {
                "message_id": message_id,
                "voice_file": voice_file,
                "model": args.model,
                "language": info.language,
                "duration": round(info.duration, 2),
                "text": " ".join(part["text"] for part in parts),
                "segments": parts,
            }
            destination = output / f"{Path(voice_file).stem}.json"
            temporary = destination.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temporary, destination)
            print(f"{index}/{len(pending)} message {message_id}, {info.duration:.0f}s audio, {time.monotonic()-start:.1f}s elapsed", flush=True)
        except Exception:
            failures += 1
            with (output.parent / "transcription_errors.log").open("a", encoding="utf-8") as log:
                log.write(f"Message {message_id}, {voice_file}\n{traceback.format_exc()}\n")
            print(f"{index}/{len(pending)} message {message_id} failed; continuing", flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
