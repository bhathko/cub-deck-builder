# freeform_playbook — 自由頁設計手冊(實驗B 專用)

> 給 GPT 在 Code Interpreter 裡照抄的自由頁畫法。**硬規範不可違反,
> 程式範式優先照抄再微調**;本檔的座標與作法已在本機實測產檔驗證過。
> 適用範圍:實驗B 的中間內容頁(封面/目錄/封底一律走工具鏈,不歸本檔管)。

## 一、硬規範(每頁必須全部成立)

1. **自由頁一律從 layout「空白(白底)」新增**:這個 layout 已內建公司制式
   內容底圖(content_bg 滿版)與左下角公司 logo(位置 0.31", 6.98",與封面/
   目錄同位)。**禁止自己畫背景、禁止自己貼 logo**(會跟 layout 的重複),
   也不得用任何滿版形狀蓋住底圖或 logo 區。
2. **logo 區保留**:y>6.9" 的左下帶(x<2.3")不放任何內容,logo 由 layout 顯示。
3. **頁碼右下角**:11pt、次文字色、兩位數字(03、04…),right-align 於
   left=12.3", top=6.95", w=0.7"。頁碼接續目錄頁(第一張自由頁是 03)。
4. **品牌色只用六色**:深 `344252`(主文字)、次 `68727E`、綠 `58D494`、
   紫 `848BF2`、藍 `4AB7F9`、線 `D8DEE4`;卡片底可用 `F7F9FB`。不得自創顏色。
5. **字體一律 Microsoft JhengHei**,且 latin 與 East Asian 都要設(見 set_font 範式;
   只設 font.name 的話中文會 fallback 成別的字)。
6. **安全區**:標題區 y 0.45–1.5";內容區 y 1.8–6.8";左右邊界 0.6"。
   logo 與頁碼所在的 y>6.9" 帶不放內容。
7. **標題區固定樣式**:綠色豎條(0.6", 0.55", 0.09"×0.5")+ 24pt 粗體深色標題
   (0.85", 0.45")+ 13pt 次色副標(0.88", 1.05")。
8. **全部可編輯物件**:只用文字框/形狀/圖片,禁止把文字轉成圖。
9. **內容忠實**:槽進頁面的每一個字與數字都要出自使用者輸入;缺的寫「待補充」。

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
    bar=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(0.6),Inches(0.55),
                               Inches(0.09),Inches(0.5))
    bar.fill.solid(); bar.fill.fore_color.rgb=GREEN; bar.line.fill.background()
    bar.shadow.inherit=False
    textbox(slide,Inches(0.85),Inches(0.45),Inches(9.5),Inches(0.6),[(title,24,DARK,True)])
    textbox(slide,Inches(0.88),Inches(1.05),Inches(9.5),Inches(0.4),[(subtitle,13,MUTED,False)])
    textbox(slide,Inches(12.3),Inches(6.95),Inches(0.7),Inches(0.35),
            [(f"{page_no:02d}",11,MUTED,False)],align=PP_ALIGN.RIGHT)

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

- **並列卡片**(2–3 欄重點):`card` 等寬排列,欄距 0.3";卡內彩色圓角
  標題條(白字 16pt 粗體)+ 「•  」列點 14pt,段後距 14pt。
- **大數字 KPI**(2–3 個指標):60pt 粗體彩色數值置中 + 18pt 粗體標籤 +
  13pt 次色說明;欄間放 1px 直線(LINE 色)。
- **水平時間軸**(3–5 節點):LINE 色細橫條 + 彩色圓點(白邊 1.5pt)+
  節點下 13pt 標籤;里程碑文字放軸上方;右下可加一張現況卡片。

同頁字級不超過 3 種;一頁塞不下就拆兩頁,禁止縮字硬塞。

## 四、QA-lite(自由頁畫完必跑,紅字就修版重畫)

```python
import sys; sys.path.insert(0,"/mnt/data/tools")
from pptx import Presentation
import text_tools as tt
prs=Presentation("/mnt/data/deck_final.pptx")
bad=0
for i,slide in enumerate(prs.slides,1):
    if i in (1,2,len(prs.slides)):        # 結構頁(封面/目錄/封底)歸 qa_check 管
        continue
    for sh in tt.iter_text_shapes(slide.shapes):
        try: ov=tt.estimate_overflow(sh)
        except Exception: continue
        if ov and ov.get("overflow"):
            bad+=1; print(f"p{i} 溢出 id={sh.shape_id}:{tt.shape_text(sh)[:15]}")
    for c in tt.text_collisions(slide):
        bad+=1; print(f"p{i} 文字重疊 area={c[0]:.2f}")
print("QA-lite:", "PASS" if bad==0 else f"FAIL({bad})")
```

修正最多三輪;三輪仍紅就換更簡單的版面(減欄、拆頁、縮短文字——改版面,
不縮字級)。

## 五、交付前自我檢查清單

- [ ] 每張自由頁:用「空白(白底)」layout(content_bg 底圖與左下 logo 自帶
      且未被遮住)、頁碼右下、只用六色、JhengHei(含 a:ea)
- [ ] 結構三頁 validator + qa_check 都 PASS(在插入自由頁**之前**跑)
- [ ] QA-lite PASS,輸出已貼給使用者
- [ ] 頁面上每個字與數字都能指回使用者輸入;缺料處寫「待補充」並列入待補清單
- [ ] 交付訊息明說:中間頁為 AI 自由設計、未經完整品質閘門,請務必人工目檢
