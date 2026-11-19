"""Group the corrected, re-timed words into subtitle chunks; write build/subs.json + .srt"""
import json
d = json.load(open('build/timeline.json'))
chunks = []
for c in d['clips']:
    ws = []
    for w in c['words']:
        if w['w'].startswith('-') and ws:            # "contoh -contoh" -> "contoh-contoh"
            ws[-1] = dict(ws[-1], w=ws[-1]['w'] + w['w'], t1=w['t1'])
        else:
            ws.append(dict(w))
    # split at commas into phrases, then balance each phrase into ~<=30-char chunks
    phrases, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        nxt = ws[i+1] if i+1 < len(ws) else None
        if nxt is None or w['w'].endswith((',', '?', '.')) or nxt['t0'] - w['t1'] > 0.45:
            phrases.append(cur); cur = []
    for ph in phrases:
        L = len(' '.join(x['w'] for x in ph)); n = max(1, -(-L // 30))
        target = L / n; acc = []; 
        for j, w in enumerate(ph):
            acc.append(w)
            done = len(' '.join(x['w'] for x in acc))
            left = len(ph) - j - 1
            if j == len(ph)-1 or (done >= target*0.85 and left >= 1 and len(chunks_tmp:=acc) and n > 1):
                if j == len(ph)-1 or done >= target*0.85:
                    chunks.append(dict(t0=acc[0]['t0'] - 0.05, words=acc, clip_end=c['t1'])); acc = []
for i, ch in enumerate(chunks):
    nxt = chunks[i+1]['t0'] if i+1 < len(chunks) else 1e9
    ch['t1'] = round(min(nxt - 0.02, max(ch['words'][-1]['t1'], ch['clip_end']) + 0.25, ch['words'][-1]['t1'] + 0.6), 3)
    ch['text'] = ' '.join(w['w'] for w in ch['words'])
# sentence-case first chunk of each clip
json.dump(chunks, open('build/subs.json', 'w'), ensure_ascii=False, indent=0)
def ts(t):
    ms = int(round(t*1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
with open('build/subtitles_ms.srt', 'w') as f:
    for i, ch in enumerate(chunks, 1):
        f.write(f"{i}\n{ts(ch['t0'])} --> {ts(ch['t1'])}\n{ch['text'].rstrip(',')}\n\n")
for ch in chunks: print(f"{ch['t0']:6.2f}-{ch['t1']:6.2f} {ch['text']}")
