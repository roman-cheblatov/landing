import sys, json, re, os
def extract_const(html, name):
    m = re.search(r'const %s\s*=\s*' % re.escape(name), html)
    if not m: return None
    dec = json.JSONDecoder()
    obj, end = dec.raw_decode(html, m.end())
    return obj
def main():
    out = {}
    for tag, base in [("orig", sys.argv[1]), ("exp1", sys.argv[2]), ("exp2", sys.argv[3])]:
        html = open(os.path.join(base, "index.html"), encoding="utf-8").read()
        db = extract_const(html, "DB"); lessons = extract_const(html, "LESSONS")
        mem = open(os.path.join(base, "memory", "index.html"), encoding="utf-8").read()
        data = extract_const(mem, "DATA")
        out[tag] = {"db": db, "lessons": lessons, "cards": data}
        keys = set()
        for q in db: keys |= set(q.keys())
        ckeys = set()
        for c in data: ckeys |= set(c.keys())
        print(tag, "questions:", len(db), "lessons:", len(lessons), "cards:", len(data))
        print("   q fields:", sorted(keys)); print("   card fields:", sorted(ckeys))
    json.dump(out, open(sys.argv[4], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
main()
