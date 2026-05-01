from __future__ import annotations

import argparse
import math
import wave
from pathlib import Path


def _tone(sample_rate: int, seconds: float, frequency: float, amplitude: float) -> list[int]:
    total = int(sample_rate * seconds)
    return [
        int(amplitude * 32767 * math.sin(2 * math.pi * frequency * index / sample_rate))
        for index in range(total)
    ]


def _silence(sample_rate: int, seconds: float) -> list[int]:
    return [0] * int(sample_rate * seconds)


def create_demo_wav(path: Path, sample_rate: int = 16_000) -> None:
    samples: list[int] = []
    samples.extend(_silence(sample_rate, 1.0))
    samples.extend(_tone(sample_rate, 0.28, 920.0, 0.82))
    samples.extend(_silence(sample_rate, 1.0))
    samples.extend(_tone(sample_rate, 0.9, 440.0, 0.45))
    samples.extend(_silence(sample_rate, 1.0))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(b"".join(sample.to_bytes(2, "little", signed=True) for sample in samples))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a tiny synthetic WAV demo fixture.")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    create_demo_wav(args.output)
    print(f"Wrote demo WAV to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
