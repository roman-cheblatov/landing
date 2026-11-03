"""Vocal separation with Demucs (MIT). Input: 44.1k stereo wav. Output: vocals / accompaniment wav."""
import sys, time
import numpy as np, soundfile as sf, torch
from demucs.pretrained import get_model
from demucs.apply import apply_model

inp, out_dir = sys.argv[1], sys.argv[2]
torch.set_num_threads(4)
wav, sr = sf.read(inp, dtype='float32', always_2d=True)
assert sr == 44100, sr
x = torch.from_numpy(wav.T.copy())
ref = x.mean(0)
x = (x - ref.mean()) / ref.std()
model = get_model('htdemucs')
model.eval()
t0 = time.time()
with torch.no_grad():
    sources = apply_model(model, x[None], device='cpu', shifts=1, split=True, overlap=0.25, progress=False, num_workers=0)[0]
sources = sources * ref.std() + ref.mean()
names = model.sources
print('sources', names, 'time', time.time() - t0, flush=True)
voc = sources[names.index('vocals')].numpy().T
acc = (sources.sum(0) - sources[names.index('vocals')]).numpy().T
sf.write(f'{out_dir}/vocals.wav', voc, sr, subtype='FLOAT')
sf.write(f'{out_dir}/accompaniment.wav', acc, sr, subtype='FLOAT')
for n, s in zip(names, sources):
    if n != 'vocals':
        sf.write(f'{out_dir}/{n}.wav', s.numpy().T, sr, subtype='FLOAT')
print('done', flush=True)
