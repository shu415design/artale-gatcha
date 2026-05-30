# ARTALE 隨機怪物扭蛋 🍁

一個超簡單的純前端小網站：按一下按鈕，隨機抽出一隻《楓之谷 Artale》怪物，顯示牠的**中文名稱**與**圖片**。可直接發佈到 GitHub Pages。

資料來源：[artalemaplestory.com](https://www.artalemaplestory.com)（約 357 隻怪物）。

---

## 📁 檔案結構

```
artale-gacha/
├── index.html          ← 網站本體（純 HTML/CSS/JS，免後端）
├── scrape.py           ← 資料爬蟲（本機跑一次，產生下面兩樣）
├── data/
│   └── monsters.json   ← 怪物資料（執行 scrape.py 後產生）
├── icons/              ← 所有怪物小圖（執行 scrape.py 後產生）
├── requirements.txt
└── README.md
```

---

## 🚀 三步驟發佈

### 1. 產生資料（在自己電腦跑一次）

```bash
pip install -r requirements.txt
python scrape.py            # 抓中文名 + 下載所有怪物圖到 icons/
```

跑完會多出 `data/monsters.json` 和 `icons/` 整個資料夾。
（想用英文名：`python scrape.py --lang en`）

> 為什麼要下載圖？把圖放進自己的 repo，網站才不會依賴別人的伺服器、也不會因對方改網址而失效。
> 若想偷懶不下載：`python scrape.py --no-images`，JSON 會改成指向線上圖片網址。

### 2. 本機預覽（可選）

因為瀏覽器限制，直接雙擊 `index.html` 會讀不到 JSON。請用簡易伺服器預覽：

```bash
python -m http.server 8000
# 開瀏覽器到 http://localhost:8000
```

### 3. 推上 GitHub 並開啟 Pages

```bash
git init
git add .
git commit -m "Artale 隨機怪物扭蛋"
git branch -M main
git remote add origin https://github.com/你的帳號/artale-gacha.git
git push -u origin main
```

然後到 GitHub repo →「Settings」→「Pages」→ Source 選 `main` 分支、`/ (root)` 資料夾 → Save。
等一兩分鐘，你的網站就會在 `https://你的帳號.github.io/artale-gacha/` 上線。

最後記得把 `index.html` 最底下那行的 repo 連結改成你自己的網址。

---

## ✨ 功能

- 🎰 拉霸式滾動動畫，抽到的怪物會「定格＋彈跳」
- 🔊 轉蛋音效（點擊後才會發聲，符合瀏覽器規範）
- 🕘 顯示最近抽到的 8 隻
- 📊 抽取次數統計
- ⌨️ 按空白鍵也能抽
- 📱 手機 / 電腦皆適用（RWD）

## 🔧 客製化

- **改外觀**：`index.html` 最上方 `:root` 裡的 CSS 變數（顏色、楓葉橘等）。
- **只想要部分怪物**：編輯 `data/monsters.json`，留下你要的項目即可。
- **加搜尋 / 篩選等級**：`monsters.json` 已含 `slug`，可自行擴充欄位。

## ⚠️ 注意

- 爬蟲已內建禮貌性延遲，請勿短時間大量重複執行，避免對小型社群網站造成負擔。
- 本專案僅供個人 / 社群同好用途，圖片與名稱版權屬原遊戲及資料庫作者。
