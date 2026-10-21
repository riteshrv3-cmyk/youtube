"""Generate per-scene Gemini voiceover and a timeline (scene times, word times, mouth openness per frame).
Usage: GEMINI_API_KEY=... python3 tools/v2/voice.py SCRIPT.json OUT_DIR"""
import json, subprocess, sys, time, wave
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import gemini

FPS = 30
GAP = 0.25  # pause between scenes (s)

def main(script_path, out):
    script = json.load(open(script_path)); out = Path(out); out.mkdir(parents=True, exist_ok=True)
    style = script["style"]; scenes = []; t0 = 0.0; pcm_all = []
    for i, sc in enumerate(script["scenes"]):
        wav = out / f"vo{i}.wav"
        if not wav.exists():
            for attempt in range(4):
                try:
                    gemini.tts(sc["say"], str(wav), voice=script["voice"], style=style); break
                except SystemExit as e:
                    if "429" in str(e) and attempt < 3: time.sleep(20); continue
                    raise
        with wave.open(str(wav)) as w:
            sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
        # trim leading/trailing silence
        idx = np.where(np.abs(x) > 600)[0]
        x = x[max(idx[0] - 1200, 0): idx[-1] + 2400] if len(idx) else x
        x = np.concatenate([x, np.zeros(int(GAP * sr), np.float32)])
        pcm_all.append(x); d = len(x) / sr
        words = sc["caption"].split(); total = sum(len(w) + 1 for w in words); acc = 0; wt = []
        speech = d - GAP
        for w_ in words:
            wt.append([w_, round(t0 + speech * acc / total, 3)]); acc += len(w_) + 1
        scenes.append({**sc, "start": round(t0, 3), "end": round(t0 + d, 3), "words": wt}); t0 += d
    x = np.concatenate(pcm_all); sr = 24000
    wave_out = out / "voice.wav"
    with wave.open(str(wave_out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(np.clip(x, -32768, 32767).astype(np.int16).tobytes())
    hop = sr // FPS; n = len(x) // hop
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
    ref = np.percentile(rms[rms > 0], 90) if np.any(rms > 0) else 1
    mouth = np.clip(rms / ref, 0, 1); mouth[mouth < 0.12] = 0
    mouth = np.convolve(mouth, [0.25, 0.5, 0.25], "same")
    tl = {"fps": FPS, "duration": round(len(x) / sr, 3), "scenes": scenes, "mouth": [round(float(m), 3) for m in mouth]}
    json.dump(tl, open(out / "timeline.json", "w"), ensure_ascii=False)
    print("duration", tl["duration"])

if __name__ == "__main__":
    main(*sys.argv[1:3])
