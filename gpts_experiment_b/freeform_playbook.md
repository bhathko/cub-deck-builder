# freeform_playbook — 自由頁設計手冊(實驗B 專用)

> 給 GPT 在 Code Interpreter 裡照抄的自由頁畫法。**硬規範不可違反,
> 程式範式優先照抄再微調**;繪製流程(layout、set_font 的 a:ea、move_slide、
> QA-lite 掃描)已在本機實測產檔驗證過。
> 適用範圍:實驗B 的中間內容頁(封面/目錄/封底一律走工具鏈,不歸本檔管)。
>
> **2026-08-05 起改用設計師視覺規範**:字級表、頁碼 28pt、標題區 H2/H6 與
> 樣式邊界為新增硬規範,頁碼幾何/字級/顏色一律對齊模板 `manifest.json` 的
> `page_number`。本檔第三節的三欄座標與 §二 的 page_base 已用
> `examples/demo_deck_expB.pptx`(2026-08-05 重產)實跑過,QA-lite 全綠;
> **但沙箱無中文字型,人眼目檢尚未做**——首次產出仍請在 PowerPoint 開檔
> 確認標題區與 28pt 頁碼的視覺比重。

## 一、硬規範(每頁必須全部成立)

1. **自由頁一律從 layout「空白(白底)」新增**:這個 layout 已內建公司制式
   內容底圖(content_bg 滿版)與左下角公司 logo(位置 0.31", 6.98",與封面/
   目錄同位)。**禁止自己畫背景、禁止自己貼 logo**(會跟 layout 的重複),
   也不得用任何滿版形狀蓋住底圖或 logo 區。
2. **logo 區保留**:y>6.9" 的左下帶(x<2.3")不放任何內容,logo 由 layout 顯示。
3. **頁碼右下角**:**28pt 粗體、主文字色 `344252`**,right-align 於
   left=12.3", top=6.72", w=0.7", h=0.5"。這組數值 = 模板 `manifest.json` 的
   `page_number`,**與工具鏈產的結構頁完全一致**,不得自訂。**數字不補零**
   ——第三頁寫 `3` 不是 `03`(引擎產的目錄頁就是 `2`,補零會讓同一份檔出現
   兩種頁碼格式)。頁碼接續目錄頁(第一張自由頁是 3)。封面/封底無頁碼。
4. **品牌色只用六色**:深 `344252`(主文字)、次 `68727E`、綠 `58D494`、
   紫 `848BF2`、藍 `4AB7F9`、線 `D8DEE4`;卡片底可用 `F7F9FB`,標籤/標題條上的
   反白字可用 `FFFFFF`。不得自創顏色。**綠 `58D494` 是強調色,只用於關鍵數字
   與重點標籤**,不得大面積鋪底。
5. **字體一律 Microsoft JhengHei**,且 latin 與 East Asian 都要設(見 set_font 範式;
   只設 font.name 的話中文會 fallback 成別的字)。
6. **字級只准用字級表的值**,禁止自創中間值(如 13pt、15pt、22pt):

   | 層級 | H1 | H1 Emphasis | H2 | H3 | H4 | H5 | H6 | p1 | p2 | Page Number |
   | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
   | 字級 | 40 | 36 | 32 | 28 | 24 | 20 | 18 | 16 | 14 | 28 |

   自由頁的用法固定:**頁面大標 H2(32)**、**核心訊息/副標 H6(18)**、
   **內容標題 H4(24)**、**再下一層標題 H5(20)**、**內文 p1(16)或 p2(14)**。
   **禁止任何內文低於 p2(14pt)**,包含卡片內說明、圖說、註記。
   唯一例外:大數字 KPI 版型的**數值本身**沿用 60pt(字級表外,⚠ 待設計師確認)。
   同頁**內容區**字級不超過 3 種(標題區與頁碼不計入)。
7. **安全區**:標題區 y 0.45–1.55";內容區 y 1.9–6.6";左右邊界 0.6"。
   底部兩塊淨空區不得放內容——左下 logo 區(y>6.9" 且 x<2.3")、
   右下頁碼區(y>6.3" 且 x>11.2",數值取自 manifest 的 `clear_zone_in`)。
8. **標題區固定樣式**:綠色豎條(0.6", 0.52", 0.09"×0.50")+ **H2 32pt 粗體**
   深色標題(0.85", 0.45", w 9.5", h 0.75")+ **H6 18pt** 次色副標
   (0.88", 1.15", w 9.5", h 0.45")。
9. **樣式邊界(拼版紀律)**:卡片一律白底或 `F7F9FB`、`D8DEE4` 淺灰細線框
   (0.75pt)、小圓角(`adjustments[0]=0.06`);要強調只能把 `58D494` /
   `848BF2` / `4AB7F9` 用在細框、標籤或小面積底色。**禁止**:陰影(一律
   `shadow.inherit=False`)、漸層、大圓角/膠囊圓角、3D 圖示、手繪插畫、
   大面積裝飾圖、模板六色以外的新色系。留白、線寬、圓角、對齊要跟同頁其他
   元件一致。
10. **底圖不得再加底色**:背景一律由 layout 的 content_bg 提供,不得在其上鋪
   任何滿版或大面積色塊/漸層當「背景色」。
11. **全部可編輯物件**:只用文字框/形狀/圖片,禁止把文字轉成圖。
12. **內容忠實**:槽進頁面的每一個字與數字都要出自使用者輸入;缺的寫「待補充」。

## 二、程式範式(照抄)

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

DARK=RGBColor(0x34,0x42,0x52); MUTED=RGBColor(0x68,0x72,0x7E)
GREEN=RGBColor(0x58,0xD4,0x94); PURPLE=RGBColor(0x84,0x8B,0xF2)
BLUE=RGBColor(0x4A,0xB7,0xF9); LINE=RGBColor(0xD8,0xDE,0xE4)
CARD=RGBColor(0xF7,0xF9,0xFB); WHITE=RGBColor(0xFF,0xFF,0xFF)
FONT="Microsoft JhengHei"; SLIDE_W,SLIDE_H=Inches(13.333),Inches(7.5)

# 字級表(pt)——只准用這些常數,禁止寫死其他數字
H1,H1E,H2,H3,H4,H5,H6,P1,P2 = 40,36,32,28,24,20,18,16,14
PAGE_NO_PT = 28            # 與模板 manifest 的 page_number.size_pt 一致
KPI_PT     = 60            # 字級表唯一例外:大數字 KPI 的數值本身(待設計師確認)

def set_font(run, size, color, bold=False):          # 中文字體必用這支
    f=run.font; f.name=FONT; f.size=Pt(size); f.bold=bold; f.color.rgb=color
    rPr=run._r.get_or_add_rPr(); ea=rPr.find(qn("a:ea"))
    if ea is None:
        ea=rPr.makeelement(qn("a:ea"),{}); rPr.append(ea)
    ea.set("typeface", FONT)

def textbox(slide,x,y,w,h,lines,align=PP_ALIGN.LEFT,anchor=MSO_ANCHOR.TOP):
    box=slide.shapes.add_textbox(x,y,w,h); tf=box.text_frame
    tf.word_wrap=True; tf.vertical_anchor=anchor
    for i,(t,sz,c,b) in enumerate(lines):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.alignment=align
        r=p.add_run(); r.text=t; set_font(r,sz,c,b)
    return box

def page_base(slide,title,subtitle,page_no):          # 每頁第一件事就是呼叫它
    # 背景(content_bg)與左下 logo 由 layout「空白(白底)」自帶,這裡不畫
    bar=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(0.6),Inches(0.52),
                               Inches(0.09),Inches(0.50))
    bar.fill.solid(); bar.fill.fore_color.rgb=GREEN; bar.line.fill.background()
    bar.shadow.inherit=False
    textbox(slide,Inches(0.85),Inches(0.45),Inches(9.5),Inches(0.75),[(title,H2,DARK,True)])
    textbox(slide,Inches(0.88),Inches(1.15),Inches(9.5),Inches(0.45),[(subtitle,H6,MUTED,False)])
    # 頁碼:幾何/字級/顏色/粗體/不補零全部對齊模板 manifest,與結構頁同一個樣子
    textbox(slide,Inches(12.3),Inches(6.72),Inches(0.7),Inches(0.5),
            [(str(page_no),PAGE_NO_PT,DARK,True)],align=PP_ALIGN.RIGHT)

def card(slide,x,y,w,h,fill=CARD):
    c=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,x,y,w,h)
    c.adjustments[0]=0.06; c.fill.solid(); c.fill.fore_color.rgb=fill
    c.line.color.rgb=LINE; c.line.width=Pt(0.75); c.shadow.inherit=False
    return c
```

新增自由頁+插到目錄後(結構檔由 render_deck 產出,只有 3 頁):

```python
prs=Presentation("/mnt/data/structural.pptx")
layout=next(l for l in prs.slide_layouts if l.name=="空白(白底)")   # 唯一允許的自由頁 layout
for draw in page_draw_functions:              # 每頁一支 draw 函式
    s=prs.slides.add_slide(layout)
    for ph in list(s.placeholders):           # 清掉 layout 殘留 placeholder
        ph._element.getparent().remove(ph._element)
    draw(s)
def move_slide(prs,old,new):
    xs=prs.slides._sldIdLst; el=list(xs)[old]; xs.remove(el); xs.insert(new,el)
for k in range(n_free):                       # 尾端的自由頁搬到目錄(idx1)之後
    move_slide(prs,3+k,2+k)
prs.save("/mnt/data/deck_final.pptx")
```

## 三、版面建議(不是硬規範,但先從這三種挑)

- **並列卡片**(2–3 欄重點):`card` 等寬排列。**三欄的實測安全值**:欄寬
  3.84"、欄距 0.30"、x = 0.60 / 4.74 / 8.88、y 1.95" 高 4.30"(底 6.25",
  收在頁碼淨空區之上);卡內標題條 x+0.35 寬 3.14",列點框 x+0.40 寬 3.04"。
  **不要用 3.95" 這種湊整數的欄寬**——乘三就會撞出右邊界。卡內彩色圓角
  標題條(白字 **H4 24pt** 粗體,條高 0.70";標題較長時降一級用
  **H5 20pt**)+ 「•  」列點 **P2 14pt**,段後距 14pt。
- **大數字 KPI**(2–3 個指標):**KPI_PT 60pt** 粗體彩色數值置中(字級表唯一
  例外)+ **H6 18pt** 粗體標籤 + **P2 14pt** 次色說明;欄間放 1px 直線(LINE 色)。
- **水平時間軸**(3–5 節點):LINE 色細橫條 + 彩色圓點(白邊 1.5pt)+
  節點下 **P2 14pt** 標籤;里程碑文字放軸上方;右下可加一張現況卡片。

同頁內容區字級不超過 3 種(標題區與頁碼不計);一頁塞不下就拆兩頁,
**禁止縮字硬塞**——字級表最小就是 P2 14pt,再小一律改版面。

## 四、QA-lite(自由頁畫完必跑,紅字就修版重畫)

掃五類:**溢出 / 文字重疊 / 字級與字體 / 品牌色 / 安全區與淨空區**。
任何一類紅字都要修版重畫。**安全區那類最容易在三欄版復發**——欄寬用預設值
乘三加欄距就會超出右邊界,或卡片底邊伸進右下頁碼區,肉眼在沒有中文字型的
沙箱裡看不出來,只有這支掃得到。

```python
import sys; sys.path.insert(0,"/mnt/data/tools")
from pptx import Presentation
from pptx.util import Inches
from pptx.enum.dml import MSO_FILL
from pptx.oxml.ns import qn
import text_tools as tt

FONT="Microsoft JhengHei"
OK_PT={40,36,32,28,24,20,18,16,14,60}      # 字級表 + 60(大數字 KPI 例外)
OK_HEX={"344252","68727E","58D494","848BF2","4AB7F9","D8DEE4","F7F9FB","FFFFFF"}

prs=Presentation("/mnt/data/deck_final.pptx"); bad=0
for i,slide in enumerate(prs.slides,1):
    if i in (1,2,len(prs.slides)):        # 結構頁(封面/目錄/封底)歸 qa_check 管
        continue
    for sh in tt.iter_text_shapes(slide.shapes):
        try: ov=tt.estimate_overflow(sh)
        except Exception: ov=None
        if ov and ov.get("overflow"):
            bad+=1; print(f"p{i} 溢出 id={sh.shape_id}:{tt.shape_text(sh)[:15]}")
        for para in sh.text_frame.paragraphs:
            for r in para.runs:
                if not r.text.strip(): continue
                tag=f"p{i}「{r.text[:10]}」"
                pt=r.font.size.pt if r.font.size else None
                if pt not in OK_PT:
                    bad+=1; print(f"{tag} 字級 {pt} 不在字級表")
                if r.font.name!=FONT:
                    bad+=1; print(f"{tag} 字體 {r.font.name}")
                ea=r._r.get_or_add_rPr().find(qn("a:ea"))
                if ea is None or ea.get("typeface")!=FONT:
                    bad+=1; print(f"{tag} 缺 a:ea 中文字體")
                try: hexc=str(r.font.color.rgb).upper()
                except Exception: hexc=None
                if hexc not in OK_HEX:
                    bad+=1; print(f"{tag} 文字色 {hexc} 不在六色內")
    for sh in slide.shapes:                # 形狀底色也只准用六色
        try:
            if sh.fill.type==MSO_FILL.SOLID:
                h=str(sh.fill.fore_color.rgb).upper()
                if h not in OK_HEX:
                    bad+=1; print(f"p{i} 形狀底色 {h} 不在六色內")
        except Exception: pass
    for sh in slide.shapes:                # 安全區:左右邊界 + 兩塊淨空區
        L,T=sh.left/914400,sh.top/914400
        R,B=L+sh.width/914400,T+sh.height/914400
        txt=sh.text_frame.text.strip() if sh.has_text_frame else ""
        if txt.isdigit() and L>11.2 and T>6.3: continue      # 頁碼本身豁免
        if L<0.6-1e-6 or R>12.733+1e-6:
            bad+=1; print(f"p{i} 超出左右邊界 {L:.2f}~{R:.2f}「{txt[:10]}」")
        if B>6.6+1e-6:
            bad+=1; print(f"p{i} 低於內容區下緣 6.6 → {B:.2f}「{txt[:10]}」")
        if B>6.3 and R>11.2:
            bad+=1; print(f"p{i} 侵入右下頁碼淨空區「{txt[:10]}」")
        if B>6.9 and L<2.3:
            bad+=1; print(f"p{i} 侵入左下 logo 淨空區「{txt[:10]}」")
    pn=[s for s in tt.iter_text_shapes(slide.shapes)                 # 右下角頁碼
        if tt.shape_text(s).strip().isdigit()
        and s.left and s.left>Inches(11.2) and s.top and s.top>Inches(6.3)]
    if len(pn)!=1:
        bad+=1; print(f"p{i} 右下角頁碼數量={len(pn)}(應為 1)")
    elif tt.shape_text(pn[0]).strip()!=str(i):
        bad+=1; print(f"p{i} 頁碼 {tt.shape_text(pn[0]).strip()!r} 應為 {str(i)!r}(不補零)")
    for c in tt.text_collisions(slide):
        bad+=1; print(f"p{i} 文字重疊 area={c[0]:.2f}")
print("QA-lite:", "PASS" if bad==0 else f"FAIL({bad})")
```

修正最多三輪;三輪仍紅就換更簡單的版面(減欄、拆頁、縮短文字——改版面,
不縮字級)。**字級/字體/顏色/頁碼四類紅字沒有「改版面」的解法,一律直接改回
規範值再重畫**;絕不可為了消溢出而把字調到 14pt 以下或改用表外字級。

## 五、交付前自我檢查清單

- [ ] 每張自由頁:用「空白(白底)」layout(content_bg 底圖與左下 logo 自帶
      且未被遮住)、只用六色、JhengHei(含 a:ea)
- [ ] 頁碼右下 28pt 粗體 `344252` @(12.3", 6.72"),數字不補零且接續目錄頁
- [ ] 字級全部落在字級表:大標 H2 32、副標 H6 18、內容標題 H4 24 / H5 20、
      內文 P1 16 或 P2 14,無任何內文低於 14pt(KPI 數值 60pt 為唯一例外)
- [ ] 無陰影、無漸層、無 3D/插畫/大面積裝飾;卡片為白底或 F7F9FB + 細灰線小圓角
- [ ] 結構三頁 validator + qa_check 都 PASS(在插入自由頁**之前**跑)
- [ ] QA-lite PASS,輸出已貼給使用者
- [ ] 頁面上每個字與數字都能指回使用者輸入;缺料處寫「待補充」並列入待補清單
- [ ] 交付訊息明說:中間頁為 AI 自由設計、未經完整品質閘門,請務必人工目檢
