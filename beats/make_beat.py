"""Generate an original beat in the style of 'HMMM' (96 BPM, F minor).

Style template taken from analysis of the reference:
  - 96 BPM, F minor, 4-bar loop: Bbm9 | Dbmaj9 | Abmaj7 | Cm7
  - Syncopated groove (16th steps 0-15): snare/clap on 0, 3, 9 (+13 variations),
    punchy kick + long gliding 808 on 7, 11, 13
  - Sparse hats with occasional rolls, warm pads/keys, hummed "mmm" lead
Usage: python3 make_beat.py out.wav
"""
import sys
import numpy as np
from scipy import signal

SR = 44100
BPM = 96
BEAT = 60 / BPM
STEP = BEAT / 4          # 16th note
BAR = BEAT * 4
rng = np.random.default_rng(7)


def midi_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env_adsr(n, a, d, s, r, sustain_len):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    sl = max(int(sustain_len * SR) - a - d, 0)
    e = np.concatenate([np.linspace(0, 1, a, endpoint=False),
                        np.linspace(1, s, d, endpoint=False),
                        np.full(sl, s),
                        np.linspace(s, 0, r)])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def lp(x, fc, order=2):
    sos = signal.butter(order, fc, btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def hp(x, fc, order=2):
    sos = signal.butter(order, fc, btype="high", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


# ---------------------------------------------------------------- instruments
def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 48 + 140 * np.exp(-t * 38)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t * 9)
    click = hp(rng.standard_normal(n), 2000) * np.exp(-t * 400) * 0.25
    return np.tanh(2.2 * (x + click)) * 0.9


def eight08(note, length, glide_from=None, glide_time=0.07):
    n = int((length + 0.08) * SR)
    t = np.arange(n) / SR
    f_target = midi_hz(note)
    if glide_from is not None:
        f0 = midi_hz(glide_from)
        f = f_target + (f0 - f_target) * np.exp(-t / glide_time * 3)
    else:
        f = f_target * (1 + 0.6 * np.exp(-t * 60))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph)
    e = env_adsr(n, 0.004, 0.3, 0.6, 0.06, length) * np.exp(-t * 1.2)
    y = np.tanh(1.6 * x * e) * 0.6          # saturation = audible harmonics
    return lp(y, 900)


def snare():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    noise = bp(rng.standard_normal(n), 1200, 9000) * np.exp(-t * 22)
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 35)
    return np.tanh(1.5 * (0.7 * noise + 0.6 * body)) * 0.55


def clap():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    base = bp(rng.standard_normal(n), 900, 5000)
    e = np.zeros(n)
    for k, d in enumerate([0, 0.010, 0.021]):
        i = int(d * SR)
        e[i:] += np.exp(-(t[: n - i]) * (180 if k < 2 else 16))
    return base * e * 0.35


def hat(open_=False, vel=1.0):
    n = int((0.25 if open_ else 0.06) * SR)
    t = np.arange(n) / SR
    x = hp(rng.standard_normal(n), 7500, 4)
    return x * np.exp(-t * (14 if open_ else 90)) * 0.22 * vel


def epiano(notes, length, vel=0.6):
    n = int((length + 1.2) * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for m in notes:
        f = midi_hz(m)
        mod = np.sin(2 * np.pi * f * 1.0 * t) * 1.6 * np.exp(-t * 4)
        tone = np.sin(2 * np.pi * f * t + mod)
        tine = np.sin(2 * np.pi * f * 7 * t) * 0.08 * np.exp(-t * 12)
        out += (tone + tine) * np.exp(-t * 1.4)
    e = env_adsr(n, 0.003, 0.1, 1.0, 0.6, length)
    return out * e * vel / len(notes) * (1 + 0.15 * np.sin(2 * np.pi * 4.5 * t))  # tremolo


def pad(notes, length):
    n = int((length + 1.5) * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for m in notes:
        for det in (-0.12, 0.0, 0.12):
            f = midi_hz(m) * 2 ** (det / 12)
            out += signal.sawtooth(2 * np.pi * f * t + rng.uniform(0, 6.28))
    out = lp(out, 1400, 2)
    return out * env_adsr(n, 0.6, 0.4, 0.8, 1.4, length) * 0.05 / len(notes)


def hum(note, length, vel=0.5, glide_from=None):
    """Formant-filtered saw that sounds like a hummed 'mmm/ooo'."""
    n = int((length + 0.4) * SR)
    t = np.arange(n) / SR
    f = midi_hz(note) * (1 + 0.012 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t * 3, 0, 1))
    if glide_from is not None:
        f = f + (midi_hz(glide_from) - midi_hz(note)) * np.exp(-t * 25)
    src = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
    y = (bp(src, 250, 420) * 1.0 + bp(src, 700, 900) * 0.35 + bp(src, 2300, 2700) * 0.08)
    return y * env_adsr(n, 0.05, 0.1, 0.85, 0.3, length) * vel


# ------------------------------------------------------------------ music data
# Fm: chord voicings (MIDI)
CHORDS = [
    [58, 61, 65, 68, 72],   # Bbm9  (Bb Db F Ab C)
    [61, 65, 68, 72, 75],   # Dbmaj9 (Db F Ab C Eb)
    [56, 60, 63, 67, 70],   # Abmaj9 (Ab C Eb G Bb)
    [60, 63, 67, 70, 74],   # Cm9   (C Eb G Bb D)
]
BASS_ROOT = [34, 37, 32, 36]  # Bb1 Db2 Ab1 C2

# 808 per bar: (step, note offset vs root, length in steps, glide_from offset)
B808 = [
    [(0, 0, 7, None), (7, 0, 4, None), (11, 3, 2, 0), (13, 0, 3, None)],
    [(0, 0, 7, None), (7, 0, 4, None), (11, 0, 2, None), (13, -1, 3, 0)],
    [(0, 0, 7, None), (7, 0, 4, None), (11, 7, 2, 0), (13, 0, 3, 7)],
    [(0, 0, 7, None), (7, 0, 4, None), (11, -2, 2, None), (13, -4, 3, -2)],
]

# Hummed lead (F minor pentatonic-ish), 4 bars: (step-from-loop-start, midi, len steps)
LEAD = [
    (0, 72, 3), (3, 75, 3), (6, 77, 4), (11, 75, 2), (13, 72, 3),
    (16, 77, 3), (19, 80, 5), (24, 77, 2), (26, 75, 6),
    (32, 72, 3), (35, 75, 3), (38, 72, 2), (40, 70, 6), (46, 68, 2),
    (48, 67, 3), (51, 68, 3), (54, 70, 4), (58, 72, 6),
]
LEAD_B = [  # answer phrase for second half of sections
    (0, 80, 2), (2, 79, 2), (4, 77, 4), (9, 75, 3), (12, 77, 4),
    (16, 80, 3), (19, 82, 3), (22, 80, 6), (29, 77, 3),
    (32, 75, 3), (35, 77, 3), (38, 75, 2), (40, 72, 8),
    (48, 70, 3), (51, 72, 3), (54, 75, 2), (56, 72, 8),
]

# keys rhythm (steps where chord stabs hit) - follows the bounce
KEY_HITS = [(0, 6), (7, 4), (11, 5)]

# Arrangement (bars): name, flags
SECTIONS = [
    ("intro", 8, dict(pad=1, keys=1, lead=1, drums=0, b808=0)),
    ("hook", 16, dict(pad=1, keys=1, lead=1, drums=2, b808=1)),
    ("break", 4, dict(pad=1, keys=0, lead=1, drums=0, b808=0)),
    ("verse", 16, dict(pad=1, keys=1, lead=0, drums=1, b808=1)),
    ("hook", 16, dict(pad=1, keys=1, lead=1, drums=2, b808=1)),
    ("outro", 4, dict(pad=1, keys=1, lead=0, drums=0, b808=0)),
]


def build():
    total_bars = sum(s[1] for s in SECTIONS)
    N = int((total_bars * BAR + 4) * SR)
    tracks = {k: np.zeros(N) for k in ("drums", "b808", "keys", "pad", "lead")}

    def add(tr, x, t):
        i = int(t * SR)
        j = min(N, i + len(x))
        if i < N:
            tracks[tr][i:j] += x[: j - i]

    K, S, C = kick(), snare(), clap()
    bar_idx = 0
    for name, nbars, fl in SECTIONS:
        for b in range(nbars):
            t0 = (bar_idx + b) * BAR
            ci = b % 4
            last_bar = b == nbars - 1
            # swing: delay off-16ths slightly (reference sits a bit behind)
            def st(s):
                return t0 + s * STEP + (0.012 if s % 2 else 0)

            if fl["pad"]:
                add("pad", pad(CHORDS[ci][:4], BAR), t0)
            if fl["keys"]:
                for s, ln in KEY_HITS:
                    v = 0.55 if s == 0 else 0.4
                    add("keys", epiano(CHORDS[ci], ln * STEP, v), st(s))
            if fl["lead"]:
                phrase = LEAD if (b // 4) % 2 == 0 else LEAD_B
                for s, m, ln in phrase:
                    if ci * 16 <= s < (ci + 1) * 16:
                        prev = None
                        add("lead", hum(m, ln * STEP, 0.45), t0 + (s - ci * 16) * STEP)
            if fl["b808"]:
                root = BASS_ROOT[ci]
                for s, off, ln, gl in B808[ci]:
                    add("b808", eight08(root + off, ln * STEP,
                                        None if gl is None else root + gl), st(s))
            if fl["drums"]:
                # snare + clap layer: 0, 3, 9 ; 13 on every 2nd bar
                sn_steps = [0, 3, 9] + ([13] if b % 2 else [])
                for s in sn_steps:
                    add("drums", S * (1.0 if s in (0, 9) else 0.75), st(s))
                    if fl["drums"] == 2:
                        add("drums", C * 0.8, st(s))
                for s in (7, 11, 13):
                    if s == 11 and b % 4 == 3:
                        continue
                    add("drums", K * (1.0 if s == 7 else 0.85), st(s))
                # hats: on snare tops + 8ths in hook, roll at end of 4-bar phrase
                hsteps = [0, 3, 9, 13] if fl["drums"] == 1 else list(range(0, 16, 2))
                for s in hsteps:
                    add("drums", hat(vel=1.0 if s % 4 == 0 else 0.6), st(s))
                if b % 4 == 3:
                    for k in range(6):  # 16th-triplet roll into next bar
                        add("drums", hat(vel=0.4 + 0.1 * k), t0 + 14 * STEP + k * STEP * 2 / 3)
                if b % 8 == 7:
                    add("drums", hat(open_=True), st(15))
            if last_bar and fl["drums"]:
                pass
        bar_idx += nbars
    # final ring-out chord
    add("pad", pad(CHORDS[0][:4], BAR * 1.5), bar_idx * BAR)
    return tracks


def reverb(x, secs=2.2, wet=0.25):
    n = int(secs * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 3.2)
    ir = lp(ir, 5000)
    ir /= np.sqrt(np.sum(ir ** 2))
    return x + wet * signal.fftconvolve(x, ir)[: len(x)]


def delay(x, time, fb=0.35, mix=0.3):
    d = int(time * SR)
    y = x.copy()
    for k in range(1, 5):
        y[d * k:] += x[: len(x) - d * k] * (fb ** k) * mix / fb
    return y


def mix(tr):
    keys = reverb(tr["keys"], 1.8, 0.3)
    lead = reverb(delay(tr["lead"], BEAT * 0.75), 2.5, 0.45)
    pad_ = reverb(tr["pad"], 3.0, 0.4)
    # sidechain-ish duck of music under the 808/kick
    duck = 1 - 0.35 * np.clip(lp(np.abs(tr["b808"]), 8), 0, 1)
    music = (keys * 0.9 + pad_ * 1.0 + lead * 0.8) * duck
    drums = reverb(tr["drums"], 0.9, 0.08)
    drums = drums * 1.3
    b808 = tr["b808"] * 0.55
    L = music + drums + b808
    # simple stereo widening: Haas-delay the music on the right channel
    sh = int(0.012 * SR)
    R = drums + b808
    R[sh:] += music[:-sh]
    st = np.stack([L, R], 1)
    st /= np.max(np.abs(st))
    st = np.tanh(st * 1.4) / np.tanh(1.4) * 0.95   # gentle glue, not a brickwall
    return st


if __name__ == "__main__":
    import wave
    out = sys.argv[1] if len(sys.argv) > 1 else "beat.wav"
    audio = mix(build())
    pcm = (audio * 32767).astype("<i2")
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote", out, f"{len(audio) / SR:.1f}s")
