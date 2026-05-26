#!/usr/bin/env python3
"""
Build blueprint-style PowerPoint for Nexus Global GTB.
Audience: CDO/CTO/CRO.
Visuals are schematic, no clip-art, no lorem ipsum.
"""

import json
import os
import math
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# ================== CONFIGS ==================

OUTLINE_PATH = "leadership-blueprint-outline-v2.json"
OUTPUT_PATH = "leadership-blueprint-presentation.pptx"

WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NAVY = RGBColor(0x00, 0x2B, 0x5B)
BLUE = RGBColor(0x1F, 0x73, 0xB7)
LIGHT_BLUE = RGBColor(0xD6, 0xE4, 0xF0)
ACCENT = RGBColor(0x3A, 0x9E, 0xDB)

FONT = "Arial"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
MARGIN = Inches(0.6)
VISUAL_TOP = Inches(3.1)
VISUAL_LEFT = MARGIN
VISUAL_W = Inches(6.6)
VISUAL_H = Inches(4.2)
VISUAL_RIGHT_TOP = Inches(4.3)
VISUAL_RIGHT_H = Inches(4.2)

# ================== HELPERS ==================

def load_outline(path=OUTLINE_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def make_slide(prs):
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    bg_fill = slide.background.fill
    bg_fill.solid()
    bg_fill.fore_color.rgb = WHITE

    # Top blue accent bar
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), SLIDE_W, Inches(0.22)
    )
    bar_fill = bar.fill
    bar_fill.solid()
    bar_fill.fore_color.rgb = NAVY
    bar.line.fill.background()

    # Left thin accent line
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0.22), Inches(0.12), SLIDE_H
    )
    line_fill = line.fill
    line_fill.solid()
    line_fill.fore_color.rgb = BLUE
    line.line.fill.background()

    return slide

def add_title(slide, text, x=MARGIN, y=Inches(0.45), w=Inches(8)):
    txBox = slide.shapes.add_textbox(x, y, w, Inches(0.55))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.font.name = FONT
    return txBox

def add_bullets(slide, bullets, x=MARGIN, y=Inches(1.1), w=Inches(6), bullet_size=14):
    txBox = slide.shapes.add_textbox(x, y, w, Inches(1.6))
    tf = txBox.text_frame
    tf.word_wrap = True

    first = True
    for b in bullets:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.text = b
        p.font.size = Pt(bullet_size)
        p.font.color.rgb = NAVY
        p.font.name = FONT
        p.space_before = Pt(2)
        p.space_after = Pt(1)
    return txBox

def add_label(slide, text, x, y, size=10, color=NAVY, bold=False):
    txBox = slide.shapes.add_textbox(x, y, Inches(2.5), Inches(0.3))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.name = FONT
    p.font.bold = bold
    return txBox

def add_box(slide, x, y, w, h, text, fill=BLUE, font_color=WHITE, font_size=9, center=True):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    sfill = shape.fill
    sfill.solid()
    sfill.fore_color.rgb = fill
    shape.line.color.rgb = NAVY
    shape.line.width = Pt(0.8)

    shape.text_frame.word_wrap = True
    tf = shape.text_frame
    tf.auto_size = None
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = font_color
    p.font.name = FONT
    p.alignment = PP_ALIGN.CENTER if center else PP_ALIGN.LEFT
    shape.text_frame.paragraphs[0].space_before = Pt(0)
    shape.text_frame.paragraphs[0].space_after = Pt(0)
    return shape

def add_rect(slide, x, y, w, h, fill=BLUE):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sfill = shape.fill
    sfill.solid()
    sfill.fore_color.rgb = fill
    shape.line.color.rgb = NAVY
    shape.line.width = Pt(0.5)
    return shape

def add_arrow(slide, x1, y1, x2, y2, color=NAVY, width=Pt(1.5)):
    def to_emu(v):
        if isinstance(v, int):
            return int(Emu(float(v)))
        if isinstance(v, float):
            return int(Emu(v))
        if isinstance(v, Emu) or hasattr(v, "emu"):
            return int(v)
        try:
            return int(Emu(v))
        except Exception:
            return int(Emu(0))

    cx1 = to_emu(x1)
    cy1 = to_emu(y1)
    cx2 = to_emu(x2)
    cy2 = to_emu(y2)

    connector = slide.shapes.add_connector(1, cx1, cy1, cx2, cy2)
    connector.line.color.rgb = color
    connector.line.width = width
    return connector

def add_grid_background(slide, spacing=Inches(0.35), alpha_color=LIGHT_BLUE):
    y = 0
    while y < SLIDE_H:
        y += spacing
        if y > SLIDE_H:
            break
        c = slide.shapes.add_connector(
            1,
            int(Emu(MARGIN)),
            int(Emu(y)),
            int(Emu(SLIDE_W - Inches(0.2))),
            int(Emu(y)),
        )
        c.line.color.rgb = alpha_color

    x = 0
    while x < SLIDE_W:
        x += spacing
        if x > SLIDE_W:
            break
        c = slide.shapes.add_connector(
            1,
            int(Emu(x)),
            int(Emu(Inches(0.5))),
            int(Emu(x)),
            int(Emu(SLIDE_H)),
        )
        c.line.color.rgb = alpha_color

# ================== VISUAL BUILDERS ==================

def visual_title_slide(slide):
    add_grid_background(slide)
    cx = Inches(6.6)
    ty = Inches(2.5)
    # Big title box (blue)
    add_box(
        slide,
        Inches(3.5),
        ty,
        Inches(6.3),
        Inches(0.6),
        "GLOBAL TRANSACTION BANKING PLATFORM",
        fill=NAVY,
        font_size=14,
    )
    add_label(slide, "End-to-End Architecture Blueprint", cx, Inches(3.2), size=11, color=NAVY)

def visual_four_pillars(slide):
    base_y = VISUAL_TOP
    box_w = Inches(1.4)
    box_h = Inches(0.9)
    gap = Inches(0.25)
    x0 = VISUAL_LEFT + Inches(0.1)

    labels = ["Canonical Graph (Neo4j)", "Kinetic Layer (PostgreSQL)", "Streaming (Confluent)", "Flink (Analytics & Decisions)"]
    for i, label in enumerate(labels):
        x = x0 + i * (box_w + gap)
        add_box(slide, x, base_y, box_w, box_h, label, fill=BLUE)
        # Underline bar
        add_rect(slide, x, base_y + box_h + Inches(0.05), box_w, Inches(0.04), fill=NAVY)
    # Center caption
    add_label(slide, "Four pillars of the platform", VISUAL_LEFT, base_y + box_h + Inches(0.25), size=9, bold=True)

def visual_ontology_graph(slide):
    cx = VISUAL_LEFT + Inches(3.2)
    cy = VISUAL_TOP + Inches(1.6)
    # Central node
    central = add_box(slide, cx - Inches(0.8), cy - Inches(0.2), Inches(1.6), Inches(0.5), "Canonical Graph", fill=NAVY)

    # Surrounding nodes
    nodes = [
        ("Party", -1.8, -0.8),
        ("Account", -0.8, -0.9),
        ("Product", 0.8, -0.9),
        ("Transaction", 1.8, -0.7),
        ("Mandate", -1.7, 0.7),
        ("Vendor / Containment Zone", 1.2, 0.8),
    ]

    for label, dx, dy in nodes:
        nx = cx + Inches(dx)
        ny = cy + Inches(dy)
        w = Inches(1.1) if "Vendor" not in label else Inches(1.6)
        add_box(slide, nx - w / 2, ny - Inches(0.18), w, Inches(0.36), label, fill=BLUE)
        # Line
        add_arrow(slide, cx, cy, nx, ny, color=BLUE)

def visual_stores_layout(slide):
    base_y = VISUAL_TOP
    box_w = Inches(2.6)
    box_h = Inches(0.8)
    gap = Inches(0.2)

    # 2x2 grid
    stores = [
        "Neo4j\n(Operational Graph)",
        "PostgreSQL\n(Kinetic + Mandates)",
        "Delta Lake\n(Analytics + History)",
        "Redis\n(Hot Cache)"
    ]

    boxes = []
    for i in range(4):
        row = i // 2
        col = i % 2
        x = VISUAL_LEFT + col * (box_w + gap)
        y = base_y + row * (box_h + gap)
        boxes.append(add_box(slide, x, y, box_w, box_h, stores[i], fill=BLUE))

    # CDC arrows: from Neo4j/PG to Confluent symbol (top center)
    cdc = add_box(slide, VISUAL_LEFT + Inches(1.3), base_y - Inches(0.4), Inches(1.6), Inches(0.3), "CDC (Confluent)", fill=NAVY)

def visual_platform_layers(slide):
    base_y = VISUAL_TOP
    w = Inches(5.5)
    h = Inches(0.55)
    x0 = VISUAL_LEFT + Inches(0.2)

    layers = [
        "APIs / LOB Integrations",
        "Entity Platform API + Async Topics (Confluent)",
        "Flink on K8s (Stream Processing)",
        "Core Stores: Neo4j / PostgreSQL / Delta Lake / Redis",
        "Azure Infrastructure + Governance"
    ]

    for i, label in enumerate(layers):
        y = base_y + i * (h + Inches(0.06))
        add_box(slide, x0, y, w, h, label, fill=BLUE)

    # Right annotation
    add_label(slide, "Layered, governed stack", VISUAL_LEFT + Inches(6), base_y, size=9)

def visual_api_async_flow(slide):
    base_y = VISUAL_TOP + Inches(0.2)
    api = add_box(slide, VISUAL_LEFT, base_y, Inches(1.7), Inches(0.5), "Entity Platform API", fill=NAVY)
    canonical = add_box(slide, VISUAL_LEFT + Inches(2.1), base_y, Inches(1.7), Inches(0.5), "Canonical (Neo4j/PG)", fill=BLUE)
    kinetic = add_box(slide, VISUAL_LEFT + Inches(4.2), base_y, Inches(1.7), Inches(0.5), "Kinetic + Proof", fill=BLUE)

    # Arrow API -> Canonical
    add_arrow(slide, api.left + api.width, api.top + api.height / 2, canonical.left, canonical.top + canonical.height / 2)
    # Arrow Canonical -> Kinetic
    add_arrow(slide, canonical.left + canonical.width, canonical.top + canonical.height / 2, kinetic.left, kinetic.top + kinetic.height / 2)

    # Confluent box with async arrows
    confluent = add_box(slide, VISUAL_LEFT + Inches(2.1), base_y + Inches(0.8), Inches(1.7), Inches(0.5), "Confluent Cloud", fill=NAVY)

    # Arrows down to async consumers
    c1 = add_box(slide, VISUAL_LEFT, base_y + Inches(1.6), Inches(1.4), Inches(0.4), "LOB Systems", fill=BLUE)
    c2 = add_box(slide, VISUAL_LEFT + Inches(2.5), base_y + Inches(1.6), Inches(1.4), Inches(0.4), "Flink / Analytics", fill=BLUE)
    c3 = add_box(slide, VISUAL_LEFT + Inches(5), base_y + Inches(1.6), Inches(1.5), Inches(0.4), "Governance / Audit", fill=BLUE)

    add_arrow(slide, confluent.left, confluent.top + confluent.height, c1.left, c1.top)
    add_arrow(slide, confluent.left + confluent.width / 2, confluent.top + confluent.height, c2.left, c2.top)
    add_arrow(slide, confluent.left + confluent.width, confluent.top + confluent.height, c3.left, c3.top)

def visual_mandate_hierarchy(slide):
    base_y = VISUAL_TOP
    x = VISUAL_LEFT + Inches(1.5)

    human = add_box(slide, x, base_y, Inches(1.6), Inches(0.5), "HumanMandate", fill=NAVY)
    system = add_box(slide, x, base_y + Inches(0.65), Inches(1.6), Inches(0.5), "SystemMandate", fill=BLUE)
    agent = add_box(slide, x, base_y + Inches(1.3), Inches(1.6), Inches(0.5), "AgentMandate", fill=BLUE)

    # Vertical arrows
    add_arrow(slide, human.left + human.width / 2, human.top + human.height, system.left + system.width / 2, system.top)
    add_arrow(slide, system.left + system.width / 2, system.top + system.height, agent.left + agent.width / 2, agent.top)

    # Proof registry
    pr = add_box(slide, VISUAL_LEFT + Inches(3.8), base_y + Inches(0.8), Inches(1.9), Inches(0.9), "Proof Registry\nAppend-only / SHA-256", fill=NAVY)

    # Arrow from hierarchy to Proof
    add_arrow(slide, system.left + system.width, system.top + system.height / 2, pr.left, pr.top + pr.height / 2)

def visual_flink_roles(slide):
    base_y = VISUAL_TOP
    confluent = add_box(slide, VISUAL_LEFT, base_y, Inches(1.6), Inches(0.5), "Confluent Cloud", fill=NAVY)
    flink = add_box(slide, VISUAL_LEFT + Inches(2.0), base_y, Inches(1.6), Inches(0.5), "Flink on K8s", fill=BLUE)

    add_arrow(slide, confluent.left + confluent.width, confluent.top + confluent.height / 2, flink.left, flink.top + flink.height / 2)

    roles = [
        "Stream joins",
        "CEP / Alerts",
        "Forecasts",
        "Liquidity signals"
    ]
    rx = VISUAL_LEFT + Inches(4.0)
    for i, role in enumerate(roles):
        y = base_y - Inches(0.1) + i * Inches(0.5)
        add_box(slide, rx, y, Inches(1.7), Inches(0.4), role, fill=BLUE)
        add_arrow(slide, flink.left + flink.width, flink.top + i * Inches(0.12), rx, y + Inches(0.2))

def visual_reporting_flow(slide):
    base_y = VISUAL_TOP
    src = add_box(slide, VISUAL_LEFT, base_y, Inches(1.5), Inches(0.5), "Events", fill=NAVY)
    flink = add_box(slide, VISUAL_LEFT + Inches(1.8), base_y, Inches(1.8), Inches(0.5), "Flink (Aggregation)", fill=BLUE)
    delta = add_box(slide, VISUAL_LEFT + Inches(3.9), base_y, Inches(2.0), Inches(0.5), "Delta Lake (Reports)", fill=BLUE)

    add_arrow(slide, src.left + src.width, src.top, flink.left, flink.top)
    add_arrow(slide, flink.left + flink.width, flink.top, delta.left, delta.top)

    add_label(slide, "BCBS-239 aligned reporting", VISUAL_LEFT, base_y + Inches(0.8), size=9)

def visual_statements_flow(slide):
    base_y = VISUAL_TOP
    events = add_box(slide, VISUAL_LEFT, base_y, Inches(1.6), Inches(0.5), "Payments + Ledger", fill=NAVY)
    flink = add_box(slide, VISUAL_LEFT + Inches(1.9), base_y, Inches(1.9), Inches(0.5), "Flink (Statement Engine)", fill=BLUE)
    stmts = add_box(slide, VISUAL_LEFT + Inches(4.1), base_y, Inches(1.8), Inches(0.5), "Statements", fill=BLUE)

    add_arrow(slide, events.left + events.width, events.top, flink.left, flink.top)
    add_arrow(slide, flink.left + flink.width, flink.top, stmts.left, stmts.top)

    add_label(slide, "Per-entity, ordered, idempotent", VISUAL_LEFT, base_y + Inches(0.8), size=9)

def visual_forecast_timeline(slide):
    base_y = VISUAL_TOP + Inches(0.6)
    horizon = add_rect(slide, VISUAL_LEFT, base_y, Inches(5.5), Inches(0.04), fill=NAVY)
    flink = add_box(slide, VISUAL_LEFT, VISUAL_TOP, Inches(1.5), Inches(0.4), "Flink", fill=BLUE)

    labels = ["T+0", "T+1", "T+7", "T+30"]
    for i, label in enumerate(labels):
        x = VISUAL_LEFT + Inches(1.0) + i * Inches(1.2)
        add_label(slide, label, x, base_y + Inches(0.15), size=9, bold=True)
        # Small tick
        add_rect(slide, x + Inches(0.1), base_y - Inches(0.06), Inches(0.04), Inches(0.16), fill=NAVY)

    add_arrow(slide, flink.left + flink.width / 2, flink.top + flink.height, VISUAL_LEFT + Inches(2.5), horizon.top, color=BLUE)

def visual_liquidity_gauge(slide):
    base_y = VISUAL_TOP + Inches(0.3)
    meter = add_box(slide, VISUAL_LEFT, base_y, Inches(5.5), Inches(0.6), "Liquidity Position Meter", fill=WHITE)
    meter.line.color.rgb = NAVY

    # Threshold lines
    for i in range(4):
        x = VISUAL_LEFT + Inches(1.0) + i * Inches(1.1)
        add_rect(slide, x, base_y - Inches(0.05), Inches(0.04), Inches(0.7), fill=BLUE)

    labels = ["Critical", "Warning", "OK", "Strong"]
    for i, label in enumerate(labels):
        x = VISUAL_LEFT + Inches(1.0) + i * Inches(1.1)
        add_label(slide, label, x, base_y + Inches(0.75), size=8)

def visual_end_to_end_diagram(slide):
    # Big blueprint diagram for this slide.
    # Two-column, full-slide schematic.

    # Left column
    left_x = MARGIN
    left_y = VISUAL_TOP
    left_w = Inches(5.9)

    # Right column
    right_x = left_x + left_w + Inches(0.3)
    right_w = Inches(4.7)

    # Left: Canonical + Kinetic + Infra

    canonical = add_box(slide, left_x, left_y, left_w, Inches(0.5), "Canonical Graph (Neo4j) + Kinetic (PostgreSQL)", fill=NAVY)
    proof = add_box(slide, left_x, left_y + Inches(0.6), Inches(2.2), Inches(0.4), "Proof Registry", fill=BLUE)
    cache = add_box(slide, left_x + Inches(2.4), left_y + Inches(0.6), Inches(2.2), Inches(0.4), "Redis (Hot Cache)", fill=BLUE)

    # Streaming layer
    streaming = add_box(slide, left_x, left_y + Inches(1.2), left_w, Inches(0.5), "Confluent Cloud (Streaming Backbone)", fill=NAVY)

    # Flink
    flink = add_box(slide, left_x, left_y + Inches(1.85), left_w, Inches(0.5), "Flink on K8s (Real-Time Intelligence)", fill=BLUE)

    # Analytics
    analytics = add_box(slide, left_x, left_y + Inches(2.5), left_w, Inches(0.5), "Delta Lake (Analytics, History, Regulatory)", fill=BLUE)

    # Vertical flow
    add_arrow(slide, canonical.left + canonical.width / 2, canonical.top + canonical.height, streaming.left + streaming.width / 2, streaming.top)
    add_arrow(slide, streaming.left + streaming.width / 2, streaming.top + streaming.height, flink.left + flink.width / 2, flink.top)
    add_arrow(slide, flink.left + flink.width / 2, flink.top + flink.height, analytics.left + analytics.width / 2, analytics.top)

    # Right: API, integrations, governance

    api = add_box(slide, right_x, left_y, right_w, Inches(0.5), "Entity Platform API + Async Topics", fill=NAVY)
    add_arrow(slide, api.left, api.top + api.height / 2, canonical.left + canonical.width, canonical.top + canonical.height / 2)

    lob = add_box(slide, right_x, left_y + Inches(0.65), Inches(2.1), Inches(0.5), "LOB Systems", fill=BLUE)
    partners = add_box(slide, right_x + Inches(2.3), left_y + Inches(0.65), Inches(2.1), Inches(0.5), "Partners / Vendors", fill=BLUE)

    governance = add_box(slide, right_x, left_y + Inches(1.4), right_w, Inches(0.5), "Governance, Mandates & Audit Logs", fill=BLUE)

    # Connect api to lob and partners
    add_arrow(slide, api.left, api.top + api.height, lob.left, lob.top)
    add_arrow(slide, api.left + api.width, api.top + api.height, partners.left, partners.top)

    # Flink to governance
    add_arrow(slide, flink.left + flink.width, flink.top, governance.left, governance.top)

    # Analytics label
    add_label(slide, "Integrated, governance-hardened", left_x, left_y + Inches(3.2), size=9, bold=True)

def visual_flywheel(slide):
    base_y = VISUAL_TOP + Inches(0.4)
    cx = VISUAL_LEFT + Inches(2.7)
    cy = base_y + Inches(1.4)

    # Center
    add_box(slide, cx - Inches(0.6), cy - Inches(0.18), Inches(1.2), Inches(0.4), "Platform", fill=NAVY)

    # Nodes around circle
    labels = [
        "Ontology",
        "Kinetic",
        "Streaming / Flink",
        "Governance",
    ]
    r = Inches(1.8)
    nodes = []
    for i, label in enumerate(labels):
        angle = -math.pi / 2 + i * (2 * math.pi / len(labels))
        x = cx + float(r) * math.cos(angle) - Inches(0.5)
        y = cy + float(r) * math.sin(angle) - Inches(0.15)
        box = add_box(slide, x, y, Inches(1.0), Inches(0.3), label, fill=BLUE)
        nodes.append((box.left + box.width / 2, box.top + box.height / 2))

    # Connectors in cycle
    for i in range(len(nodes)):
        x1, y1 = nodes[i]
        x2, y2 = nodes[(i + 1) % len(nodes)]
        add_arrow(slide, x1, y1, x2, y2, color=BLUE)
    # One arrow from last node back to first
    # already handled by cycle

    add_label(slide, "Continuous improvement flywheel", VISUAL_LEFT, base_y + Inches(2.8), size=9, bold=True)

VISUAL_MAP = {
    "title_slide": visual_title_slide,
    "four_pillars": visual_four_pillars,
    "ontology_graph": visual_ontology_graph,
    "stores_layout": visual_stores_layout,
    "platform_layers": visual_platform_layers,
    "api_async_flow": visual_api_async_flow,
    "mandate_hierarchy": visual_mandate_hierarchy,
    "flink_roles": visual_flink_roles,
    "reporting_flow": visual_reporting_flow,
    "statements_flow": visual_statements_flow,
    "forecast_timeline": visual_forecast_timeline,
    "liquidity_gauge": visual_liquidity_gauge,
    "end_to_end_diagram": visual_end_to_end_diagram,
    "flywheel": visual_flywheel,
}

# ================== MAIN ==================

def build():
    outline = load_outline()
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # Remove default layouts that we don't need (optional; kept for compatibility)
    for slide_info in outline["slides"]:
        slide = make_slide(prs)
        title = slide_info["title"]
        bullets = slide_info.get("bullets", [])
        visual_type = slide_info.get("visual")

        add_title(slide, title)
        if bullets:
            add_bullets(slide, bullets)

        builder = VISUAL_MAP.get(visual_type)
        if builder:
            builder(slide)

    prs.save(OUTPUT_PATH)
    print(f"Saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    # Ensure we run from script directory for path consistency
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    build()
