// Render tools/v2/scene.html frame by frame and mux with the voice + a soft beat.
// Usage: node tools/v2/render.js OUT_DIR [--preview t1,t2,...]
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

(async () => {
  const out = process.argv[2];
  const tl = JSON.parse(fs.readFileSync(path.join(out, 'timeline.json'), 'utf8'));
  const previewArg = process.argv.indexOf('--preview');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.resolve(__dirname, 'scene.html'));
  await page.evaluate(t => window.setup(t), tl);

  if (previewArg > 0) {
    for (const t of process.argv[previewArg + 1].split(',').map(Number)) {
      await page.evaluate(x => window.render(x), t);
      await page.screenshot({ path: path.join(out, `preview_${t}.png`) });
    }
    await browser.close();
    return;
  }

  const silent = path.join(out, 'silent.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(tl.fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', silent], { stdio: ['pipe', 'inherit', 'inherit'] });
  const frames = Math.ceil(tl.duration * tl.fps);
  for (let i = 0; i < frames; i++) {
    await page.evaluate(x => window.render(x), i / tl.fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`frame ${i}/${frames}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();

  const T = tl.duration.toFixed(2);
  const beat = `aevalsrc='0.04*sin(2*PI*110*t)+0.03*sin(2*PI*164.8*t)+0.025*sin(2*PI*220*t)+0.3*sin(2*PI*55*t)*exp(-16*mod(t,0.5))+0.05*(random(0)-0.5)*exp(-40*mod(t+0.25,0.5))':s=24000:d=${T}`;
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', silent, '-i', path.join(out, 'voice.wav'), '-f', 'lavfi', '-i', beat,
    '-filter_complex', `[1:a]loudnorm=I=-15:TP=-1.5[v];[2:a]volume=0.35,afade=out:st=${(tl.duration - 1).toFixed(2)}:d=1[m];[v][m]amix=inputs=2:duration=first:normalize=0[a]`,
    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-movflags', '+faststart',
    path.join(out, 'short.mp4')]);
  console.log('done', path.join(out, 'short.mp4'));
})();
