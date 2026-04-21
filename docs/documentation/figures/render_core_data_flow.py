from PIL import Image, ImageDraw, ImageFont

W, H = 1720, 1080
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
    title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 34)
    subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
    group_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 24)
    box_title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 18)
    text_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 20)
    small_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 17)
except Exception:
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()
    group_font = ImageFont.load_default()
    box_title_font = ImageFont.load_default()
    text_font = ImageFont.load_default()
    small_font = ImageFont.load_default()


def rounded_box(x1, y1, x2, y2, fill, outline, radius=18, width=2):
    draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=fill, outline=outline, width=width)


def text_size(text, font, spacing=4):
    lines = text.split("\n")
    widths, heights = [], []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    return max(widths) if widths else 0, sum(heights) + spacing * (len(lines) - 1)


def center_text(box, text, font, fill=COLORS["title"], spacing=5):
    x1, y1, x2, y2 = box
    lines = text.split("\n")
    _, total_h = text_size(text, font, spacing)
    y = y1 + ((y2 - y1) - total_h) / 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = x1 + ((x2 - x1) - w) / 2
        draw.text((x, y), line, font=font, fill=fill)
        y += h + spacing


def left_text(box, title, lines, title_font, body_font, fill=COLORS["title"], title_offset=10, body_start=38, line_gap=22):
    x1, y1, x2, y2 = box
    draw.text((x1 + 14, y1 + title_offset), title, font=title_font, fill=fill)
    y = y1 + body_start
    for line in lines:
        draw.text((x1 + 16, y), line, font=body_font, fill=fill)
        y += line_gap


def draw_arrow_head(x1, y1, x2, y2, fill):
    ah = 10
    if abs(x2 - x1) > abs(y2 - y1):
        if x2 > x1:
            pts = [(x2, y2), (x2 - ah, y2 - ah), (x2 - ah, y2 + ah)]
        else:
            pts = [(x2, y2), (x2 + ah, y2 - ah), (x2 + ah, y2 + ah)]
    else:
        if y2 > y1:
            pts = [(x2, y2), (x2 - ah, y2 - ah), (x2 + ah, y2 - ah)]
        else:
            pts = [(x2, y2), (x2 - ah, y2 + ah), (x2 + ah, y2 + ah)]
    draw.polygon(pts, fill=fill)


def draw_label(label, x, y, fill):
    bbox = draw.textbbox((0, 0), label, font=small_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.rounded_rectangle((x - tw / 2 - 5, y - th / 2 - 3, x + tw / 2 + 5, y + th / 2 + 3), radius=6, fill=BG)
    draw.text((x - tw / 2, y - th / 2), label, font=small_font, fill=fill)


def arrow(x1, y1, x2, y2, fill=COLORS["arrow"], width=4, dashed=False, label=None, label_xy=None):
    if dashed:
        steps = 16
        for i in range(steps):
            if i % 2 == 0:
                sx = x1 + (x2 - x1) * i / steps
                sy = y1 + (y2 - y1) * i / steps
                ex = x1 + (x2 - x1) * (i + 1) / steps
                ey = y1 + (y2 - y1) * (i + 1) / steps
                draw.line((sx, sy, ex, ey), fill=fill, width=width)
    else:
        draw.line((x1, y1, x2, y2), fill=fill, width=width)
    draw_arrow_head(x1, y1, x2, y2, fill)
    if label:
        if label_xy is None:
            label_xy = ((x1 + x2) / 2, (y1 + y2) / 2)
        draw_label(label, label_xy[0], label_xy[1], fill)


def polyline_arrow(points, fill=COLORS["arrow"], width=4, dashed=False, label=None, label_xy=None):
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        if dashed:
            steps = 18
            for j in range(steps):
                if j % 2 == 0:
                    sx = x1 + (x2 - x1) * j / steps
                    sy = y1 + (y2 - y1) * j / steps
                    ex = x1 + (x2 - x1) * (j + 1) / steps
                    ey = y1 + (y2 - y1) * (j + 1) / steps
                    draw.line((sx, sy, ex, ey), fill=fill, width=width)
        else:
            draw.line((x1, y1, x2, y2), fill=fill, width=width)
    x1, y1 = points[-2]
    x2, y2 = points[-1]
    draw_arrow_head(x1, y1, x2, y2, fill)
    if label and label_xy is not None:
        draw_label(label, label_xy[0], label_xy[1], fill)


center_text((0, 24, W, 66), "Core Data Flow Across Major Modules", title_font)
center_text((0, 66, W, 92), "Business Sustainability Management Platform", subtitle_font, fill=COLORS["subtitle"])

# Left roles
rounded_box(60, 130, 270, 285, COLORS["actors"], COLORS["border"])
left_text((60, 130, 270, 285), "User Roles", ["- Store Staff", "- Region Manager", "- HQ Manager", "- Admin"], group_font, small_font, body_start=40, line_gap=22)

# Inputs section
rounded_box(380, 115, 1325, 380, COLORS["input_group"], COLORS["border"], radius=22)
center_text((380, 126, 1325, 156), "Operational and Governance Inputs", group_font)

boxes = [
    (410, 195, 635, 345, "Carbon Tracking", ["- activity value", "- date / category", "- emission calculation"], COLORS["white"], COLORS["border"]),
    (660, 195, 885, 345, "Waste Management", ["- waste type", "- recycled weight", "- disposal details"], COLORS["white"], COLORS["border"]),
    (910, 195, 1135, 345, "Training / ESG Inputs", ["- training records", "- supplier scores", "- policy records"], COLORS["white"], COLORS["border"]),
    (1160, 195, 1310, 345, "OCR-assisted Input", ["- bill image / PDF", "- extracted fields", "- prefill support"], COLORS["support"], (214, 182, 86)),
]
for x1, y1, x2, y2, title, lines, fill, outline in boxes:
    rounded_box(x1, y1, x2, y2, fill, outline)
    left_text((x1, y1, x2, y2), title, lines, box_title_font, small_font, title_offset=12, body_start=42, line_gap=22)

# database
rounded_box(470, 435, 770, 735, COLORS["db_group"], COLORS["border"], radius=22)
center_text((470, 446, 770, 474), "Central Data Layer", group_font)
rounded_box(515, 505, 725, 690, COLORS["db_group"], (184, 84, 80), radius=40)
center_text((515, 505, 725, 690), "MySQL Database\n- user\n- carbon_record\n- waste_record\n- report\n- supplier / policy\n- alert_log / audit_log", text_font)

# logic
rounded_box(870, 435, 1245, 735, COLORS["logic_group"], COLORS["border"], radius=22)
center_text((870, 446, 1245, 474), "Application Logic and Processing", group_font)
rounded_box(910, 505, 1205, 695, COLORS["white"], (150, 115, 166))
left_text((910, 505, 1205, 695), "Flask Backend", ["- validation and permissions", "- aggregation and comparison", "- alert threshold checks", "- compliance scoring", "- report generation"], group_font, small_font, body_start=42)

# outputs
rounded_box(250, 815, 1160, 1010, COLORS["output_group"], COLORS["border"], radius=22)
center_text((250, 968, 1160, 998), "User-facing Outputs and Management Use", group_font)
outputs = [
    (290, 885, 475, 950, "Dashboard Analytics"),
    (505, 885, 710, 950, "Reports and PDF Export"),
    (740, 885, 945, 950, "Alerts and Notifications"),
    (975, 885, 1130, 950, "Compliance / Audit Review"),
]
for x1, y1, x2, y2, label in outputs:
    rounded_box(x1, y1, x2, y2, COLORS["white"], (108, 142, 191))
    center_text((x1, y1, x2, y2), label, text_font)

# legend
rounded_box(1325, 860, 1690, 1010, COLORS["white"], COLORS["border"], radius=18)
draw.text((1350, 878), "Legend", font=group_font, fill=COLORS["title"])
draw.line((1355, 932, 1415, 932), fill=COLORS["arrow"], width=4)
draw.polygon([(1415, 932), (1405, 924), (1405, 940)], fill=COLORS["arrow"])
draw.text((1430, 922), "Main operational flow", font=small_font, fill=COLORS["title"])
arrow(1355, 964, 1415, 964, fill=(214, 182, 86), width=3, dashed=True)
draw.text((1430, 954), "Optional / support flow", font=small_font, fill=COLORS["title"])

# arrows
arrow(270, 215, 410, 215)
arrow(522, 345, 585, 435)
arrow(772, 345, 620, 435)
arrow(1022, 345, 660, 435)
polyline_arrow([(1235, 195), (1235, 172), (522, 172), (522, 195)], fill=(214, 182, 86), width=3, dashed=True, label="prefill", label_xy=(1065, 180))
polyline_arrow([(1235, 345), (1235, 368), (772, 368), (772, 345)], fill=(214, 182, 86), width=3, dashed=True, label="prefill", label_xy=(1040, 378))
arrow(770, 595, 870, 595)
polyline_arrow([(620, 690), (620, 860), (382, 860), (382, 885)])
polyline_arrow([(650, 690), (650, 860), (607, 860), (607, 885)])
polyline_arrow([(1245, 595), (1290, 595), (1290, 860), (842, 860), (842, 885)])
polyline_arrow([(1245, 630), (1315, 630), (1315, 860), (1052, 860), (1052, 885)])
polyline_arrow([(725, 645), (805, 645), (805, 860), (842, 860), (842, 885)], fill=(150, 115, 166), width=3, label="aggregated indicators", label_xy=(835, 742))
polyline_arrow([(725, 610), (760, 610), (760, 860), (742, 860), (742, 885)], fill=(150, 115, 166), width=3, label="threshold checks", label_xy=(760, 710))

out_path = "/Users/liuhaopu/Desktop/大三下课件/课设2/项目文件/docs/documentation/figures/system_core_data_flow.png"
img.save(out_path)
print(f"saved to {out_path}")
