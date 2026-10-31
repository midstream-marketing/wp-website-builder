"""
blocks_elite.py — Elite Property Network: the "secure terminal" family.

Built 2026-09-11 from the client's written blueprint ("Page 1 - The AML
Funnel.docx", final MASTER LANDING PAGE BLUEPRINT). The blueprint specifies
every section's layout, grounds and visual, so these factories MATCH it rather
than interpret it — see clients/elite-property/design-spec.json, which names
each device and the stock block it displaces.

    ep.brandbar     slim wordmark bar (the blueprint has no header at all)
    ep.hero         §1  60/40 split, pill eyebrow, massive H1, scan card
    ep.bridge       §2  obsidian vault section with the data-pipeline diagram
    ep.steps        §3  three steps with ghost monospace numerals
    ep.compare      §4  franchise vs. wholesale grid, highlighted column
    ep.pricing      §5  three tiers, dark heading block on the middle card
    ep.ledger       §6  two-column tech ledger with a sticky index
    ep.final        §7  obsidian closing CTA, largest button on the page
    ep.footer       §8  black four-column footer, built into the page
    ep.countryjoin  join page: one button per country -> that country's form
    ep.simplehero   join page opener

Two things people assume need an image or custom CSS, and do not:

  * The HERO SCAN CARD and the BRIDGE DIAGRAM are containers, not pictures —
    a progress track with a 99% fill, an avatar circle, field rows, a status
    pill; three nodes joined by a glowing bar. They recolour with the palette,
    stay sharp at any width, and cannot 404 on import. The reviewer comment in
    the client's doc asks for software to "look physical, substantial, and
    real"; a drawn interface does that without inventing a screenshot of a
    product nobody has shown us.
  * Semantic status colours (green PASSED, red WARNING) come from the brand's
    `extra_colors`, added to tokens.py for this client. Borrowing the orange
    CTA colour for a status would make an action and a verdict look alike.

The MONOSPACE face is inline typography in exactly two devices — the ghost
step numerals and the ledger labels — because the blueprint names a mono face
for those two places only. Adding it to the global type scale would change
every other kit's tokens for one client's two details.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, link,
    gap, color_ref, typo_ref, icon,
)
from .tokens import C, T
from .blocks import block, _row, _col, _tracks, _button, KIT_CONTAINER

# Stable ids from clients/elite-property/intake.json -> brand.extra_colors.
X = {
    "pass": "succ016", "pass_tint": "sutn017", "pass_dark": "sudk018",
    "warn": "warn019", "warn_tint": "wrtn020", "black": "blk0021",
    "ghost": "ghst022", "soft": "dkmu023", "glow": "glow024",
    "panel": "pnel025",
}

EP_PAD = dims(104, 0, 104, 0)
EP_PAD_T = dims(72, 24, 72, 24)
EP_PAD_M = dims(56, 20, 56, 20)
R_EP = box(12)
MONO = "JetBrains Mono"

# Blue-tinted shadow for the two "highlighted" objects the blueprint names
# (the Elite comparison column's head and the middle pricing card). Colour is
# a literal inside the shadow control, which is how Elementor stores it.
BLUE_SHADOW = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 18, "blur": 44,
                              "spread": -12,
                              "color": "rgba(0, 122, 255, 0.28)"},
}
SOFT_SHADOW = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {"horizontal": 0, "vertical": 24, "blur": 60,
                              "spread": -18,
                              "color": "rgba(11, 15, 25, 0.18)"},
}


# ───────────────────────────── primitives ─────────────────────────────

def _sec(children, bg="white", pad=None, extra=None):
    grounds = {"white": C["white"], "grey": C["surface"],
               "dark": "secondary", "black": X["black"]}
    s = {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column", "flex_gap": gap(40),
        "padding": pad or EP_PAD, "padding_tablet": EP_PAD_T,
        "padding_mobile": EP_PAD_M,
        "background_background": "classic",
    }
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref(grounds.get(bg, C["white"]))})


def _h(text, size="h2", token="primary", color="secondary", align="left"):
    """Heading. `token` defaults to the kit's mixed-case Heading step: the
    section-title token is UPPERCASE, which is unreadable on this blueprint's
    sentence-length headlines."""
    return widget("heading", {"title": text, "header_size": size,
                              "align": align},
                  globals_={"title_color": color_ref(color),
                            "typography_typography": typo_ref(token)})


def _p(html, color="text", small=False, align="left"):
    return widget("text-editor", {
        "editor": html if html.strip().startswith("<") else f"<p>{html}</p>",
        "align": align,
    }, globals_={"text_color": color_ref(color),
                 "typography_typography": typo_ref(
                     T["body_small"] if small else "text")})


def _mono(text, size=12, color=None, weight="600", spacing=1.2,
          align="left", tag="div", transform="uppercase"):
    """Monospace label — inline typography, see the module docstring."""
    return widget("heading", {
        "title": text, "header_size": tag, "align": align,
        "typography_typography": "custom",
        "typography_font_family": MONO,
        "typography_font_size": slider(size),
        "typography_font_weight": weight,
        "typography_letter_spacing": slider(spacing),
        "typography_line_height": slider(1.3, "em"),
        "typography_text_transform": transform,
    }, globals_={"title_color": color_ref(color or C["ink_primary"])})


def _pill(text, fg, bg, icon_cls=None, size=11):
    """Inline pill. A heading widget sized `_element_width: auto` shrinks to
    its label, which a container cannot be told to do."""
    label = text.upper()
    return widget("heading", {
        "title": (f'<i class="{icon_cls}"></i>&nbsp; ' if icon_cls else "")
                 + label,
        "header_size": "div", "align": "left",
        "_element_width": "auto",
        "_padding": dims(6, 14, 6, 14),
        "_border_radius": box(100),
        "_background_background": "classic",
        "typography_typography": "custom",
        "typography_font_size": slider(size),
        "typography_font_weight": "800",
        "typography_letter_spacing": slider(1.4),
        "typography_text_transform": "uppercase",
        "typography_line_height": slider(1.3, "em"),
    }, globals_={"title_color": color_ref(fg),
                 "_background_color": color_ref(bg)})


def _cta(label, href, big=False):
    """The one action colour: orange fill, obsidian label (7.3:1)."""
    b = _button(label, href, "accent", "fas fa-arrow-right")
    b["settings"]["border_radius"] = box(8)
    if big:
        b["settings"]["text_padding"] = dims(24, 52, 24, 52)
        b["settings"]["text_padding_mobile"] = dims(18, 24, 18, 24)
    return b


def _ico(cls, color, size=18):
    return widget("icon", {"selected_icon": icon(cls), "size": slider(size),
                           "align": "left", "view": "default"},
                  globals_={"primary_color": color_ref(color)})


def _ticks(items, color, text_color="text", small=False):
    """Green status ticks instead of bullets — blueprint §2 and §5. Each item
    may carry a bold lead ("LEAD: rest") which is kept as the blueprint's own
    emphasis."""
    rows = []
    for it in items:
        lead, _, rest = it.partition(": ")
        txt = f"<strong>{lead}:</strong> {rest}" if rest else it
        rows.append(repeater_item(text=txt,
                                  selected_icon=icon("fas fa-check-circle"),
                                  link=link("")))
    return widget("icon-list", {
        "icon_list": rows, "space_between": slider(14), "icon_size": slider(16),
    }, globals_={"icon_color": color_ref(color),
                 "text_color": color_ref(text_color),
                 "icon_typography_typography": typo_ref(
                     T["body_small"] if small else "text")})


def _box(children, bg, extra=None, glob=None):
    s = {"content_width": "full", "flex_direction": "column",
         "flex_gap": gap(12), "background_background": "classic"}
    if extra:
        s.update(extra)
    g = {"background_color": color_ref(bg)}
    if glob:
        g.update(glob)
    return container(children, s, globals_=g)


# ─────────────────────────────── chrome ───────────────────────────────

@block("ep.brandbar")
def ep_brandbar(props):
    """A slim wordmark bar. NOT in the blueprint — which has no header at all —
    and added because a regulatory-trust page that opens with no name on it
    reads as anonymous. No navigation: this is a single-purpose landing page
    and every exit link costs conversions. One line in build_ir.py removes it."""
    mark = widget("heading", {"title": props["name"], "header_size": "div",
                              "align": "left"},
                  globals_={"title_color": color_ref("secondary"),
                            "typography_typography": typo_ref(T["h_small"])})
    link_ = _button(props["cta"]["label"], props["cta"]["href"], "ghost", None)
    link_["settings"]["border_radius"] = box(8)
    link_["settings"]["text_padding"] = dims(10, 18, 10, 18)
    w = _tracks([60, 40], 20)
    return container([_row([
        _col([mark], w[0], extra={"flex_justify_content": "center"}),
        _col([link_], w[1], extra={"flex_align_items": "flex-end",
                                   "flex_justify_content": "center"}),
    ], 20, align="center", extra={"flex_direction_mobile": "row"})], {
        "content_width": "boxed", "boxed_width": slider(KIT_CONTAINER),
        "flex_direction": "column",
        "padding": dims(16, 0, 16, 0), "padding_tablet": dims(14, 24, 14, 24),
        "padding_mobile": dims(12, 20, 12, 20),
        "border_border": "solid", "border_width": dims(0, 0, 1, 0),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})


# ──────────────────────────── §1 the hero ─────────────────────────────

def _scan_card(p):
    """The software mock-up — blueprint §1 right column, drawn in containers."""
    head = _row([
        _col([_mono(p.get("title", "Client identity scan"), 11,
                    C["muted"])], None),
        _col([_pill(p.get("live", "Live"), X["pass"], X["pass_tint"],
                    "fas fa-circle", 10)], None,
             extra={"flex_align_items": "flex-end"}),
    ], 12, align="center", extra={"flex_direction_mobile": "row",
                                  "flex_wrap": "nowrap"})

    avatar = container([_ico("fas fa-user", "primary", 26)], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center", "flex_align_items": "center",
        "width": slider(64), "min_height": slider(64),
        "border_radius": box(999), "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface_alt"])})
    who = _col([
        _h(p.get("subject", "Verifying client identity"), "div",
           T["h_small"], "secondary"),
        _mono(p.get("subject_meta", "Biometric + document match"), 11,
              C["muted"], "500", 0.4, transform="none"),
    ], None, extra={"flex_gap": gap(4), "flex_justify_content": "center"})
    ident = _row([avatar, who], 16, align="center",
                 extra={"flex_direction_mobile": "row", "flex_wrap": "nowrap"})

    fields = []
    for f in p.get("fields", []):
        fields.append(_row([
            _col([_p(f["label"], C["muted"], small=True)], None),
            _col([_mono(f["value"], 11, X["pass"], "700", 0.6)], None,
                 extra={"flex_align_items": "flex-end"}),
        ], 10, align="center", extra={
            "flex_direction_mobile": "row", "flex_wrap": "nowrap",
            "padding": dims(10, 0, 10, 0),
            "border_border": "solid", "border_width": dims(0, 0, 1, 0)}))
        fields[-1]["settings"]["__globals__"] = {
            "border_color": color_ref(C["border"])}

    pct = int(p.get("progress", 99))
    track = container([container([], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(pct, "%"), "min_height": slider(8),
        "border_radius": box(999), "background_background": "classic",
    }, globals_={"background_color": color_ref("primary")})], {
        "content_width": "full", "flex_direction": "row",
        "min_height": slider(8), "border_radius": box(999),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["border"])})
    progress = _col([
        _row([_col([_p(p.get("progress_label", "Scan progress"),
                       C["muted"], small=True)], None),
              _col([_mono(f"{pct}%", 12, "secondary", "700")], None,
                   extra={"flex_align_items": "flex-end"})],
             10, align="center", extra={"flex_direction_mobile": "row",
                                        "flex_wrap": "nowrap"}),
        track,
    ], None, extra={"flex_gap": gap(8)})

    badge = _pill(p.get("badge", "Verification passed"), X["pass"],
                  X["pass_tint"], "fas fa-check-circle", 12)

    return _box([head, ident, container(fields, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(0)}), progress, badge], C["white"], extra={
        "flex_gap": gap(20),
        "padding": dims(28, 28, 30, 28),
        "padding_mobile": dims(22, 18, 24, 18),
        "border_radius": box(16),
        "border_border": "solid", "border_width": box(1),
        **SOFT_SHADOW,
    }, glob={"border_color": color_ref(C["border"])})


@block("ep.hero")
def ep_hero(props):
    """Blueprint §1: 60/40, text left, the scan card right; stacks on mobile.

    The H1 is the blueprint's own line with ONE word added — see
    build_ir.py: the client's separate SEO directive requires the primary
    high-intent keyword in the H1, and 'Real Estate' is the part of
    'Australian real estate AML compliance software' the blueprint's line was
    missing. The directive is the later and more specific instruction."""
    left = [_pill(props["eyebrow"], C["ink_primary"], C["surface_alt"])]
    left.append(_h(props["h1"], "h1", T["hero"], "secondary"))
    if props.get("sub"):
        left.append(_p(f"<strong>{props['sub']}</strong>", "secondary"))
    if props.get("hook_title"):
        left.append(_h(props["hook_title"], "h2", T["h_small"], C["ink_primary"]))
    for para in props.get("hook", []):
        left.append(_p(para, "text", small=True))
    left.append(_cta(props["cta"]["label"], props["cta"]["href"]))
    if props.get("micro"):
        left.append(_mono(props["micro"], 11, C["muted"], "500", 0.6,
                          transform="none"))
    w = _tracks([60, 40], 48)
    return _sec([_row([
        _col(left, w[0], extra={"flex_gap": gap(20)}),
        _col([_scan_card(props.get("card", {}))], w[1],
             extra={"flex_justify_content": "center"}),
    ], 48, align="center")], "white", pad=dims(88, 0, 104, 0))


@block("ep.simplehero")
def ep_simplehero(props):
    """Join-page opener: pill, H1, one paragraph, centred."""
    inner = [_pill(props["eyebrow"], C["ink_primary"], C["surface_alt"]),
             _h(props["h1"], "h1", T["hero"], "secondary", "center")]
    for para in props.get("paras", []):
        inner.append(_p(para, "text", align="center"))
    return _sec([_col(inner, 76, extra={
        "flex_gap": gap(20), "flex_align_items": "center",
        "margin": dims(0, "auto", 0, "auto")})], "white",
        pad=dims(88, 0, 72, 0))


# ───────────────────────── §2 the vault bridge ─────────────────────────

def _bridge_diagram(p):
    """Blueprint §2 left column: brand node -> glowing bridge -> server stack."""
    def node(icon_cls, label, big=False):
        size = 92 if big else 68
        tile = container([_ico(icon_cls, C["white"], 34 if big else 24)], {
            "content_width": "full", "flex_direction": "column",
            "flex_justify_content": "center", "flex_align_items": "center",
            "width": slider(size), "min_height": slider(size),
            "border_radius": box(14),
            "border_border": "solid", "border_width": box(2),
            "background_background": "classic",
        }, globals_={"background_color": color_ref("secondary"),
                     "border_color": color_ref(X["glow"])})
        return [tile, _mono(label, 10, X["soft"], "600", 0.8,
                            align="center")]

    stack = []
    for _ in range(3):
        unit = container([_ico("fas fa-circle", X["pass_dark"], 7)], {
            "content_width": "full", "flex_direction": "row",
            "flex_justify_content": "flex-end", "flex_align_items": "center",
            "min_height": slider(22), "padding": dims(0, 10, 0, 10),
            "border_radius": box(5),
            "border_border": "solid", "border_width": box(1),
            "background_background": "classic",
        }, globals_={"background_color": color_ref("secondary"),
                     "border_color": color_ref(X["glow"])})
        stack.append(unit)
    server = container(stack, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(6), "width": slider(100, "%")})

    line = container([], {
        "content_width": "full", "flex_direction": "column",
        "min_height": slider(6), "border_radius": box(999),
        "background_background": "classic",
        "box_shadow_box_shadow_type": "yes",
        "box_shadow_box_shadow": {"horizontal": 0, "vertical": 0, "blur": 22,
                                  "spread": 2,
                                  "color": "rgba(0, 122, 255, 0.75)"},
    }, globals_={"background_color": color_ref(X["glow"])})

    w = _tracks([24, 44, 32], 10)
    col_a = _col(node(p.get("brand_icon", "fas fa-building"),
                      p.get("brand", "Your Independent Brand")), w[0],
                 extra={"flex_align_items": "center", "flex_gap": gap(10),
                        "width_mobile": slider(w[0], "%")})
    col_b = _col([
        _pill(p.get("status", "Encrypted Stream: Active"), X["pass_dark"],
              "secondary", "fas fa-lock", 9),
        line,
        _mono(p.get("bridge", "Secure API Data Bridge"), 10, X["soft"],
              "600", 0.8, align="center"),
    ], w[1], extra={"flex_align_items": "center", "flex_gap": gap(12),
                    "flex_justify_content": "center",
                    "width_mobile": slider(w[1], "%")})
    col_c = _col([server, _mono(p.get("mainframe",
                                      "Oxbridge Global Mainframe Backbone"),
                                10, X["soft"], "600", 0.8, align="center")],
                 w[2], extra={"flex_align_items": "center", "flex_gap": gap(10),
                              "width_mobile": slider(w[2], "%")})
    # The diagram stays a ROW on mobile: a pipeline drawn top-to-bottom stops
    # reading as brand -> bridge -> backbone.
    row = _row([col_a, col_b, col_c], 10, align="center",
               extra={"flex_direction_mobile": "row", "flex_wrap": "nowrap"})
    return _box([row], X["panel"], extra={
        "padding": dims(40, 26, 40, 26), "padding_mobile": dims(26, 12, 26, 12),
        "border_radius": box(16),
        "border_border": "solid", "border_width": box(1),
    }, glob={"border_color": color_ref(C["rule_dark"])})


@block("ep.bridge")
def ep_bridge(props):
    """Blueprint §2: obsidian ground, 45/55, diagram left, copy right."""
    right = [_h(props["heading"], "h2", "primary", C["white"])]
    for para in props.get("paras", []):
        right.append(_p(para, X["soft"]))
    if props.get("features"):
        right.append(_ticks(props["features"], X["pass_dark"], C["white"]))
    w = _tracks([45, 55], 56)
    return _sec([_row([
        _col([_bridge_diagram(props.get("diagram", {}))], w[0],
             extra={"flex_justify_content": "center"}),
        _col(right, w[1], extra={"flex_gap": gap(18)}),
    ], 56, align="center")], "dark")


# ─────────────────────────── §3 the steps ─────────────────────────────

@block("ep.steps")
def ep_steps(props):
    """Blueprint §3: three columns, each with a large semi-transparent
    monospace numeral BEHIND the text.

    The numeral is absolutely positioned in the card's top-right corner at
    14% blue, so it reads as a watermark behind the icon row and never sits
    under body copy — which keeps every paragraph at full contrast without
    relying on negative z-index stacking."""
    head = _col([
        *([_pill(props["eyebrow"], C["ink_primary"], C["surface_alt"])]
          if props.get("eyebrow") else []),
        _h(props["heading"], "h2", "primary", "secondary", "center"),
        *([_p(props["intro"], "text", align="center")]
          if props.get("intro") else []),
    ], 78, extra={"flex_gap": gap(14), "flex_align_items": "center",
                  "margin": dims(0, "auto", 16, "auto")})

    steps = props.get("steps", [])
    w = _tracks([1] * max(len(steps), 1), 24)[0]
    cards = []
    for i, st in enumerate(steps, 1):
        ghost = widget("heading", {
            "title": f"{i:02d}", "header_size": "div", "align": "right",
            "typography_typography": "custom",
            "typography_font_family": MONO,
            "typography_font_size": slider(104),
            "typography_font_size_mobile": slider(80),
            "typography_font_weight": "300",
            "typography_line_height": slider(1, "em"),
            "_position": "absolute",
            "_offset_orientation_h": "end", "_offset_x_end": slider(18),
            "_offset_orientation_v": "start", "_offset_y": slider(10),
            "_z_index": 0,
        }, globals_={"title_color": color_ref(X["ghost"])})
        cards.append(container([
            ghost,
            _ico(st.get("icon", "fas fa-circle"), "primary", 30),
            _h(st["title"], "h3", T["h_small"], "secondary"),
            _p(st["text"], "text", small=True),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(14),
            "width": slider(w, "%"), "width_mobile": slider(100, "%"),
            "padding": dims(34, 28, 34, 28),
            "border_radius": R_EP,
            "border_border": "solid", "border_width": box(1),
            "overflow": "hidden",
            "background_background": "classic",
        }, globals_={"background_color": color_ref(C["white"]),
                     "border_color": color_ref(C["border"])}))
    return _sec([head, _row(cards, 24, align="stretch")],
                props.get("bg", "grey"))


# ─────────────────────────── §4 the comparison ─────────────────────────

@block("ep.compare")
def ep_compare(props):
    """Blueprint §4 — the true-cost grid.

    Row by row, so a row's three cells are always level however much a cell
    wraps. The Elite column is continuous: every Elite cell carries the same
    2px blue side borders and the cells touch, so the column reads as one
    highlighted panel with the [ THE WHOLESALE ADVANTAGE ] tag at its head.
    The blueprint's box-shadow is applied to the column HEAD only — a shadow
    on every stacked cell draws a seam between rows.

    Held at three columns on mobile with smaller type: a comparison stacked
    into three lists stops being a comparison."""
    rows = props.get("rows", [])
    w = _tracks([30, 33, 37], 12)

    def cell(kids, width, bg=None, sides=False, top=False, bottom=False,
             shadow=False):
        s = {"content_width": "full", "flex_direction": "column",
             "flex_gap": gap(6), "width": slider(width, "%"),
             "width_tablet": slider(width, "%"),
             "width_mobile": slider(width, "%"),
             "padding": dims(18, 18, 18, 18),
             "padding_mobile": dims(12, 8, 12, 8)}
        g = {}
        if bg:
            s["background_background"] = "classic"
            g["background_color"] = color_ref(bg)
        if sides:
            s.update({"border_border": "solid",
                      "border_width": dims(2 if top else 0, 2,
                                           2 if bottom else 0, 2),
                      "border_radius": dims(12 if top else 0, 12 if top else 0,
                                            12 if bottom else 0,
                                            12 if bottom else 0)})
            g["border_color"] = color_ref("primary")
        if shadow:
            s.update(BLUE_SHADOW)
        return container(kids, s, globals_=g or None)

    def line(cells, rule=True):
        r = container(cells, {
            "content_width": "full", "flex_direction": "row",
            "flex_direction_mobile": "row", "flex_wrap": "nowrap",
            "flex_gap": gap(12), "flex_gap_mobile": gap(4),
            "flex_align_items": "stretch",
            **({"border_border": "solid",
                "border_width": dims(0, 0, 1, 0)} if rule else {}),
        })
        if rule:
            r["settings"]["__globals__"] = {
                "border_color": color_ref(C["border"])}
        return r

    head = line([
        cell([_mono(props.get("label_head", "Feature"), 11, C["muted"])], w[0]),
        cell([_h(props["franchise_head"], "h3", T["h_small"], C["muted"])],
             w[1], bg=X["warn_tint"]),
        cell([_pill(props["tag"], C["white"], "primary", None, 10),
              _h(props["elite_head"], "h3", T["h_small"], "secondary"),
              *([_p(props["elite_sub"], C["muted"], small=True)]
                if props.get("elite_sub") else [])],
             w[2], bg=C["white"], sides=True, top=True, shadow=True),
    ], rule=False)

    lines = [head]
    for n, r in enumerate(rows):
        last = n == len(rows) - 1
        lines.append(line([
            cell([_h(r["feature"], "div", T["h_small"], "secondary")], w[0]),
            cell([_row([_ico("fas fa-times-circle", X["warn"], 15),
                        _p(r["franchise"], "text", small=True)], 8,
                       align="flex-start",
                       extra={"flex_direction_mobile": "row",
                              "flex_wrap": "nowrap"})],
                 w[1], bg=X["warn_tint"]),
            cell([_row([_ico("fas fa-check-circle", X["pass"], 15),
                        _p(f"<strong>{r['elite']}</strong>", "secondary",
                           small=True)], 8, align="flex-start",
                       extra={"flex_direction_mobile": "row",
                              "flex_wrap": "nowrap"})],
                 w[2], bg=C["white"], sides=True, bottom=last),
        ], rule=not last))

    intro = _col([
        _h(props["heading"], "h2", "primary", "secondary", "center"),
        *([_p(props["intro"], "text", align="center")]
          if props.get("intro") else []),
    ], 78, extra={"flex_gap": gap(14), "flex_align_items": "center",
                  "margin": dims(0, "auto", 8, "auto")})
    table = container(lines, {"content_width": "full",
                              "flex_direction": "column", "flex_gap": gap(0)})
    kids = [intro, table]
    if props.get("footnote"):
        kids.append(_p(props["footnote"], C["muted"], small=True, align="center"))
    return _sec(kids, props.get("bg", "white"))


# ──────────────────────────── §5 the pricing ───────────────────────────

@block("ep.pricing")
def ep_pricing(props):
    """Blueprint §5 — three tiers; the middle one carries a DARK heading block
    inside a light card, the blue shadow border and the accent badge."""
    tiers = props.get("tiers", [])
    wd, wt = _tracks([1, 1, 1], 24)[0], 100
    cards = []
    for t in tiers:
        feat = t.get("featured", False)
        on = C["white"] if feat else "secondary"
        top = []
        if feat and props.get("badge"):
            top.append(_pill(props["badge"], C["on_accent"], C["accent_fill"],
                             None, 10))
        top += [
            _h(t["name"], "h3", T["h_small"], on),
            _h(t["price"], "div", T["hero"], on),
            _p(t.get("term", ""), X["soft"] if feat else C["muted"], small=True),
        ]
        heading = _box(top, "secondary" if feat else C["white"], extra={
            "flex_gap": gap(6), "padding": dims(26, 26, 22, 26),
            "border_radius": dims(10, 10, 0, 0)})
        body = container([
            _ticks(t.get("features", []), X["pass"], "text", small=True),
            _cta(t["cta"]["label"], t["cta"]["href"]),
        ], {"content_width": "full", "flex_direction": "column",
            "flex_gap": gap(22), "flex_justify_content": "space-between",
            "padding": dims(22, 26, 28, 26), "_flex_grow": 1})
        cards.append(container([heading, body], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(0),
            "width": slider(wd, "%"), "width_tablet": slider(wt, "%"),
            "width_mobile": slider(100, "%"),
            "border_radius": R_EP, "overflow": "hidden",
            "border_border": "solid", "border_width": box(2 if feat else 1),
            "background_background": "classic",
            **(BLUE_SHADOW if feat else {}),
        }, globals_={"background_color": color_ref(C["white"]),
                     "border_color": color_ref("primary" if feat
                                               else C["border"])}))

    intro = _col([
        _h(props["heading"], "h2", "primary", "secondary", "center"),
        *([_p(props["intro"], "text", align="center")]
          if props.get("intro") else []),
    ], 78, extra={"flex_gap": gap(14), "flex_align_items": "center",
                  "margin": dims(0, "auto", 8, "auto")})
    kids = [intro, _row(cards, 24, align="stretch")]
    if props.get("callout"):
        kids.append(_box([_row([
            _ico("fas fa-lightbulb", C["ink_primary"], 22),
            _p(props["callout"], "secondary", small=True),
        ], 14, align="flex-start", extra={"flex_direction_mobile": "row",
                                           "flex_wrap": "nowrap"})],
            C["surface_alt"], extra={"padding": dims(22, 26, 22, 26),
                                     "border_radius": R_EP}))
    return _sec(kids, props.get("bg", "white"),
                extra={"_element_id": props["anchor"]} if props.get("anchor")
                else None)


# ──────────────────────────── §6 the ledger ────────────────────────────

@block("ep.ledger")
def ep_ledger(props):
    """Blueprint §6 — the two-column tech ledger the client chose over an
    accordion ('option 2').

    The left column is Elementor Pro sticky (`sticky: top`, 40px offset,
    `sticky_parent` so it releases at the end of the section) — the
    blueprint's `position: sticky; top: 40px`, done with the builder's own
    control rather than CSS. Desktop only: on a phone the two columns stack,
    and a pinned block over stacked answers would cover them.

    The row is aligned to flex-START on purpose. A stretched column is already
    as tall as the section, so it has nowhere to stick."""
    index = []
    for it in props.get("items", []):
        index.append(container([_mono(it["label"], 11, C["ink_primary"])], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(12, 0, 12, 0),
            "border_border": "solid", "border_width": dims(0, 0, 1, 0)}))
        index[-1]["settings"]["__globals__"] = {
            "border_color": color_ref(C["border"])}

    left = container([
        _h(props["heading"], "h2", "primary", "secondary"),
        *([_p(props["intro"], "text")] if props.get("intro") else []),
        container(index, {"content_width": "full",
                          "flex_direction": "column", "flex_gap": gap(0),
                          "margin": dims(8, 0, 0, 0)}),
    ], {"content_width": "full", "flex_direction": "column",
        "flex_gap": gap(16),
        "width": slider(_tracks([38, 58], 56)[0], "%"),
        "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%"),
        "sticky": "top", "sticky_on": ["desktop"], "sticky_offset": 40,
        "sticky_parent": "yes"})

    blocks = []
    for it in props.get("items", []):
        blocks.append(container([
            _mono(it["label"], 11, C["ink_primary"]),
            _h(it["q"], "h3", T["h_small"], "secondary"),
            _p(it["a"], "text"),
        ], {"content_width": "full", "flex_direction": "column",
            "flex_gap": gap(10), "padding": dims(28, 0, 28, 0),
            "border_border": "solid", "border_width": dims(0, 0, 1, 0)}))
        blocks[-1]["settings"]["__globals__"] = {
            "border_color": color_ref(C["border"])}
    if props.get("vault"):
        v = props["vault"]
        blocks.append(_box([_row([
            _ico("fas fa-shield-alt", C["ink_primary"], 20),
            _col([_p(v["text"], "secondary", small=True),
                  widget("button", {
                      "text": v["label"], "link": link(v["href"]),
                      "text_padding": dims(0, 0, 0, 0),
                      "selected_icon": icon("fas fa-arrow-right"),
                      "icon_align": "right",
                  }, globals_={"button_text_color": color_ref(C["ink_primary"]),
                               "background_color": color_ref(C["transparent"]),
                               "typography_typography": typo_ref("accent")})],
                 None, extra={"flex_gap": gap(8)}),
        ], 14, align="flex-start", extra={"flex_direction_mobile": "row",
                                           "flex_wrap": "nowrap"})],
            C["surface_alt"], extra={"padding": dims(22, 24, 22, 24),
                                     "border_radius": R_EP,
                                     "margin": dims(16, 0, 0, 0)}))
    right = container(blocks, {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(0),
        "width": slider(_tracks([38, 58], 56)[1], "%"),
        "width_tablet": slider(100, "%"), "width_mobile": slider(100, "%")})

    return _sec([_row([left, right], 56, align="flex-start")],
                props.get("bg", "white"))


# ─────────────────────────── §7 the final CTA ──────────────────────────

@block("ep.final")
def ep_final(props):
    """Blueprint §7 — centred, obsidian, the largest button on the page."""
    anchors = widget("heading", {
        "title": " &nbsp;•&nbsp; ".join(props.get("anchors", [])),
        "header_size": "div", "align": "center",
        "typography_typography": "custom",
        "typography_font_size": slider(11),
        "typography_font_weight": "700",
        "typography_letter_spacing": slider(1.6),
        "typography_text_transform": "uppercase",
        "typography_line_height": slider(1.7, "em"),
    }, globals_={"title_color": color_ref(X["soft"])})
    inner = [
        _h(props["heading"], "h2", T["hero"], C["white"], "center"),
        _p(props.get("sub", ""), X["soft"], align="center"),
        container([_cta(props["cta"]["label"], props["cta"]["href"], big=True)],
                  {"content_width": "full", "flex_direction": "column",
                   "flex_align_items": "center", "margin": dims(10, 0, 4, 0)}),
        anchors,
    ]
    return _sec([_col(inner, 80, extra={
        "flex_gap": gap(20), "flex_align_items": "center",
        "margin": dims(0, "auto", 0, "auto")})], "dark",
        pad=dims(120, 0, 120, 0))


# ──────────────────────────── §8 the footer ────────────────────────────

@block("ep.footer")
def ep_footer(props):
    """Blueprint §8 — black, four columns of small muted type, in the page.

    Built into the page rather than as a Theme Builder footer: each sub-domain
    is a single-page site on the Elementor Canvas template, which renders no
    theme chrome at all."""
    def head(t):
        return _mono(t, 10, C["white"], "700", 1.4)

    def small(t, color=X["soft"]):
        return _p(t, color, small=True)

    def links(items):
        return widget("icon-list", {
            "icon_list": [repeater_item(text=i["text"], link=link(i["href"]),
                                        selected_icon={"value": "",
                                                       "library": ""})
                          for i in items],
            "space_between": slider(10),
        }, globals_={"text_color": color_ref(X["soft"]),
                     "icon_typography_typography": typo_ref(T["body_small"])})

    c = props
    col1 = [widget("heading", {"title": c["name"], "header_size": "div",
                               "align": "left"},
                   globals_={"title_color": color_ref(C["white"]),
                             "typography_typography": typo_ref(T["h_small"])})]
    col1 += [small(t) for t in c.get("status", [])]
    cols = [
        col1,
        [head(c["subdomains_head"]), links(c["subdomains"])],
        [head(c["legal_head"]), links(c["legal"])],
        [head(c["disclaimer_head"]), small(c["disclaimer"])],
    ]
    w = _tracks([24, 22, 24, 30], 32)
    row = _row([_col(k, w[i], extra={"flex_gap": gap(14)})
                for i, k in enumerate(cols)], 32, align="flex-start")
    base = container([small(c["copyright"])], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(24, 0, 0, 0),
        "border_border": "solid", "border_width": dims(1, 0, 0, 0)})
    base["settings"]["__globals__"] = {"border_color": color_ref(C["rule_dark"])}
    return _sec([row, base], "black", pad=dims(72, 0, 40, 0))


# ──────────────────────── join page: per-country ───────────────────────

@block("ep.countryjoin")
def ep_countryjoin(props):
    """One page, one button per country — the client's question about pages
    2 and 3, answered as a working device.

    Elementor Pro NESTED TABS: the three tab titles are the country buttons.
    Each panel holds a short form whose email SUBJECT and a HIDDEN field both
    carry the country, so a request lands in the Oxbridge Global Support
    inbox already labelled '[Australia] ...' and sortable by rule.

    Why a button opens a form rather than sending on its own: a bare button
    has nothing to send. Until the person gives a name and a way to reach
    them, the support team would receive 'someone in New Zealand clicked'.
    The country button still does exactly what was asked — it routes the
    request to the right country — it just collects the four fields that make
    the request actionable."""
    countries = props.get("countries", [])
    panels = []
    for ctry in countries:
        fields = [
            repeater_item(custom_id="full_name", field_type="text",
                          field_label="Full name", placeholder="Your full name",
                          required="true", width="50"),
            repeater_item(custom_id="email", field_type="email",
                          field_label="Email", placeholder="you@agency.com",
                          required="true", width="50"),
            repeater_item(custom_id="mobile", field_type="tel",
                          field_label="Mobile", placeholder=ctry["phone_hint"],
                          required="true", width="50"),
            repeater_item(custom_id="firm", field_type="text",
                          field_label="Agency or firm",
                          placeholder="Business name", required="", width="50"),
            repeater_item(custom_id="role", field_type="select",
                          field_label="Your role", required="true", width="100",
                          field_options="\n".join(props.get("roles", []))),
            repeater_item(custom_id="message", field_type="textarea",
                          field_label="Anything the support team should know?",
                          placeholder="Optional", required="", width="100",
                          rows=3),
            repeater_item(custom_id="country", field_type="hidden",
                          field_label="Country", field_value=ctry["name"],
                          width="100"),
        ]
        form = widget("form", {
            "form_name": f"Join request - {ctry['name']}",
            "form_fields": fields,
            "button_text": ctry["button"],
            "button_size": "md", "input_size": "md",
            "email_to": props.get("email", ""),
            "email_subject": f"[{ctry['name']}] Elite Property Network join request",
            "success_message": ctry["success"],
            "button_border_radius": box(8),
        }, globals_={"button_background_color": color_ref(C["accent_fill"]),
                     "button_text_color": color_ref(C["on_accent"]),
                     "field_text_color": color_ref("secondary")})
        panels.append(container([
            _h(ctry["title"], "h3", T["h_medium"], "secondary"),
            _p(ctry["text"], "text", small=True),
            form,
        ], {"content_width": "full", "flex_direction": "column",
            "flex_gap": gap(16), "padding": dims(32, 32, 34, 32),
            "padding_mobile": dims(22, 16, 24, 16)}))

    tabs = widget("nested-tabs", {
        "tabs": [repeater_item(tab_title=c["label"]) for c in countries],
        "tabs_justify_horizontal": "stretch",
        "tabs_title_space_between": slider(10),
        "tabs_title_spacing": slider(0),
        "tabs_title_border_radius": dims(10, 10, 0, 0),
        "tabs_title_background_color_background": "classic",
        "tabs_title_background_color_active_background": "classic",
        "box_border_border": "solid", "box_border_width": box(1),
        "box_border_radius": dims(0, 0, 12, 12),
        "box_background_color_background": "classic",
    }, globals_={
        "tabs_title_background_color_color": color_ref(C["surface"]),
        "tabs_title_background_color_active_color": color_ref("secondary"),
        "title_text_color": color_ref("secondary"),
        "title_text_color_active": color_ref(C["white"]),
        "box_border_color": color_ref(C["border"]),
        "box_background_color_color": color_ref(C["white"]),
    }, children=panels)

    head = _col([
        _h(props["heading"], "h2", "primary", "secondary", "center"),
        *([_p(props["intro"], "text", align="center")]
          if props.get("intro") else []),
    ], 78, extra={"flex_gap": gap(14), "flex_align_items": "center",
                  "margin": dims(0, "auto", 8, "auto")})
    return _sec([head, _col([tabs], 86, extra={
        "margin": dims(0, "auto", 0, "auto")})], props.get("bg", "grey"),
        extra={"_element_id": props["anchor"]} if props.get("anchor") else None)
