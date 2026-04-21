from PIL import Image, ImageDraw, ImageFont
import math

W, H = 1920, 1100
BG = "white"

COLORS = {
    "title": (40, 40, 40),
    "subtitle": (110, 110, 110),
    "border": (110, 110, 110),
    "arrow": (90, 90, 90),
    "user": (218, 232, 252),
    "query": (213, 232, 212),
    "process": (225, 213, 231),
    "store": (248, 206, 204),
    "ai": (255, 242, 204),
    "white": (255, 255, 255),
}

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

try:
    title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 46)
    subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 27)
    step_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 28)
    body_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 24)
    small_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 21)
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
    sizes = [measure(l, font) for l in lines]
    total_h = sum(h for _, h in sizes) + spacing * (len(lines) - 1)
    cy = y1 + ((y2 - y1) - total_h) / 2
    for i, line in enumerate(lines):
        w, h = sizes[i]
        draw.text((x1 + ((x2 - x1) - w) / 2, cy), line, font=font, fill=fill)
        cy += h + spacing


def left_text_ac(box, title, lines, tfont, bfont, fill=COLORS["title"],
                 title_offset=12, body_start=48, line_gap=30):
    x1, y1, x2, y2 = box
    max_w = measure(title, tfont)[0]
    for l in lines:
        w = measure(l, bfont)[0]
        if w > max_w:
            max_w = w
    pad = max(((x2 - x1) - max_w) // 2, 10)
    draw.text((x1 + pad, y1 + title_offset), title, font=tfont, fill=fill)
    y = y1 + body_start
    for l in lines:
        draw.text((x1 + pad, y), l, font=bfont, fill=fill)
        y += line_gap


def arrow_h(x1, y, x2, fill=COLORS["arrow"], width=4):
    draw.line((x1, y, x2, y), fill=fill, width=width)
    ah = 12
    if x2 > x1:
        draw.polygon([(x2, y), (x2 - ah, y - ah), (x2 - ah, y + ah)], fill=fill)
    else:
        draw.polygon([(x2, y), (x2 + ah, y - ah), (x2 + ah, y + ah)], fill=fill)


def arrow_v(x, y1, y2, fill=COLORS["arrow"], width=4):
    draw.line((x, y1, x, y2), fill=fill, width=width)
    ah = 12
    if y2 > y1:
        draw.polygon([(x, y2), (x - ah, y2 - ah), (x + ah, y2 - ah)], fill=fill)
    else:
        draw.polygon([(x, y2), (x - ah, y2 + ah), (x + ah, y2 + ah)], fill=fill)


def dashed_line(x1, y1, x2, y2, fill=(214, 182, 86), width=3):
    length = math.hypot(x2 - x1, y2 - y1)
    segs = max(int(length / 14), 4)
    for j in range(segs):
        if j % 2 == 0:
            sx = x1 + (x2 - x1) * j / segs
            sy = y1 + (y2 - y1) * j / segs
            ex = x1 + (x2 - x1) * (j + 1) / segs
            ey = y1 + (y2 - y1) * (j + 1) / segs
            draw.line((sx, sy, ex, ey), fill=fill, width=width)


def dashed_arrow_v(x, y1, y2, fill=(214, 182, 86), width=3):
    dashed_line(x, y1, x, y2, fill, width)
    ah = 10
    if y2 > y1:
        draw.polygon([(x, y2), (x - ah, y2 - ah), (x + ah, y2 - ah)], fill=fill)
    else:
        draw.polygon([(x, y2), (x - ah, y2 + ah), (x + ah, y2 + ah)], fill=fill)


def dashed_arrow_h(x1, y, x2, fill=(214, 182, 86), width=3):
    dashed_line(x1, y, x2, y, fill, width)
    ah = 10
    if x2 > x1:
        draw.polygon([(x2, y), (x2 - ah, y - ah), (x2 - ah, y + ah)], fill=fill)
    else:
        draw.polygon([(x2, y), (x2 + ah, y - ah), (x2 + ah, y + ah)], fill=fill)


def label_bg(text, x, y, fill=COLORS["arrow"]):
    tw, th = measure(text, small_font)
    draw.rounded_rectangle((x - tw / 2 - 5, y - th / 2 - 3,
                             x + tw / 2 + 5, y + th / 2 + 3), radius=6, fill=BG)
    draw.text((x - tw / 2, y - th / 2), text, font=small_font, fill=fill)


# ── Title ──
center_text((0, 12, W, 70), "Sustainability Reporting and PDF Export Workflow", title_font)
center_text((0, 72, W, 108), "From Data Selection to Downloadable Report", subtitle_font,
            fill=COLORS["subtitle"])

# ── Layout: 3 rows x columns ──
# Row 1 (top): Steps 1–3
# Row 2 (mid): Steps 4–6
# Row 3 (bot): Step 7 + AI + DB

BW, BH = 400, 195   # box width, height
GX = 55              # gap between columns
R1Y = 140            # row 1 top
R2Y = 420            # row 2 top
R3Y = 700            # row 3 top

# Column x positions (3 columns)
C1L = 120
C2L = C1L + BW + GX
C3L = C2L + BW + GX

# ── Row 1 ──
S1 = (C1L, R1Y, C1L + BW, R1Y + BH)
rounded_box(*S1, COLORS["user"], COLORS["border"])
left_text_ac(S1, "1. User Request",
             ["Manager / Admin selects", "reporting period, triggers", "report generation"],
             step_font, body_font)

S2 = (C2L, R1Y, C2L + BW, R1Y + BH)
rounded_box(*S2, COLORS["query"], COLORS["border"])
left_text_ac(S2, "2. Data Retrieval",
             ["Query carbon_record and", "waste_record for the", "selected date range"],
             step_font, body_font)

S3 = (C3L, R1Y, C3L + BW, R1Y + BH)
rounded_box(*S3, COLORS["process"], COLORS["border"])
left_text_ac(S3, "3. Aggregation",
             ["Summarise totals, averages,", "category breakdowns, SDG", "12-related indicators"],
             step_font, body_font)

# Row 1 arrows
arrow_h(S1[2], R1Y + BH // 2, S2[0])
arrow_h(S2[2], R1Y + BH // 2, S3[0])

# ── Row 2 ──
S4 = (C1L, R2Y, C1L + BW, R2Y + BH)
rounded_box(*S4, COLORS["store"], COLORS["border"])
left_text_ac(S4, "4. Persist Report",
             ["Store structured report", "as a database record for", "future listing and review"],
             step_font, body_font)

S5 = (C2L, R2Y, C2L + BW, R2Y + BH)
rounded_box(*S5, COLORS["process"], COLORS["border"])
left_text_ac(S5, "5. Render HTML",
             ["Jinja2 template populates", "report content, tables,", "and chart placeholders"],
             step_font, body_font)

S6 = (C3L, R2Y, C3L + BW, R2Y + BH)
rounded_box(*S6, COLORS["store"], COLORS["border"])
left_text_ac(S6, "6. Generate PDF",
             ["WeasyPrint converts the", "rendered HTML into a", "downloadable PDF file"],
             step_font, body_font)

# Row 1→2 connector: S3 bottom → S4 top (wrap around)
mid3 = (S3[0] + S3[2]) // 2
arrow_v(mid3, S3[3], S3[3] + 30)
draw.line((mid3, S3[3] + 30, C1L - 30, S3[3] + 30), fill=COLORS["arrow"], width=4)
draw.line((C1L - 30, S3[3] + 30, C1L - 30, R2Y + BH // 2), fill=COLORS["arrow"], width=4)
arrow_h(C1L - 30, R2Y + BH // 2, S4[0])

# Row 2 arrows
arrow_h(S4[2], R2Y + BH // 2, S5[0])
arrow_h(S5[2], R2Y + BH // 2, S6[0])

# ── Row 3 ──
S7 = (C1L, R3Y, C1L + BW, R3Y + BH)
rounded_box(*S7, COLORS["user"], COLORS["border"])
left_text_ac(S7, "7. User Download",
             ["PDF served to browser", "for download, review, or", "external submission"],
             step_font, body_font)

AI = (C2L, R3Y, C2L + BW, R3Y + BH)
rounded_box(*AI, COLORS["ai"], (214, 182, 86))
left_text_ac(AI, "AI Commentary (optional)",
             ["External API generates", "narrative ESG insights;", "mock fallback for testing"],
             step_font, body_font)

DB = (C3L, R3Y, C3L + BW, R3Y + BH)
rounded_box(*DB, COLORS["store"], (184, 84, 80))
left_text_ac(DB, "MySQL Database",
             ["report table stores all", "generated report records", "as persistent artefacts"],
             step_font, body_font)

# S6 → S7 (wrap down-left)
mid6 = (S6[0] + S6[2]) // 2
arrow_v(mid6, S6[3], S6[3] + 30)
draw.line((mid6, S6[3] + 30, C1L - 30, S6[3] + 30), fill=COLORS["arrow"], width=4)
draw.line((C1L - 30, S6[3] + 30, C1L - 30, R3Y + BH // 2), fill=COLORS["arrow"], width=4)
arrow_h(C1L - 30, R3Y + BH // 2, S7[0])

# AI dashed: S5 bottom → AI top
mid5 = (S5[0] + S5[2]) // 2
dashed_arrow_v(mid5, S5[3], AI[1], fill=(214, 182, 86))
label_bg("optional enrichment", mid5 + 120, (S5[3] + AI[1]) // 2, fill=(214, 182, 86))

# AI → S6: route upward from AI top-right, then right, then up to S6 bottom
# go from AI top center-right up into the gap, then right to above S6, then down into S6
ai_exit_x = AI[2] - 50
gap_y = S5[3] + 18  # just below row 2 boxes
mid6x = (S6[0] + S6[2]) // 2 + 50
dashed_line(ai_exit_x, AI[1], ai_exit_x, gap_y, fill=(214, 182, 86))
dashed_line(ai_exit_x, gap_y, mid6x, gap_y, fill=(214, 182, 86))
dashed_arrow_v(mid6x, gap_y, S6[3], fill=(214, 182, 86))
label_bg("inject commentary", (ai_exit_x + mid6x) // 2, gap_y - 14, fill=(214, 182, 86))

# DB dashed: S4 right side → DB left side (horizontal path avoids vertical overlap)
mid4y = (S4[1] + S4[3]) // 2 + 30
db_midy = (DB[1] + DB[3]) // 2
dashed_line(S4[2], mid4y, S4[2] + 20, mid4y, fill=(184, 84, 80))
dashed_line(S4[2] + 20, mid4y, S4[2] + 20, R3Y + BH + 20, fill=(184, 84, 80))
dashed_line(S4[2] + 20, R3Y + BH + 20, DB[0] - 20, R3Y + BH + 20, fill=(184, 84, 80))
dashed_line(DB[0] - 20, R3Y + BH + 20, DB[0] - 20, db_midy, fill=(184, 84, 80))
dashed_arrow_h(DB[0] - 20, db_midy, DB[0], fill=(184, 84, 80))
label_bg("persist", (S4[2] + 20 + DB[0] - 20) // 2, R3Y + BH + 32, fill=(184, 84, 80))

# ── Legend ──
LX = 1500
LY = R3Y
rounded_box(LX, LY, LX + 380, LY + 195, COLORS["white"], COLORS["border"], radius=14)
draw.text((LX + 25, LY + 14), "Legend", font=step_font, fill=COLORS["title"])
# solid
draw.line((LX + 25, LY + 68, LX + 95, LY + 68), fill=COLORS["arrow"], width=4)
draw.polygon([(LX + 95, LY + 68), (LX + 83, LY + 58), (LX + 83, LY + 78)], fill=COLORS["arrow"])
draw.text((LX + 110, LY + 56), "Sequential flow", font=small_font, fill=COLORS["title"])
# dashed
dashed_line(LX + 25, LY + 108, LX + 95, LY + 108, fill=(214, 182, 86))
draw.polygon([(LX + 95, LY + 108), (LX + 83, LY + 98), (LX + 83, LY + 118)], fill=(214, 182, 86))
draw.text((LX + 110, LY + 96), "Optional / support", font=small_font, fill=COLORS["title"])
# persist
dashed_line(LX + 25, LY + 148, LX + 95, LY + 148, fill=(184, 84, 80))
draw.polygon([(LX + 95, LY + 148), (LX + 83, LY + 138), (LX + 83, LY + 158)], fill=(184, 84, 80))
draw.text((LX + 110, LY + 136), "Database persist", font=small_font, fill=COLORS["title"])

out_path = "/Users/liuhaopu/Desktop/大三下课件/课设2/项目文件/docs/documentation/figures/report_workflow.png"
img.save(out_path)
print(f"saved to {out_path}")
