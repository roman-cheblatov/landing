import json, openpyxl, collections, csv, sys
S = sys.argv[1]
all_ = json.load(open(f"{S}/work/all.json", encoding="utf-8"))
V = {t: {q["id"]: q for q in all_[t]["db"]} for t in all_}
L = {t: all_[t]["lessons"] for t in all_}
C = {t: {c["id"]: c for c in all_[t]["cards"]} for t in all_}
ids = [q["id"] for q in all_["orig"]["db"]]
assert ids == [q["id"] for q in all_["exp1"]["db"]] == [q["id"] for q in all_["exp2"]["db"]], "ID order differs"
cids = [c["id"] for c in all_["orig"]["cards"]]
assert cids == [c["id"] for c in all_["exp1"]["cards"]] == [c["id"] for c in all_["exp2"]["cards"]]

# letter normalisation: trainer uses a/b/v/g ; registries use а/б/в/г or А/Б/В/Г
LAT2CYR = {"a":"А","b":"Б","v":"В","g":"Г","d":"Д","e":"Е"}
def norm(x):
    if x is None: return ""
    s = str(x).strip()
    if s in LAT2CYR: return LAT2CYR[s]
    return s.upper().replace("A","А").replace("B","Б").replace("V","В").replace("G","Г")

# registries
wb1 = openpyxl.load_workbook(f"{S}/in/xlsx/exp.xlsx", data_only=True)
r1 = {}
rows = list(wb1["Реєстр 290"].iter_rows(values_only=True)); h1 = rows[0]
for r in rows[1:]:
    d = dict(zip(h1, r)); r1[d["ID"]] = d
wb2 = openpyxl.load_workbook(f"{S}/in/exp2/2_Реєстри/Реєстр_експертизи_держіспит_СНУ_2026.xlsx", data_only=True)
r2 = {}
rows = list(wb2["Питання (290)"].iter_rows(values_only=True)); h2 = rows[0]
for r in rows[1:]:
    d = dict(zip(h2, r)); r2[d["ID"]] = d
print("registry ids match:", set(r1)==set(ids)==set(r2))

cnt = collections.Counter()
out = []
for i in ids:
    o, a, b = V["orig"][i], V["exp1"][i], V["exp2"][i]
    x1, x2 = r1[i], r2[i]
    row = {
      "id": i, "src_o": o["sourceId"], "src_1": a["sourceId"], "src_2": b["sourceId"],
      "ans_o": norm(o["answer"]), "ans_1": norm(a["answer"]), "ans_2": norm(b["answer"]),
      "grad_o": o["gradeable"], "grad_1": a["gradeable"], "grad_2": b["gradeable"],
      "x1_indep": norm(x1["Незалежна відповідь"]), "x1_also": x1["Також правильні"] or "", "x1_status": x1["Статус"], "x1_level": x1["Рівень підтвердження"],
      "x2_after": norm(x2["Ключ після експертизи"]), "x2_sci": norm(x2["Науково коректна відповідь"]), "x2_auth": norm(x2["Ймовірна авторська відповідь"]),
      "x2_conf": x2["Впевненість"], "x2_cat": x2["Категорія"], "x2_changed": x2["Ключ змінено"],
      "status_o": o["status"], "status_1": a["status"], "status_2": b["status"],
      "q_same": (o["question"]==a["question"]==b["question"]),
      "opts_same_1": [x["label"] for x in o["options"]]==[x["label"] for x in a["options"]],
      "opts_same_2": [x["label"] for x in o["options"]]==[x["label"] for x in b["options"]],
      "warn_1_changed": o["warning"]!=a["warning"], "warn_2_changed": o["warning"]!=b["warning"],
      "expl_1_changed": o["explain"]!=a["explain"], "expl_2_changed": o["explain"]!=b["explain"],
      "lesson_1_changed": L["orig"][i]!=L["exp1"][i], "lesson_2_changed": L["orig"][i]!=L["exp2"][i],
      "x1_defect": x1["Дефект формулювання"] or "",
    }
    out.append(row)
    if row["ans_1"]!=row["ans_2"]: cnt["answer exp1!=exp2"]+=1
    if row["ans_o"]!=row["ans_1"]: cnt["answer orig!=exp1"]+=1
    if row["ans_o"]!=row["ans_2"]: cnt["answer orig!=exp2"]+=1
    if row["grad_1"]!=row["grad_2"]: cnt["gradeable exp1!=exp2"]+=1
    if row["x1_indep"]!=row["x2_sci"]: cnt["x1 indep != x2 sci"]+=1
    if row["x1_indep"]!=row["x2_after"]: cnt["x1 indep != x2 after"]+=1
    if row["x2_sci"]!=row["x2_auth"]: cnt["x2 sci != x2 auth"]+=1
    if row["x2_after"]!=row["ans_2"]: cnt["x2 after != exp2 trainer answer"]+=1
    if row["x1_indep"]!=row["ans_1"]: cnt["x1 indep != exp1 trainer answer"]+=1
    if row["src_o"]!=row["src_2"]: cnt["sourceId changed by exp2"]+=1
    if row["src_o"]!=row["src_1"]: cnt["sourceId changed by exp1"]+=1
    if not row["q_same"]: cnt["question text differs"]+=1
    if not row["opts_same_1"]: cnt["options changed by exp1"]+=1
    if not row["opts_same_2"]: cnt["options changed by exp2"]+=1
    for k in ["warn_1_changed","warn_2_changed","expl_1_changed","expl_2_changed","lesson_1_changed","lesson_2_changed"]:
        if row[k]: cnt[k]+=1
    f1 = row["x1_status"]!="ПІДТВЕРДЖЕНО"; f2 = row["x2_cat"]!="Підтверджено"
    cnt[f"flag exp1={f1} exp2={f2}"]+=1
    if row["status_1"]!=row["status_2"]: cnt["status field exp1!=exp2"]+=1
for k,v in sorted(cnt.items()): print(f"{k}: {v}")
with open(f"{S}/work/cmp_questions.tsv","w",encoding="utf-8",newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()), delimiter="\t"); w.writeheader(); w.writerows(out)
print()
print("=== answer differs between trainers (orig/exp1/exp2) or registries ===")
for r in out:
    if len({r["ans_o"],r["ans_1"],r["ans_2"]})>1 or r["x1_indep"]!=r["x2_sci"] or r["x1_indep"]!=r["x2_after"] or r["grad_1"]!=r["grad_2"]:
        print(f'{r["id"]} src={r["src_o"]} | trainer o/1/2 = {r["ans_o"]}/{r["ans_1"]}/{r["ans_2"]} grad={r["grad_o"]}/{r["grad_1"]}/{r["grad_2"]} | X1 indep={r["x1_indep"]} also={r["x1_also"]} [{r["x1_status"]}] | X2 after={r["x2_after"]} sci={r["x2_sci"]} auth={r["x2_auth"]} conf={r["x2_conf"]} [{r["x2_cat"]}]')
print()
print("=== cards: differences ===")
for i in cids:
    o,a,b = C["orig"][i], C["exp1"][i], C["exp2"][i]
    diffs = [k for k in o if (o[k]!=a[k] or o[k]!=b[k])]
    if diffs:
        print(i, "fields changed:", {k:("1" if o[k]!=a[k] else "")+("2" if o[k]!=b[k] else "") for k in diffs})
    # check card answer vs trainer key (exp1/exp2)
    for t in ["exp1","exp2"]:
        q = V[t][i]; card = C[t][i]
        ans_label = next(x["label"] for x in q["options"] if x["id"]==q["answer"]) if q.get("answer") else None
        if card["options"][card["correctIdx"]] != card["answer"]:
            print("  !! card", i, t, "correctIdx mismatch")
