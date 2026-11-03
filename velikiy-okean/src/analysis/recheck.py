"""Re-check ambiguous windows with Whisper: unbiased vs lyric-prompted, on vocal stem clips."""
import sys, numpy as np, soundfile as sf
from faster_whisper import WhisperModel
wav, sr = sf.read('work/vocals_16k.wav', dtype='float32')
m = WhisperModel('large-v3', device='cpu', compute_type='int8', cpu_threads=4)
checks = [
  (118.5, 137.0, 'Прими меня, Великий Океан... Веди меня, Великий Океан...'),
  (63.3, 69.9, None),
  (28.5, 42.6, None),
  (188.5, 218.5, None),
  (315.9, 337.5, None),
  (296.0, 317.5, 'Великий Океан — единое Сознание, Душа, из которой вышли все живые существа для того, чтобы осознать свою природу и вновь воссоединиться с Океаном.'),
  (227.0, 243.0, 'то было пусто, но нет во мне ни боли… страха… грусти – я знаю, выбор нам судьбою дан!'),
  (43.0, 47.5, 'Твои капли - сонмы живых существ.'),
]
for a, b, prompt in checks:
    clip = wav[int(a*sr):int(b*sr)]
    for pr in ([None, prompt] if prompt else [None]):
        segs, _ = m.transcribe(clip, language='ru', beam_size=5, word_timestamps=True, vad_filter=False,
                               condition_on_previous_text=False, initial_prompt=pr, temperature=0.0)
        segs = list(segs)
        txt = ' | '.join(f"[{a+s.start:.2f}-{a+s.end:.2f} lp={s.avg_logprob:.2f} nsp={s.no_speech_prob:.2f}] " +
                         ' '.join(f"{w.word.strip()}({a+w.start:.2f},{w.probability:.2f})" for w in s.words) for s in segs)
        print(f"WINDOW {a}-{b} prompt={'yes' if pr else 'no'}: {txt or '(nothing)'}\n", flush=True)
