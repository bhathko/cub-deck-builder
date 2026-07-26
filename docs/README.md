# docs — 文件索引

> 一句話分工:**ARCHITECTURE 講「現在長什麼樣」、MAINTENANCE 講「怎麼做」、
> WORKLOG 講「為什麼」、FEEDBACK 講「哪裡不對」。**
> 想快速上手不必讀完——照下表挑一份。

| 你想知道 | 讀這份 | 大小 |
| --- | --- | --- |
| 系統現在長什麼樣(目錄、管線、模板包、綁定、驗收) | [ARCHITECTURE.md](ARCHITECTURE.md) | 中 |
| 我要改規則 / 加模板 / 發新版,步驟是什麼 | [MAINTENANCE.md](MAINTENANCE.md) | 小 |
| 這個設計當初為什麼這樣決定?否決過什麼? | [WORKLOG.md](WORKLOG.md) | 大(歷史檔) |
| 產出不如預期,怎麼回報才會真的變好 | [FEEDBACK.md](FEEDBACK.md) | 小 |
| 我是設計師 / 非技術同事 | [給設計師/](給設計師/) | 一個資料夾,先看它的 README |

## 讀的順序(第一次接手)

1. repo 根的 [`README.md`](../README.md) — 三分鐘知道這是什麼、目錄怎麼分
2. [`../AGENTS.md`](../AGENTS.md) — **11 條硬規則,唯一必背**
3. [ARCHITECTURE.md](ARCHITECTURE.md) — 一次看懂現行結構
4. 真的要動手時再開 [MAINTENANCE.md](MAINTENANCE.md);
   遇到「為什麼不那樣做」的疑問再查 [WORKLOG.md](WORKLOG.md)

## 這幾份的邊界(避免找錯地方)

- **ARCHITECTURE 不寫歷史**:看到「我們曾考慮 X 但否決」那類內容,去 WORKLOG。
- **WORKLOG 不是現況**:它的章節是時間序,早期章節描述的是**當時**的樣子
  (路徑、檔名都可能已經變了),別拿它當現況依據。
- **MAINTENANCE 不重複硬規則**:規則以 [`../AGENTS.md`](../AGENTS.md) 為準,
  MAINTENANCE 只講操作步驟。
- **給 GPT Builder 的操作**在 [`../gpts/DEPLOY.md`](../gpts/DEPLOY.md),不在這裡。
- **可執行的回歸案例**在 [`../engine/REGRESSION.md`](../engine/REGRESSION.md)。
