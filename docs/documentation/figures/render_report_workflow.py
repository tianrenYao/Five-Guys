from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1060
BG = "white"

COLORS = {
    "title": (40, 40, 40),
    "subtitle": (110, 110, 110),
    "border": (110, 110, 110),
    "arrow": (90, 90, 90),
    "user": (218, 232, 252),       # blue-ish
    "query": (213, 232, 212),      # green-ish
    "process": (225, 213, 231),    # purple-ish
    "output": (248, 206, 204),     # red-ish
    "ai": (255, 242, 204),         # yellow-ish
    "white": (255, 255, 255),
}

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

try:
    title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 44)
    subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 24)
    step_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
    body_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 22)
    small_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 20)
except Exception:
    title_font = step_font = body_font = small_font = subtitle_font = ImageFont.load_default()


def measure(text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def rounded_box(x1, y1, x2, y2, fill, outline, radius=18, width=2):
    draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=fill, outline=outline, width=width)


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


def left_text_centered(box, title, lines, tfont, bfont, fill=COLORS["title"],
                       title_offset=10, body_start=40, line_gap=26):
    x1, y1, x2, y2 = box
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


def arrow_right(x1, y, x2, fill=COLORS["arrow"], width=4):
    draw.line((x1, y, x2, y), fill=fill, width=width)
    ah = 12
    draw.polygon([(x2, y), (x2 - ah, y - ah), (x2 - ah, y + ah)], fill=fill)


def arrow_down(x, y1, y2, fill=COLORS["arrow"], width=4):
    draw.line((x, y1, x, y2), fill=fill, width=width)
    ah = 12
    draw.polygon([(x, y2), (x - ah, y2 - ah), (x + ah, y2 - ah)], fill=fill)


def dashed_arrow_down(x, y1, y2, fill=(214, 182, 86), width=3):
    segs = max(int(abs(y2 - y1) / 12), 4)
    for j in range(segs):
        if j % 2 == 0:
            sy = y1 + (y2 - y1) * j / segs
            ey = y1 + (y2 - y1) * (j + 1) / segs
            draw.line((x, sy, x, ey), fill=fill, width=width)
    ah = 10
    draw.polygon([(x, y2), (x - ah, y2 - ah), (x + ah, y2 - ah)], fill=fill)


def label_on_arrow(text, x, y, fill=COLORS["arrow"]):
    tw, th = measure(text, small_font)
    draw.rounded_rectangle((x - tw / 2 - 5, y - th / 2 - 3,
                             x + tw / 2 + 5, y + th / 2 + 3), radius=6, fill=BG)
    draw.text((x - tw / 2, y - th / 2), text, font=small_font, fill=fill)


# ── Title ──
center_text((0, 15, W, 68), "Sustainability Reporting and PDF Export Workflow", title_font)
center_text((0, 68, W, 100), "From Data Selection to Downloadable Report", subtitle_font,
            fill=COLORS["subtitle"])

# ── Row 1: Trigger ──
# Step 1: User action
S1 = (60, 140, 380, 310)
rounded_box(*S1, COLORS["user"], COLORS["border"])
left_text_centered(S1, "1. User Request",
                   ["Manager / Admin selects", "a reporting period and", "triggers report generation"],
                   step_font, body_font, body_start=44, line_gap=28)

# Step 2: Query data
S2 = (480, 140, 820, 310)
rounded_box(*S2, COLORS["query"], COLORS["border"])
left_text_centered(S2, "2. Data Retrieval",
                   ["Query carbon_record and", "waste_record tables for", "the selected date range"],
                   step_font, body_font, body_start=44, line_gap=28)

# Step 3: Aggregation
S3 = (920, 140, 1280, 310)
rounded_box(*S3, COLORS["process"], COLORS["border"])
left_text_centered(S3, "3. Aggregation",
                   ["Summarise totals, averages,", "category breakdowns, and", "SDG 12 indicators"],
                   step_font, body_font, body_start=44, line_gap=28)

# Step 4: Store report
S4 = (1380, 140, 1860, 310)
rounded_box(*S4, COLORS["output"], COLORS["border"])
left_text_centered(S4, "4. Persist Report",
                   ["Store structured report as", "a database record for", "future listing and review"],
                   step_font, body_font, body_start=44, line_gap=28)

# Arrows row 1
arrow_right(S1[2], 225, S2[0])
arrow_right(S2[2], 225, S3[0])
arrow_right(S3[2], 225, S4[0])

# ── Row 2: Export path ──
# Step 5: Render HTML
S5 = (280, 420, 720, 590)
rounded_box(*S5, COLORS["process"], COLORS["border"])
left_text_centered(S5, "5. Render HTML Template",
                   ["Jinja2 template populates", "report content, tables,", "and chart placeholders"],
                   step_font, body_font, body_start=44, line_gap=28)

# Step 6: WeasyPrint
S6 = (820, 420, 1260, 590)
rounded_box(*S6, COLORS["output"], COLORS["border"])
left_text_centered(S6, "6. Generate PDF",
                   ["WeasyPrint converts the", "rendered HTML into a", "downloadable PDF file"],
                   step_font, body_font, body_start=44, line_gap=28)

# Step 7: Download
S7 = (1360, 420, 1700, 590)
rounded_box(*S7, COLORS["user"], COLORS["border"])
left_text_centered(S7, "7. User Download",
                   ["PDF served to browser", "for download, review,", "or external submission"],
                   step_font, body_font, body_start=44, line_gap=28)

# Arrow from Step 4 down to Step 5
mid4x = (S4[0] + S4[2]) // 2
arrow_down(mid4x, S4[3], S4[3] + 48)
# horizontal to S5
draw.line((mid4x, S4[3] + 48, S5[0] + 60, S4[3] + 48), fill=COLORS["arrow"], width=4)
arrow_down(S5[0] + 60, S4[3] + 48, S5[1])

arrow_right(S5[2], 505, S6[0])
arrow_right(S6[2], 505, S7[0])

# ── Row 3: AI commentary (optional) ──
AI_BOX = (280, 700, 720, 870)
rounded_box(*AI_BOX, COLORS["ai"], (214, 182, 86))
left_text_centered(AI_BOX, "Optional: AI Commentary",
                   ["External API generates", "narrative ESG insights;", "mock fallback for testing"],
                   step_font, body_font, body_start=44, line_gap=28)

# Dashed arrow from Step 5 bottom to AI box
mid5x = (S5[0] + S5[2]) // 2
dashed_arrow_down(mid5x, S5[3], AI_BOX[1])
label_on_arrow("optional enrichment", mid5x, (S5[3] + AI_BOX[1]) // 2, fill=(214, 182, 86))

# Dashed arrow from AI box right to Step 6 bottom
draw.line((AI_BOX[2], (AI_BOX[1] + AI_BOX[3]) // 2,
           (S6[0] + S6[2]) // 2, (AI_BOX[1] + AI_BOX[3]) // 2),
          fill=(214, 182, 86), width=3)
# dashed segments
mid6x = (S6[0] + S6[2]) // 2
ai_mid_y = (AI_BOX[1] + AI_BOX[3]) // 2
segs = 20
for j in range(segs):
    if j % 2 == 0:
        sx = AI_BOX[2] + (mid6x - AI_BOX[2]) * j / segs
        ex = AI_BOX[2] + (mid6x - AI_BOX[2]) * (j + 1) / segs
        draw.line((sx, ai_mid_y, ex, ai_mid_y), fill=(214, 182, 86), width=3)

# arrow head up from ai_mid_y to S6 bottom
segs2 = max(int((ai_mid_y - S6[3]) / 12), 4)
for j in range(abs(segs2)):
    if j % 2 == 0:
        sy = ai_mid_y - (ai_mid_y - S6[3]) * j / abs(segs2)
        ey = ai_mid_y - (ai_mid_y - S6[3]) * (j + 1) / abs(segs2)
        draw.line((mid6x, sy, mid6x, ey), fill=(214, 182, 86), width=3)
ah = 10
draw.polygon([(mid6x, S6[3]), (mid6x - ah, S6[3] + ah), (mid6x + ah, S6[3] + ah)],
             fill=(214, 182, 86))
label_on_arrow("inject commentary", mid6x + 80, (S6[3] + ai_mid_y) // 2, fill=(214, 182, 86))

# ── Database symbol on the side ──
DB = (1400, 700, 1700, 850)
rounded_box(*DB, (248, 206, 204), (184, 84, 80), radius=30)
left_text_centered(DB, "MySQL Database",
                   ["report table stores all", "generated report records"],
                   step_font, body_font, body_start=42, line_gap=26)

# dashed line from Step 4 to DB
mid4_bottom = (S4[0] + S4[2]) // 2 + 100
dashed_arrow_down(mid4_bottom, S4[3] + 10, DB[1], fill=(184, 84, 80))
label_on_arrow("persist", mid4_bottom, (S4[3] + 10 + DB[1]) // 2, fill=(184, 84, 80))

# ── Legend ──
LEG = (1400, 900, 1880, 1040)
rounded_box(*LEG, COLORS["white"], COLORS["border"], radius=14)
draw.text((1425, 912), "Legend", font=step_font, fill=COLORS["title"])
draw.line((1425, 956, 1490, 956), fill=COLORS["arrow"], width=4)
draw.polygon([(1490, 956), (1478, 946), (1478, 966)], fill=COLORS["arrow"])
draw.text((1505, 944), "Sequential flow", font=small_font, fill=COLORS["title"])
# dashed
segs = 8
for j in range(segs):
    if j % 2 == 0:
        sx = 1425 + (1490 - 1425) * j / segs
        ex = 1425 + (1490 - 1425) * (j + 1) / segs
        draw.line((sx, 996, ex, 996), fill=(214, 182, 86), width=3)
draw.polygon([(1490, 996), (1478, 986), (1478, 1006)], fill=(214, 182, 86))
draw.text((1505, 984), "Optional path", font=small_font, fill=COLORS["title"])

out_path = "/Users/liuhaopu/Desktop/大三下课件/课设2/项目文件/docs/documentation/figures/report_workflow.png"
img.save(out_path)
print(f"saved to {out_path}")
