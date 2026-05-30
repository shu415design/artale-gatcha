#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產生「隨機抽怪物」網站所需的資料。

artalemaplestory.com 的資料藏在 Next.js App Router 的 RSC 串流裡。
網站的內部資料其實是英文 + 一張翻譯表，渲染時即時翻成中文。
圖片網址則是用英文名推導（lowercase + 連字號）。

本腳本：
  1. 抓 /zh/monsters 頁面
  2. 從 self.__next_f.push 取出 RSC 串流
  3. 用正則抓出所有怪物物件（name+level+hp 是怪物獨有 pattern）
  4. 抓出翻譯表 (英→中)
  5. 把英文名翻成中文，從英文名推導 slug，組出圖片 URL，下載圖片

用法：
  pip install -r requirements.txt
  python scrape.py              # 中文名（預設）
  python scrape.py --lang en    # 英文名
  python scrape.py --no-images  # 不下載圖
  python scrape.py --debug      # 把 RSC 串流存到暫存目錄供除錯
"""
import argparse, json, os, re, tempfile, time, requests
from bs4 import BeautifulSoup

BASE = "https://www.artalemaplestory.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ArtaleGachaBot/1.0)"}


def fetch_html(lang):
    url = f"{BASE}/{lang}/monsters"
    print(f"[*] 抓取頁面：{url}")
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def extract_rsc_stream(html):
    """從 <script>self.__next_f.push([1,"..."])</script> 把所有字串拼起來。"""
    soup = BeautifulSoup(html, "html.parser")
    parts = []
    for s in soup.find_all("script"):
        txt = (s.string or "").strip()
        if "self.__next_f.push" not in txt:
            continue
        m = re.search(r'self\.__next_f\.push\(\s*\[\s*\d+\s*,\s*(".*?")\s*\]\s*\)',
                      txt, re.DOTALL)
        if not m:
            continue
        try:
            payload = json.loads(m.group(1))   # JS 字串 == JSON 字串
            if isinstance(payload, str):
                parts.append(payload)
        except Exception:
            pass
    return "".join(parts)


def extract_monster_names(stream):
    """
    怪物物件的獨特特徵：name + level + hp。
    （道具沒有 hp、裝備有 level 沒有 hp、所以這個組合是怪物獨有。）
    """
    names = []
    seen = set()
    for m in re.finditer(r'"name":"([^"]{1,80})","level":\d+,"hp":\d+', stream):
        n = m.group(1)
        if n not in seen:
            seen.add(n)
            names.append(n)
    return names


def extract_translations(stream):
    """
    翻譯表項目：英文 key → 中文 value。
    註：原始碼為了避開資料庫不允許 key 含 '.' 的限制，把 '.' 存成 '$dot'。
        例如 "Jr. Necki" 會存成 "Jr$dot Necki"，查詢時需要還原。
    """
    trans = {}
    for m in re.finditer(
        r'"([A-Za-z][A-Za-z 0-9\'\-/\.\$]{0,80})":"([\u4e00-\u9fff][^"]*)"',
        stream,
    ):
        en, zh = m.group(1), m.group(2)
        if en not in trans:
            trans[en] = zh
    return trans


def translate(en, trans):
    """先直接查；查不到時把 '.' 換成 '$dot' 再試一次。"""
    if en in trans:
        return trans[en]
    if "." in en:
        return trans.get(en.replace(".", "$dot"))
    return None


def slug_from_name(name):
    """
    英文名 → URL slug：lowercase、特殊字元去掉、空白換 -
    e.g. 'Orange Mushroom' → 'orange-mushroom'
         "Lupin's Curse" → 'lupins-curse'
    """
    s = name.lower().replace("'", "").replace("’", "")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def download_icons(mons):
    os.makedirs("icons", exist_ok=True)
    failed = []
    for i, m in enumerate(mons, 1):
        path = f"icons/{m['slug']}.gif"
        m["img"] = path
        if os.path.exists(path):
            continue
        try:
            r = requests.get(m["remote"], headers=HEADERS, timeout=30)
            r.raise_for_status()
            open(path, "wb").write(r.content)
            print(f"  [{i}/{len(mons)}] {path}")
            time.sleep(0.12)
        except Exception as e:
            failed.append((m["slug"], m.get("name_en", m["name"]), str(e)))
            m["img"] = m["remote"]   # 退回用線上圖
            print(f"  [{i}/{len(mons)}] 失敗 {path}（將用線上圖）")
    if failed:
        print(f"\n[!] {len(failed)} 隻圖下載失敗（slug 推導可能不準），前 5 個：")
        for s, n, e in failed[:5]:
            print(f"    - {n}（slug={s}）")
        print("    這些怪物在網頁上會自動退回用線上圖，仍可顯示。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="zh", choices=["zh", "en"])
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()

    html = fetch_html(a.lang)
    stream = extract_rsc_stream(html)
    print(f"[*] 取得 RSC 串流 {len(stream)} bytes")

    if a.debug:
        p = os.path.join(tempfile.gettempdir(), "artale_rsc.txt")
        open(p, "w", encoding="utf-8").write(stream)
        print(f"[debug] RSC 串流存到 {p}")

    en_names = extract_monster_names(stream)
    print(f"[*] 解析到 {len(en_names)} 隻怪物（英文名）")

    trans = extract_translations(stream) if a.lang == "zh" else {}
    if a.lang == "zh":
        print(f"[*] 翻譯表 {len(trans)} 筆")

    mons = []
    no_trans = []
    for en in en_names:
        if a.lang == "zh":
            zh = translate(en, trans)
            if zh is None:
                no_trans.append(en)
                zh = en
        else:
            zh = en
        slug = slug_from_name(en)
        mons.append({
            "name": zh,
            "name_en": en,
            "slug": slug,
            "remote": f"{BASE}/images/monsters/{slug}.gif",
        })

    if no_trans:
        print(f"[!] {len(no_trans)} 隻沒中文翻譯，會顯示英文名：")
        for n in no_trans[:10]:
            print(f"    - {n}")
        if len(no_trans) > 10:
            print(f"    ...（還有 {len(no_trans)-10} 隻）")

    mons.sort(key=lambda m: m["slug"])

    if a.no_images:
        for m in mons:
            m["img"] = m["remote"]
    else:
        print("[*] 下載 icon 中…")
        download_icons(mons)

    os.makedirs("data", exist_ok=True)
    with open("data/monsters.json", "w", encoding="utf-8") as f:
        json.dump(mons, f, ensure_ascii=False, indent=2)
    print(f"[+] 已輸出 data/monsters.json（{len(mons)} 筆）")
    print("[完成]")


if __name__ == "__main__":
    main()
