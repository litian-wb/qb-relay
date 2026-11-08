#!/usr/bin/env python3
"""单次运行：从当前 runner 的出口 IP 取 key，然后跑最多 10 条查询。

用法: python3 qb.py "qq_tel=110182068;tel_qq=13651895189;wb_tel=2803301701"
类型: qq_tel tel_qq wb_tel tel_wb qq_lol lol_qq tel_address
"""
import json
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://api.heikebook.com/api/v1"
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")
HDR = {"User-Agent": UA, "Origin": "https://qb.heikebook.com",
       "Referer": "https://qb.heikebook.com/", "Accept": "application/json"}

PATHS = {
    "qq_tel": ("/sgk/qq/qq", "qq"),
    "tel_qq": ("/sgk/qq/phone", "phone"),
    "wb_tel": ("/sgk/wb/uid", "uid"),
    "tel_wb": ("/sgk/wb/phone", "phone"),
    "qq_lol": ("/sgk/lol/qq", "qq"),
    "lol_qq": ("/sgk/lol/name", "name"),
    "tel_address": ("/sgk/qq/phone", "phone"),
}


def get(url, retries=2):
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HDR)
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8", "ignore"))
        except Exception as e:
            if i == retries:
                return {"code": -1, "msg": f"{type(e).__name__}: {e}"}
            time.sleep(2)


def fresh_key():
    j = get(BASE + "/qbapp/get")
    return ((j.get("data") or {}).get("key") or "")


def main():
    raw = sys.argv[1] if len(sys.argv) > 1 else ""
    items = []
    for part in raw.replace("\n", ";").split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            t, v = part.split("=", 1)
        else:
            t, v = "qq_tel", part
        t, v = t.strip(), v.strip()
        if t in PATHS and v:
            items.append((t, v))

    out = {"ip_run": True, "count": len(items), "results": []}
    if not items:
        json.dump(out, open("result.json", "w"), ensure_ascii=False)
        print(json.dumps(out, ensure_ascii=False))
        return

    key = fresh_key()
    out["key_ok"] = bool(key)
    for t, v in items:
        path, field = PATHS[t]
        url = f"{BASE}{path}?{field}={urllib.parse.quote(v)}&qb_key={key}"
        j = get(url)
        code = j.get("code")
        item = {"type": t, "q": v, "code": code, "msg": j.get("msg"), "data": j.get("data")}
        out["results"].append(item)
        print(f"{t} {v} -> {code} {j.get('msg')}", flush=True)
        if code == 401:      # 本 IP 额度已尽，后面的不必再试
            out["quota_hit"] = True
            break
        time.sleep(0.6)

    json.dump(out, open("result.json", "w"), ensure_ascii=False)
    print("\nRESULT_JSON " + json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
