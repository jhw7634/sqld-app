# 문제은행 검사: python3 check.py
# 1) 형식 검사 (보기 4개, 정답 번호, 대제목, 문항 수, 보기별 풀이 why: 정답 칸만 비우고 보기 번호 대신 내용으로)
# 2) check가 달린 SQL 문제는 DuckDB로 실제 실행해서 정답 보기와 결과가 같은지 확인
#    - sql:  결과가 정답 보기와 같고, 나머지 보기와는 달라야 함
#    - sqls: 보기 4개의 SQL 중 정답 번호의 결과만 나머지 셋과 달라야 함
#    - db: "sqlite"면 SQLite로 실행 (SAVEPOINT, 외래키 CASCADE처럼 DuckDB에 없는 기능)
# Oracle 문법(NVL, DECODE 등)은 아래 매크로로 흉내 내고, NULL 정렬도 Oracle처럼 맞춤
import collections, decimal, json, re, subprocess, sys
import sqlite3
import duckdb

src = subprocess.run(["node", "-e", "global.window={};require('./questions.js');"
                      "console.log(JSON.stringify({u:window.SQLD_UNITS,q:window.SQLD_QUESTIONS,t:window.SQLD_TRAPS||[],s:window.SQLD_STUDY||[]}))"],
                     capture_output=True, text=True, check=True, cwd=sys.path[0]).stdout
data = json.loads(src)
units = {u["id"]: u for u in data["u"]}
qs = data["q"]
traps = {t["id"] for t in data["t"]}
errors = []

ORACLE = """
SET default_null_order='nulls_last_on_asc_first_on_desc';
CREATE MACRO nvl(a, b) AS coalesce(a, b);
CREATE MACRO nvl2(a, b, c) AS CASE WHEN a IS NOT NULL THEN b ELSE c END;
CREATE MACRO decode(e, s1, r1) AS CASE WHEN e IS NOT DISTINCT FROM s1 THEN r1 END,
  (e, s1, r1, d) AS CASE WHEN e IS NOT DISTINCT FROM s1 THEN r1 ELSE d END,
  (e, s1, r1, s2, r2) AS CASE WHEN e IS NOT DISTINCT FROM s1 THEN r1 WHEN e IS NOT DISTINCT FROM s2 THEN r2 END,
  (e, s1, r1, s2, r2, d) AS CASE WHEN e IS NOT DISTINCT FROM s1 THEN r1 WHEN e IS NOT DISTINCT FROM s2 THEN r2 ELSE d END,
  (e, s1, r1, s2, r2, s3, r3, d) AS CASE WHEN e IS NOT DISTINCT FROM s1 THEN r1 WHEN e IS NOT DISTINCT FROM s2 THEN r2 WHEN e IS NOT DISTINCT FROM s3 THEN r3 ELSE d END;
"""

def cell(v):
    if v is None: return "NULL"
    if isinstance(v, float): v = decimal.Decimal(repr(v))
    if isinstance(v, decimal.Decimal):
        v = v.normalize()
        return format(v, "f") if v != v.to_integral() else str(int(v))
    return str(v)

def fmt(rows):
    if not rows: return "결과 없음"
    if len(rows[0]) == 1: return ", ".join(cell(r[0]) for r in rows)
    if len(rows) == 1: return ", ".join(map(cell, rows[0]))
    return ", ".join("(" + ", ".join(map(cell, r)) + ")" for r in rows)

def run(setup, sql, db=None):
    if db == "sqlite":
        c = sqlite3.connect(":memory:", isolation_level=None)
        c.execute("PRAGMA foreign_keys = ON")
        if setup: c.executescript(setup)
        return fmt(c.execute(sql).fetchall())
    c = duckdb.connect()
    c.execute(ORACLE)
    if setup: c.execute(setup)
    return fmt(c.execute(sql).fetchall())

norm = lambda t: re.sub(r"\s+", " ", str(t)).strip()
ids = collections.Counter(q["id"] for q in qs)
checked = 0
for q in qs:
    where = q.get("id", "?")
    need = ["id", "unit", "freq", "subject", "topic", "q", "options", "answer", "exp"]
    miss = [k for k in need if not q.get(k)]
    if miss: errors.append(f"{where}: 빠진 항목 {miss}"); continue
    if ids[q["id"]] > 1: errors.append(f"{where}: id 중복")
    if q["unit"] not in units: errors.append(f"{where}: 없는 대제목 {q['unit']}")
    elif units[q["unit"]]["subject"] != q["subject"]: errors.append(f"{where}: 과목과 대제목이 안 맞음")
    if q.get("trap") and q["trap"] not in traps: errors.append(f"{where}: 없는 함정 {q['trap']}")
    if q["freq"] not in ("high", "mid", "low"): errors.append(f"{where}: freq 값 오류")
    o = q["options"]
    if len(o) != 4 or len({norm(x) for x in o}) != 4: errors.append(f"{where}: 보기는 서로 다른 4개여야 함")
    if q["answer"] not in (1, 2, 3, 4): errors.append(f"{where}: 정답 번호 오류")
    w = q.get("why")
    if not (isinstance(w, list) and len(w) == 4 and all(isinstance(x, str) for x in w)):
        errors.append(f"{where}: why는 보기 4개에 맞춘 풀이 4칸이어야 함")
    elif [bool(x.strip()) for x in w] != [i + 1 != q["answer"] for i in range(4)]:
        errors.append(f"{where}: why는 정답 칸만 비우고 나머지 보기 풀이를 채워야 함")
    elif any(re.search(r"[①②③④]|[1-4]번 보기", x) for x in w):
        errors.append(f"{where}: why에는 보기 번호 대신 내용으로 적기")
    ck = q.get("check")
    if not ck: continue
    try:
        if "sql" in ck:
            got = norm(run(ck.get("setup"), ck["sql"], ck.get("db")))
            if got != norm(o[q["answer"] - 1]):
                errors.append(f"{where}: 실행 결과 [{got}] ≠ 정답 보기 [{o[q['answer'] - 1]}]")
            others = [i + 1 for i, x in enumerate(o) if i + 1 != q["answer"] and norm(x) == got]
            if others: errors.append(f"{where}: 다른 보기 {others}도 실행 결과와 같음")
        else:
            res = [norm(run(ck.get("setup"), s, ck.get("db"))) for s in ck["sqls"]]
            odd = [i + 1 for i, r in enumerate(res) if res.count(r) == 1]
            if odd != [q["answer"]] or len(set(res)) != 2:
                errors.append(f"{where}: 보기별 결과 {res} → 다른 하나가 정답 {q['answer']}번이 아님")
        checked += 1
    except Exception as e:
        errors.append(f"{where}: 실행 오류 {str(e).splitlines()[0]}")

# 공부 탭 예시: 화면에 보여 주는 표(data)로 DB를 만들고 SQL을 실행해서 결과 표(out)와 칸 이름·값이 같은지 확인
# (Oracle의 MINUS는 DuckDB 문법인 EXCEPT로 바꿔 실행, DUAL은 한 줄짜리 표로 만들어 둠)
def study(ex):
    sqlite = ex.get("db") == "sqlite"
    c = sqlite3.connect(":memory:") if sqlite else duckdb.connect()
    if not sqlite: c.execute(ORACLE)
    tables = {"DUAL": {"cols": ["DUMMY"], "rows": [["X"]]}, **ex["data"]}
    for name, t in tables.items():
        types = ["INTEGER" if any(isinstance(r[i], int) for r in t["rows"]) else "VARCHAR" for i in range(len(t["cols"]))]
        c.execute(f"CREATE TABLE {name} ({', '.join(f'{k} {v}' for k, v in zip(t['cols'], types))})")
        if t["rows"]: c.executemany(f"INSERT INTO {name} VALUES ({', '.join('?' * len(t['cols']))})", t["rows"])
    if sqlite: c.commit()
    sql = re.sub(r"\bMINUS\b", "EXCEPT", ex["sql"])
    parts = [x for x in sql.split(";") if x.strip()] + ([ex["after"]] if ex.get("after") else [])
    for x in parts[:-1]: c.execute(x)
    cur = c.execute(parts[-1])
    rows, cols = [list(map(cell, r)) for r in cur.fetchall()], [d[0] for d in cur.description]
    want = [list(map(cell, r)) for r in ex["out"]["rows"]]
    flat = parts[-1]
    while re.search(r"\([^()]*\)", flat): flat = re.sub(r"\([^()]*\)", "", flat)
    if "ORDER BY" not in flat.upper(): rows, want = sorted(rows), sorted(want) # 정렬하지 않은 결과는 순서 상관없이 비교
    return cols == ex["out"]["cols"] and rows == want, f"{cols} {rows}"

ran = 0
for l in data["s"]:
    if l.get("unit") not in units: errors.append(f"공부 {l['id']}: 없는 대제목 {l.get('unit')}")
    for k, ex in enumerate(l["ex"]):
        for name, t in {**ex["data"], **({"out": ex["out"]} if "out" in ex else {})}.items():
            if any(len(r) != len(t["cols"]) for r in t["rows"]): errors.append(f"공부 {l['id']} 예시 {k + 1}: {name} 칸 수가 안 맞음")
        if "out" not in ex:
            if ex.get("after"): errors.append(f"공부 {l['id']} 예시 {k + 1}: after에는 out이 필요함")
            continue
        try:
            ok, got = study(ex)
            if not ok: errors.append(f"공부 {l['id']} 예시 {k + 1}: 실행 결과 {got} ≠ out")
            ran += 1
        except Exception as e:
            errors.append(f"공부 {l['id']} 예시 {k + 1}: 실행 오류 {str(e).splitlines()[0]}")
print(f"공부 탭: {len(data['s'])}개 설명, 예시 {ran}개 실행 확인")

# 문항 수와 정답 번호 분포
sets = collections.defaultdict(list)
for q in qs: sets[f"실전 {q['exam']}" if q.get("exam") else "함정" if q.get("trap") else "연습"].append(q)
for name, lst in sorted(sets.items()):
    by_subj = collections.Counter(q["subject"] for q in lst)
    ans = collections.Counter(q["answer"] for q in lst)
    print(f"{name}: {len(lst)}문항 (1과목 {by_subj[1]}, 2과목 {by_subj[2]}) · 정답 분포 {dict(sorted(ans.items()))}")
    if name.startswith("실전") and (by_subj[1], by_subj[2]) != (10, 40):
        errors.append(f"{name}: 1과목 10, 2과목 40문항이어야 함")
print(f"SQL 실행 검증 {checked}문항")
print("\n".join(errors) if errors else "문제 없음")
sys.exit(1 if errors else 0)
