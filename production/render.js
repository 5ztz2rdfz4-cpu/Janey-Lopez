// Usage: node render.js stills t1,t2,...  outdir      -> PNG stills
//        node render.js video  startFrame endFrame out.mp4   -> encoded segment (30 fps)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const PORT = process.env.PORT || 8765, FPS = 30;
(async () => {
  const [mode, a, b, out] = process.argv.slice(2);
  const browser = await chromium.launch({ args: ['--disable-web-security'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', m => console.log('[page]', m.text())); page.on('pageerror', e => console.error('[pageerror]', e.message));
  await page.goto(`http://127.0.0.1:${PORT}/doc.html`);
  await page.waitForFunction('window.READY === true');
  const shot = () => page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: 1080, height: 1920 } });
  if (mode === 'stills') {
    fs.mkdirSync(b, { recursive: true });
    for (const t of a.split(',').map(Number)) { await page.evaluate(t => draw(t), t); fs.writeFileSync(`${b}/t${t.toFixed(2).padStart(6, '0')}.png`, await shot()); }
  } else {
    const s = +a, e = +b;
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', FPS, '-c:v', 'png', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', '-r', FPS, out], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = s; f < e; f++) {
      await page.evaluate(t => draw(t), f / FPS);
      const buf = await shot();
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 150 === 0) console.log(out, f);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
