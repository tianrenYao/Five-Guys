from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1300
BG = "white"

COLORS = {
    "title": (40, 40, 40),
    "subtitle": (110, 110, 110),
    "border": (110, 110, 110),
    "arrow": (90, 90, 90),
    "actors": (218, 232, 252),
    "input_group": (213, 232, 212),
    "db_group": (248, 206, 204),
    "logic_group": (225, 213, 231),
    "output_group": (218, 232, 252),
    "support": (255, 242, 204),
    "white": (255, 255, 255),
}

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

try:
    title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 46)
    subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 27)
    group_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 32)
    box_title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 24)
    text_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 28)
    small_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 25)
except Exception:
    title_font = group_font = box_title_font = text_font = small_font = subtitle_font = ImageFont.load_default()


def rounded_box(x1, y1, x2, y2, fill, outline, radius=18, width=2):
    draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=fill, outline=outline, width=width)


def measure(text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def center_text(box, text, font, fill=COLORS["title"], spacing=5):
    x1, y1, x2, y2 = box
    lines = text.split("\n")
    line_sizes = [measure(line, font) for line in lines]
    total_h = sum(h for _, h in line_sizes) + spacing * (len(lines) - 1)
    cy = y1 + ((y2 - y1) - total_h) / 2
    for i, line in enumerate(lines):
        w, h = line_sizes[i]
        cx = x1 + ((x2 - x1) - w) / 2
        draw.text((cx, cy), line, font=font, fill=fill)
        cy += h + spacing


def left_text(box, title, lines, tfont, bfont, fill=COLORS["title"],
              title_offset=12, body_start=42, line_gap=22, pad_x=14,
              auto_center=False):
    x1, y1, x2, y2 = box
    if auto_center:
        max_w = measure(title, tfont)[0]
        for line in lines:
            w = measure(line, bfont)[0]
            if w > max_w:
                max_w = w
        pad_x = max(((x2 - x1) - max_w) // 2, 10)
    draw.text((x1 + pad_x, y1 + title_offset), title, font=tfont, fill=fill)
    y = y1 + body_start
    for line in lines:
        draw.text((x1 + pad_x, y), line, font=bfont, fill=fill)
        y += line_gap


def draw_arrow_head(x1, y1, x2, y2, fill):
    ah = 10
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) > abs(dy):
        if dx > 0:
            pts = [(x2, y2), (x2 - ah, y2 - ah), (x2 - ah, y2 + ah)]
        else:
            pts = [(x2, y2), (x2 + ah, y2 - ah), (x2 + ah, y2 + ah)]
    else:
        if dy > 0:
            pts = [(x2, y2), (x2 - ah, y2 - ah), (x2 + ah, y2 - ah)]
        else:
            pts = [(x2, y2), (x2 - ah, y2 + ah), (x2 + ah, y2 + ah)]
    draw.polygon(pts, fill=fill)


def draw_label(label, x, y, fill):
    tw, th = measure(label, small_font)
    draw.rounded_rectangle((x - tw / 2 - 5, y - th / 2 - 3,
                             x + tw / 2 + 5, y + th / 2 + 3), radius=6, fill=BG)
    draw.text((x - tw / 2, y - th / 2), label, font=small_font, fill=fill)


def _draw_seg(x1, y1, x2, y2, fill, width, dashed):
    if dashed:
        import math
        length = math.hypot(x2 - x1, y2 - y1)
        segs = max(int(length / 12), 4)
        for j in range(segs):
            if j % 2 == 0:
                draw.line((x1 + (x2 - x1) * j / segs, y1 + (y2 - y1) * j / segs,
                           x1 + (x2 - x1) * (j + 1) / segs, y1 + (y2 - y1) * (j + 1) / segs),
                          fill=fill, width=width)
    else:
        draw.line((x1, y1, x2, y2), fill=fill, width=width)


def arrow(x1, y1, x2, y2, fill=COLORS["arrow"], width=4, dashed=False,
          label=None, label_xy=None):
    _draw_seg(x1, y1, x2, y2, fill, width, dashed)
    draw_arrow_head(x1, y1, x2, y2, fill)
    if label:
        lx, ly = label_xy or ((x1 + x2) / 2, (y1 + y2) / 2)
        draw_label(label, lx, ly, fill)


def polyline(points, fill=COLORS["arrow"], width=4, dashed=False,
             label=None, label_xy=None):
    for i in range(len(points) - 1):
        _draw_seg(*points[i], *points[i + 1], fill, width, dashed)
    draw_arrow_head(*points[-2], *points[-1], fill)
    if label and label_xy:
        draw_label(label, *label_xy, fill)


# ── Title ──
center_text((0, 15, W, 72), "Core Data Flow Across Major Modules", title_font)
center_text((0, 72, W, 105), "Business Sustainability Management Platform", subtitle_font, fill=COLORS["subtitle"])

# ── Row 1: User Roles + Input Section ──
UR = (30, 128, 290, 370)
rounded_box(*UR, COLORS["actors"], COLORS["border"])
left_text(UR, "User Roles",
          ["• Store Staff", "• Region Manager", "• HQ Manager", "• Admin"],
          group_font, small_font, body_start=48, line_gap=28, auto_center=True)

GR = (340, 112, 1890, 460)
rounded_box(*GR, COLORS["input_group"], COLORS["border"], radius=22)
center_text((GR[0], 118, GR[2], 162), "Operational and Governance Inputs", group_font)

input_boxes = [
    (370,  185, 710,  430, "Carbon Tracking",
     ["• activity value", "• date / category", "• emission calculation"],
     COLORS["white"], COLORS["border"]),
    (735,  185, 1075, 430, "Waste Management",
     ["• waste type", "• recycled weight", "• disposal details"],
     COLORS["white"], COLORS["border"]),
    (1100, 185, 1440, 430, "Training / ESG Inputs",
     ["• training records", "• supplier scores", "• policy records"],
     COLORS["white"], COLORS["border"]),
    (1465, 185, 1860, 430, "OCR-assisted Input",
     ["• bill image / PDF", "• extracted fields", "• prefill support"],
     COLORS["support"], (214, 182, 86)),
]
for bx in input_boxes:
    x1, y1, x2, y2, title, lines, fill, outline = bx
    rounded_box(x1, y1, x2, y2, fill, outline)
    left_text((x1, y1, x2, y2), title, lines,
              box_title_font, small_font, title_offset=12, body_start=48, line_gap=32,
              auto_center=True)

# ── Row 2: Central Data Layer + Application Logic ──
DB = (320, 520, 820, 910)
rounded_box(*DB, COLORS["db_group"], COLORS["border"], radius=22)
center_text((DB[0], 530, DB[2], 570), "Central Data Layer", group_font)
DB_INNER = (350, 600, 790, 880)
rounded_box(*DB_INNER, COLORS["db_group"], (184, 84, 80), radius=36)
left_text(DB_INNER, "MySQL Database",
          ["• user", "• carbon_record", "• waste_record",
           "• report", "• supplier / policy", "• alert_log / audit_log"],
          box_title_font, text_font, body_start=40, line_gap=28, auto_center=True)

LG = (900, 520, 1570, 910)
rounded_box(*LG, COLORS["logic_group"], COLORS["border"], radius=22)
center_text((LG[0], 530, LG[2], 570), "Application Logic and Processing", group_font)
LG_INNER = (940, 600, 1540, 880)
rounded_box(*LG_INNER, COLORS["white"], (150, 115, 166))
left_text(LG_INNER, "Flask Backend",
          ["• validation and permissions", "• aggregation and comparison",
           "• alert threshold checks", "• compliance scoring",
           "• report generation"],
          group_font, small_font, body_start=52, line_gap=30, auto_center=True)

# ── Row 3: Outputs ──
OUT = (100, 990, 1550, 1250)
rounded_box(*OUT, COLORS["output_group"], COLORS["border"], radius=22)
center_text((OUT[0], 1195, OUT[2], 1240), "User-facing Outputs and Management Use", group_font)

output_boxes = [
    (130,  1030, 470,  1125, "Dashboard Analytics"),
    (495,  1030, 835,  1125, "Reports and PDF Export"),
    (860,  1030, 1200, 1125, "Alerts and Notifications"),
    (1225, 1030, 1530, 1125, "Compliance / Audit Review"),
]
for x1, y1, x2, y2, label in output_boxes:
    rounded_box(x1, y1, x2, y2, COLORS["white"], (108, 142, 191))
    center_text((x1, y1, x2, y2), label, small_font)

# ── Legend ──
LEG = (1610, 1010, 1900, 1200)
rounded_box(*LEG, COLORS["white"], COLORS["border"], radius=18)
draw.text((1632, 1025), "Legend", font=group_font, fill=COLORS["title"])
draw.line((1632, 1085, 1698, 1085), fill=COLORS["arrow"], width=4)
draw.polygon([(1698, 1085), (1686, 1075), (1686, 1095)], fill=COLORS["arrow"])
draw.text((1712, 1073), "Main flow", font=small_font, fill=COLORS["title"])
arrow(1632, 1130, 1698, 1130, fill=(214, 182, 86), width=3, dashed=True)
draw.text((1712, 1118), "Support flow", font=small_font, fill=COLORS["title"])

# ── Arrows ──
arrow(290, 250, 370, 250)

arrow(540, 430, 530, 520)
arrow(905, 430, 620, 520)
arrow(1270, 430, 720, 520)

ocr_cx = (1465 + 1860) // 2
carbon_cx = (370 + 710) // 2
waste_cx = (735 + 1075) // 2
polyline([(ocr_cx, 185), (ocr_cx, 165), (carbon_cx, 165), (carbon_cx, 185)],
         fill=(214, 182, 86), width=3, dashed=True,
         label="prefill", label_xy=(1200, 172))
polyline([(ocr_cx, 430), (ocr_cx, 448), (waste_cx, 448), (waste_cx, 430)],
         fill=(214, 182, 86), width=3, dashed=True,
         label="prefill", label_xy=(1270, 458))

arrow(DB[2], 710, LG[0], 710)

polyline([(570, DB[3]), (570, 975), (300, 975), (300, 1030)])
polyline([(620, DB[3]), (620, 975), (650, 975), (650, 1030)])

polyline([(LG[2], 700), (1600, 700), (1600, 975), (1010, 975), (1010, 1030)])
polyline([(LG[2], 750), (1630, 750), (1630, 975), (1365, 975), (1365, 1030)])

polyline([(DB[2], 760), (860, 760), (860, 975), (880, 975), (880, 1030)],
         fill=(150, 115, 166), width=3,
         label="threshold checks", label_xy=(870, 860))
polyline([(DB[2], 810), (880, 810), (880, 975), (1100, 975), (1100, 1030)],
         fill=(150, 115, 166), width=3,
         label="aggregated indicators", label_xy=(892, 895))

out_path = "/Users/liuhaopu/Desktop/大三下课件/课设2/项目文件/docs/documentation/figures/system_core_data_flow.png"
img.save(out_path)
print(f"saved to {out_path}")
