from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re
import shutil

ROOT = Path("my_project")
SRC = ROOT / "source" / "slides.md"
OUT = ROOT / "qa_preview_v4"
COVER_BG = ROOT / "assets/backgrounds/cover_bg.png"
CONTENT_BG = ROOT / "assets/backgrounds/content_bg.png"
LOGO = ROOT / "assets/logos/cathay_logo.png"
PYRAMID_TEMPLATE = ROOT / "style_reference/rendered_examples/pyramid/pyramid_layered_maturity_detail.png"

W, H = 1600, 900
S = 120
DARK = (52, 66, 82)
MUTED = (104, 114, 126)
GREEN = (88, 212, 148)
PURPLE = (132, 139, 242)
BLUE = (74, 183, 249)
LINE = (214, 222, 230)
WHITE = (255, 255, 255)

FONT_PATH = "C:/Windows/Fonts/msjh.ttc"
BOLD_PATH = "C:/Windows/Fonts/msjhbd.ttc"


def font(pt, bold=False):
    path = BOLD_PATH if bold and Path(BOLD_PATH).exists() else FONT_PATH
    return ImageFont.truetype(path, max(8, round(pt * S / 72)))


F = {
    "H1": font(40, True),
    "H1E": font(36, True),
    "H2": font(32, True),
    "H4": font(24, True),
    "H5": font(20, True),
    "H6": font(18),
    "H6B": font(18, True),
    "P1": font(16),
    "P1B": font(16, True),
    "P2": font(14),
    "P2B": font(14, True),
    "PN": font(28),
    "SM": font(12),
}


def parse_slides(text):
    pattern = re.compile(r"^## Slide\s+(\d+)\s*$", re.M)
    matches = list(pattern.finditer(text))
    result = {}
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        result[int(match.group(1))] = text[start:end]
    return result


def section(block, heading):
    match = re.search(
        r"^###\s+" + re.escape(heading) + r"\s*\n(.*?)(?=^###\s+|^---\s*$|\Z)",
        block,
        re.S | re.M,
    )
    return match.group(1).strip() if match else ""


def split_kv(text):
    for sep in ("：", ":"):
        if sep in text:
            key, value = text.split(sep, 1)
            return key.strip(), value.strip()
    return text.strip(), ""


def required(block):
    data = {}
    for line in section(block, "必須出現的文字").splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and ("：" in stripped or ":" in stripped):
            key, value = split_kv(stripped[2:].strip())
            data[key] = value
    return data


def nested(block, heading="內容"):
    raw = section(block, heading)
    items = []
    current = None
    for line in raw.splitlines():
        if not line.strip().startswith("- "):
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()[2:].strip()
        if indent == 0:
            current = {"title": text, "children": []}
            items.append(current)
        elif current:
            current["children"].append(text)
    return items


def toc_items(block):
    items = []
    current = None
    for line in section(block, "必須出現的文字").splitlines():
        stripped = line.strip()
        if stripped.startswith("- 第 "):
            if current:
                items.append(current)
            current = {"title": "", "subtitle": ""}
        elif current and stripped.startswith("- 大標"):
            current["title"] = split_kv(stripped[2:].strip())[1]
        elif current and stripped.startswith("- 副標"):
            current["subtitle"] = split_kv(stripped[2:].strip())[1]
    if current:
        items.append(current)
    return items


def bg(path):
    return Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS)


def draw_wrapped(draw, xy, text, fnt, fill=DARK, max_width=None, line_spacing=1.15):
    x, y = xy
    if max_width is None:
        draw.multiline_text((x, y), text, font=fnt, fill=fill, spacing=int(fnt.size * 0.15))
        return
    lines = []
    for para in str(text).split("\n"):
        current = ""
        for ch in para:
            test = current + ch
            if draw.textbbox((0, 0), test, font=fnt)[2] <= max_width or not current:
                current = test
            else:
                lines.append(current)
                current = ch
        lines.append(current)
    draw.multiline_text((x, y), "\n".join(lines), font=fnt, fill=fill, spacing=int(fnt.size * (line_spacing - 1)))


def rounded(draw, box, fill=WHITE, outline=LINE, r=10, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def label(draw, box, text, fill=GREEN, fnt=None, txt=WHITE):
    fnt = fnt or F["P1B"]
    draw.rectangle(box, fill=fill, outline=fill)
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    draw.multiline_text((cx, cy), text, font=fnt, fill=txt, anchor="mm", align="center", spacing=2)


def card(draw, box, title, body="", title_color=DARK, fill=WHITE):
    rounded(draw, box, fill=fill, outline=LINE, r=10, width=1)
    x1, y1, x2, y2 = box
    if title:
        draw_wrapped(draw, (x1 + 18, y1 + 16), title, F["P1B"], title_color, max_width=x2 - x1 - 36)
        body_y = y1 + 58
    else:
        body_y = y1 + 18
    if body:
        draw_wrapped(draw, (x1 + 18, body_y), body, F["P2"], DARK, max_width=x2 - x1 - 36, line_spacing=1.18)


def logo_and_page(image, draw, page=None):
    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA")
        logo.thumbnail((165, 45), Image.LANCZOS)
        image.paste(logo, (36, H - 62), logo)
    if page is not None:
        draw.text((W - 62, H - 55), str(page), font=F["PN"], fill=DARK, anchor="ra")


def header(draw, title, subtitle):
    draw_wrapped(draw, (58, 42), title, F["H2"], DARK, max_width=1380)
    if subtitle:
        draw_wrapped(draw, (60, 118), subtitle, F["H6"], MUTED, max_width=1380)


def bullets(lines):
    return "\n".join("• " + line for line in lines)


source = SRC.read_text(encoding="utf-8")
slides = parse_slides(source)

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

images = []

# 1 cover
image = bg(COVER_BG)
d = ImageDraw.Draw(image)
req = required(slides[1])
label(d, (48, 250, 195, 302), "內部簡報", DARK, F["P1B"])
dark_title = req["主標題"]
emphasis = req["副標題"]
x, y, gap = 42, 342, 28
dark_w = d.textbbox((0, 0), dark_title, font=F["H1"])[2]
em_w = d.textbbox((0, 0), emphasis, font=F["H1E"])[2]
available = 940
if dark_w < available * 0.52 and dark_w + gap + em_w <= available:
    d.text((x, y), dark_title, font=F["H1"], fill=DARK, anchor="la")
    d.text((x + dark_w + gap, y), emphasis, font=F["H1E"], fill=GREEN, anchor="la")
    meta_y = y + 84
else:
    d.text((x, y), dark_title, font=F["H1"], fill=DARK, anchor="la")
    d.text((x, y + 76), emphasis, font=F["H1E"], fill=GREEN, anchor="la")
    meta_y = y + 160
d.text((x, meta_y), f"{req['日期']}  |  {req['報告人']}", font=F["H6B"], fill=MUTED, anchor="la")
logo_and_page(image, d)
images.append(image)

# 2 TOC
image = bg(CONTENT_BG)
d = ImageDraw.Draw(image)
d.text((90, 140), "Contents", font=F["P2"], fill=MUTED)
d.text((90, 180), "目錄", font=F["H2"], fill=DARK)
for i, item in enumerate(toc_items(slides[2])):
    y = 165 + i * 132
    d.ellipse((610, y, 642, y + 32), outline=MUTED, width=1)
    d.text((626, y + 16), str(i + 1), font=F["SM"], fill=MUTED, anchor="mm")
    d.text((685, y - 4), item["title"], font=F["H5"], fill=DARK)
    if item["subtitle"] != "無":
        draw_wrapped(d, (685, y + 42), item["subtitle"], F["P2"], MUTED, max_width=650)
logo_and_page(image, d, 2)
images.append(image)

# 3 overview
image = bg(CONTENT_BG)
d = ImageDraw.Draw(image)
req = required(slides[3])
header(d, req["主標題"], req["副標題"])
d.ellipse((625, 270, 885, 530), fill=DARK, outline=DARK)
d.multiline_text((755, 400), "年度目標\n更快決策\n更穩服務", font=F["P1B"], fill=WHITE, anchor="mm", align="center", spacing=5)
nodes = [
    ("核心任務", "串接流程、資料、服務與人才能力"),
    ("2 項大型專案", "數據治理｜服務體驗升級"),
    ("12 個里程碑", "對齊 Q1-Q4 推進節奏"),
    ("40%", "報表處理時間節省目標"),
    ("30%", "服務回應一致性提升目標"),
    ("年度目標", "管理更快、服務更穩、能力可複製"),
]
positions = [(70, 190), (70, 360), (70, 530), (1040, 190), (1040, 360), (1040, 530)]
for (title, body), (px, py) in zip(nodes, positions):
    card(d, (px, py, px + 450, py + 108), title, body, GREEN)
logo_and_page(image, d, 3)
images.append(image)

# 4 info columns
image = bg(CONTENT_BG)
d = ImageDraw.Draw(image)
req = required(slides[4])
header(d, req["主標題"], req["副標題"])
columns = nested(slides[4])
for x_pos, item, color in zip([70, 560, 1050], columns, [GREEN, DARK, BLUE]):
    label(d, (x_pos, 188, x_pos + 390, 236), item["title"], color, F["P1B"])
    card(d, (x_pos, 260, x_pos + 390, 675), "", bullets(item["children"]), color)
logo_and_page(image, d, 4)
images.append(image)

# 5 data before/after
image = bg(CONTENT_BG)
d = ImageDraw.Draw(image)
req = required(slides[5])
header(d, req["主標題"], req["副標題"])
data = nested(slides[5])
label(d, (80, 185, 515, 232), "Before", GREEN, F["P1B"])
label(d, (1085, 185, 1520, 232), "After", PURPLE, F["P1B"])
card(d, (80, 265, 515, 555), "改善前", bullets(data[0]["children"]), GREEN)
card(d, (1085, 265, 1520, 555), "改善後", bullets(data[1]["children"]), PURPLE)
d.polygon([(690, 365), (900, 365), (900, 330), (1010, 410), (900, 490), (900, 455), (690, 455)], fill=(225, 231, 236))
label(d, (80, 615, 1520, 662), "關鍵改善目標", DARK, F["P1B"])
for i, text in enumerate(data[2]["children"]):
    key, value = split_kv(text)
    px = 100 + i * 488
    card(d, (px, 705, px + 405, 790), key, value, GREEN)
logo_and_page(image, d, 5)
images.append(image)

# 6 evaluation
image = bg(CONTENT_BG)
d = ImageDraw.Draw(image)
req = required(slides[6])
header(d, req["主標題"], req["副標題"])
options = nested(slides[6])
for x_pos, color, item in zip([80, 570, 1060], [GREEN, PURPLE, DARK], options[:3]):
    name, subtitle = split_kv(item["title"])
    label(d, (x_pos, 178, x_pos + 400, 225), name, color, F["P1B"])
    d.text((x_pos + 200, 250), subtitle, font=F["P1B"], fill=color, anchor="mm")
    card(d, (x_pos, 290, x_pos + 400, 430), "優點", item["children"][0].replace("優點：", ""), GREEN)
    card(d, (x_pos, 475, x_pos + 400, 615), "待改善", item["children"][1].replace("缺點：", ""), PURPLE)
label(d, (80, 670, 250, 718), "建議方向", DARK, F["P1B"])
draw_wrapped(d, (285, 678), "　".join(options[3]["children"]), F["P1B"], DARK, max_width=1180)
logo_and_page(image, d, 6)
images.append(image)

# 7 story
image = bg(CONTENT_BG)
d = ImageDraw.Draw(image)
req = required(slides[7])
header(d, req["主標題"], req["副標題"])
story = nested(slides[7])
phases = [
    ("過去", story[1]["children"][0].replace("過去：", ""), PURPLE),
    ("現在", story[1]["children"][1].replace("現在：", ""), GREEN),
    ("未來", story[1]["children"][2].replace("未來：", ""), DARK),
]
for x_pos, (name, body, color) in zip([80, 570, 1060], phases):
    label(d, (x_pos, 182, x_pos + 400, 230), name, color, F["P1B"])
    card(d, (x_pos, 270, x_pos + 400, 410), "故事", body, color)
card(d, (80, 470, 480, 690), "專案背景", bullets(story[0]["children"][:2]), DARK)
card(d, (570, 470, 970, 690), "改善重點", "• 服務分級\n• 回應腳本\n• 知識庫", GREEN)
card(d, (1060, 470, 1460, 690), "預期成果", bullets(story[2]["children"]), BLUE)
logo_and_page(image, d, 7)
images.append(image)

# 8 pyramid, keep template-like slanted hierarchy
image = bg(CONTENT_BG)
d = ImageDraw.Draw(image)
req = required(slides[8])
header(d, req["主標題"], req["副標題"])
levels = nested(slides[8])
# Isometric stepped pyramid inspired by the template page 54.
# Keep it below the subtitle area and away from the explanation column.
base_x = 40
top_y = 235
step_h = 68
front_x = [250, 210, 170, 130, 90]
front_w = [390, 330, 270, 210, 150]
depth_x = 58
depth_y = -28
fills_front = [(35, 48, 61), (79, 105, 130), (34, 128, 82), (52, 183, 112), GREEN]
fills_top = [(185, 199, 213), (173, 195, 214), (147, 218, 180), (171, 232, 199), (196, 241, 216)]
for idx, item in enumerate(levels):
    _, name = split_kv(item["title"])
    layer = 4 - idx
    x = base_x + front_x[layer]
    y = top_y + layer * step_h
    w = front_w[layer]
    # Top face
    top_poly = [(x, y), (x + w, y), (x + w + depth_x, y + depth_y), (x + depth_x, y + depth_y)]
    front_poly = [(x, y), (x + w, y), (x + w + 26, y + step_h - 8), (x + 26, y + step_h - 8)]
    right_poly = [(x + w, y), (x + w + depth_x, y + depth_y), (x + w + depth_x + 25, y + depth_y + step_h - 8), (x + w + 26, y + step_h - 8)]
    d.polygon(top_poly, fill=fills_top[idx])
    d.polygon(front_poly, fill=fills_front[idx])
    d.polygon(right_poly, fill=tuple(max(0, c - 25) for c in fills_front[idx]))
    d.line(top_poly + [top_poly[0]], fill=(245, 245, 245), width=1)
    d.line(front_poly + [front_poly[0]], fill=(245, 245, 245), width=1)
    # Keep labels horizontal for readability in preview, but positioned inside the layer.
    d.text((x + w / 2 + 8, y + step_h / 2 - 2), name, font=F["P1B"], fill=WHITE, anchor="mm")

# Explanations align with the pyramid layers, like the template.
desc_x = 620
for i, item in enumerate(levels):
    level, name = split_kv(item["title"])
    y = 205 + i * 82
    d.text((desc_x, y), f"{level}｜{name}", font=F["P1B"], fill=GREEN)
    draw_wrapped(d, (desc_x, y + 34), item["children"][0], F["P2"], DARK, max_width=500)

# Right-side note card, matching the template's white card treatment.
rounded(d, (1190, 190, 1535, 660), fill=(248, 251, 253), outline=LINE, r=10, width=1)
d.rectangle((1216, 225, 1224, 430), fill=GREEN)
d.text((1244, 225), "能力堆疊重點", font=F["P1B"], fill=GREEN)
draw_wrapped(d, (1244, 265), "由服務標準化開始，逐層累積知識、流程、訓練與持續優化機制。", F["P2"], DARK, max_width=245)
d.text((1244, 380), "年度落地", font=F["P1B"], fill=DARK)
draw_wrapped(d, (1244, 420), "Q2 建立標準\nQ3 推動訓練\nQ4 固化機制", F["P2"], DARK, max_width=245)
# Redraw slide 8 cleanly so the preview follows the page-54 pyramid template:
# slanted hierarchy on the left, layer-aligned explanations in the middle,
# and one light note card on the right.
image = bg(CONTENT_BG)
d = ImageDraw.Draw(image)
req_vals = list(required(slides[8]).values())
header(d, req_vals[0] if len(req_vals) > 0 else "", req_vals[1] if len(req_vals) > 1 else "")
levels = nested(slides[8])

def darker(rgb, amount=28):
    return tuple(max(0, c - amount) for c in rgb)

layer_specs = [
    (80, 650, 440, 78, DARK, (184, 199, 213)),
    (120, 575, 370, 74, (85, 111, 138), (172, 195, 214)),
    (160, 502, 300, 70, (34, 128, 82), (148, 219, 181)),
    (200, 430, 230, 68, (52, 183, 112), (172, 232, 201)),
    (240, 360, 160, 66, GREEN, (198, 242, 218)),
]

for idx, item in enumerate(levels[:5]):
    _, name = split_kv(item["title"])
    if not name:
        name = item["title"]
    x, y, w, h, front_color, top_color = layer_specs[idx]
    depth_x, depth_y, slant = 70, 34, 34
    top_poly = [(x, y), (x + w, y), (x + w + depth_x, y - depth_y), (x + depth_x, y - depth_y)]
    front_poly = [(x, y), (x + w, y), (x + w + slant, y + h), (x + slant, y + h)]
    side_poly = [
        (x + w, y),
        (x + w + depth_x, y - depth_y),
        (x + w + depth_x + slant, y + h - depth_y),
        (x + w + slant, y + h),
    ]
    d.polygon(top_poly, fill=top_color)
    d.polygon(side_poly, fill=darker(front_color, 34))
    d.polygon(front_poly, fill=front_color)
    d.line(top_poly + [top_poly[0]], fill=(247, 249, 250), width=1)
    d.line(front_poly + [front_poly[0]], fill=(247, 249, 250), width=1)
    d.text((x + w / 2 + 24, y + h / 2 + 10), name, font=F["P1B"], fill=WHITE, anchor="mm")

desc_positions = [334, 418, 502, 586, 670]
for y, item in zip(desc_positions, list(reversed(levels[:5]))):
    level, name = split_kv(item["title"])
    if not name:
        name = item["title"]
    rounded(d, (595, y - 18, 1140, y + 66), fill=(250, 252, 253), outline=None, r=6, width=1)
    d.text((620, y), f"{level}｜{name}", font=F["P1B"], fill=GREEN)
    body = item["children"][0] if item["children"] else ""
    draw_wrapped(d, (620, y + 34), body, F["P2"], DARK, max_width=475, line_spacing=1.08)

rounded(d, (1185, 190, 1540, 690), fill=(248, 251, 253), outline=LINE, r=8, width=1)
d.rectangle((1218, 225, 1226, 430), fill=GREEN)
d.text((1248, 225), "能力堆疊重點", font=F["P1B"], fill=GREEN)
draw_wrapped(
    d,
    (1248, 265),
    "由服務標準化開始，逐層累積知識、流程、訓練與持續優化機制。",
    F["P2"],
    DARK,
    max_width=250,
)
d.text((1248, 395), "年度落地", font=F["P1B"], fill=DARK)
draw_wrapped(d, (1248, 435), "Q2 建立標準\nQ3 推動訓練\nQ4 固化機制", F["P2"], DARK, max_width=250)
logo_and_page(image, d, 8)
images.append(image)

# Replace the legacy P8 drawing with the exact page-54 template artwork.
# The template image supplies the pyramid, bands, card geometry, logo, and background;
# only the editable-looking text content is overlaid for this preview.
image = Image.open(PYRAMID_TEMPLATE).convert("RGB").resize((W, H), Image.LANCZOS)
d = ImageDraw.Draw(image)
req = required(slides[8])
levels = nested(slides[8])
# The reference image already contains the exact template background. Use the
# clean background to clear the placeholder title, player controls, and final
# page number while keeping the page-54 geometry as the visual contract.
clean_bg = bg(CONTENT_BG)
image.paste(clean_bg.crop((0, 0, W, 136)), (0, 0))
image.paste(clean_bg.crop((0, 820, 260, 900)), (0, 820))
d = ImageDraw.Draw(image)
draw_wrapped(d, (58, 42), req["主標題"], F["H2"], DARK, max_width=1380)
draw_wrapped(d, (60, 112), req["副標題"], F["P2"], MUTED, max_width=1380)

label_boxes = [
    (0, 174, 122, 226),
    (28, 286, 170, 344),
    (64, 410, 218, 470),
    (82, 535, 264, 596),
    (126, 670, 322, 732),
]
label_colors = [GREEN, (52, 183, 112), (34, 128, 82), (92, 121, 150), DARK]

# The rendered template contains placeholder paragraphs in the central lane.
# Clear that lane as one replaceable content zone, then redraw the five
# template-like horizontal rows with project text.
d.rectangle((105, 136, 1125, 735), fill=(247, 249, 250))

row_specs = [
    (115, 145, 1050, 230, GREEN),
    (172, 260, 1080, 345, GREEN),
    (244, 375, 1100, 460, GREEN),
    (310, 493, 1100, 578, DARK),
    (384, 625, 1100, 710, DARK),
]
for (x1, y1, x2, y2, title_color), item in zip(row_specs, reversed(levels[:5])):
    level, name = split_kv(item["title"])
    d.rectangle((x1 - 2, y1 - 2, x2 + 2, y2 + 2), fill=WHITE)
    d.text((x1, y1), f"{level}｜{name}", font=F["H5"], fill=title_color)
    body = item["children"][0] if item["children"] else ""
    draw_wrapped(d, (x1, y1 + 39), body, F["P2"], DARK, max_width=x2 - x1, line_spacing=1.08)

for box, item, fill in zip(label_boxes, reversed(levels[:5]), label_colors):
    _, name = split_kv(item["title"])
    x1, y1, x2, y2 = box
    d.rectangle((x1, y1, x2, y2), fill=fill)
    d.text(((x1 + x2) / 2, (y1 + y2) / 2), name, font=F["P2B"], fill=WHITE, anchor="mm")

def paint_from_column(box, sample_x):
    x1, y1, x2, y2 = box
    for yy in range(y1, y2 + 1):
        d.line((x1, yy, x2, yy), fill=image.getpixel((sample_x, yy)))

paint_from_column((1085, 140, 1545, 215), 1548)
paint_from_column((1085, 215, 1545, 470), 1548)
paint_from_column((1085, 495, 1545, 565), 1548)
paint_from_column((1085, 565, 1545, 735), 1548)
d.text((1110, 172), "能力堆疊重點", font=F["H4"], fill=GREEN)
draw_wrapped(d, (1110, 220), "由服務標準化開始，逐層累積知識、流程、訓練與持續優化機制。", F["P2"], DARK, max_width=370)
draw_wrapped(d, (1110, 395), "# 標準化　# 文件化　# 協作化", F["P2"], GREEN, max_width=370)
d.text((1130, 528), "年度落地", font=F["H4"], fill=DARK)
draw_wrapped(d, (1130, 577), "Q2 建立標準\nQ3 推動訓練\nQ4 固化機制", F["P2"], DARK, max_width=320)
draw_wrapped(d, (1130, 700), "# 訓練　# 追蹤　# 優化", F["P2"], DARK, max_width=320)

image.paste(clean_bg.crop((1475, 815, 1598, 900)), (1475, 815))
d = ImageDraw.Draw(image)
logo_and_page(image, d, 8)
images[-1] = image

# 9 timeline
image = bg(CONTENT_BG)
d = ImageDraw.Draw(image)
req = required(slides[9])
header(d, req["主標題"], req["副標題"])
rows = nested(slides[9])
x0, col_w = 245, 315
for i, quarter in enumerate(["Q1\n盤點", "Q2\n建置", "Q3\n推廣", "Q4\n固化"]):
    label(d, (x0 + i * col_w, 190, x0 + i * col_w + 270, 262), quarter, GREEN if i < 3 else DARK, F["H5"])
row_defs = [
    (rows[0]["title"].replace("：", ""), rows[0]["children"], 315),
    (rows[1]["title"].replace("：", ""), rows[1]["children"], 500),
]
for title, values, y in row_defs:
    draw_wrapped(d, (70, y + 28), title, F["P1B"], MUTED, max_width=145)
    for i, value in enumerate(values[:4]):
        card(d, (x0 + i * col_w, y, x0 + i * col_w + 270, y + 125), "", value, GREEN)
draw_wrapped(d, (70, 713), rows[2]["title"].replace("：", ""), F["P1B"], MUTED, max_width=145)
cycle_x, cycle_gap, cycle_w = 245, 260, 225
for i, value in enumerate(rows[2]["children"][:5]):
    card(d, (cycle_x + i * cycle_gap, 685, cycle_x + i * cycle_gap + cycle_w, 810), "", value, GREEN)
logo_and_page(image, d, 9)
images.append(image)

# 10 closing
image = bg(COVER_BG)
d = ImageDraw.Draw(image)
d.text((90, 420), "Thank you", font=F["H2"], fill=DARK, anchor="la")
images.append(image)

for i, image in enumerate(images, 1):
    image.save(OUT / f"slide_{i:02d}.png")

thumbs = []
for i, image in enumerate(images, 1):
    thumb = image.copy()
    thumb.thumbnail((380, 214), Image.LANCZOS)
    canvas = Image.new("RGB", (400, 250), (255, 255, 255))
    canvas.paste(thumb, (10, 10))
    ImageDraw.Draw(canvas).text((10, 226), f"slide_{i:02d}", font=F["SM"], fill=DARK)
    thumbs.append(canvas)
sheet = Image.new("RGB", (800, 1250), (235, 238, 241))
for idx, thumb in enumerate(thumbs):
    sheet.paste(thumb, ((idx % 2) * 400, (idx // 2) * 250))
sheet.save(OUT / "contact_sheet.png")

print(OUT)
