from PIL import Image, ImageDraw, ImageFont

W, H = 1500, 930
BG = "white"

COLORS = {
    "user": (227, 242, 253),
    "ui": (232, 245, 233),
    "biz": (255, 243, 224),
    "sup": (243, 229, 245),
    "data": (236, 239, 241),
    "group": (245, 247, 250),
    "border": (120, 144, 156),
    "text": (33, 33, 33),
    "arrow": (110, 110, 110),
}

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

try:
    title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 34)
    group_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 24)
    text_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)
    small_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
except Exception:
    title_font = ImageFont.load_default()
    group_font = ImageFont.load_default()
    text_font = ImageFont.load_default()
    small_font = ImageFont.load_default()


def rounded_box(x1, y1, x2, y2, fill, outline, radius=18, width=2):
    draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=fill, outline=outline, width=width)


def center_text(box, text, font, fill=COLORS["text"], spacing=4):
    x1, y1, x2, y2 = box
    lines = text.split("\n")
    heights = []
    widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    total_h = sum(heights) + spacing * (len(lines) - 1)
    y = y1 + ((y2 - y1) - total_h) / 2
    for i, line in enumerate(lines):
        w = widths[i]
        h = heights[i]
        x = x1 + ((x2 - x1) - w) / 2
        draw.text((x, y), line, font=font, fill=fill)
        y += h + spacing


def group_box(x1, y1, x2, y2, title):
    rounded_box(x1, y1, x2, y2, COLORS["group"], COLORS["border"], radius=22, width=2)
    draw.text((x1 + 18, y1 + 12), title, font=group_font, fill=COLORS["text"])


def arrow(x1, y1, x2, y2):
    draw.line((x1, y1, x2, y2), fill=COLORS["arrow"], width=4)
    ah = 10
    if y2 > y1:
        draw.polygon([(x2, y2), (x2 - ah, y2 - ah), (x2 + ah, y2 - ah)], fill=COLORS["arrow"])
    else:
        draw.polygon([(x2, y2), (x2 - ah, y2 + ah), (x2 + ah, y2 + ah)], fill=COLORS["arrow"])


center_text((0, 16, W, 64), "Overall System Architecture", title_font)

# Layer 1
ux1, uy1, ux2, uy2 = 90, 85, 1410, 225
group_box(ux1, uy1, ux2, uy2, "User Layer")
user_boxes = [
    (140, 132, 530, 200, "Admin / HQ Manager"),
    (555, 132, 945, 200, "Region Manager"),
    (970, 132, 1360, 200, "Store Staff"),
]
for x1, y1, x2, y2, text in user_boxes:
    rounded_box(x1, y1, x2, y2, COLORS["user"], COLORS["border"])
    center_text((x1, y1, x2, y2), text, text_font)

# Layer 2
ax1, ay1, ax2, ay2 = 70, 280, 1430, 675
group_box(ax1, ay1, ax2, ay2, "Application Layer")

# Presentation
px1, py1, px2, py2 = 95, 332, 400, 640
group_box(px1, py1, px2, py2, "Presentation")
for box in [
    (128, 388, 367, 478, "Jinja2\nTemplates", "ui"),
    (128, 502, 367, 592, "Bootstrap UI", "ui"),
]:
    x1, y1, x2, y2, text, kind = box
    rounded_box(x1, y1, x2, y2, COLORS[kind], COLORS["border"])
    center_text((x1, y1, x2, y2), text, text_font)

# Business Modules
bx1, by1, bx2, by2 = 435, 332, 1060, 640
group_box(bx1, by1, bx2, by2, "Business Modules")
for box in [
    (475, 382, 1020, 468, "Operations\nCarbon · Waste · Reports", "biz"),
    (475, 478, 1020, 564, "Governance\nESG · Policy · Compliance", "biz"),
    (475, 574, 1020, 628, "Monitoring\nAlerts · Anomaly · Audit", "biz"),
]:
    x1, y1, x2, y2, text, kind = box
    rounded_box(x1, y1, x2, y2, COLORS[kind], COLORS["border"])
    center_text((x1, y1, x2, y2), text, text_font)

# Support
sx1, sy1, sx2, sy2 = 1090, 332, 1405, 640
group_box(sx1, sy1, sx2, sy2, "Support")
for box in [
    (1122, 388, 1372, 478, "Auth & RBAC", "sup"),
    (1122, 502, 1372, 592, "OCR & AI\nService", "sup"),
]:
    x1, y1, x2, y2, text, kind = box
    rounded_box(x1, y1, x2, y2, COLORS[kind], COLORS["border"])
    center_text((x1, y1, x2, y2), text, text_font)

# Layer 3
dx1, dy1, dx2, dy2 = 145, 720, 1355, 875
group_box(dx1, dy1, dx2, dy2, "Data & External Services")
for box in [
    (210, 775, 510, 855, "MySQL Database", "data"),
    (600, 775, 900, 855, "WeasyPrint ·\nFlask-Mail", "data"),
    (990, 775, 1290, 855, "OCR Libs ·\nAI API", "data"),
]:
    x1, y1, x2, y2, text, kind = box
    rounded_box(x1, y1, x2, y2, COLORS[kind], COLORS["border"])
    center_text((x1, y1, x2, y2), text, text_font)

# Main arrows
arrow(750, 225, 750, 280)
arrow(750, 675, 750, 720)

# Secondary subtle connectors
for x in [250, 750, 1250]:
    draw.line((x, 640, x, 675), fill=(180, 180, 180), width=2)
for x in [335, 750, 1140]:
    draw.line((x, 225, x, 280), fill=(180, 180, 180), width=2)

# Footer note

img.save("/Users/liuhaopu/Desktop/大三下课件/课设2/项目文件/docs/documentation/figures/system_architecture_compact.png")
print("saved")
