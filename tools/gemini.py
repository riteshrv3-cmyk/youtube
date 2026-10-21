"""Minimal Gemini API helpers (TTS + image). Reads the key from the GEMINI_API_KEY env var."""
import base64, json, os, subprocess, sys, urllib.request

BASE = "https://generativelanguage.googleapis.com/v1beta/models"

def _post(model, body):
    req = urllib.request.Request(f"{BASE}/{model}:generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{model}: HTTP {e.code}: {e.read().decode()[:600]}")

def tts(text, out_wav, voice="Puck", model="gemini-2.5-flash-preview-tts", style=""):
    prompt = f"{style}\n{text}" if style else text
    d = _post(model, {"contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"responseModalities": ["AUDIO"],
                                           "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}})
    pcm = base64.b64decode(d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
    raw = out_wav + ".pcm"; open(raw, "wb").write(pcm)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", "24000", "-ac", "1",
                    "-i", raw, out_wav], check=True)
    os.remove(raw)

def image(prompt, out_png, model="gemini-2.5-flash-image", aspect="9:16", ref=None):
    parts = [{"text": prompt}]
    if ref:
        parts.insert(0, {"inlineData": {"mimeType": "image/png", "data": base64.b64encode(open(ref, "rb").read()).decode()}})
    d = _post(model, {"contents": [{"parts": parts}],
                      "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}}})
    for p in d["candidates"][0]["content"]["parts"]:
        if "inlineData" in p:
            open(out_png, "wb").write(base64.b64decode(p["inlineData"]["data"])); return
    raise SystemExit("no image in response: " + json.dumps(d)[:400])

if __name__ == "__main__":
    kind, text, out = sys.argv[1:4]
    (tts if kind == "tts" else image)(text, out)
