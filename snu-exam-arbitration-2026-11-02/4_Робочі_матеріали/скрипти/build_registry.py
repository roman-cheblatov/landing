# -*- coding: utf-8 -*-
import json, sys, collections, openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
S = sys.argv[1]; D = f"{S}/out/deliver/2_Реєстри"
final = json.load(open(f"{S}/work/final.json", encoding="utf-8"))
cards = json.load(open(f"{S}/work/cards_final.json", encoding="utf-8"))
all_ = json.load(open(f"{S}/work/all.json", encoding="utf-8"))
C = {t:{c["id"]:c for c in all_[t]["cards"]} for t in all_}
LAT2CYR = {"a":"А","b":"Б","v":"В","g":"Г","d":"Д","e":"Е"}
cyr = lambda x: LAT2CYR.get(x, "—") if x else "—"
fin = {r["id"]: r for r in final}

wb = openpyxl.Workbook()
def sheet(title, header, rows, widths=None):
    ws = wb.create_sheet(title)
    ws.append(header)
    for c in ws[1]: c.font = Font(bold=True); c.fill = PatternFill("solid", fgColor="DDEBF7"); c.alignment = Alignment(wrap_text=True, vertical="top")
    for r in rows: ws.append([("" if v is None else v) for v in r])
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment = Alignment(wrap_text=True, vertical="top")
    if widths:
        for i,w in enumerate(widths, start=1): ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    return ws
wb.remove(wb.active)

# ---- Підсумок
st = collections.Counter(r["status"] for r in final); cf = collections.Counter(r["conf"] for r in final)
flag = collections.Counter(r["flagged_by"] for r in final)
summary = [
 ("Дата арбітражної експертизи", "02.11.2026"),
 ("Виконавець", "Арбітражна експертиза (Claude Fable 5.1) на основі двох незалежних експертиз: експертиза 1 (Excel-реєстр + сайт audit-2026-11-02-v5.0) та експертиза 2 (Claude Fable 5.1, v5.0)"),
 ("Перевірено питань", 290), ("Перевірено карток", 65),
 ("Прямих конфліктів ключів між експертизами", "4 (1.3, 3.9, 7.6, 7.29)"),
 ("Питань, позначених спірними/непідтвердженими хоча б однією експертизою", f"{sum(v for k,v in flag.items() if k)} (лише експертиза 1 — {flag['1']}; лише експертиза 2 — {flag['2']}; обидві — {flag['12']})"),
 ("Питань, у яких обидві експертизи збіглися без зауважень (сліпий перегляд арбітра)", flag[""]),
 ("Остаточний статус: ПІДТВЕРДЖЕНО", st["ПІДТВЕРДЖЕНО"]), ("Остаточний статус: ВИПРАВЛЕНО (ключ змінено)", f'{st["ВИПРАВЛЕНО"]} (1.3 → Б, 3.9 → А, 7.6 → Г)'),
 ("Остаточний статус: СПІРНО", st["СПІРНО"]), ("Остаточний статус: НЕ ПІДТВЕРДЖЕНО", st["НЕ ПІДТВЕРДЖЕНО"]),
 ("Впевненість: висока / середня / низька", f'{cf["висока"]} / {cf["середня"]} / {cf["низька"]}'),
 ("Пул «надійний ключ» / «спірні, умовні, виправлені, низька впевненість» у тренажері", f'{sum(1 for r in final if r["pool"]=="safe")} / {sum(1 for r in final if r["pool"]=="risk")}'),
 ("Ключів змінено відносно оригінального тренажера", "4 (1.3 В→Б; 3.9 Б→А; 7.6 А→Г; 7.29 — умовний А замість «не оцінюється»)"),
 ("Ключів змінено відносно експертизи 1", "2 (1.3 В→Б; 7.29 умовний А)"), ("Ключів змінено відносно експертизи 2", "2 (3.9 Б→А; 7.6 А→Г)"),
 ("Карток зі зміненою відповіддю", 0), ("Карток з оновленими нотатками/зауваженнями", "22 (див. аркуш «Картки (65)»)"),
 ("Обмеження", "Офіційного ключа кафедри (Moodle) немає; PDF-збірник і студентські файли ключів арбітру не надано; мережева політика сесії блокувала прямий доступ до більшості сайтів (vue.gov.ua, osvita.ua, files.znu.edu.ua, psych.vernadskyjournals.in.ua, psyfactor.org, lib.mdpu.org.ua, studfile.net тощо) — перевірка виконана через пошукові фрагменти; усі такі випадки позначено в колонці «Джерела арбітражу»."),
]
sheet("Підсумок", ["Показник", "Значення"], summary, [60, 120])

# ---- Питання (290)
hdr = ["ID","№ у збірнику 2026","№ (стара нумерація тренажера)","Дисципліна","Запитання","Варіанти",
       "Ключ тренажера (до експертиз)","Ключ експертизи 1","Ключ експертизи 2","ОСТАТОЧНИЙ КЛЮЧ","Статус арбітражу","Впевненість","Пул у тренажері",
       "Позначено спірним (1 — експертиза 1, 2 — експертиза 2)","Статус експертизи 1","Рівень підтвердження (експ. 1)","Категорія експертизи 2","Впевненість (експ. 2)",
       "Обґрунтування арбітражу","Джерела арбітражу (перевірено в сесії)","Джерела експертизи 1","Джерело експертизи 2","Дефект формулювання (експ. 1)","Зауваження сліпого проходу (експ. 1)","Зауваження у тренажері (warning)"]
rows = []
for r in final:
    opts = " ".join(f"{LAT2CYR.get(i,i).lower()}) {lab}" for i,lab in r["options"])
    rows.append([r["id"], r["sourceId"], r["sourceId_old"], r["subject"], r["question"], opts,
                 cyr(r["key_orig"]) if r["gradeable_orig"] else "— (не оцінювалось)", cyr(r["key_exp1"]), cyr(r["key_exp2"]), cyr(r["key_final"]), r["status"], r["conf"],
                 "надійний" if r["pool"]=="safe" else "спірні/умовні", r["flagged_by"] or "—", r["exp1_status"], r["exp1_level"], r["exp2_cat"], r["exp2_conf"],
                 r["basis"], r["arb_sources"], r["exp1_sources"], r["exp2_source"], r["exp1_defect"], r["exp1_blind"], r["warning"]])
sheet("Питання (290)", hdr, rows, [8,9,9,22,45,60,10,8,8,10,16,10,12,10,16,14,18,10,60,50,50,30,30,40,50])

# ---- Розбіжності експертиз
hdr2 = ["ID","№","Тип розбіжності","Експертиза 1","Експертиза 2","Рішення арбітражу","Підстава"]
rows2 = []
for r in final:
    types = []
    if r["key_exp1"]!=r["key_exp2"]: types.append("прямий конфлікт ключів")
    if r["flagged_by"]=="1": types.append("позначено спірним лише експертизою 1")
    if r["flagged_by"]=="2": types.append("позначено спірним лише експертизою 2")
    if r["flagged_by"]=="12" and r["key_exp1"]==r["key_exp2"]: types.append("обидві позначили спірним (різні формулювання)")
    if not types: continue
    rows2.append([r["id"], r["sourceId"], "; ".join(types),
                  f'{cyr(r["key_exp1"])} — {r["exp1_status"]} ({r["exp1_level"]})', f'{cyr(r["key_exp2"])} — {r["exp2_cat"]} (впевненість: {r["exp2_conf"]})',
                  f'{cyr(r["key_final"])} — {r["status"]} ({r["conf"]})', r["basis"]])
sheet("Розбіжності експертиз", hdr2, rows2, [8,8,30,40,40,30,80])

# ---- Картки (65)
hdr3 = ["ID","Категорія","Запитання","Сигнал (cue)","Відповідь картки","Ключ тесту (остаточний)","Збіг з ключем","Статус арбітражу","Нотатка (остаточна)","Асоціація (остаточна)","Зауваження (warning)","Що змінено відносно оригіналу"]
rows3 = []
for c in cards:
    i = c["id"]; r = fin[i]; o = C["orig"][i]
    right = next(lab for k,lab in r["options"] if k==r["key_final"])
    changed = [k for k in ("note","association","warning","status","options") if o[k]!=c[k]]
    rows3.append([i, {"authors":"Автори й теорії","dates":"Дати","terms":"Поняття"}.get(c["cat"], c["cat"]), c["question"], c["cue"], c["answer"], right, "так", r["status"], c["note"], c["association"], c["warning"], ", ".join(changed) or "—"])
sheet("Картки (65)", hdr3, rows3, [8,14,45,30,25,25,8,16,50,40,50,20])

# ---- Журнал змін тренажера
hdr4 = ["Файл","ID / місце","Поле","Зміна"]
rows4 = []
for r in final:
    if r["key_final"]!=r["key_exp2"]: rows4.append(["index.html", r["id"], "answer/keys", f'{cyr(r["key_exp2"])} → {cyr(r["key_final"])} ({r["status"]})'])
for r in final:
    rows4.append(["index.html", r["id"], "status / arb / explain", f'Статус «{r["status"]}» ({r["conf"]}); пул «{"надійний" if r["pool"]=="safe" else "спірні/умовні"}»; до explain додано обґрунтування арбітражу'])
    if r["warning"]: rows4.append(["index.html", r["id"], "warning", r["warning"]])
lessons_final = json.load(open(f"{S}/work/lessons_final.json", encoding="utf-8"))
for i in lessons_final:
    if lessons_final[i] != all_["exp2"]["lessons"][i]: rows4.append(["index.html", i, "LESSONS", f'note: {lessons_final[i]["note"]} | association: {lessons_final[i]["association"]}'])
rows4 += [["index.html","константи","KEY_VERSION","'fable-review-v5.0-2026-11-02' → 'arbitration-v6.0-2026-11-02'; додано ARBITRATION_V6_CHANGED_IDS=[03-09,07-06], AUDIT_V5_KEYS_DIFF=[01-03,07-29]; REKEYED_IDS доповнено 03-09, 07-06"],
          ["index.html","migrateSingleKey","логіка міграції","Скидання прогресу лише для змінених ключів залежно від попередньої версії (v5.0 Fable: 3.9, 7.6; аудит експертизи 1: 1.3, 7.29; v4.0: 1.3, 3.9, 7.6, 7.29; старіші — як раніше)"],
          ["index.html","keysafe","фільтр надійності","Пул визначається полем arb.pool (263 надійних / 27 спірних) замість рядка status"],
          ["index.html","UI","тексти","Підписи фільтра, попередження, підпис версії 6.0"],
          ["memory/index.html","DATA","status/warning/note/association","Статуси й зауваження узгоджено з арбітражем; нотатки 22 карток уточнено; відповіді не змінювались"],
          ["memory/index.html","footer","текст","Версія 6.0"], ["sw.js","CACHE","назва кешу","'…-v2-review' → '…-v3-arbitration' (клієнти отримають оновлення)"]]
sheet("Журнал змін тренажера", hdr4, rows4, [16,12,20,120])
wb.save(f"{D}/Реєстр_арбітражної_експертизи_держіспит_СНУ_2026.xlsx")

# ---- Markdown registry (compact)
md = ["# Остаточний реєстр 290 питань (арбітражна експертиза 02.11.2026)", "",
      "Умовні позначення: ключ до експертиз / експертиза 1 / експертиза 2 / **остаточний**; статуси: ПІДТВЕРДЖЕНО, ВИПРАВЛЕНО, СПІРНО, НЕ ПІДТВЕРДЖЕНО.", "",
      "| ID | № 2026 | Ключ: до / Е1 / Е2 / **остаточний** | Статус | Впевненість | Позначали | Обґрунтування арбітражу |", "|---|---|---|---|---|---|---|"]
for r in final:
    k0 = cyr(r["key_orig"]) if r["gradeable_orig"] else "—"
    md.append(f'| {r["id"]} | {r["sourceId"]} | {k0} / {cyr(r["key_exp1"])} / {cyr(r["key_exp2"])} / **{cyr(r["key_final"])}** | {r["status"]} | {r["conf"]} | {("Е"+", Е".join(r["flagged_by"])) if r["flagged_by"] else "—"} | {r["basis"].replace("|","/")} |')
open(f"{D}/Реєстр_290_питань_арбітраж.md","w",encoding="utf-8").write("\n".join(md))
md2 = ["# Остаточний реєстр 65 карток пам’яті (арбітражна експертиза 02.11.2026)", "", "| ID | Запитання | Відповідь | Статус | Зауваження | Змінено |", "|---|---|---|---|---|---|"]
for row in rows3: md2.append(f'| {row[0]} | {row[2].replace("|","/")} | {row[4]} | {row[7]} | {row[10].replace("|","/")} | {row[11]} |')
open(f"{D}/Реєстр_65_карток_арбітраж.md","w",encoding="utf-8").write("\n".join(md2))
md3 = ["# Таблиця розбіжностей між експертизами та рішення арбітражу", "", "| ID | № | Тип | Експертиза 1 | Експертиза 2 | Арбітраж | Підстава |", "|---|---|---|---|---|---|---|"]
for row in rows2: md3.append("| " + " | ".join(str(x).replace("|","/") for x in row) + " |")
open(f"{S}/out/deliver/1_Звіт/Таблиця_розбіжностей_експертиз.md","w",encoding="utf-8").write("\n".join(md3))
print("rows:", len(rows), "discrepancies:", len(rows2), "cards:", len(rows3), "changelog:", len(rows4))
print("status:", dict(st), "conf:", dict(cf), "flag:", dict(flag))
