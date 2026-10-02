# NCKU Campus

手機優先的成大課表與教室導航展示網站。無帳號、無後端資料庫，不處理學生帳密或成績。

## 功能

- 115–1 官方公開課程快照：資工、通識、外語、國文、體育及踏溯台南。
- 搜尋、類別／年級篩選、勾選與移除課程、衝堂提醒。
- 週課表與每日課程、分組習課選擇、修課學分統計。
- OpenStreetMap 互動底圖、官方館舍座標、成大室內地圖連結及 Google Maps 步行導航。
- 初次使用載入明確標示的示範課表。修改只儲存在目前瀏覽器，不跨裝置同步；可清空或還原。

## 本機執行

需要 Node.js 22 以上，無須安裝 npm 套件：

```sh
node scripts/serve.mjs
```

開啟 http://127.0.0.1:4173/ 。`dist/` 可直接交給任何靜態網站主機。

```sh
node --test scripts/model.test.mjs
```

## 資料來源與範圍

資料擷取日期：2026-10-02；學期：115-1。`dist/data.json` 為公開課程資料快照，不是即時選課服務。

- [成大官方課程查詢](https://course.ncku.edu.tw/index.php?c=qry_all)
- [成大地理資訊系統](https://nckumap.ncku.edu.tw/map.php)
- [官方課程節次時間表](https://cid-acad.ncku.edu.tw/var/file/42/1042/img/761/1132-TIME.pdf)
- [Leaflet](https://leafletjs.com/) 1.9.4；授權附於 `dist/vendor/LEAFLET-LICENSE.txt`。
- 地圖圖磚 © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright)。

選課清單略過只有要求說明、未提供選課序號的占位列。習課分組保留於主課程下，由使用者依教師公告選擇，不會自動將所有分組排入課表。館舍座標是中心點，不是入口；官方未提供樓層或位置時會標示缺漏。固定每週課表不會推斷停課、假日或補課。

`scripts/import_courses.py` 為公開資料匯入工具，需要 Python、lxml 及網路連線。重新匯入前必須核對來源學期及日期；不應將其他學期資料覆寫成 115-1。

## 隱私與展示限制

這是公開展示網站，任何取得網址的人皆可使用。課表變更只存於各自瀏覽器；網站不儲存真實個人成績、密碼或身份資料。定位只在使用者按下「我的位置」後請求，不會上傳至本站後端。外部底圖、字型、成大地圖與 Google Maps 需網路連線。這裡的勾選不會在校方系統完成選課。
