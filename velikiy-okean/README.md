# Великий Океан — Тихое возвращение (музыкальный фильм)

Авторский музыкальный фильм на песню Романа Ангелиса «Великий Океан — Тихое возвращение» (5:37.52). Формат 16:9, 1920×1080, 24 к/с, оригинальный звук без изменений.

## Статус

| Этап | Статус | Где |
|---|---|---|
| 1. Проверка окружения и инструментов | готово | `docs/ENVIRONMENT.md` |
| 2. Точный таймлайн по реальному аудио | готово | `docs/TIMELINE.md`, `.json`, `.csv`, `timeline_analysis.png` |
| 2. Режиссёрская раскадровка (44 плана) | готово, на утверждение | `docs/STORYBOARD.md`, `docs/shots.json` |
| 3. Стиль-гайд и референс героя | готово | `docs/STYLE_GUIDE.md`, `docs/CHARACTER_REFERENCE.md`, `refs/` |
| 4. Тестовая сцена 0:00–0:29.13 (планы 01–04) | отрендерена, **ждёт одобрения** | `test/contact_sheet.png`, MP4 — локально в `out/` (не в git) |
| 5. Производство всего фильма | после одобрения теста | — |
| 6. Финальный рендер и проверка | после производства | `out/` |

## Как устроено

- `src/analysis/` — анализ аудио: Demucs (вокал), pYIN (высота тона), Whisper large-v3 (пословные метки), сборка таймлайна.
- `src/storyboard.py` — раскадровка как данные → `docs/STORYBOARD.md` и `docs/shots.json`.
- `src/engine/` — процедурный рендер-движок (GLSL raymarching, офлайн на CPU через Mesa llvmpipe):
  - `shaders/world.frag` — небо, облака, луна и солнце, океан (15 волн с реальной дисперсией, накат, пена), пляж, объёмный туман, герой (SDF);
  - `shaders/dof.frag`, `shaders/final.frag` — физическая ГРИП, ACES, грейдинг, халация, зерно;
  - `hero.py` — скелет, пропорции, планирование шагов, позы;
  - `film.py` — планы фильма как функции времени аудио (камера, свет, действие);
  - `render_range.py` — рендер диапазона кадров в MP4; `assemble.py` — сведение с оригинальным звуком (stream copy) и технические проверки.

## Воспроизведение

```bash
# зависимости: python3.12 venv с numpy, moderngl, pillow (+ torch, demucs, faster-whisper, librosa для анализа)
cp "Великий Океан — Тихое возвращение.mp3" media/source.mp3
python src/engine/noisetex.py work/cache                      # процедурные текстуры шума
xvfb-run -a python src/engine/render_range.py 0 698 work/test/test_video.mp4
python src/engine/assemble.py work/test/test_video.mp4 out/test_0000-0698.mp4 --f0 0 --f1 698 --sheet test/contact_sheet.png
```

## Медиа

Репозиторий публичный, поэтому MP3 и MP4 с песней **не коммитятся** (см. `.gitignore`). Они лежат локально в `media/` и `out/`.
