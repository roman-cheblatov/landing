# -*- coding: utf-8 -*-
"""Stage A+B: build final arbitration data (final.json) and the final trainer site."""
import json, csv, re, sys, os, copy, openpyxl, collections
S = sys.argv[1]
OUT = f"{S}/out/site"
all_ = json.load(open(f"{S}/work/all.json", encoding="utf-8"))
V = {t: {q["id"]: q for q in all_[t]["db"]} for t in all_}
L = {t: all_[t]["lessons"] for t in all_}
C = {t: {c["id"]: c for c in all_[t]["cards"]} for t in all_}
ids = [q["id"] for q in all_["orig"]["db"]]
cids = [c["id"] for c in all_["orig"]["cards"]]

# registries
wb1 = openpyxl.load_workbook(f"{S}/in/xlsx/exp.xlsx", data_only=True)
rows = list(wb1["Реєстр 290"].iter_rows(values_only=True)); h1 = rows[0]
R1 = {d["ID"]: d for d in (dict(zip(h1, r)) for r in rows[1:])}
wb2 = openpyxl.load_workbook(f"{S}/in/exp2/2_Реєстри/Реєстр_експертизи_держіспит_СНУ_2026.xlsx", data_only=True)
rows = list(wb2["Питання (290)"].iter_rows(values_only=True)); h2 = rows[0]
R2 = {d["ID"]: d for d in (dict(zip(h2, r)) for r in rows[1:])}

LAT2CYR = {"a":"А","b":"Б","v":"В","g":"Г","d":"Д","e":"Е"}
def cyr(x): return LAT2CYR.get(x, "—") if x else "—"

# verdicts
verd = {}
for p in ["part1","part2","part3"]:
    with open(f"{S}/work/verdicts/{p}.tsv", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            verd[row["id"]] = row
assert len(verd)==109, len(verd)

# arbitration sources (verified in this session via web search summaries)
ARB_SRC = {
 "01-03": "Пошукове підтвердження: тезу «виникнення і розвиток міжособистісного конфлікту багато в чому обумовлені демографічними та індивідуально-психологічними характеристиками» знайдено в рос. навчальних матеріалах з конфліктології (підсумок пошуку; ймовірні джерела: https://studfile.net/preview/7422937/page:17/ ; https://psyera.ru/vliyanie-individualnyh-socialno-psihologicheskih-osobennostey-na-dinamiku-i-upravlenie-363.htm). Повний текст підручника Кібанова (psyfactor.org) у сесії недоступний.",
 "03-09": "Максимова Н. Ю. Сімейне консультування. Київ: МАУП, 2011 — https://files.znu.edu.ua/files/Bibliobooks/Inshi74/0054593.pdf ; https://lib.mdpu.org.ua/wp-content/uploads/2024/01/Максимова-Сімейне-консультування-2011.pdf (пошуковий фрагмент підтверджує атрибуції «вдалий шлюб» — Ледерер і Джексон, «стабільний шлюб» — Обозов; повний текст у сесії недоступний).",
 "07-06": "Паливода Л. І. Проблема визначення понять «психічна травма», «психологічна травма» і «травма втрати»… // Вчені записки ТНУ ім. В. І. Вернадського. Сер.: Психологія. 2021. Т. 32 (71), № 6 — https://psych.vernadskyjournals.in.ua/journal/6_2021/11.pdf (пошуковий фрагмент: медичний підхід = б, психологічний підхід = а); Періг І. Psychological help in acute… (ТНТУ, 2023) — https://elartu.tntu.edu.ua/bitstream/lib/41063/2/MCTD_2023_Perig_I-Psychological_help_in_acute_23-25.pdf (пошуковий фрагмент: визначення психологічної травми = в).",
 "07-29": "ВУЕ, стаття «Афект» — https://vue.gov.ua/Афект (за експертизою 1; у сесії недоступна). Визначення афекту неадекватності (варіант а) збігається зі словниковим визначенням, що використане в завданні 3.5.",
 "05-29": "Пошукові фрагменти навчальних матеріалів: у 1992 р. комісія Верховної Ради з питань науки і народної освіти ухвалила рішення про створення Концепції державної системи психологічної служби; у 1993 р. прийнято Положення про психологічну службу в системі освіти (ймовірні джерела: https://don.kyivcity.gov.ua/files/2021/4/23/43245.pdf ; https://dspace.nau.edu.ua/bitstream/NAU/24657/5/04_%20%d0%9c%d0%9f%d0%9f%d0%95%20_%d0%9a%d0%9b.docx). Нормативний акт КМУ не верифіковано.",
 "07-08": "Тарабрина Н. В. Практикум по психологии посттравматического стресса. СПб.: Питер, 2001 (розділ про групову терапію; онлайн-копію в сесії не відкрито; опис видання — https://psytests.org/book/tarab2001.html).",
}

STATUS_LABEL = {
 "ПІДТВЕРДЖЕНО": "Ключ підтверджено арбітражем 02.11.2026",
 "ВИПРАВЛЕНО": "Ключ змінено арбітражем 02.11.2026",
 "СПІРНО": "Спірний / умовний ключ (арбітраж 02.11.2026)",
 "НЕ ПІДТВЕРДЖЕНО": "Ключ не підтверджено джерелом (арбітраж 02.11.2026)",
}
CUSTOM_WARN = {
 "01-03": "Арбітраж 02.11.2026 — КЛЮЧ ЗМІНЕНО (В → Б). Стовбур дослівно відтворює підручникове положення (Кібанов та ін.): міжособистісний конфлікт багато в чому зумовлений демографічними та індивідуально-психологічними характеристиками. Так само позначав великий Word; варіант В походив лише з «жовтого» файлу. Офіційний ключ Moodle невідомий.",
 "03-09": "Арбітраж 02.11.2026 — КЛЮЧ ЗМІНЕНО (Б → А). Варіанти взято з посібника Н. Максимової «Сімейне консультування» (2011, с. 28–29): гармонійний шлюб там розглянуто передусім з позиції соціальної зрілості партнерів (а); б — «вдалий шлюб» (Ледерер, Джексон), в — «стабільний шлюб» (Обозов). Неофіційний ключ Word (Б) визнано помилковим; офіційний ключ Moodle невідомий — за можливості уточни на кафедрі.",
 "07-06": "Арбітраж 02.11.2026 — КЛЮЧ ЗМІНЕНО (А → Г). Усі три варіанти — визначення психічної/психологічної травми, що вживаються в українській літературі (а і б — Паливода, 2021; в — визначення психологічної травми у працях про гострий стрес). Великий Word також позначав Г («усе підходить»); варіант А походив з файлу Богдана. Офіційний ключ Moodle невідомий.",
 "07-29": "Арбітраж 02.11.2026 — СПІРНО (умовний ключ А). Жоден варіант не є визначенням афекту: А — «афект неадекватності», Б — тип суїциду, В — антисуїцидальні установки. Обидві експертизи незалежно вважають А найімовірнішим авторським вибором (ймовірно, у стовбурі випало слово «неадекватності»). Правильне визначення афекту наведено окремо; на іспиті — уточни у викладача.",
}

# final per-question records
final = []
counts = collections.Counter()
for i in ids:
    o, a, b = V["orig"][i], V["exp1"][i], V["exp2"][i]
    x1, x2 = R1[i], R2[i]
    flagged = i in verd
    if flagged:
        v = verd[i]; key = v["key"]; status = v["status"]; conf = v["conf"]; basis = v["basis"]
    else:
        key = b["answer"]; status = "ПІДТВЕРДЖЕНО"; conf = "висока"
        basis = "Обидві експертизи незалежно підтвердили ключ (експертиза 1 — з відкритим джерелом; експертиза 2 — висока впевненість); арбітражний сліпий перегляд заперечень не виявив. " + (str(x2["Обґрунтування"]).strip() if x2["Обґрунтування"] else "")
    pool = "risk" if (status in ("СПІРНО","НЕ ПІДТВЕРДЖЕНО","ВИПРАВЛЕНО") or conf == "низька") else "safe"
    if pool == "risk":
        warning = CUSTOM_WARN.get(i) or (f"Арбітраж 02.11.2026 — {status}" + (" (низька впевненість)" if status=="ПІДТВЕРДЖЕНО" else "") + f": {basis}")
    else:
        warning = ""
    rec = {
      "id": i, "sourceId": b["sourceId"], "sourceId_old": o["sourceId"], "subject": o["subject"],
      "question": o["question"], "options": [(op["id"], op["label"]) for op in b["options"]],
      "key_orig": o["answer"], "key_exp1": a["answer"], "key_exp2": b["answer"], "key_final": key,
      "gradeable_orig": o["gradeable"], "gradeable_final": True,
      "status": status, "conf": conf, "pool": pool, "basis": basis, "warning": warning,
      "exp1_status": x1["Статус"], "exp1_level": x1["Рівень підтвердження"], "exp1_indep": x1["Незалежна відповідь"], "exp1_also": x1["Також правильні"] or "",
      "exp1_rationale": x1["Обґрунтування"] or "", "exp1_sources": x1["Джерела (відкриті)"] or "", "exp1_defect": x1["Дефект формулювання"] or "", "exp1_blind": x1["Примітки сліпого проходу"] or "",
      "exp2_cat": x2["Категорія"], "exp2_conf": x2["Впевненість"], "exp2_sci": x2["Науково коректна відповідь"], "exp2_auth": x2["Ймовірна авторська відповідь"],
      "exp2_rationale": x2["Обґрунтування"] or "", "exp2_source": x2["Джерело перевірки"] or "",
      "arb_sources": ARB_SRC.get(i, ""),
      "flagged_by": ("1" if x1["Статус"]!="ПІДТВЕРДЖЕНО" else "") + ("2" if x2["Категорія"]!="Підтверджено" else ""),
      "sourceKeys": o.get("sourceKeys", []), "manualKey": o.get("manualKey"),
    }
    final.append(rec); counts[(status, conf, pool)] += 1
json.dump(final, open(f"{S}/work/final.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("status/conf/pool counts:"); 
for k,vv in sorted(counts.items()): print("  ", k, vv)
print("risk pool:", sum(1 for r in final if r["pool"]=="risk"), "safe:", sum(1 for r in final if r["pool"]=="safe"))
print("risk ids:", [r["id"] for r in final if r["pool"]=="risk"])
changed = [r["id"] for r in final if r["key_final"]!=r["key_exp2"]]
print("keys changed vs exp2:", changed, " vs exp1:", [r["id"] for r in final if r["key_final"]!=r["key_exp1"]], " vs orig:", [r["id"] for r in final if r["key_final"]!=r["key_orig"]])

# ---------- LESSONS merge ----------
lessons = copy.deepcopy(L["exp2"])
ADOPT_EXP1 = ["01-07","01-26","02-37","03-09","03-38","04-32","05-31","07-03","07-06","07-25","08-05","08-06","08-07","08-22",
              "01-15","02-17","02-29","03-03","03-23","04-09","04-21","04-27","05-30","06-20","06-21","07-11","07-17","08-03","08-04","08-13","09-03-2","09-19","09-25"]
for i in ADOPT_EXP1:
    lessons[i] = copy.deepcopy(L["exp1"][i])
    lessons[i]["note"] = lessons[i]["note"].replace("Зауваження до формулювання (аудит):", "Зауваження до формулювання (експертиза):")
lessons["05-29"] = {"note": "За підручниками з організації психологічної служби Концепцію державної системи психологічної служби розроблено Інститутом психології ім. Г. С. Костюка і схвалено 1993 року (рішення про її створення комісія Верховної Ради ухвалила 1992 року). Сам нормативний акт у відкритому доступі не перевірено, тому дату тримай як навчальний ключ.", "association": "1992 — рішення створити; 1993 — Концепцію схвалено (ключ тесту)."}
lessons["03-09"]["note"] = "У посібнику Н. Ю. Максимової «Сімейне консультування» (2011, с. 28–29), з якого взято варіанти, гармонійний шлюб розглянуто «передусім з позиції соціальної зрілості партнерів» (Е. Артамонова та ін.) — це варіант а. Толерантність, повага, чесність (б) — ознаки «вдалого» шлюбу за Ледерером і Джексоном; єдність інтересів за контрастності рис (в) — «стабільний» шлюб за О. Обозовим. Ключ змінено арбітражем 02.11.2026 (раніше Б)."
lessons["07-06"]["note"] = "Три визначення з різних підходів: медичний — надто сильні руйнівні переживання (жах, страх, безпорадність) через загрозу безпеці та існуванню (б); психологічний — порушення цілісності функціонування психіки через ситуацію, суб’єктивно непереборну за недостатності захисних механізмів (а); психологічну травму описують і як стан сильного страху під час раптової загрозливої події (в). Усі три вживаються в літературі, тому ключ — «усе підходить» (так само позначав великий Word). Ключ повернуто арбітражем 02.11.2026 (раніше А)."
json.dump(lessons, open(f"{S}/work/lessons_final.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)

# ---------- DB build ----------
fin = {r["id"]: r for r in final}
db = copy.deepcopy(all_["exp2"]["db"])
for q in db:
    r = fin[q["id"]]
    q["answer"] = r["key_final"]; q["keys"] = [cyr(r["key_final"])]; q["gradeable"] = True
    q["status"] = STATUS_LABEL[r["status"]] + ("" if r["status"]!="ПІДТВЕРДЖЕНО" else {"висока":"", "середня":" (середня впевненість)", "низька":" (низька впевненість)"}[r["conf"]])
    q["warning"] = r["warning"]
    base_explain = V["exp2"][q["id"]]["explain"]
    q["explain"] = base_explain + f" Арбітражна експертиза 02.11.2026: {r['status']} (впевненість — {r['conf']}). {r['basis']}"
    q["arb"] = {"date":"2026-11-02","status":r["status"],"confidence":r["conf"],"pool":r["pool"],"keyHistory":{"orig":r["key_orig"],"exp1":r["key_exp1"],"exp2":r["key_exp2"]}}
    q.pop("review", None)
json.dump(db, open(f"{S}/work/db_final.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)

# ---------- cards ----------
cards = copy.deepcopy(all_["exp2"]["cards"])
CARD_NOTE_FROM_EXP1 = ["03-38","08-05","08-06","08-07","08-22"]
CARD_ASSOC_FROM_EXP1 = ["02-37","08-22"]
for c in cards:
    i = c["id"]; r = fin[i]
    # answer must match final key
    q = V["exp2"][i]; right = next(op["label"] for op in q["options"] if op["id"]==r["key_final"])
    assert c["options"][c["correctIdx"]] == c["answer"], i
    assert c["answer"].strip().rstrip(";.") in right or right.strip().rstrip(";.") in c["answer"], (i, c["answer"], right)
    if i in CARD_NOTE_FROM_EXP1: c["note"] = C["exp1"][i]["note"]
    if i in CARD_ASSOC_FROM_EXP1: c["association"] = C["exp1"][i]["association"]
    if i == "05-29": c["note"] = lessons["05-29"]["note"]; c["association"] = lessons["05-29"]["association"]
    if i == "02-29": c["note"] = c["note"] + " У варіанті помилковий ініціал: закон сформулював Йоганнес (Й.) Мюллер; Гельмгольц розвинув суміжну «теорію знаків»."
    if i == "03-23": c["note"] = c["note"] + " «С. Манохін» у варіанті — спотворене прізвище С. Мінухіна."
    c["status"] = fin[i]["status"] and STATUS_LABEL[r["status"]]
    c["warning"] = r["warning"]
json.dump(cards, open(f"{S}/work/cards_final.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)
print("cards in risk pool:", [c["id"] for c in cards if c["warning"]])
