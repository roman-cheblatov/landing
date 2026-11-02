# -*- coding: utf-8 -*-
import json, sys, os, re, shutil
S = sys.argv[1]; OUT = f"{S}/out/site"; os.makedirs(f"{OUT}/memory", exist_ok=True)
SRC = f"{S}/in/exp2/3_Тренажери_v5.0_Netlify/site"
db = json.load(open(f"{S}/work/db_final.json", encoding="utf-8"))
lessons = json.load(open(f"{S}/work/lessons_final.json", encoding="utf-8"))
cards = json.load(open(f"{S}/work/cards_final.json", encoding="utf-8"))
def js(o): return json.dumps(o, ensure_ascii=False, separators=(",",":")).replace("</", "<\\/")
def rep(text, old, new, count=1):
    n = text.count(old)
    assert n == count, (n, old[:80])
    return text.replace(old, new)

# ---- index.html ----
html = open(f"{SRC}/index.html", encoding="utf-8").read()
lines = html.split("\n")
assert lines[99].startswith("const DB=") and lines[99].endswith("];"), lines[99][:30]
assert lines[100].startswith("const LESSONS=") and lines[100].endswith("};"), lines[100][:30]
lines[99] = "const DB=" + js(db) + ";"
lines[100] = "const LESSONS=" + js(lessons) + ";"
html = "\n".join(lines)
html = rep(html, "const KEY_VERSION='fable-review-v5.0-2026-11-02';", "const KEY_VERSION='arbitration-v6.0-2026-11-02';")
html = rep(html, 'const REKEYED_IDS=["01-03","01-22","01-24","03-24","04-06","04-33","07-13","09-07","07-29"];',
                 'const REKEYED_IDS=["01-03","01-22","01-24","03-24","04-06","04-33","07-13","09-07","07-29","03-09","07-06"];')
html = rep(html, 'const REVIEW_V5_CHANGED_IDS=["01-03","07-29"]; // ключі, змінені незалежною експертизою 02.11.2026',
                 'const REVIEW_V5_CHANGED_IDS=["01-03","07-29"]; // ключі, змінені другою незалежною експертизою 02.11.2026 (v5.0)\n'
                 'const ARBITRATION_V6_CHANGED_IDS=["03-09","07-06"]; // ключі, змінені арбітражною експертизою 02.11.2026 (v6.0) відносно v5.0\n'
                 'const AUDIT_V5_KEYS_DIFF=["01-03","07-29"]; // відмінності v6.0 від версії audit-2026-11-02-v5.0 (експертиза 1)')
html = rep(html, """ const changed=(state.keyVersion==='centralization-04-02-v4.0-2026-10-22')?REVIEW_V5_CHANGED_IDS
   :(state.keyVersion==='trauma-07-06-v3.8-2026-10-22')?[...REVIEW_V5_CHANGED_IDS,'04-02']
   :(state.keyVersion==='single-answer-2026-10-22')?[...REVIEW_V5_CHANGED_IDS,'07-06','04-02']
   :[...new Set([...REKEYED_IDS,'07-06','04-02'])];""",
""" const changed=(state.keyVersion==='fable-review-v5.0-2026-11-02')?[...ARBITRATION_V6_CHANGED_IDS]
   :(state.keyVersion==='audit-2026-11-02-v5.0')?[...AUDIT_V5_KEYS_DIFF]
   :(state.keyVersion==='centralization-04-02-v4.0-2026-10-22')?[...REVIEW_V5_CHANGED_IDS,...ARBITRATION_V6_CHANGED_IDS]
   :(state.keyVersion==='trauma-07-06-v3.8-2026-10-22')?[...REVIEW_V5_CHANGED_IDS,...ARBITRATION_V6_CHANGED_IDS,'04-02']
   :(state.keyVersion==='single-answer-2026-10-22')?[...REVIEW_V5_CHANGED_IDS,...ARBITRATION_V6_CHANGED_IDS,'07-06','04-02']
   :[...new Set([...REKEYED_IDS,'07-06','04-02'])];""")
html = rep(html, "const keysafe=q=>q.status==='Один варіант у Word (неофіційний)';", "const keysafe=q=>Boolean(q.arb&&q.arb.pool==='safe');")
html = rep(html, '<option value="safe">Без зафіксованих зауважень (202 запитань)</option><option value="risk">Лише спірні / проблемні (88)</option>',
                 '<option value="safe">Ключ підтверджено арбітражем (263 запитання)</option><option value="risk">Спірні, умовні, виправлені, низька впевненість (27)</option>')
old_callout = re.search(r'<p class="callout warning">⚠ За методичкою СНУ.*?</p>', html).group(0)
new_callout = ('<p class="callout warning">⚠ За методичкою СНУ (розділ 4, с. 8) у кожному завданні лише один правильний варіант. У тренажері одна відповідь на запитання. '
  'Для всіх 290 завдань установлено один навчальний ключ. Ключі пройшли дві незалежні експертизи та арбітражну експертизу 02.11.2026: 263 ключі підтверджено, '
  '27 позначено як спірні, умовні, виправлені або з низькою впевненістю (змінено ключі 1.3, 3.9, 7.6; 7.29 має умовний ключ). Ключі не підтверджені кафедрою — офіційний ключ Moodle невідомий. '
  'На пробному іспиті добираються лише завдання з навчальним ключем.</p>')
html = rep(html, old_callout, new_callout)
old_footer = re.search(r'<div class="footer">Версія 5\.0 \(02\.11\.2026\).*?</div>', html).group(0)
new_footer = ('<div class="footer">Версія 6.0 (02.11.2026) · Ключ № 6.0 після арбітражної експертизи (дві незалежні експертизи + арбітраж: змінено 1.3, 3.9, 7.6; умовний ключ 7.29; нумерація за збірником 2026) · '
  'Спрощений розбір помилок · Мініуроки з поясненнями й асоціаціями · Одна відповідь · перенесення попереднього прогресу та адаптивне повторення · Оригінальні тексти запитань збережено</div>')
html = rep(html, old_footer, new_footer)
open(f"{OUT}/index.html", "w", encoding="utf-8").write(html)

# ---- memory/index.html ----
m = open(f"{SRC}/memory/index.html", encoding="utf-8").read()
ml = m.split("\n")
assert ml[27].startswith("const DATA=") and ml[27].endswith("];"), ml[27][:30]
ml[27] = "const DATA=" + js(cards) + ";"
m = "\n".join(ml)
m = rep(m, "Картки й пояснення пройшли другу незалежну експертизу 02.11.2026 (версія 5.0).", "Картки й пояснення пройшли дві незалежні експертизи та арбітражну експертизу 02.11.2026 (версія 6.0).")
open(f"{OUT}/memory/index.html", "w", encoding="utf-8").write(m)

# ---- sw.js, manifest ----
sw = open(f"{SRC}/sw.js", encoding="utf-8").read()
sw = rep(sw, "const CACHE='snu-2026-trainers-2026-11-02-v2-review';", "const CACHE='snu-2026-trainers-2026-11-02-v3-arbitration';")
open(f"{OUT}/sw.js", "w", encoding="utf-8").write(sw)
shutil.copy(f"{SRC}/manifest.webmanifest", f"{OUT}/manifest.webmanifest")
print("built:", os.listdir(OUT), os.path.getsize(f"{OUT}/index.html"), os.path.getsize(f"{OUT}/memory/index.html"))
