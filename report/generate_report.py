"""从 report/report_content.md 生成可复现的一页中文 PDF。"""
from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "report" / "report_content.md"
OUTPUT = ROOT / "output" / "pdf" / "DataCo供应链分析_一页结论.pdf"
MIRROR = ROOT / "report" / OUTPUT.name

NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#2F6690")
LIGHT_BLUE = colors.HexColor("#EAF2F8")
ORANGE = colors.HexColor("#E07A5F")
TEXT = colors.HexColor("#263238")
MUTED = colors.HexColor("#5F6B73")


def register_chinese_fonts() -> tuple[str, str]:
    candidates = [
        (Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/msyhbd.ttc")),
        (Path("C:/Windows/Fonts/simhei.ttf"), Path("C:/Windows/Fonts/simhei.ttf")),
        (Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"), Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")),
        (Path("/System/Library/Fonts/PingFang.ttc"), Path("/System/Library/Fonts/PingFang.ttc")),
    ]
    for regular, bold in candidates:
        if regular.exists():
            bold_path = bold if bold.exists() else regular
            pdfmetrics.registerFont(TTFont("SCRegular", str(regular)))
            pdfmetrics.registerFont(TTFont("SCBold", str(bold_path)))
            return "SCRegular", "SCBold"
    raise FileNotFoundError("未找到可用中文字体；请安装微软雅黑、黑体、Noto Sans CJK 或苹方。")


def inline_markup(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", escaped)
    return escaped


def parse_source() -> tuple[str, str, list[str], list[tuple[str, list[str]]]]:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    title = next(line[2:] for line in lines if line.startswith("# "))
    subtitle = next(line[2:] for line in lines if line.startswith("> "))
    metrics: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_bullets: list[str] = []
    in_metrics = False

    for line in lines:
        if line == "## 核心指标":
            in_metrics = True
            continue
        if line.startswith("## ") and line != "## 核心指标":
            if current_title is not None:
                sections.append((current_title, current_bullets))
            current_title = line[3:]
            current_bullets = []
            in_metrics = False
            continue
        if line.startswith("- "):
            if in_metrics:
                metrics.append(line[2:])
            elif current_title is not None:
                current_bullets.append(line[2:])
    if current_title is not None:
        sections.append((current_title, current_bullets))
    return title, subtitle, metrics, sections


def footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D8E1E8"))
    canvas.line(18 * mm, 12 * mm, A4[0] - 18 * mm, 12 * mm)
    canvas.setFont("SCRegular", 6.8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 8 * mm, "DataCo Smart Supply Chain｜教学模拟数据｜口径与限制详见 README")
    canvas.drawRightString(A4[0] - 18 * mm, 8 * mm, "可复现分析成果")
    canvas.restoreState()


def build() -> Path:
    regular, bold = register_chinese_fonts()
    title, subtitle, metrics, sections = parse_source()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title=title,
        author="DataCo Supply Chain Analysis",
    )
    styles = {
        "title": ParagraphStyle("Title", fontName=bold, fontSize=21, leading=25, textColor=NAVY),
        "subtitle": ParagraphStyle("Subtitle", fontName=regular, fontSize=9.3, leading=13, textColor=MUTED),
        "section": ParagraphStyle("Section", fontName=bold, fontSize=11.3, leading=14, textColor=BLUE, spaceAfter=2.2 * mm),
        "body": ParagraphStyle("Body", fontName=regular, fontSize=8.25, leading=11.2, textColor=TEXT, alignment=TA_LEFT, spaceAfter=1.3 * mm),
        "metric_value": ParagraphStyle("MetricValue", fontName=bold, fontSize=13, leading=15, textColor=NAVY, alignment=TA_LEFT),
        "metric_label": ParagraphStyle("MetricLabel", fontName=regular, fontSize=6.8, leading=8.5, textColor=MUTED, alignment=TA_LEFT),
    }

    story = [
        Paragraph(inline_markup(title), styles["title"]),
        Paragraph(inline_markup(subtitle), styles["subtitle"]),
        Spacer(1, 4 * mm),
    ]

    metric_cells = []
    for metric in metrics:
        value, label = metric.split("｜", 1)
        metric_cells.append([
            Paragraph(inline_markup(value), styles["metric_value"]),
            Paragraph(inline_markup(label), styles["metric_label"]),
        ])
    metric_table = Table([metric_cells], colWidths=[(A4[0] - 36 * mm) / len(metric_cells)] * len(metric_cells))
    metric_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D8E5")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C7D8E5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([metric_table, Spacer(1, 4.2 * mm)])

    for section_title, bullets in sections:
        block = [Paragraph(inline_markup(section_title), styles["section"])]
        for bullet in bullets:
            block.append(Paragraph("<font color='#E07A5F'>●</font> " + inline_markup(bullet), styles["body"]))
        block.append(Spacer(1, 2.2 * mm))
        story.append(KeepTogether(block))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    shutil.copy2(OUTPUT, MIRROR)
    print(f"[OK] 已生成 {OUTPUT.relative_to(ROOT)}，并同步到 {MIRROR.relative_to(ROOT)}")
    return OUTPUT


if __name__ == "__main__":
    build()

