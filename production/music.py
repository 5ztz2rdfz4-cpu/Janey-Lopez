"""Original cinematic documentary score + motion-graphics SFX, synthesised with numpy.
No vocals, no samples. Outputs build/music.wav and build/sfx.wav (48k stereo, 90 s)."""
import numpy as np, wave
SR = 48000; T = 90.0; N = int(SR*T)
rng = np.random.default_rng(7)
def hz(m): return 440*2**((m-69)/12)
def write(path, x):
    x = x / max(1e-9, np.abs(x).max()) * 0.89
    w = wave.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x*32767).astype(np.int16).tobytes()); w.close()
def lp(x, fc):  # one-pole low-pass (fc may be array)
    fc = np.broadcast_to(np.asarray(fc, float), x.shape[:1])
    a = np.exp(-2*np.pi*fc/SR); y = np.empty_like(x); z = np.zeros(x.shape[1:])
    for i in range(len(x)): z = (1-a[i])*x[i] + a[i]*z; y[i] = z
    return y
def lp_fast(x, fc):  # constant cutoff, vectorised via FFT
    X = np.fft.rfft(x, axis=0); f = np.fft.rfftfreq(len(x), 1/SR)
    H = 1/np.sqrt(1+(f/fc)**4); return np.fft.irfft(X*(H[:, None] if x.ndim > 1 else H), n=len(x), axis=0)
def hp_fast(x, fc):
    X = np.fft.rfft(x, axis=0); f = np.fft.rfftfreq(len(x), 1/SR)
    H = (f/fc)**2/np.sqrt(1+(f/fc)**4); return np.fft.irfft(X*(H[:, None] if x.ndim > 1 else H), n=len(x), axis=0)
def env(n, a, r):  # attack / release (s), sustain between
    e = np.ones(n); na, nr = int(a*SR), int(r*SR)
    if na: e[:na] = np.linspace(0, 1, na)**1.5
    if nr: e[-nr:] *= np.linspace(1, 0, nr)**2
    return e
def place(buf, x, t, pan=0.0, g=1.0):
    i = int(t*SR); x = x[:max(0, len(buf)-i)]
    L, R = np.cos((pan+1)*np.pi/4), np.sin((pan+1)*np.pi/4)
    buf[i:i+len(x), 0] += x*L*g*1.414; buf[i:i+len(x), 1] += x*R*g*1.414
def auto(points):  # piecewise-linear automation curve over the timeline
    ts, vs = zip(*points); return np.interp(np.arange(N)/SR, ts, vs)

BPM = 90; BEAT = 60/BPM; BAR = 4*BEAT
# D minor: i - VI - III - VII ; final section lifts to VI - VII - i(add9) - III
PROG = [(50, [62, 65, 69]), (46, [62, 65, 70]), (53, [60, 65, 69]), (48, [60, 64, 67])]
LIFT = [(46, [62, 65, 70, 74]), (48, [64, 67, 72]), (50, [62, 65, 69, 76]), (53, [65, 69, 72, 77])]
def chord_at(t):
    k = int(t // BAR); return (LIFT if t >= 79.4 else PROG)[k % 4]

music = np.zeros((N, 2))
# ---- pad (detuned saw stack, soft) ----
pad = np.zeros((N, 2))
nb = int(np.ceil(T/BAR))+1
for k in range(nb):
    t0 = k*BAR; root, notes = chord_at(t0+.01)
    dur = BAR + 1.6; n = int(dur*SR); tt = np.arange(n)/SR
    for m in notes + [root+12]:
        for d, pan in ((-.0025, -.6), (0, 0), (.0025, .6)):
            f = hz(m)*(1+d); s = np.zeros(n)
            for h in range(1, 9): s += np.sin(2*np.pi*f*h*tt + h*1.3)/h**1.6
            place(pad, s*env(n, 1.2, 1.6)*0.05, t0, pan)
pad = lp_fast(pad, 1800)
music += pad * auto([(0, .55), (10, .7), (30, .8), (79, .85), (80.5, 1.0), (88, .9), (90, 0)])[:, None]
# ---- drone / sub ----
tt = np.arange(N)/SR
drone = (np.sin(2*np.pi*hz(38)*tt) + .4*np.sin(2*np.pi*hz(50)*tt+.5)) * (.5+.5*np.sin(2*np.pi*.07*tt))
music += (drone*.10*auto([(0, 0), (1, 1), (88, 1), (90, 0)]))[:, None]
# ---- piano-like arpeggio (from scene 2) ----
arp = np.zeros((N, 2)); pat = [0, 1, 2, 3, 2, 1, 3, 2]
t = 11.0 - (11.0 % (BEAT/2))
while t < 88.5:
    root, notes = chord_at(t); tones = sorted(notes) + [notes[0]+12, notes[1]+12]
    m = tones[pat[int(round(t/(BEAT/2))) % 8] % len(tones)] + 12
    n = int(2.2*SR); x = np.arange(n)/SR; f = hz(m)
    s = (np.sin(2*np.pi*f*x) + .35*np.sin(4*np.pi*f*x) + .12*np.sin(6*np.pi*f*x)) * np.exp(-x*2.6) * np.minimum(1, x/0.004)
    place(arp, s*.05, t, pan=np.sin(t*1.7)*.5)
    t += BEAT/2
music += arp * auto([(0, 0), (11, 0), (13, .8), (30, 1), (79.3, 1), (79.5, .5), (88, .8), (90, 0)])[:, None]
# ---- pulse bass (8ths) from youth scene ----
bass = np.zeros((N, 2)); t = 30.6 - (30.6 % (BEAT/2))
while t < 79.3:
    root, _ = chord_at(t); n = int(.32*SR); x = np.arange(n)/SR
    s = np.tanh(2*np.sin(2*np.pi*hz(root-12)*x)) * np.exp(-x*9) * np.minimum(1, x/.006)
    place(bass, s*.09, t); t += BEAT/2
music += lp_fast(bass, 500) * auto([(30, 0), (31.5, .8), (54, 1), (69, 1.15), (79.2, 1.2), (79.4, 0)])[:, None]
# ---- soft cinematic percussion (kick on 1 & 3, tom pickup) ----
perc = np.zeros((N, 2)); t = 40.0 - (40.0 % BEAT)
while t < 79.3:
    b = int(round(t/BEAT)) % 4
    if b in (0, 2):
        n = int(.5*SR); x = np.arange(n)/SR; f = 45+80*np.exp(-x*30)
        place(perc, np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*7)*.3, t)
    if b == 3 and t > 54:
        n = int(.25*SR); x = np.arange(n)/SR
        place(perc, lp_fast(rng.standard_normal(n), 2500)*np.exp(-x*22)*.05, t+BEAT/2, pan=.3)
    t += BEAT
music += perc * auto([(40, 0), (41, .7), (54, .9), (69, 1), (79.3, 1)])[:, None]
# ---- shimmer (high airy layer) ----
sh = lp_fast(hp_fast(rng.standard_normal((N, 2)), 5000), 9000) * (0.5+0.5*np.sin(2*np.pi*.2*tt))[:, None]
music += sh * .012 * auto([(0, .5), (54, .6), (69, 1), (79.4, 1.4), (90, 0)])[:, None]
# ---- reverb (FFT convolution with a decaying-noise IR) ----
irn = int(3.2*SR); x = np.arange(irn)/SR
ir = np.stack([rng.standard_normal(irn), rng.standard_normal(irn)], 1)*np.exp(-x*2.1)[:, None]
ir = lp_fast(ir, 6000); ir /= np.sqrt((ir**2).sum(0))
L = 1 << int(np.ceil(np.log2(N+irn)))
wet = np.fft.irfft(np.fft.rfft(music, L, axis=0)*np.fft.rfft(ir, L, axis=0), L, axis=0)[:N]
music = music*.75 + wet*.55
music *= auto([(0, 0), (.3, 1), (88.2, 1), (90, 0)])[:, None]
write('build/music.wav', music)

# =================== SFX ===================
sfx = np.zeros((N, 2))
def whoosh(t, d=0.9, g=1.0, up=True):
    n = int(d*SR); x = np.linspace(0, 1, n)
    e = np.sin(np.pi*x)**2 * (x**.6 if up else 1)
    fc = 300 + 5000*np.sin(np.pi*x)**2
    s = lp(rng.standard_normal((n, 2)), fc) * e[:, None]
    i = int(t*SR); sfx[i:i+n] += s[:N-i]*.55*g
def impact(t, g=1.0):
    n = int(2.6*SR); x = np.arange(n)/SR; f = 32+70*np.exp(-x*9)
    boom = np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*2.2)
    hit = lp_fast(rng.standard_normal(n), 1200)*np.exp(-x*14)*.6
    place(sfx, (boom+hit)*.9*g, t)
def blip(t, f=1400, g=1.0, pan=0.):
    n = int(.18*SR); x = np.arange(n)/SR
    s = (np.sin(2*np.pi*f*x)+.3*np.sin(2*np.pi*f*1.5*x))*np.exp(-x*38)*np.minimum(1, x/.002)
    place(sfx, s*.16*g, t, pan)
def pop(t, g=1.0):  # soft UI pop for card/chip reveals
    n = int(.12*SR); x = np.arange(n)/SR; f = 500+900*np.exp(-x*60)
    place(sfx, np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*30)*.18*g, t)
def chime(t, g=1.0):  # gold shimmer on key typography
    for k, m in enumerate([86, 90, 93, 98]):
        n = int(1.6*SR); x = np.arange(n)/SR
        place(sfx, np.sin(2*np.pi*hz(m)*x)*np.exp(-x*3.2)*.045*g, t+k*.05, pan=(k-1.5)*.3)
def riser(t0, t1, g=1.0):
    n = int((t1-t0)*SR); x = np.linspace(0, 1, n)
    s = lp(rng.standard_normal((n, 2)), 200+6000*x**2)*(x**2)[:, None]
    tone = np.sin(2*np.pi*np.cumsum(110+330*x**2)/SR)*x**2*.3
    s += tone[:, None]; i = int(t0*SR); sfx[i:i+n] += s*.4*g
def tick(t, g=1.0):
    n = int(.03*SR); place(sfx, hp_fast(rng.standard_normal(n), 3000)*np.exp(-np.arange(n)/SR*200)*.12*g, t)
def room(t0, t1, g=1.0):  # ambient air bed
    n = int((t1-t0)*SR); s = lp_fast(rng.standard_normal((n, 2)), 400)*env(n, 2, 2)[:, None]
    i = int(t0*SR); sfx[i:i+n] += s*.05*g

impact(0.15, 1.0); room(0, 90, 1)
for b in [11.0, 30.75, 40.2, 54.15, 69.3]: whoosh(b-.55, .95)
whoosh(59.0, .7, .6); whoosh(64.35, .7, .6)              # issue-panel slides
riser(76.6, 79.45, .9); impact(79.45, .8)                  # into the finale
for t in [1.2, 2.8, 5.0]: tick(t, .8)                       # portrait ring draw / card move
whoosh(4.8, .7, .5)
for t in [6.4, 7.9, 8.55, 8.85, 9.2, 9.5, 9.95]: tick(t)    # title words
chime(9.2, .9)
for i, t in enumerate([21.3, 22.4, 23.75, 24.5]): blip(t, 1100+i*180, 1, (i-1.5)*.3)
whoosh(25.2, .7, .4)
for t in [27.0, 29.15]: pop(t); blip(t+.05, 1650, .6)
for t in [16.4]: chime(t, .7)
for t in [35.75, 37.75, 38.85]: pop(t); blip(t+.04, 1500, .5)
blip(36.85, 900, .8)                                        # ballot drops in
for i in range(18): tick(41.4+i*.1, .5)
chime(46.25, .9); chime(51.75, 1.0)
for t in [50.2, 50.9, 52.3]: pop(t, .9)
for t in [51.9, 52.3, 52.7]: whoosh(t-.1, .45, .25)
for t in [55.9, 60.2, 66.2]: pop(t); chime(t+.1, .5)
for k in range(5): blip(65.6+k*.18, 900+k*150, .5)
for k in range(3): tick(66.8+k*.4, .8)
for i in range(5): pop(70.4+i*.45, .8)
for i in range(5): blip(72.3+i*.3, 1300+i*90, .45, (i-2)*.3)
chime(75.7, 1.0); chime(82.75, 1.0)
write('build/sfx.wav', sfx)
print('ok')
