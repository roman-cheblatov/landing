import sys, numpy as np, soundfile as sf, librosa
y, sr = sf.read(sys.argv[1], dtype='float32', always_2d=True)
y = y.mean(1)
hop = 480  # 10 ms at 48k
S = np.abs(librosa.stft(y, n_fft=4096, hop_length=hop))
freqs = librosa.fft_frequencies(sr=sr, n_fft=4096)
def band(lo, hi):
    m = (freqs >= lo) & (freqs < hi)
    return 10*np.log10((S[m]**2).sum(0) + 1e-12)
tot = 10*np.log10((S**2).sum(0) + 1e-12)
low, mid, high = band(20, 250), band(250, 2500), band(2500, 10000)
n = S.shape[1]
t = np.arange(n) * hop / sr
print('dur', len(y)/sr)
print(' sec | total  low   mid   high')
for s in range(0, int(len(y)/sr)+1):
    m = (t >= s) & (t < s+1)
    if m.sum() == 0: continue
    print(f'{s:4d} | {tot[m].mean():5.1f} {low[m].mean():5.1f} {mid[m].mean():5.1f} {high[m].mean():5.1f}')
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
print('tempo', tempo)
