#!/usr/bin/env python3
"""单次运行：从当前 runner 出口 IP 取 key，跑最多 10 条查询。

遇到 401 会自动重新取 key 再试（key 与 IP 绑定，换 key 能排除 key 失效）。
"""
import json
import sys
import time
import urllib.error
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


def get(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers=HDR)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        try:
            j = json.loads(body)
            j.setdefault("code", e.code)
            return j
        except Exception:
            return {"code": e.code, "msg": f"HTTP {e.code}"}
    except Exception as e:
        return {"code": -1, "msg": f"{type(e).__name__}"}


def fresh_key():
    return ((get(BASE + "/qbapp/get").get("data") or {}).get("key") or "")


def main():
    raw = sys.argv[1] if len(sys.argv) > 1 else ""
    items = []
    for part in raw.replace("\n", ";").split(";"):
        part = part.strip()
        if not part:
            continue
        t, v = (part.split("=", 1) + [""])[:2] if "=" in part else ("qq_tel", part)
        if t.strip() in PATHS and v.strip():
            items.append((t.strip(), v.strip()))

    out = {"count": len(items), "results": []}
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

        if j.get("code") == 401:
            # 换 key 再试一次（可能是 key 过期）
            key = fresh_key()
            j = get(f"{BASE}{path}?{field}={urllib.parse.quote(v)}&qb_key={key}")

        code = j.get("code")
        out["results"].append({"type": t, "q": v, "code": code,
                               "msg": j.get("msg"), "data": j.get("data")})
        print(f"{t} {v} -> {code} {j.get('msg')}", flush=True)
        if code == 401:
            out["quota_hit"] = True
            break
        time.sleep(0.5)

    json.dump(out, open("result.json", "w"), ensure_ascii=False)
    print("\nRESULT_JSON " + json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
