"""Word-level transcription with faster-whisper (MIT). Unbiased pass: no lyric prompt."""
import sys, json, time
import numpy as np, soundfile as sf
from faster_whisper import WhisperModel
audio, out_json, model_name = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else 'large-v3')
prompt = sys.argv[4] if len(sys.argv) > 4 else None
m = WhisperModel(model_name, device='cpu', compute_type='int8', cpu_threads=4)
t0 = time.time()
wav, sr = sf.read(audio, dtype='float32')
assert sr == 16000 and wav.ndim == 1
segs, info = m.transcribe(wav, language='ru', beam_size=5, word_timestamps=True,
                          vad_filter=False, condition_on_previous_text=False,
                          initial_prompt=prompt, temperature=0.0,
                          no_speech_threshold=0.5, compression_ratio_threshold=2.4)
out = []
for s in segs:
    d = dict(start=s.start, end=s.end, text=s.text, avg_logprob=s.avg_logprob, no_speech_prob=s.no_speech_prob,
             words=[dict(start=w.start, end=w.end, word=w.word, p=w.probability) for w in (s.words or [])])
    out.append(d)
    print(f'[{s.start:7.2f} -> {s.end:7.2f}] ({s.avg_logprob:.2f}) {s.text}', flush=True)
json.dump(dict(model=model_name, prompt=prompt, segments=out, secs=time.time()-t0), open(out_json, 'w'), ensure_ascii=False, indent=1)
print('elapsed', time.time() - t0)
