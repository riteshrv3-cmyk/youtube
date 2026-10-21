"""Build a sample vertical Short locally: neural Hindi TTS + PIL motion cards + burned captions.
Used when cloud generation credits are unavailable. Usage: python3 tools/build_sample_short.py OUT_DIR"""
import asyncio, os, subprocess, sys, textwrap
from pathlib import Path
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
VOICE = "hi-IN-SwaraNeural"
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_REG = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf"

# (voiceover in Devanagari for correct pronunciation, caption in Roman Hinglish, headline, scene kind)
SCENES = [
    ("रिज़्यूमे बनाने में घंटों लगते हैं? अब सिर्फ़ तीस सेकंड में बनेगा!",
     "Resume banane me ghante lagte hain? Ab sirf 30 second me!", "30 SEC RESUME", "hook"),
    ("स्टेप वन: अपना एक्सपीरियंस छोटे बुलेट पॉइंट्स में लिखो।",
     "Step 1: apna experience chhote bullet points me likho.", "STEP 1", "bullets"),
    ("स्टेप टू: ये प्रॉम्प्ट चैटजीपीटी में पेस्ट करो।",
     "Step 2: ye prompt ChatGPT me paste karo.", "STEP 2", "prompt"),
    ("एआई तुम्हारे पॉइंट्स को प्रोफेशनल, ए टी एस फ्रेंडली रिज़्यूमे में बदल देगा।",
     "AI tumhare points ko professional, ATS-friendly resume me badal dega.", "ATS FRIENDLY", "resume"),
    ("ऐसे दस फ्री प्रॉम्प्ट्स चाहिए? लिंक पिन्ड कमेंट में है। फॉलो करो!",
     "Aise 10 FREE prompts chahiye? Link pinned comment me. Follow karo!", "FREE PROMPTS", "cta"),
]
ACC = (255, 204, 0)

def font(p, s): return ImageFont.truetype(p, s)

def background():
    img = Image.new("RGB", (W, H), (10, 10, 20))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.ellipse((-300, 200, 900, 1300), fill=(0, 90, 110))
    d.ellipse((300, 900, 1400, 2000), fill=(120, 70, 0))
    glow = glow.filter(ImageFilter.GaussianBlur(220))
    return Image.blend(img, glow, 0.85)

def centered(d, y, text, f, fill):
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=fill)

def card(d, box, fill=(24, 24, 38), outline=(70, 70, 100)):
    d.rounded_rectangle(box, radius=36, fill=fill, outline=outline, width=3)

def scene_img(caption, headline, kind):
    img = background()
    d = ImageDraw.Draw(img)
    # brand bar
    centered(d, 110, "AI WALA HINGLISH", font(FONT, 40), (200, 200, 220))
    # headline pill
    hf = font(FONT, 96)
    tw = d.textlength(headline, font=hf)
    d.rounded_rectangle(((W - tw) / 2 - 40, 260, (W + tw) / 2 + 40, 400), radius=30, fill=ACC)
    centered(d, 272, headline, hf, (0, 0, 0))
    m = font(MONO, 38); r = font(FONT_REG, 44); b = font(FONT, 54)
    if kind == "hook":
        card(d, (140, 520, 940, 1260))
        centered(d, 640, "Resume", font(FONT, 120), (255, 255, 255))
        centered(d, 800, "1 ghanta  →  30 sec", b, ACC)
        for i in range(5):
            d.rounded_rectangle((220, 950 + i * 55, 860 - i * 70, 975 + i * 55), radius=12, fill=(60, 60, 90))
    elif kind == "bullets":
        card(d, (110, 520, 970, 1260))
        for i, t in enumerate(["• 2 saal sales intern", "• Excel + Canva", "• 50+ clients handle kiye", "• Team lead, college fest"]):
            d.text((170, 600 + i * 150), t, font=b, fill=(235, 235, 245))
    elif kind == "prompt":
        card(d, (90, 520, 990, 1300), fill=(18, 18, 28))
        d.text((140, 560), "ChatGPT  >  New chat", font=r, fill=(150, 150, 170))
        prompt = ("Act as a professional resume writer. Turn my bullet points into an ATS-friendly "
                  "resume for a [role] job. Use action verbs, numbers and a 2-line summary. "
                  "My points: [paste here]")
        for i, line in enumerate(textwrap.wrap(prompt, 36)):
            d.text((140, 660 + i * 62), line, font=m, fill=(120, 255, 170))
    elif kind == "resume":
        card(d, (150, 500, 930, 1320), fill=(245, 245, 250), outline=(245, 245, 250))
        d.text((210, 560), "RAHUL SHARMA", font=font(FONT, 60), fill=(20, 20, 30))
        d.text((210, 640), "Sales & Marketing Associate", font=r, fill=(90, 90, 110))
        for i, t in enumerate(["✓ Summary", "✓ Experience", "✓ Skills", "✓ ATS keywords"]):
            d.text((210, 760 + i * 120), t, font=b, fill=(0, 140, 90))
    elif kind == "cta":
        card(d, (140, 560, 940, 1240))
        centered(d, 640, "10", font(FONT, 260), ACC)
        centered(d, 920, "FREE AI PROMPTS", b, (255, 255, 255))
        centered(d, 1040, "↓ pinned comment ↓", r, (200, 200, 220))
    # caption box
    cf = font(FONT, 58)
    lines = textwrap.wrap(caption, 26)
    top = 1420
    d.rounded_rectangle((60, top - 30, W - 60, top + len(lines) * 78 + 20), radius=28, fill=(0, 0, 0))
    for i, line in enumerate(lines):
        centered(d, top + i * 78, line, cf, (255, 255, 255) if i else ACC)
    # disclosure
    centered(d, 1830, "Tool tutorial • results may vary", font(FONT_REG, 30), (150, 150, 170))
    return img

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(p)]).decode())

async def _edge(text, out):
    await edge_tts.Communicate(text, VOICE, rate="+12%", proxy=os.environ.get("HTTPS_PROXY")).save(str(out))

def tts(text, out):
    """Neural voice via edge-tts; falls back to offline espeak-ng (robotic placeholder) if blocked."""
    try:
        asyncio.run(_edge(text, out))
    except Exception:
        wav = out.with_suffix(".wav")
        subprocess.run(["espeak-ng", "-v", "hi", "-s", "160", "-p", "55", "-w", str(wav), text], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), str(out)], check=True)

def main(out):
    out = Path(out); work = out / "work"; work.mkdir(parents=True, exist_ok=True)
    clips = []
    for i, (vo, cap, head, kind) in enumerate(SCENES):
        a = work / f"vo{i}.mp3"; tts(vo, a)
        png = work / f"s{i}.png"; scene_img(cap, head, kind).save(png)
        t = dur(a) + 0.35
        frames = int(t * 30)
        clip = work / f"c{i}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png), "-i", str(a),
            "-filter_complex",
            f"[0:v]scale=1188:2112,zoompan=z='min(1+0.0009*on,1.1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30,"
            f"fade=in:st=0:d=0.15[v];[1:a]apad[a]",
            "-map", "[v]", "-map", "[a]", "-t", f"{t:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "44100", str(clip)], check=True)
        clips.append(clip)
    lst = work / "list.txt"; lst.write_text("".join(f"file '{c.name}'\n" for c in clips))
    joined = work / "joined.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(joined)], check=True)
    T = dur(joined)
    final = out / "sample_short_resume.mp4"
    beat = (f"aevalsrc='0.05*sin(2*PI*110*t)+0.04*sin(2*PI*164.8*t)+0.03*sin(2*PI*220*t)"
            f"+0.35*sin(2*PI*55*t)*exp(-18*mod(t,0.5))':s=44100:d={T:.2f}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(joined), "-f", "lavfi", "-i", beat,
                    "-filter_complex", "[1:a]volume=0.5,afade=out:st=" + f"{T-1:.2f}" + ":d=1[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", "20", "-c:a", "aac",
                    "-movflags", "+faststart", str(final)], check=True)
    scene_img(SCENES[0][1], SCENES[0][2], "hook").save(out / "thumbnail.png")
    print(final, f"{dur(final):.1f}s")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "output/sample")
