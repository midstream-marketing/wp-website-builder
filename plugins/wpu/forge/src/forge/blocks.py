"""
blocks.py — the block library.

Each factory takes plain props (copy + media, produced by the agents) and
returns a container tree. Colour and typography go through __globals__;
geometry is literal. Adding a design capability means adding a factory
here, never loosening the compiler.

Register a factory with @block("name") and it becomes usable from the IR.
"""
from __future__ import annotations

import math

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link, icon,
    gap, color_ref, typo_ref, dynamic, css,
)
from .tokens import C, T

BLOCKS: dict[str, callable] = {}


def block(name: str):
    def deco(fn):
        if name in BLOCKS:
            raise ValueError(
                f"Block {name!r} is already registered by "
                f"{BLOCKS[name].__name__}(). Re-registering silently replaces "
                f"it, and the failure surfaces in whichever other client used "
                f"the original. Pick a distinct name.")
        BLOCKS[name] = fn
        fn.block_name = name
        return fn
    return deco


# ───────────────────────────── shared parts ─────────────────────────────

SECTION_PAD = dims(104, 0, 104, 0)
SECTION_PAD_T = dims(76, 24, 76, 24)
SECTION_PAD_M = dims(60, 20, 60, 20)

# Elementor exposes no global for a shadow colour — it is one composite
# control — so this is the single place a literal colour is unavoidable.
# Kept as one constant rather than scattered through the factories.
CARD_SHADOW = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {
        "horizontal": 0, "vertical": 10, "blur": 30, "spread": -6,
        "color": "rgba(11, 13, 11, 0.10)",
    },
}
CARD_SHADOW_SOFT = {
    "box_shadow_box_shadow_type": "yes",
    "box_shadow_box_shadow": {
        "horizontal": 0, "vertical": 4, "blur": 16, "spread": -4,
        "color": "rgba(11, 13, 11, 0.07)",
    },
}

# Must match tokens.build_kit's container_width. Column percentages are
# resolved against this so the gap has somewhere to live.
KIT_CONTAINER = 1240
# The tablet breakpoint is 768px wide and SECTION_PAD_T takes 24px off each
# side, so a boxed section is 720px across there — not 760. Eight pixels of
# optimism is enough: a two-up tablet grid computed against 760 comes out at
# 2x48.42% + a 24px gap, which is 100.17% of the 720px it actually gets, and
# the second card drops onto its own line.
TABLET_CONTAINER = 720


def _gap_pct(px, container=KIT_CONTAINER):
    return px / container * 100


def _tracks(ratios, gap_px, container=KIT_CONTAINER):
    """Column widths as percentages, with room reserved for the gaps.

    A flex row that wraps breaks a line the moment the children's widths plus
    the gaps exceed 100% — it does not shrink them. Splitting the *available*
    width rather than the full width is what keeps a 3-up grid 3-up.
    """
    avail = 100 - _gap_pct(gap_px, container) * (len(ratios) - 1)
    total = float(sum(ratios))
    return [round(avail * r / total, 2) for r in ratios]


def _track(cols, gap_px, container=KIT_CONTAINER):
    """Width of one column in an even `cols`-wide grid."""
    return _tracks([1] * cols, gap_px, container)[0]


def _grid_widths(cols, gap_px):
    """Desktop / tablet widths for a wrapping card grid."""
    return _track(cols, gap_px), _track(2, gap_px, TABLET_CONTAINER)


def _section(children, bg="white", pad=None, direction="column", extra=None):
    """Standard outer section container with responsive padding."""
    bg_token = {"white": C["white"], "surface": C["surface"],
                "alt": C["surface_alt"], "dark": "secondary",
                "primary": "primary"}.get(bg, C["white"])
    s = {
        "content_width": "boxed",
        "flex_direction": direction,
        "padding": pad or SECTION_PAD,
        "padding_tablet": SECTION_PAD_T,
        "padding_mobile": SECTION_PAD_M,
        "background_background": "classic",
    }
    if extra:
        s.update(extra)
    return container(children, s, globals_={"background_color": color_ref(bg_token)})


def _pct_width(el):
    """The child's own width as a percentage, or None if it is auto-sized."""
    w = (el.get("settings") or {}).get("width")
    if isinstance(w, dict) and w.get("unit") == "%" and             isinstance(w.get("size"), (int, float)):
        return float(w["size"])
    return None


def _single_line(children, gap_px, container_px=KIT_CONTAINER):
    """Were these children sized to sit on exactly one line?

    True for a split (any mix of widths adding up to a line) and for a grid
    whose item count does not exceed one line's worth. False for a grid that
    is meant to wrap — six cards in a three-up.
    """
    widths = [_pct_width(c) for c in children]
    if len(widths) < 2 or any(w is None for w in widths):
        return False
    g = _gap_pct(gap_px, container_px)
    if len(set(widths)) > 1:
        return True
    w = widths[0]
    if not w:
        return False
    per_line = max(1, round((100 + g) / (w + g)))
    return len(widths) <= per_line


def _row(children, gap_px=32, align="stretch", justify="flex-start", wrap="wrap", extra=None):
    s = {
        "content_width": "full",
        "flex_direction": "row",
        "flex_gap": gap(gap_px),
        "flex_align_items": align,
        "flex_justify_content": justify,
        "flex_wrap": wrap,
        "flex_direction_mobile": "column",
    }
    # A percentage width survives nesting; a px gap does not. The widths above
    # reserve room for the gap against a 1240px container, so the same row
    # placed inside a padded panel or a half-width column has less than it was
    # promised, exceeds 100%, and wraps — a 2-up becomes stacked, a 4-up
    # becomes 3-and-1. Where the children were sized for one line, saying so
    # outright removes the arithmetic from the picture: flexbox shrinks them
    # to fit whatever width is actually there, at any nesting depth.
    #
    # Tablet gets `wrap` back, because the columns are full width there (see
    # `_col`) and stacking is what should happen.
    if wrap == "wrap" and _single_line(children, gap_px):
        s["flex_wrap"] = "nowrap"
        s["flex_wrap_tablet"] = "wrap"
    _stack_tablet_if_needed(children, gap_px)
    if extra:
        s.update(extra)
    return container(children, s)


def _stack_tablet_if_needed(children, gap_px):
    """Make the row stack cleanly at tablet when it cannot hold a line there.

    Wrapping is not stacking. A row that no longer fits at 720px breaks the
    line but keeps every child at its own width, so a 52/48 split becomes two
    half-width blocks under one another with a ragged right edge — the
    "not properly aligned" tablet rendering. Once it is going to break, every
    child goes full width, which is a real stack.

    Children that are already full width at tablet count as fitting, so this
    only fires on the mixed case a single `_col` default cannot resolve on its
    own: one child stacked, its sibling still on the desktop width.
    """
    widths = []
    for c in children:
        s = c.get("settings") or {}
        w = s.get("width_tablet") or s.get("width")
        if not (isinstance(w, dict) and w.get("unit") == "%"
                and isinstance(w.get("size"), (int, float))):
            return
        widths.append(float(w["size"]))
    if len(widths) < 2:
        return
    g = _gap_pct(gap_px, TABLET_CONTAINER)
    if len(set(widths)) == 1:
        w = widths[0]
        per_line = max(1, round((100 + g) / (w + g))) if w else 1
        if per_line * w + (per_line - 1) * g <= 100.05:
            return
    elif sum(widths) + g * (len(widths) - 1) <= 100.05:
        return
    for c in children:
        (c.get("settings") or {})["width_tablet"] = slider(100, "%")


def _col(children, width_pct=None, extra=None):
    s = {"content_width": "full", "flex_direction": "column", "flex_gap": gap(16)}
    if width_pct:
        s["width"] = slider(width_pct, "%")
        # Tablet stacks by default. A desktop column width is reserved against
        # a 1240px container, so at 768px the same px gap eats two and a half
        # times the share it was budgeted — the widths no longer fit on a line
        # and the row wraps. Wrapping is not stacking: the halves keep their
        # 51% and drop under one another, leaving a ragged right edge, which
        # is the "not properly aligned" tablet rendering. Full width per line
        # is a real stack. A call site that wants a genuine tablet grid passes
        # its own width_tablet in `extra`, which wins over this.
        s["width_tablet"] = slider(100, "%")
        s["width_mobile"] = slider(100, "%")
    if extra:
        s.update(extra)
    return container(children, s)


def _eyebrow(text, on_dark=False):
    # 12px uppercase is small text: on light it takes the ink variant, on dark
    # the raw brand colour already clears 4.5:1.
    return widget("heading", {
        "title": text, "header_size": "div", "align": "left",
    }, globals_={
        "title_color": color_ref(C["brand_on_dark"] if on_dark else C["ink_primary"]),
        "typography_typography": typo_ref(T["eyebrow"]),
    })


def _scrim(el, side="left", strength=0.92):
    """Directional gradient over a hero photo.

    A flat overlay dims the whole image equally, which is why our heroes read
    as "photo behind a grey sheet". Every reference instead runs an opaque
    wedge under the copy that clears off the subject, so the headline has
    contrast and the photograph still reads.
    """
    stops = {
        "left":  "90deg, rgba(0,0,0,%.2f) 0%%, rgba(0,0,0,%.2f) 42%%, rgba(0,0,0,.15) 78%%",
        "right": "270deg, rgba(0,0,0,%.2f) 0%%, rgba(0,0,0,%.2f) 42%%, rgba(0,0,0,.15) 78%%",
        "bottom": "0deg, rgba(0,0,0,%.2f) 0%%, rgba(0,0,0,%.2f) 40%%, rgba(0,0,0,.10) 85%%",
    }[side] % (strength, strength * 0.72)
    el["settings"]["custom_css"] = css(
        "selector::before { content:''; position:absolute; inset:0; "
        f"background: linear-gradient({stops}); pointer-events:none; z-index:0; }}",
        "selector > .e-con-inner, selector > .elementor-widget-wrap "
        "{ position:relative; z-index:1; }",
    )
    return el


def _angle(el, edge="bottom", depth=64):
    """Diagonal section edge — the device that stops a page reading as a
    stack of rectangles. `depth` is the rise of the cut in pixels."""
    if edge == "bottom":
        path = f"polygon(0 0, 100% 0, 100% calc(100% - {depth}px), 0 100%)"
    elif edge == "top":
        path = f"polygon(0 {depth}px, 100% 0, 100% 100%, 0 100%)"
    else:  # both
        path = (f"polygon(0 {depth}px, 100% 0, 100% calc(100% - {depth}px), 0 100%)")
    prev = el["settings"].get("custom_css", "")
    el["settings"]["custom_css"] = (prev + "\n" if prev else "") + css(
        f"selector {{ clip-path: {path}; }}")
    return el


def _hover_lift(el, rise=6):
    """Cards that respond to the cursor. Static cards are the clearest tell
    that a page was generated rather than designed."""
    prev = el["settings"].get("custom_css", "")
    el["settings"]["custom_css"] = (prev + "\n" if prev else "") + css(
        "selector { transition: transform .28s ease, box-shadow .28s ease; }",
        f"selector:hover {{ transform: translateY(-{rise}px); "
        "box-shadow: 0 18px 44px -12px rgba(11,13,11,.22); }",
    )
    return el


def _chip(text, icon_cls="fas fa-circle-check", on_dark=False, align="flex-start"):
    """Pill eyebrow — small icon plus label on a tinted rounded container.

    Opt-in rather than a change to _eyebrow, because sites built against a
    different reference use the plain uppercase variant.
    """
    pill = container([
        widget("icon", {
            "selected_icon": icon(icon_cls), "size": slider(12),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(
            C["brand_on_dark"] if on_dark else C["ink_primary"])}),
        widget("heading", {"title": text, "header_size": "div", "align": "left"},
               globals_={
                   "title_color": color_ref(C["white"] if on_dark else C["ink_primary"]),
                   "typography_typography": typo_ref(T["eyebrow"]),
               }),
    ], {
        "content_width": "full",
        "flex_direction": "row",
        "flex_gap": gap(8),
        "flex_align_items": "center",
        "padding": dims(8, 16, 8, 16),
        "border_radius": box(999),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(
        C["overlay"] if on_dark else C["surface_alt"])})
    # An Elementor container defaults to width:100%, so a pill left to itself
    # stretches the full column. There is no fit-content option on the width
    # slider, so the width is estimated from the label: 12px uppercase with
    # 1.6px tracking runs ~8.4px per character, plus icon, gap and padding.
    pill["settings"]["width"] = slider(round(58 + len(text) * 8.4))
    pill["settings"]["width_mobile"] = slider(round(54 + len(text) * 8.0))
    return _row([pill], justify=align,
                extra={"flex_wrap": "wrap", "flex_align_items": "center"})


def _ticks(items, on_dark=False, columns=2):
    """Feature checkmarks laid out in columns rather than one long list."""
    per = max(1, -(-len(items) // columns))
    chunks = [items[i:i + per] for i in range(0, len(items), per)]
    widths = _tracks([1] * len(chunks), 24)
    cols = []
    for ch, w in zip(chunks, widths):
        cols.append(_col([widget("icon-list", {
            "icon_list": [repeater_item(text=t, selected_icon=icon("fas fa-circle-check"),
                                        link=link("")) for t in ch],
            "space_between": slider(12),
            "icon_size": slider(15),
        }, globals_={
            "icon_color": color_ref(C["brand_on_dark"] if on_dark else C["ink_primary"]),
            "text_color": color_ref(C["white"] if on_dark else "text"),
            "icon_typography_typography": typo_ref(T["body_small"]),
        })], w))
    return _row(cols, gap_px=24)


def _faq(items, first_open=True):
    """Nested accordion with the first panel open.

    Six of the eight reference sites open one item by default — it shows the
    accordion is interactive without demanding a click. The flat `accordion`
    widget cannot do it (no default-state control); `nested-accordion` can,
    and keeps each answer as a real container rather than an HTML string.
    """
    titles, panels = [], []
    for q in items:
        titles.append(repeater_item(item_title=q["q"]))
        panels.append(container([_text(q["a"], small=True)], {
            "content_width": "full",
            "flex_direction": "column",
            "padding": dims(4, 0, 18, 0),
        }))
    return widget("nested-accordion", {
        "items": titles,
        "default_state": "expanded" if first_open else "all_collapsed",
        "title_tag": "h3",
        "accordion_item_title_icon_position": "right",
        "accordion_item_title_space_between": slider(10),
        "accordion_item_title_distance_from_content": slider(8),
    }, globals_={
        # `title_typography_typography` is the registry's name for this
        # control. The old key here was `accordion_item_title_typography_
        # typography`, which is not a nested-accordion control at all, so
        # every FAQ heading in every kit has been rendering at the theme
        # default size rather than at T["h_small"]. __globals__ keys are
        # never validated, so nothing reported it.
        "title_typography_typography": typo_ref(T["h_small"]),
        # UNVERIFIED. Neither registry file lists a title or icon COLOUR
        # control for nested-accordion, so these two may be doing nothing
        # either. They are left in place rather than deleted because the
        # registry is mined and may simply be missing that style section -
        # removing a key that does work would lose the colour. Confirm
        # against a live Elementor before touching them.
        "accordion_item_title_color": color_ref("secondary"),
        "accordion_item_title_icon_color": color_ref(C["ink_primary"]),
    }, children=panels)


def _heading(text, size="h2", token=None, align="left", on_dark=False, tone="dark"):
    """tone: 'dark' body headings, 'brand' section titles, 'on_dark' reversed."""
    if on_dark:
        col = C["white"]
    elif tone == "brand":
        col = C["ink_primary"]
    else:
        col = "secondary"
    return widget("heading", {
        "title": text, "header_size": size, "align": align,
    }, globals_={
        "title_color": color_ref(col),
        "typography_typography": typo_ref(token or T["h_large"]),
    })


def _text(html, align="left", on_dark=False, small=False):
    return widget("text-editor", {
        "editor": html if html.strip().startswith("<") else f"<p>{html}</p>",
        "align": align,
    }, globals_={
        "text_color": color_ref(C["on_dark"] if on_dark else "text"),
        "typography_typography": typo_ref(T["body_small"] if small else "text"),
    })


# Set by compile_site() from ir["buttons"]["primary_style"]. When a client
# opts in, every block that asks for the default "primary" fill gets this
# style instead — which is how a whole kit switches to gradient CTAs without
# threading a prop through twenty factories. Absent the key it stays None and
# output is unchanged.
PRIMARY_STYLE: str | None = None


def set_primary_style(style: str | None) -> None:
    global PRIMARY_STYLE
    PRIMARY_STYLE = style


def _button(label, url, style="primary", icon_cls="fas fa-arrow-right"):
    # Both filled styles switch together. Block factories pick between
    # "primary" and "accent" for their own compositional reasons, so honouring
    # only one leaves a kit with two different CTA treatments scattered
    # through it. Ghost variants are untouched — they are a different job.
    if style in ("primary", "accent") and PRIMARY_STYLE:
        style = PRIMARY_STYLE
    s = {
        "text": label,
        "link": link(url),
        "selected_icon": icon(icon_cls) if icon_cls else {"value": "", "library": ""},
        "icon_align": "right",
        "text_padding": dims(16, 32, 16, 32),
        "border_radius": box(8),
        "border_border": "solid",
        "border_width": box(1),
    }
    # Label colour comes from the contrast-derived token, not a fixed white:
    # a bright brand fill needs a dark label to stay legible.
    if style == "primary":
        g = {
            "button_text_color": color_ref(C["on_primary"]),
            "background_color": color_ref("primary"),
            "border_color": color_ref("primary"),
            "hover_color": color_ref(C["white"]),
            "button_background_hover_color": color_ref("secondary"),
            "button_hover_border_color": color_ref("secondary"),
            "typography_typography": typo_ref("accent"),
        }
    elif style == "accent":
        g = {
            "button_text_color": color_ref(C["on_accent"]),
            "background_color": color_ref(C["accent_fill"]),
            "border_color": color_ref(C["accent_fill"]),
            "hover_color": color_ref(C["white"]),
            "button_background_hover_color": color_ref("secondary"),
            "button_hover_border_color": color_ref("secondary"),
            "typography_typography": typo_ref("accent"),
        }
    elif style == "gradient":
        # 135-degree gradient fill, the reference site's signature button.
        # Elementor expresses this on the button widget as a background TYPE
        # of "gradient" plus two colour stops — `background_color` is the
        # start and `background_color_b` the end, and both still route
        # through __globals__ so the kit re-skins normally.
        s.update({
            "background_background": "gradient",
            "background_gradient_type": "linear",
            "background_gradient_angle": slider(135, "deg"),
            "background_color_stop": slider(0, "%"),
            "background_color_b_stop": slider(100, "%"),
            "border_border": "none",
            "border_width": box(0),
        })
        g = {
            "button_text_color": color_ref(C["on_primary"]),
            "background_color": color_ref("secondary"),
            "background_color_b": color_ref("primary"),
            "hover_color": color_ref(C["white"]),
            "button_background_hover_color": color_ref("primary"),
            "typography_typography": typo_ref("accent"),
        }
    elif style == "pill":
        # Thin outlined capsule on a dark ground. Fills with the brand colour
        # on hover rather than inverting to white, which keeps it quiet.
        s.update({
            "border_radius": box(999),
            "border_border": "solid",
            "border_width": box(1),
            "text_padding": dims(15, 34, 15, 34),
        })
        g = {
            "button_text_color": color_ref(C["white"]),
            "background_color": color_ref(C["transparent"]),
            "border_color": color_ref(C["rule_dark"]),
            "hover_color": color_ref(C["on_primary"]),
            "button_background_hover_color": color_ref("primary"),
            "button_hover_border_color": color_ref("primary"),
            "typography_typography": typo_ref("accent"),
        }
    elif style == "ghost_dark":
        # A transparent button inherits whatever is behind it. On a dark hero
        # the standard ghost's dark label is invisible — this is the variant
        # for dark grounds.
        g = {
            "button_text_color": color_ref(C["white"]),
            "background_color": color_ref(C["transparent"]),
            "border_color": color_ref(C["rule_dark"]),
            "hover_color": color_ref(C["on_accent"]),
            "button_background_hover_color": color_ref("accent"),
            "button_hover_border_color": color_ref("accent"),
            "typography_typography": typo_ref("accent"),
        }
    else:  # ghost
        g = {
            "button_text_color": color_ref("secondary"),
            "background_color": color_ref(C["transparent"]),
            "border_color": color_ref(C["border"]),
            "hover_color": color_ref(C["white"]),
            "button_background_hover_color": color_ref("secondary"),
            "button_hover_border_color": color_ref("secondary"),
            "typography_typography": typo_ref("accent"),
        }
    return widget("button", s, globals_=g)


# ─────────────────────────────── blocks ───────────────────────────────

@block("hero.split")
def hero_split(props):
    """Headline + subcopy + dual CTA on the left, image on the right."""
    w_left, w_right = _tracks([52, 48], 48)
    dark_hero = props.get("dark", True)
    left = _col([
        *( [_eyebrow(props["eyebrow"], on_dark=dark_hero)] if props.get("eyebrow") else [] ),
        _heading(props["h1"], "h1", T["hero"], on_dark=props.get("dark", True)),
        _text(props.get("intro", ""), on_dark=props.get("dark", True)),
        _row([
            _button(props["cta"]["label"], props["cta"]["href"], "accent"),
            *( [_button(props["cta2"]["label"], props["cta2"]["href"], "ghost_dark", None)]
               if props.get("cta2") else [] ),
        ], gap_px=16, extra={"flex_wrap": "wrap", "margin": dims(12, 0, 0, 0)}),
    ], w_left, extra={"flex_gap": gap(20), "flex_justify_content": "center"})

    right = _col([
        widget("image", {
            "image": media(props["image"]["url"], props["image"]["alt"]),
            "image_size": "full",
            "image_border_radius": box(16),
            "width": slider(100, "%"),
        })
    ], w_right)

    inner = _row([left, right], gap_px=48, align="center")
    dark = props.get("dark", True)
    sec = _section([inner], bg="dark" if dark else "surface",
                   pad=dims(120, 0, 120, 0),
                   extra={"min_height": slider(84, "vh"),
                          "flex_justify_content": "center"})
    if props.get("background"):
        sec["settings"].update({
            "background_image": media(props["background"], ""),
            "background_position": "center center",
            "background_size": "cover",
            "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(0.82),
        })
        sec["settings"]["__globals__"]["background_overlay_color"] = color_ref("secondary")
    # overlap_header removed: the header is a separate Theme Builder
    # document rendered before this one, so a negative top margin paints
    # the hero over the nav rather than tucking beneath it.
        sec["settings"]["padding"] = dims(200, 0, 120, 0)
    return sec


@block("trust.bar")
def trust_bar(props):
    """Row of short proof points under the hero."""
    items = [
        repeater_item(text=i["text"], selected_icon=icon(i.get("icon", "fas fa-check")),
                      link=link(""))
        for i in props["items"]
    ]
    lst = widget("icon-list", {
        "icon_list": items,
        "view": "inline",
        "space_between": slider(28),
        "icon_size": slider(16),
        "icon_align": "left",
    }, globals_={
        "icon_color": color_ref(C["ink_primary"]),
        "text_color": color_ref("secondary"),
        "icon_typography_typography": typo_ref(T["meta"]),
    })
    return _section([lst], bg="surface", pad=dims(28, 0, 28, 0),
                    extra={"flex_align_items": "center"})


@block("services.grid")
def services_grid(props):
    """Section heading + N icon-box cards."""
    head = _col([
        *( [_eyebrow(props["eyebrow"])] if props.get("eyebrow") else [] ),
        _heading(props["heading"], "h2", T["h_large"], align="center", tone="brand"),
        *( [_text(props["intro"], align="center")] if props.get("intro") else [] ),
    ], extra={"flex_align_items": "center", "content_width": "boxed", "boxed_width": slider(760),
              "margin": dims(0, "auto", 40, "auto")})

    cols = props.get("columns", 3)
    width, width_t = _grid_widths(cols, 24)
    cards = []
    for it in props["items"]:
        card = widget("icon-box", {
            "title_text": it["title"],
            "description_text": it["text"],
            "selected_icon": icon(it.get("icon", "fas fa-star")),
            "position": "top",
            "text_align": "left",
            "title_size": "h3",
            "icon_size": slider(28),
            "icon_space": slider(18),
            "title_bottom_space": slider(10),
        }, globals_={
            "primary_color": color_ref(C["ink_primary"]),
            "title_color": color_ref("secondary"),
            "description_color": color_ref("text"),
            "title_typography_typography": typo_ref(T["h_medium"]),
            "description_typography_typography": typo_ref(T["body_small"]),
        })
        if it.get("href"):
            card["settings"]["link"] = link(it["href"])
        wrap = container([card], {
            "content_width": "full",
            "flex_direction": "column",
            "width": slider(width, "%"),
            "width_tablet": slider(width_t, "%"),
            "width_mobile": slider(100, "%"),
            "padding": box(30),
            "border_radius": box(16),
            "border_border": "solid",
            "border_width": box(1),
            "background_background": "classic",
            **CARD_SHADOW_SOFT,
        }, globals_={
            "background_color": color_ref(C["white"]),
            "border_color": color_ref(C["border"]),
        })
        cards.append(wrap)

    return _section([head, _row(cards, gap_px=24)], bg=props.get("bg", "surface"))


@block("about.split")
def about_split(props):
    w_img, w_body = _tracks([46, 54], 56)
    img = _col([widget("image", {
        "image": media(props["image"]["url"], props["image"]["alt"]),
        "image_size": "full",
        "image_border_radius": box(16),
        "width": slider(100, "%"),
    })], w_img)
    body = _col([
        *( [_eyebrow(props["eyebrow"])] if props.get("eyebrow") else [] ),
        _heading(props["heading"], "h2", T["h_large"], tone="brand"),
        _text(props["body"]),
        *( [widget("icon-list", {
            "icon_list": [repeater_item(text=p, selected_icon=icon("fas fa-circle-check"),
                                        link=link("")) for p in props["points"]],
            "space_between": slider(12),
            "icon_size": slider(16),
        }, globals_={"icon_color": color_ref(C["ink_primary"]),
                     "text_color": color_ref("text"),
                     "icon_typography_typography": typo_ref("text")})]
           if props.get("points") else [] ),
        *( [_button(props["cta"]["label"], props["cta"]["href"])] if props.get("cta") else [] ),
    ], w_body, extra={"flex_gap": gap(18), "flex_justify_content": "center"})
    order = [body, img] if props.get("reverse") else [img, body]
    return _section([_row(order, gap_px=56, align="center")], bg=props.get("bg", "white"))


@block("stats.row")
def stats_row(props):
    w_stat = _track(len(props["items"]), 24)
    cells = []
    for s in props["items"]:
        cells.append(_col([
            widget("counter", {
                "starting_number": 0,
                "ending_number": s["value"],
                "suffix": s.get("suffix", ""),
                "title": s["label"],
                "duration": 2000,
                "title_tag": "div",
            }, globals_={
                "number_color": color_ref(C["ink_primary"]),
                "title_color": color_ref(C["muted"]),
                "typography_typography": typo_ref(T["h_large"]),
                "title_typography_typography": typo_ref(T["meta"]),
            })
        ], w_stat, extra={"flex_align_items": "center"}))
    return _section([_row(cells, gap_px=24, justify="space-between")],
                    bg=props.get("bg", "white"), pad=dims(64, 0, 64, 0))


@block("areas.grid")
def areas_grid(props):
    """Areas We Serve — chunked icon-lists so it stays scannable."""
    head = _col([
        *( [_eyebrow(props["eyebrow"])] if props.get("eyebrow") else [] ),
        _heading(props["heading"], "h2", T["h_large"], align="center", tone="brand"),
        *( [_text(props["intro"], align="center")] if props.get("intro") else [] ),
    ], extra={"flex_align_items": "center", "margin": dims(0, "auto", 36, "auto")})

    areas = props["areas"]
    per = max(1, -(-len(areas) // props.get("columns", 4)))
    chunks = [areas[i:i + per] for i in range(0, len(areas), per)]
    w_chunk = _track(len(chunks), 24)
    cols = []
    for ch in chunks:
        cols.append(_col([widget("icon-list", {
            "icon_list": [repeater_item(
                text=a["name"],
                selected_icon=icon("fas fa-location-dot"),
                link=link(a.get("href", "")),
            ) for a in ch],
            "space_between": slider(10),
            "icon_size": slider(14),
        }, globals_={"icon_color": color_ref(C["ink_primary"]),
                     "text_color": color_ref("text"),
                     "icon_typography_typography": typo_ref(T["body_small"])})],
            w_chunk))
    children = [head, _row(cols, gap_px=24)]
    if props.get("map_query"):
        children.append(widget("google_maps", {
            "address": props["map_query"],
            "zoom": slider(11),
            "height": slider(320),
            "height_mobile": slider(240),
        }))
    return _section(children, bg=props.get("bg", "white"))


@block("process.steps")
def process_steps(props):
    w_step, w_step_t = _grid_widths(len(props["steps"]), 20)
    cards = []
    for n, st in enumerate(props["steps"], 1):
        cards.append(container([
            widget("heading", {"title": f"{n:02d}", "header_size": "div"},
                   globals_={"title_color": color_ref(C["ink_primary"]),
                             "typography_typography": typo_ref(T["h_large"])}),
            _heading(st["title"], "h3", T["h_medium"]),
            _text(st["text"], small=True),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(8),
            "width": slider(w_step, "%"),
            "width_tablet": slider(w_step_t, "%"),
            "width_mobile": slider(100, "%"),
            "padding": box(30),
            "border_radius": box(18),
            "background_background": "classic",
            **CARD_SHADOW_SOFT,
        }, globals_={"background_color": color_ref(C["white"])}))
    head = _col([_heading(props["heading"], "h2", T["h_large"], align="center",
                          tone="brand")],
                extra={"flex_align_items": "center", "margin": dims(0, "auto", 44, "auto")})
    return _section([head, _row(cards, gap_px=20)], bg=props.get("bg", "surface"))


@block("faq.accordion")
def faq_accordion(props):
    acc = _faq(props["items"], props.get("first_open", True))
    head = _col([_heading(props.get("heading", "Frequently Asked Questions"),
                          "h2", T["h_large"], align="center", tone="brand")],
                extra={"flex_align_items": "center", "margin": dims(0, "auto", 40, "auto")})
    body = _col([acc], 76, extra={"margin": dims(0, "auto", 0, "auto")})
    return _section([head, _row([body], justify="center")], bg=props.get("bg", "white"))


@block("cta.band")
def cta_band(props):
    """Elementor Pro call-to-action — one widget replacing a whole stack."""
    cta = widget("call-to-action", {
        "skin": "cover" if props.get("image") else "classic",
        "title": props["heading"],
        "description": props.get("text", ""),
        "button": props["cta"]["label"],
        "link": link(props["cta"]["href"]),
        "title_tag": "h2",
        "layout": "above",
        "alignment": "center",
        "vertical_position": "middle",
        "min-height": slider(props.get("min_height", 300)),
        "padding": dims(64, 32, 64, 32),
        "button_padding": dims(16, 34, 16, 34),
        "button_border_radius": box(8),
        "title_spacing": slider(14),
        "description_spacing": slider(26),
        **({"bg_image": media(props["image"], "")} if props.get("image") else {}),
    }, globals_={
        "title_typography_typography": typo_ref(T["h_large"]),
        "description_typography_typography": typo_ref("text"),
    })
    return _section([cta], bg=props.get("bg", "primary"), pad=dims(0, 0, 0, 0))


@block("contact.block")
def contact_block(props):
    w_info, w_form = _tracks([46, 54], 48)
    # A client brief usually specifies the exact intake fields; `fields` lets
    # the IR carry them rather than forcing every site through one shape.
    if props.get("fields"):
        fields = []
        for f in props["fields"]:
            item = {
                "custom_id": f["id"],
                "field_type": f.get("type", "text"),
                "field_label": f["label"],
                "placeholder": f.get("placeholder", ""),
                "required": "true" if f.get("required") else "",
                "width": str(f.get("width", 100)),
            }
            if f.get("options"):
                item["field_options"] = "\n".join(f["options"])
            if f.get("rows"):
                item["rows"] = f["rows"]
            if f.get("acceptance_text"):
                item["acceptance_text"] = f["acceptance_text"]
            fields.append(repeater_item(**item))
    else:
        fields = [
            repeater_item(custom_id="name", field_type="text", field_label="Name",
                          placeholder="Your name", required="true", width="50"),
            repeater_item(custom_id="phone", field_type="tel", field_label="Phone",
                          placeholder="Phone number", required="true", width="50"),
            repeater_item(custom_id="email", field_type="email", field_label="Email",
                          placeholder="Email address", required="true", width="100"),
            repeater_item(custom_id="message", field_type="textarea",
                          field_label="How can we help?",
                          placeholder="Tell us about the job", required="", width="100", rows=4),
        ]
    form = widget("form", {
        "form_name": props.get("form_name", "Contact"),
        "submit_actions": ["email"],
        "form_fields": fields,
        "button_text": props.get("submit_label", "Send Request"),
        "button_size": "md",
        "button_width": "100",
        "input_size": "md",
        "show_labels": "",
        "row_gap": slider(14),
        "column_gap": slider(14),
        "success_message": props.get("success_message",
                                     "Thanks — we'll be in touch shortly."),
        "email_to": props.get("email", ""),
        "email_subject": f"New enquiry — {props.get('business', 'website')}",
    }, globals_={
        "button_background_color": color_ref(C["accent_fill"]),
        "button_text_color": color_ref(C["on_accent"]),
        "field_text_color": color_ref("secondary"),
    })

    details = []
    for d in props["details"]:
        details.append(repeater_item(
            text=d["text"], selected_icon=icon(d.get("icon", "fas fa-circle-info")),
            link=link(d.get("href", "")),
        ))
    info = _col([
        *( [_eyebrow(props["eyebrow"])] if props.get("eyebrow") else [] ),
        _heading(props["heading"], "h2", T["h_large"], tone="brand"),
        *( [_text(props["intro"])] if props.get("intro") else [] ),
        widget("icon-list", {
            "icon_list": details,
            "space_between": slider(14),
            "icon_size": slider(18),
        }, globals_={"icon_color": color_ref(C["ink_primary"]),
                     "text_color": color_ref("text"),
                     "icon_typography_typography": typo_ref("text")}),
    ], w_info, extra={"flex_gap": gap(16)})

    form_col = container([form], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(w_form, "%"), "width_mobile": slider(100, "%"),
        "padding": box(34), "border_radius": box(20),
        "background_background": "classic",
        **CARD_SHADOW,
    }, globals_={"background_color": color_ref(C["white"])})

    return _section([_row([info, form_col], gap_px=48, align="flex-start")],
                    bg=props.get("bg", "surface"))


@block("header.simple")
def header_simple(props):
    logo = widget("theme-site-logo", {
        "align": "left", "width": slider(props.get("logo_width", 160)),
        # Omitted entirely when unset so the widget uses Site Identity.
        **({"image": media(props["logo"], props.get("business", ""))}
           if props.get("logo") else {}),
    })
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal",
        "align_items": "end",
        "pointer": "underline",
        "menu_space_between": slider(26),
        "toggle_align": "right",
    }, globals_={
        "color_menu_item": color_ref("secondary"),
        "color_menu_item_hover": color_ref(C["ink_primary"]),
        "menu_typography_typography": typo_ref("accent"),
    })
    cta = _button(props["cta"]["label"], props["cta"]["href"], "accent", "fas fa-phone")
    # A seven-item menu wraps to two lines at 56%; the nav needs the room more
    # than the logo and CTA columns do.
    w_logo, w_nav, w_cta = _tracks([16, 66, 18], 20)
    bar = container([
        _row([
            _col([logo], w_logo, extra={"flex_justify_content": "center"}),
            _col([nav], w_nav, extra={"flex_justify_content": "center"}),
            _col([cta], w_cta, extra={"flex_justify_content": "center",
                                      "flex_align_items": "flex-end"}),
        ], gap_px=20, align="center")
    ], {
        "content_width": "boxed",
        "flex_direction": "row",
        "padding": dims(18, 0, 18, 0),
        "padding_mobile": dims(14, 20, 14, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"])})

    if not props.get("topbar"):
        return bar

    # Thin utility strip above the nav — hours, address, contact. Hidden on
    # mobile, where it would push the whole page down for marginal value.
    strip = container([
        widget("icon-list", {
            "icon_list": [repeater_item(text=i["text"],
                                        selected_icon=icon(i.get("icon", "fas fa-circle-info")),
                                        link=link(i.get("href", "")))
                          for i in props["topbar"]],
            "view": "inline",
            "space_between": slider(26),
            "icon_size": slider(13),
        }, globals_={"icon_color": color_ref(C["brand_on_dark"]),
                     "text_color": color_ref(C["on_dark"]),
                     "icon_typography_typography": typo_ref(T["meta"])}),
    ], {
        "content_width": "boxed",
        "flex_direction": "row",
        "flex_justify_content": "space-between",
        "flex_align_items": "center",
        "padding": dims(9, 0, 9, 0),
        "hide_mobile": "hidden-mobile",
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})

    return container([strip, bar], {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(0),
    })


@block("footer.simple")
def footer_simple(props):
    # No logo URL means the client uploads it to Site Identity instead; fall
    # back to the theme logo widget rather than shipping an empty image.
    logo_w = (
        widget("image", {"image": media(props["logo"], props.get("business", "")),
                         "width": slider(150), "align": "left"})
        if props.get("logo") else
        widget("theme-site-logo", {"align": "left", "width": slider(160)})
    )
    groups = props.get("groups", [])
    # The map, when present, is a column like any other and has to be in the
    # width solve — appending it afterwards would push the row past 100%.
    has_map = bool(props.get("map_query"))
    ratios = [34] + [22] * len(groups) + ([26] if has_map else [])
    widths = _tracks(ratios, 32)
    w_brand, w_group = widths[0], widths[1:1 + len(groups)]
    w_map = widths[-1] if has_map else None
    brand = _col([
        logo_w,
        _text(props.get("blurb", ""), on_dark=True, small=True),
        widget("social-icons", {
            "social_icon_list": [
                repeater_item(social_icon=icon(f"fab fa-{s['network']}"),
                              link=link(s["url"], external=True))
                for s in props.get("socials", [])
            ],
            "align": "left", "icon_size": slider(16), "shape": "circle",
            "icon_spacing": slider(10),
        }) if props.get("socials") else widget("spacer", {"space": slider(0)}),
    ], w_brand, extra={"flex_gap": gap(14)})

    def col(title, items, width):
        return _col([
            _heading(title, "h4", T["h_small"], on_dark=True),
            widget("icon-list", {
                "icon_list": [repeater_item(text=i["text"], link=link(i.get("href", "")),
                                            selected_icon={"value": "", "library": ""})
                              for i in items],
                "space_between": slider(9),
            }, globals_={"text_color": color_ref(C["on_dark"]),
                         "icon_typography_typography": typo_ref(T["body_small"])}),
        ], width, extra={"flex_gap": gap(12)})

    cols = [brand] + [col(g["title"], g["items"], w)
                      for g, w in zip(groups, w_group)]

    # All eight references close the footer with a map, review badges, or both.
    # The map earns its place on a local-service site: it states the service
    # area geographically at the moment someone is deciding whether to call.
    if has_map:
        cols.append(_col([
            _heading(props.get("map_title", "Find Us"), "h4", T["h_small"],
                     on_dark=True),
            container([widget("google_maps", {
                "address": props["map_query"],
                "zoom": slider(props.get("map_zoom", 9)),
                "height": slider(150),
            })], {
                "content_width": "full", "flex_direction": "column",
                "border_radius": box(10), "overflow": "hidden",
            }),
        ], w_map, extra={"flex_gap": gap(12)}))
    bottom = _text(props.get("copyright", ""), align="center", on_dark=True, small=True)

    return container([
        _row(cols, gap_px=32, align="flex-start"),
        widget("divider", {"weight": slider(1), "gap": slider(28), "look": "line"},
               globals_={"color": color_ref(C["rule_dark"])}),
        bottom,
    ], {
        "content_width": "boxed",
        "flex_direction": "column",
        "padding": dims(72, 0, 40, 0),
        "padding_mobile": dims(52, 20, 32, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})


def _photo(img, height=260, radius=0):
    """Fixed-height cover image. Keeps cards in a grid the same height."""
    return widget("image", {
        "image": media(img["url"], img["alt"]),
        "image_size": "full",
        "width": slider(100, "%"),
        "height": slider(height),
        "height_mobile": slider(round(height * 0.8)),
        "object-fit": "cover",
        "object-position": "center center",
        "image_border_radius": box(radius),
    })


def _section_head(props, on_dark=False):
    return _col([
        *( [_eyebrow(props["eyebrow"], on_dark=on_dark)] if props.get("eyebrow") else [] ),
        _heading(props["heading"], "h2", T["h_large"], align="center",
                 on_dark=on_dark, tone="brand"),
        *( [_text(props["intro"], align="center", on_dark=on_dark)]
           if props.get("intro") else [] ),
    ], extra={"flex_align_items": "center", "content_width": "boxed", "boxed_width": slider(820),
              "margin": dims(0, "auto", 48, "auto")})


@block("services.cards")
def services_cards(props):
    """Photo service cards. The icon-box grid reads generic; photographs sell
    turf, so this is the variant used on lead-gen pages."""
    cols = props.get("columns", 3)
    width, width_t = _grid_widths(cols, 24)
    # `caption` is the reference site's treatment: photograph plus a centred
    # label, no body copy. The card is the picture; the words get out of its way.
    caption = props.get("caption_only", False)
    cards = []
    for it in props["items"]:
        # Six of eight references close every service card with a Read More.
        # It signals there is depth behind the card, which a bare title does
        # not — and it gives the card a second, larger click target.
        more = props.get("more_label", "Read More")
        body = container([
            _heading(it["title"], "h3", T["h_medium"],
                     align="center" if caption else "left"),
            *( [_text(it["text"], small=True)]
               if it.get("text") and not caption else [] ),
            *( [widget("icon-list", {
                "icon_list": [repeater_item(
                    text=more, selected_icon=icon("fas fa-arrow-right"),
                    link=link(it["href"]))],
                "icon_align": "right",
                "space_between": slider(0),
                "icon_size": slider(12),
            }, globals_={
                "icon_color": color_ref(C["ink_primary"]),
                "text_color": color_ref(C["ink_primary"]),
                "icon_typography_typography": typo_ref("accent"),
            })] if it.get("href") and props.get("show_more", True) else [] ),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(8),
            "padding": dims(20, 22, 22, 22) if caption else dims(24, 26, 28, 26),
            "flex_align_items": "center" if caption else "flex-start",
        })
        # In caption mode the photograph is inset with its own radius rather
        # than bled to the card edge — the reference site's card anatomy.
        photo = _photo(it["image"], props.get("image_height", 240),
                       radius=14 if caption else 0)
        card_settings = {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(0),
            "width": slider(width, "%"),
            "width_tablet": slider(width_t, "%"),
            "width_mobile": slider(100, "%"),
            "padding": box(14) if caption else box(0),
            "border_radius": box(18),
            "background_background": "classic",
            **CARD_SHADOW,
        }
        if not caption:
            card_settings["overflow"] = "hidden"
        if it.get("href"):
            card_settings["link"] = link(it["href"])
        cards.append(_hover_lift(container(
            [photo, body], card_settings,
            globals_={"background_color": color_ref(C["white"])},
        )))
    return _section([_section_head(props), _row(cards, gap_px=24)],
                    bg=props.get("bg", "surface"))


@block("gallery.grid")
def gallery_grid(props):
    """Project grid built from image widgets rather than the Pro Gallery
    widget — every tile keeps real alt text, which V8 cares about and the
    gallery control cannot carry."""
    cols = props.get("columns", 3)
    width, width_t = _grid_widths(cols, 18)
    tiles = []
    for img in props["items"]:
        tiles.append(container([
            _photo(img, props.get("height", 280), radius=14),
            # A caption is what turns a stock grid into a project record.
            *( [_text(img["caption"], small=True)] if img.get("caption") else [] ),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(10),
            "width": slider(width, "%"),
            "width_tablet": slider(width_t, "%"),
            "width_mobile": slider(100, "%"),
        }))
    children = [_section_head(props, on_dark=props.get("bg") == "dark"),
                _row(tiles, gap_px=18)]
    if props.get("cta"):
        children.append(_row([_button(props["cta"]["label"], props["cta"]["href"], "accent")],
                             justify="center", extra={"margin": dims(40, 0, 0, 0)}))
    return _section(children, bg=props.get("bg", "white"))


@block("gallery.pairs")
def gallery_pairs(props):
    """Before / after pairs. Elementor has no comparison-slider widget in the
    allowed vocabulary, so the pair is shown side by side and labelled."""
    w_half = _track(2, 20)
    rows = []
    for p in props["items"]:
        def half(img, label):
            return _col([
                widget("heading", {"title": label, "header_size": "div", "align": "left"},
                       globals_={"title_color": color_ref(C["ink_primary"]),
                                 "typography_typography": typo_ref(T["eyebrow"])}),
                _photo(img, props.get("height", 300), radius=12),
            ], w_half, extra={"flex_gap": gap(10)})

        rows.append(container([
            _row([half(p["before"], props.get("before_label", "Before")),
                  half(p["after"], props.get("after_label", "After"))], gap_px=20),
            *( [_text(p["caption"], small=True)] if p.get("caption") else [] ),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(14),
            "padding": box(20),
            "border_radius": box(18),
            "background_background": "classic",
            **CARD_SHADOW_SOFT,
        }, globals_={"background_color": color_ref(C["white"])}))

    return _section([_section_head(props),
                     _col(rows, extra={"flex_gap": gap(24)})],
                    bg=props.get("bg", "surface"))


@block("reviews.grid")
def reviews_grid(props):
    """Review cards. No testimonial widget is in the allowed vocabulary, so
    the card is assembled from core widgets."""
    def stars(n=5):
        return widget("icon-list", {
            "icon_list": [repeater_item(text="", selected_icon=icon("fas fa-star"),
                                        link=link("")) for _ in range(n)],
            "view": "inline",
            "space_between": slider(2),
            "icon_size": slider(16),
        # A star rating carries meaning, so it takes the readable variant
        # rather than the bright fill colour.
        }, globals_={"icon_color": color_ref(C["ink_primary"])})

    cols = props.get("columns", 3)
    width, width_t = _grid_widths(cols, 22)
    cards = []
    for rv in props["items"]:
        cards.append(container([
            stars(rv.get("rating", 5)),
            _text(rv["quote"]),
            widget("divider", {"weight": slider(1), "gap": slider(14), "look": "line"},
                   globals_={"color": color_ref(C["border"])}),
            _heading(rv["name"], "h4", T["h_small"]),
            *( [_text(rv["meta"], small=True)] if rv.get("meta") else [] ),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(10),
            "width": slider(width, "%"),
            "width_tablet": slider(width_t, "%"),
            "width_mobile": slider(100, "%"),
            "padding": box(30),
            "border_radius": box(18),
            "background_background": "classic",
            **CARD_SHADOW_SOFT,
        }, globals_={"background_color": color_ref(C["white"])}))

    children = [_section_head(props), _row(cards, gap_px=22)]
    if props.get("cta"):
        children.append(_row([_button(props["cta"]["label"], props["cta"]["href"], "accent")],
                             justify="center", extra={"margin": dims(40, 0, 0, 0)}))
    return _section(children, bg=props.get("bg", "surface"))


@block("pricing.cards")
def pricing_cards(props):
    """Financing / package options. `featured` lifts one card with the brand
    colour rather than a shadow, which cannot be expressed without CSS."""
    width, width_t = _grid_widths(len(props["items"]), 22)
    cards = []
    for it in props["items"]:
        feat = it.get("featured", False)
        cards.append(container([
            _eyebrow(it["name"], on_dark=feat),
            _heading(it["amount"], "div", T["h_large"], on_dark=feat),
            *( [_text(it["term"], small=True, on_dark=feat)] if it.get("term") else [] ),
            widget("divider", {"weight": slider(1), "gap": slider(16), "look": "line"},
                   globals_={"color": color_ref(C["rule_dark"] if feat else C["border"])}),
            widget("icon-list", {
                "icon_list": [repeater_item(text=p, selected_icon=icon("fas fa-circle-check"),
                                            link=link("")) for p in it["points"]],
                "space_between": slider(11),
                "icon_size": slider(15),
            }, globals_={"icon_color": color_ref(C["brand_on_dark"] if feat else C["ink_primary"]),
                         "text_color": color_ref(C["on_dark"] if feat else "text"),
                         "icon_typography_typography": typo_ref(T["body_small"])}),
            *( [_button(it["cta"]["label"], it["cta"]["href"],
                        "accent" if feat else "ghost")] if it.get("cta") else [] ),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(12),
            "width": slider(width, "%"),
            "width_tablet": slider(width_t, "%"),
            "width_mobile": slider(100, "%"),
            "padding": box(34),
            "border_radius": box(20),
            "background_background": "classic",
            **(CARD_SHADOW if feat else CARD_SHADOW_SOFT),
        }, globals_={
            "background_color": color_ref("secondary" if feat else C["white"]),
        }))
    return _section([_section_head(props), _row(cards, gap_px=22, align="stretch")],
                    bg=props.get("bg", "white"))


@block("hero.banner")
def hero_banner(props):
    """Short full-bleed photo band with a centred uppercase title.

    This is the reference site's page header on every inner page — a wide
    image strip, not a tall split. `highlight` puts the title on a filled
    block, which is how their service pages treat it.
    """
    # The reference home page runs this band with no text at all — the pitch
    # lives in the split below it. An empty title yields a clean image strip.
    if not props.get("h1"):
        head = widget("spacer", {"space": slider(0)})
    elif props.get("highlight"):
        head = container([
            _heading(props["h1"], "h1", T["h_large"], align="center", on_dark=True),
        ], {
            "content_width": "full", "flex_direction": "column",
            "padding": dims(10, 28, 12, 28),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(C["ink_primary"])})
    else:
        head = _heading(props["h1"], "h1", T["h_large"], align="center", on_dark=True)

    sec = _section([_row([head], justify="center", extra={"flex_wrap": "nowrap"})],
                   bg="dark",
                   pad=dims(props.get("pad", 150), 24, props.get("pad", 150), 24),
                   extra={"flex_justify_content": "center",
                          "flex_align_items": "center",
                          "padding_mobile": dims(96, 20, 96, 20)})
    sec["settings"].update({
        "background_image": media(props["image"]["url"], props["image"]["alt"]),
        "background_position": "center center",
        "background_size": "cover",
        "background_repeat": "no-repeat",
        "background_overlay_background": "classic",
        "background_overlay_opacity": slider(props.get("overlay", 0.28)),
    })
    sec["settings"]["__globals__"]["background_overlay_color"] = color_ref("secondary")
    _scrim(sec, props.get("scrim", "bottom"), 0.80)
    # overlap_header removed: the header is a separate Theme Builder
    # document rendered before this one, so a negative top margin paints
    # the hero over the nav rather than tucking beneath it.
    return sec


@block("intro.split")
def intro_split(props):
    """Statement on the left, the actual pitch on the right.

    The reference home page uses this instead of headline-over-image: the
    left column is a short brand statement, the right carries the green
    heading, body copy and the call to action.
    """
    w_left, w_right = _tracks([40, 60], 56)
    left = _col([
        _heading(props["statement"], "h2", "primary", tone="dark"),
    ], w_left, extra={"flex_justify_content": "center"})

    right = _col([
        *( [widget("icon-list", {
            "icon_list": [repeater_item(text=b, selected_icon=icon("fas fa-star"),
                                        link=link("")) for b in props["badges"]],
            "view": "inline", "space_between": slider(18), "icon_size": slider(14),
        }, globals_={"icon_color": color_ref(C["ink_primary"]),
                     "text_color": color_ref("secondary"),
                     "icon_typography_typography": typo_ref(T["meta"])})]
           if props.get("badges") else [] ),
        _heading(props["heading"], "h2", T["h_large"], tone="brand"),
        _text(props["body"]),
        _row([
            _button(props["cta"]["label"], props["cta"]["href"], "accent"),
            *( [_button(props["cta2"]["label"], props["cta2"]["href"], "ghost", None)]
               if props.get("cta2") else [] ),
        ], gap_px=14, extra={"margin": dims(8, 0, 0, 0)}),
    ], w_right, extra={"flex_gap": gap(16), "flex_justify_content": "center"})

    return _section([_row([left, right], gap_px=56, align="center")],
                    bg=props.get("bg", "white"))


@block("process.band")
def process_band(props):
    """Numbered steps as small cards over a photograph — the reference site's
    'our installation process' treatment. The plain-background variant is
    process.steps."""
    n = len(props["steps"])
    w_step, _ = _grid_widths(n, 18)
    cards = []
    for i, st in enumerate(props["steps"], 1):
        cards.append(container([
            _eyebrow(f"Step {i}"),
            _heading(st["title"], "h3", T["h_small"], align="center"),
            *( [_text(st["text"], align="center", small=True)] if st.get("text") else [] ),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(6),
            "width": slider(w_step, "%"),
            "width_tablet": slider(_track(2, 18, TABLET_CONTAINER), "%"),
            "width_mobile": slider(100, "%"),
            "padding": dims(24, 16, 26, 16),
            "border_radius": box(14),
            "flex_align_items": "center",
            "background_background": "classic",
            **CARD_SHADOW_SOFT,
        }, globals_={"background_color": color_ref(C["white"])}))

    head = _col([_heading(props["heading"], "h2", T["h_large"], align="center",
                          on_dark=True)],
                extra={"flex_align_items": "center",
                       "margin": dims(0, "auto", 40, "auto")})
    sec = _section([head, _row(cards, gap_px=18, justify="center", align="stretch")],
                   bg="dark", pad=dims(84, 0, 84, 0))
    if props.get("background"):
        sec["settings"].update({
            "background_image": media(props["background"]["url"],
                                      props["background"]["alt"]),
            "background_position": "center center",
            "background_size": "cover",
            "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(0.6),
        })
        sec["settings"]["__globals__"]["background_overlay_color"] = color_ref("secondary")
    return sec


@block("checklist.split")
def checklist_split(props):
    """Image beside a stack of circled-check points — the reference site's
    'the <brand> way' section. Each point carries a bold lead and a sentence,
    which is what separates it from a plain bulleted list."""
    w_img, w_body = _tracks([46, 54], 44)
    img = _col([widget("image", {
        "image": media(props["image"]["url"], props["image"]["alt"]),
        "image_size": "full",
        "image_border_radius": box(18),
        "width": slider(100, "%"),
        "height": slider(props.get("image_height", 560)),
        "height_mobile": slider(320),
        "object-fit": "cover",
        "object-position": "center center",
    })], w_img)

    points = []
    for p in props["items"]:
        points.append(widget("icon-box", {
            "title_text": p["title"],
            "description_text": p.get("text", ""),
            "selected_icon": icon(p.get("icon", "fas fa-check")),
            "view": "stacked",
            "shape": "circle",
            "position": "left",
            "text_align": "left",
            "title_size": "h3",
            "icon_size": slider(13),
            "icon_padding": slider(9),
            "icon_space": slider(16),
            "title_bottom_space": slider(4),
        }, globals_={
            "primary_color": color_ref(C["ink_primary"]),
            "secondary_color": color_ref(C["white"]),
            "title_color": color_ref("secondary"),
            "description_color": color_ref("text"),
            "title_typography_typography": typo_ref(T["h_small"]),
            "description_typography_typography": typo_ref(T["body_small"]),
        }))

    # The points sit on a raised white card, not loose on the section — that
    # panel is what makes the reference layout read as deliberate.
    panel = container([
        *( [_eyebrow(props["eyebrow"])] if props.get("eyebrow") else [] ),
        _heading(props["heading"], "h2", T["h_large"], tone="brand"),
        *( [_text(props["intro"])] if props.get("intro") else [] ),
        *points,
        *( [_button(props["cta"]["label"], props["cta"]["href"], "accent")]
           if props.get("cta") else [] ),
    ], {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(18),
        "width": slider(w_body, "%"),
        "width_mobile": slider(100, "%"),
        "padding": dims(44, 44, 44, 44),
        "padding_mobile": dims(28, 22, 28, 22),
        "border_radius": box(20),
        "background_background": "classic",
        **CARD_SHADOW,
    }, globals_={"background_color": color_ref(C["white"])})

    order = [panel, img] if props.get("reverse") else [img, panel]
    return _section([_row(order, gap_px=44, align="center")],
                    bg=props.get("bg", "surface"))


@block("stats.band")
def stats_band(props):
    """Counters as dark cards over a photograph. The reference site uses this
    as the visual break between content blocks; a plain white counter row does
    not carry the same weight."""
    w_cell, _ = _grid_widths(len(props["items"]), 22)
    cells = []
    for i, s in enumerate(props["items"]):
        # The reference band leads with one inverted card so the row has an
        # entry point rather than reading as four identical tiles.
        lead = i == 0 and props.get("lead_card", True)
        cells.append(container([
            widget("counter", {
                "starting_number": 0,
                "ending_number": s["value"],
                "suffix": s.get("suffix", ""),
                "title": s["label"],
                "duration": 2000,
                "title_tag": "div",
            }, globals_={
                "number_color": color_ref(C["ink_primary"] if lead else C["white"]),
                "title_color": color_ref("secondary" if lead else C["on_dark"]),
                "typography_typography": typo_ref(T["hero"]),
                "title_typography_typography": typo_ref(T["meta"]),
            })
        ], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(w_cell, "%"),
            "width_tablet": slider(_track(2, 22, TABLET_CONTAINER), "%"),
            "width_mobile": slider(100, "%"),
            "padding": dims(34, 22, 34, 22),
            "border_radius": box(16),
            "flex_align_items": "center",
            "background_background": "classic",
        }, globals_={"background_color": color_ref(
            C["white"] if lead else "secondary")}))

    sec = _section([_row(cells, gap_px=22, justify="center")],
                   bg="dark", pad=dims(84, 0, 84, 0))
    if props.get("background"):
        sec["settings"].update({
            "background_image": media(props["background"]["url"],
                                      props["background"]["alt"]),
            "background_position": "center center",
            "background_size": "cover",
            "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(0.55),
        })
        sec["settings"]["__globals__"]["background_overlay_color"] = \
            color_ref("secondary")
    return sec


@block("cta.split")
def cta_split(props):
    """Closing call to action as a photograph beside the ask, rather than a
    flat colour band. Mixed-case heading — an uppercase section title reads as
    a label, and this is meant to read as an invitation."""
    w_img, w_body = _tracks([48, 52], 56)
    img = _col([widget("image", {
        "image": media(props["image"]["url"], props["image"]["alt"]),
        "image_size": "full",
        "image_border_radius": box(18),
        "width": slider(100, "%"),
        "height": slider(props.get("image_height", 380)),
        "height_mobile": slider(240),
        "object-fit": "cover",
        "object-position": "center center",
    })], w_img)

    body = _col([
        *( [_eyebrow(props["eyebrow"])] if props.get("eyebrow") else [] ),
        _heading(props["heading"], "h2", "primary", tone="dark"),
        *( [_text(props["text"])] if props.get("text") else [] ),
        _row([
            _button(props["cta"]["label"], props["cta"]["href"], "accent"),
            *( [_button(props["cta2"]["label"], props["cta2"]["href"], "ghost", None)]
               if props.get("cta2") else [] ),
        ], gap_px=14, extra={"margin": dims(10, 0, 0, 0)}),
    ], w_body, extra={"flex_gap": gap(16), "flex_justify_content": "center"})

    order = [body, img] if props.get("reverse") else [img, body]
    return _section([_row(order, gap_px=56, align="center")],
                    bg=props.get("bg", "surface"))


@block("list.cards")
def list_cards(props):
    """Service categories as cards, each a heading over a bulleted list.

    A services page that reads as one long list buries the breadth it is
    trying to show; grouping into named categories is what makes scope
    legible."""
    cols = props.get("columns", 2)
    width, width_t = _grid_widths(cols, 24)
    cards = []
    for it in props["items"]:
        cards.append(container([
            *( [widget("icon", {"selected_icon": icon(it["icon"]), "size": slider(24),
                                "align": "left", "view": "default"},
                       globals_={"primary_color": color_ref(C["ink_primary"])})]
               if it.get("icon") else [] ),
            _heading(it["title"], "h3", T["h_medium"]),
            *( [_text(it["text"], small=True)] if it.get("text") else [] ),
            widget("icon-list", {
                "icon_list": [repeater_item(text=b, selected_icon=icon("fas fa-check"),
                                            link=link("")) for b in it["points"]],
                "space_between": slider(11),
                "icon_size": slider(13),
            }, globals_={"icon_color": color_ref(C["ink_primary"]),
                         "text_color": color_ref("text"),
                         "icon_typography_typography": typo_ref(T["body_small"])}),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(12),
            "width": slider(width, "%"),
            "width_tablet": slider(width_t, "%"),
            "width_mobile": slider(100, "%"),
            "padding": box(32),
            "border_radius": box(16),
            "background_background": "classic",
            **CARD_SHADOW_SOFT,
        }, globals_={"background_color": color_ref(C["white"])}))

    children = [_section_head(props)] if props.get("heading") else []
    children.append(_row(cards, gap_px=24, align="stretch"))
    return _section(children, bg=props.get("bg", "surface"))


@block("badges.strip")
def badges_strip(props):
    """Third-party proof marks — Google, Facebook, Yelp, BBB, manufacturer.

    Five of eight references run this directly under the hero. It is the one
    place where borrowed authority is legitimate: these are badges the business
    has actually earned, supplied as image files, not claims this system makes.
    """
    items = props["items"]
    if props.get("use_addon"):
        strip = widget("ha-logo-grid", {
            "logo_list": [repeater_item(image=media(i["url"], i["alt"]),
                                        link=link(i.get("href", "")))
                          for i in items],
            "columns": str(min(len(items), 6)),
            "grid_border_radius": box(12),
        })
    else:
        # Core fallback: a plain row of images keeps the kit installable
        # without an addon pack.
        cells = []
        w = _track(min(len(items), 6), 28)
        for i in items:
            cells.append(_col([widget("image", {
                "image": media(i["url"], i["alt"]),
                "image_size": "full",
                "width": slider(props.get("logo_width", 130)),
                "align": "center",
            })], w, extra={"flex_align_items": "center",
                           "flex_justify_content": "center"}))
        strip = _row(cells, gap_px=28, justify="center", align="center")

    children = []
    if props.get("heading"):
        children.append(_col([_text(props["heading"], align="center", small=True)],
                             extra={"flex_align_items": "center",
                                    "margin": dims(0, "auto", 22, "auto")}))
    children.append(strip)
    return _section(children, bg=props.get("bg", "white"),
                    pad=dims(44, 0, 44, 0))


@block("note.panel")
def note_panel(props):
    """A single bordered panel for a caveat or disclosure — scope limits,
    licensing notes. Deliberately plain: it must not read as a promotion."""
    panel = container([
        _heading(props["heading"], "h3", T["h_small"]),
        _text(props["text"], small=True),
    ], {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(8),
        "padding": dims(26, 30, 28, 30),
        "border_radius": box(12),
        "border_border": "solid",
        "border_width": {"unit": "px", "top": "1", "right": "1",
                         "bottom": "1", "left": "5", "isLinked": False},
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["ink_primary"])})
    return _section([panel], bg=props.get("bg", "white"),
                    pad=dims(0, 0, 88, 0))


@block("hero.feature")
def hero_feature(props):
    """Photographic hero: chip, headline, checkmark grid, dual CTA.

    The copy sits over the image on one side rather than beside it, so the
    photograph carries the full width — the reference layout's opening move.
    """
    w_copy, _ = _tracks([58, 42], 40)
    left = _col([
        *( [_chip(props["eyebrow"], props.get("eyebrow_icon", "fas fa-location-dot"),
                  on_dark=True)] if props.get("eyebrow") else [] ),
        _heading(props["h1"], "h1", T["hero"], on_dark=True),
        *( [_text(props["intro"], on_dark=True)] if props.get("intro") else [] ),
        *( [_ticks(props["ticks"], on_dark=True)] if props.get("ticks") else [] ),
        _row([
            _button(props["cta"]["label"], props["cta"]["href"], "accent"),
            *( [_button(props["cta2"]["label"], props["cta2"]["href"], "ghost_dark", None)]
               if props.get("cta2") else [] ),
        ], gap_px=14, extra={"margin": dims(14, 0, 0, 0)}),
    ], w_copy, extra={"flex_gap": gap(20), "flex_justify_content": "center"})

    sec = _section([_row([left], align="center")], bg="dark",
                   pad=dims(150, 0, 170, 0),
                   extra={"min_height": slider(props.get("min_height", 76), "vh"),
                          "flex_justify_content": "center",
                          "padding_mobile": dims(110, 20, 120, 20)})
    sec["settings"].update({
        "background_image": media(props["image"]["url"], props["image"]["alt"]),
        "background_position": props.get("focus", "center center"),
        "background_size": "cover",
        "background_repeat": "no-repeat",
        "background_overlay_background": "classic",
        "background_overlay_opacity": slider(props.get("overlay", 0.30)),
    })
    sec["settings"]["__globals__"]["background_overlay_color"] = color_ref("secondary")
    _scrim(sec, props.get("scrim", "left"), 0.90)
    # overlap_header removed: the header is a separate Theme Builder
    # document rendered before this one, so a negative top margin paints
    # the hero over the nav rather than tucking beneath it.
    return sec


@block("form.bar")
def form_bar(props):
    """Short capture form on a raised card that overlaps the hero above it.

    Putting the form above the fold is the single biggest conversion lever on
    a local-service page; the negative margin is what makes it read as one
    unit with the hero rather than a separate band.
    """
    fields = []
    n = max(1, len(props["fields"]))
    fw = str(int(100 / (n + 1)))
    for f in props["fields"]:
        item = {
            "custom_id": f["id"],
            "field_type": f.get("type", "text"),
            "field_label": f["label"],
            "placeholder": f.get("placeholder", f["label"]),
            "required": "true" if f.get("required") else "",
            "width": fw,
        }
        if f.get("options"):
            item["field_options"] = "\n".join(f["options"])
        fields.append(repeater_item(**item))

    form = widget("form", {
        "form_name": props.get("form_name", "Quick Quote"),
        "submit_actions": ["email"],
        "form_fields": fields,
        "button_text": props.get("submit_label", "Submit"),
        "button_size": "md",
        "button_width": fw,
        "input_size": "md",
        "show_labels": "",
        "row_gap": slider(12),
        "column_gap": slider(12),
        "success_message": props.get("success_message", "Thanks — we'll be in touch."),
        "email_to": props.get("email", ""),
        "email_subject": f"Quote request — {props.get('business', 'website')}",
    }, globals_={
        "button_background_color": color_ref(C["accent_fill"]),
        "button_text_color": color_ref(C["on_accent"]),
        "field_text_color": color_ref("secondary"),
    })

    card = container([
        _row([
            _col([_heading(props["heading"], "h2", T["h_medium"])], 30),
            _col([widget("icon-list", {
                "icon_list": [repeater_item(text=t, selected_icon=icon("fas fa-circle-check"),
                                            link=link("")) for t in props.get("ticks", [])],
                "view": "inline", "space_between": slider(22), "icon_size": slider(14),
            }, globals_={"icon_color": color_ref(C["ink_primary"]),
                         "text_color": color_ref("text"),
                         "icon_typography_typography": typo_ref(T["meta"])})], 68)
            if props.get("ticks") else _col([], 68),
        ], gap_px=24, align="center"),
        form,
    ], {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(18),
        "padding": dims(28, 30, 30, 30),
        "padding_mobile": dims(22, 18, 24, 18),
        "border_radius": box(16),
        "background_background": "classic",
        **CARD_SHADOW,
    }, globals_={"background_color": color_ref(C["white"])})

    return _section([card], bg=props.get("bg", "surface"),
                    pad=dims(0, 0, 72, 0),
                    extra={"margin": dims(-86, 0, 0, 0),
                           "margin_mobile": dims(-56, 0, 0, 0)})


@block("about.collage")
def about_collage(props):
    """Three-photo collage beside the copy — one tall frame plus a stacked
    pair, which reads as a body of work rather than a single staged shot."""
    w_img, w_body = _tracks([48, 52], 52)
    imgs = props["images"]
    lead, rest = imgs[0], imgs[1:3]
    collage = _col([
        _photo(lead, props.get("lead_height", 300), radius=16),
        *( [_row([
            _col([_photo(r, 190, radius=14)], w)
            for r, w in zip(rest, _tracks([1] * len(rest), 16))
        ], gap_px=16)] if rest else [] ),
    ], w_img, extra={"flex_gap": gap(16)})

    body = _col([
        *( [_chip(props["eyebrow"], props.get("eyebrow_icon", "fas fa-user"))]
           if props.get("eyebrow") else [] ),
        _heading(props["heading"], "h2", T["h_large"], tone="brand"),
        _text(props["body"]),
        *( [_button(props["cta"]["label"], props["cta"]["href"], "accent")]
           if props.get("cta") else [] ),
    ], w_body, extra={"flex_gap": gap(16), "flex_justify_content": "center"})

    order = [body, collage] if props.get("reverse") else [collage, body]
    return _section([_row(order, gap_px=52, align="center")],
                    bg=props.get("bg", "white"))


@block("why.panel")
def why_panel(props):
    """Reasons stacked under a filled highlight card, set beside the section
    heading and a photograph."""
    w_left, w_right = _tracks([46, 54], 48)
    # Which ground the reason rows sit on. `_dk` belongs to the editorial
    # family and reads a different bg vocabulary, so it cannot answer this;
    # `_section`'s two dark grounds are the whole set.
    dk = props.get("bg", "surface") in ("dark", "primary")

    highlight = container([
        _heading(props["highlight"]["title"], "h3", T["h_small"], on_dark=True),
        _text(props["highlight"]["text"], on_dark=True, small=True),
    ], {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(8),
        "padding": dims(24, 26, 26, 26),
        "border_radius": box(14),
        "background_background": "classic",
    }, globals_={"background_color": color_ref("primary")})

    rows = [highlight]
    for it in props["items"]:
        rows.append(container([
            _heading(it["title"], "h3", T["h_small"]),
            _text(it["text"], small=True),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(6),
            "padding": dims(18, 0, 18, 0),
            "border_border": "solid",
            "border_width": {"unit": "px", "top": "0", "right": "0",
                             "bottom": "1", "left": "0", "isLinked": False},
        }, globals_={"border_color": color_ref(
            C["rule_dark"] if dk else C["border"])}))

    left = _col(rows, w_left, extra={"flex_gap": gap(0)})
    right = _col([
        *( [_chip(props["eyebrow"], props.get("eyebrow_icon", "fas fa-thumbs-up"))]
           if props.get("eyebrow") else [] ),
        _heading(props["heading"], "h2", T["h_large"], tone="brand"),
        *( [_text(props["intro"])] if props.get("intro") else [] ),
        *( [_photo(props["image"], props.get("image_height", 320), radius=16)]
           if props.get("image") else [] ),
    ], w_right, extra={"flex_gap": gap(18)})

    return _section([_row([left, right], gap_px=48, align="flex-start")],
                    bg=props.get("bg", "surface"))


@block("areas.chips")
def areas_chips(props):
    """Coverage map above the locations as pills. Pills scan far faster than
    a bulleted list once the count passes about eight."""
    head = _col([
        *( [_chip(props["eyebrow"], props.get("eyebrow_icon", "fas fa-map-location-dot"),
                  align="center")] if props.get("eyebrow") else [] ),
        _heading(props["heading"], "h2", T["h_large"], align="center", tone="brand"),
        *( [_text(props["intro"], align="center")] if props.get("intro") else [] ),
    ], extra={"flex_align_items": "center", "content_width": "boxed", "boxed_width": slider(820),
              "margin": dims(0, "auto", 40, "auto")})

    children = [head]
    if props.get("map_query"):
        children.append(container([widget("google_maps", {
            "address": props["map_query"],
            "zoom": slider(props.get("zoom", 9)),
            "height": slider(430),
            "height_mobile": slider(260),
        })], {
            "content_width": "full", "flex_direction": "column",
            "border_radius": box(16), "overflow": "hidden",
            "margin": dims(0, 0, 32, 0),
        }))

    # `panel: dark` lifts the pills onto a filled card that overlaps the map,
    # so the coverage list reads as one object with it rather than a caption.
    dark = props.get("panel") == "dark"
    pills = []
    for a in props["areas"]:
        pills.append(container([
            widget("icon", {"selected_icon": icon("fas fa-location-dot"),
                            "size": slider(12), "align": "center", "view": "default"},
                   globals_={"primary_color": color_ref(
                       C["brand_on_dark"] if dark else C["ink_primary"])}),
            widget("heading", {"title": a["name"], "header_size": "div", "align": "left"},
                   globals_={"title_color": color_ref(C["white"] if dark else "secondary"),
                             "typography_typography": typo_ref(T["meta"])}),
        ], {
            "content_width": "full", "flex_direction": "row",
            "flex_gap": gap(8), "flex_align_items": "center",
            "padding": dims(10, 18, 10, 18),
            "border_radius": box(999),
            "border_border": "solid", "border_width": box(1),
            "background_background": "classic",
        }, globals_={
            "background_color": color_ref(C["overlay"] if dark else C["white"]),
            "border_color": color_ref(C["rule_dark"] if dark else C["border"]),
        }))

    if dark:
        inner = [_row(pills, gap_px=12, justify="center")]
        if props.get("cta"):
            inner.append(_row([_button(props["cta"]["label"], props["cta"]["href"],
                                       "accent")], justify="center",
                              extra={"margin": dims(22, 0, 0, 0)}))
        children.append(container(inner, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(0),
            "padding": dims(34, 34, 36, 34),
            "padding_mobile": dims(24, 18, 26, 18),
            "border_radius": box(18),
            "margin": dims(-64, 0, 0, 0),
            "margin_mobile": dims(-32, 0, 0, 0),
            "background_background": "classic",
        }, globals_={"background_color": color_ref("secondary")}))
    else:
        children.append(_row(pills, gap_px=12, justify="center"))
    return _section(children, bg=props.get("bg", "white"))


@block("faq.split")
def faq_split(props):
    """Heading and a route onward on the left, questions on the right — keeps
    the accordion from floating in the middle of a wide page."""
    w_left, w_right = _tracks([38, 62], 52)
    left = _col([
        *( [_chip(props["eyebrow"], props.get("eyebrow_icon", "fas fa-circle-question"))]
           if props.get("eyebrow") else [] ),
        _heading(props["heading"], "h2", T["h_large"], tone="brand"),
        *( [_text(props["intro"])] if props.get("intro") else [] ),
        *( [_button(props["cta"]["label"], props["cta"]["href"], "accent")]
           if props.get("cta") else [] ),
    ], w_left, extra={"flex_gap": gap(16), "flex_justify_content": "flex-start"})

    acc = _faq(props["items"], props.get("first_open", True))
    right = _col([acc], w_right)
    return _section([_row([left, right], gap_px=52, align="flex-start")],
                    bg=props.get("bg", "surface"))


@block("cta.panel")
def cta_panel(props):
    """Closing call to action as a filled panel inset from the page edge,
    with the photograph inside the panel rather than beside it."""
    w_body, w_img = _tracks([56, 44], 40)
    body = _col([
        _heading(props["heading"], "h2", T["h_large"], on_dark=True),
        *( [_text(props["text"], on_dark=True)] if props.get("text") else [] ),
        _row([
            _button(props["cta"]["label"], props["cta"]["href"], "accent"),
            *( [_button(props["cta2"]["label"], props["cta2"]["href"], "ghost_dark", None)]
               if props.get("cta2") else [] ),
        ], gap_px=14, extra={"margin": dims(8, 0, 0, 0)}),
    ], w_body, extra={"flex_gap": gap(16), "flex_justify_content": "center"})

    kids = [body]
    if props.get("image"):
        kids.append(_col([_photo(props["image"], props.get("image_height", 300),
                                 radius=14)], w_img))

    panel_settings = {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(52, 52, 52, 52),
        "padding_mobile": dims(32, 22, 32, 22),
        "border_radius": box(22),
        "background_background": "classic",
    }
    # Filled with the dark ground, not the brand colour: white copy on a
    # mid-tone brand fill rarely clears 4.5:1.
    panel_globals = {"background_color": color_ref(props.get("fill", "secondary"))}
    if props.get("background"):
        panel_settings.update({
            "background_image": media(props["background"]["url"],
                                      props["background"]["alt"]),
            "background_position": "center center",
            "background_size": "cover",
            "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(0.78),
        })
        panel_globals["background_overlay_color"] = color_ref("secondary")

    panel = container([_row(kids, gap_px=40, align="center")],
                      panel_settings, globals_=panel_globals)
    return _section([panel], bg=props.get("bg", "surface"))


@block("reviews.embed")
def reviews_embed(props):
    """A slot for a real reviews widget rather than authored testimonials.

    The shortcode goes in a text-editor widget, which WordPress runs through
    the_content — so plugin shortcodes render normally. Using this instead of
    hand-written review cards means the page never shows a testimonial the
    business did not actually receive.
    """
    slot = container([
        widget("text-editor", {
            "editor": props["shortcode"],
            "align": "center",
        }, globals_={
            "text_color": color_ref("text"),
            "typography_typography": typo_ref("text"),
        }),
    ], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(36, 30, 36, 30),
        "padding_mobile": dims(24, 18, 24, 18),
        "border_radius": box(18),
        "background_background": "classic",
        **CARD_SHADOW_SOFT,
    }, globals_={"background_color": color_ref(C["white"])})

    children = [_section_head(props), slot]
    if props.get("note"):
        children.append(_col([_text(props["note"], align="center", small=True)],
                             extra={"flex_align_items": "center",
                                    "margin": dims(18, "auto", 0, "auto")}))
    return _section(children, bg=props.get("bg", "surface"))


@block("hero.impact")
def hero_impact(props):
    """Dark ground, copy on the left, photograph on the right.

    Differs from hero.split in weight rather than structure: an oversized
    headline, a chip above it, and a row of proof badges beneath the buttons.
    """
    w_left, w_right = _tracks([54, 46], 44)
    left = _col([
        *( [_chip(props["eyebrow"], props.get("eyebrow_icon", "fas fa-location-dot"),
                  on_dark=True)] if props.get("eyebrow") else [] ),
        _heading(props["h1"], "h1", T["hero"], on_dark=True),
        *( [_text(props["intro"], on_dark=True)] if props.get("intro") else [] ),
        _row([
            _button(props["cta"]["label"], props["cta"]["href"], "accent"),
            *( [_button(props["cta2"]["label"], props["cta2"]["href"], "ghost_dark", None)]
               if props.get("cta2") else [] ),
        ], gap_px=14, extra={"margin": dims(6, 0, 0, 0)}),
        *( [widget("icon-list", {
            "icon_list": [repeater_item(text=b, selected_icon=icon("fas fa-star"),
                                        link=link("")) for b in props["badges"]],
            "view": "inline", "space_between": slider(24), "icon_size": slider(14),
        }, globals_={"icon_color": color_ref(C["brand_on_dark"]),
                     "text_color": color_ref(C["on_dark"]),
                     "icon_typography_typography": typo_ref(T["meta"])})]
           if props.get("badges") else [] ),
    ], w_left, extra={"flex_gap": gap(20), "flex_justify_content": "center"})

    right = _col([_photo(props["image"], props.get("image_height", 440), radius=18)],
                 w_right)

    sec = _section([_row([left, right], gap_px=44, align="center")],
                   bg="dark", pad=dims(96, 0, 96, 0),
                   extra={"flex_justify_content": "center"})
    # overlap_header removed: the header is a separate Theme Builder
    # document rendered before this one, so a negative top margin paints
    # the hero over the nav rather than tucking beneath it.
    return sec


@block("why.split")
def why_split(props):
    """Photograph plus two proof badges on one side, the argument on the other."""
    w_img, w_body = _tracks([46, 54], 48)
    badges = []
    for b in props.get("badges", []):
        badges.append(container([
            widget("icon", {"selected_icon": icon(b.get("icon", "fas fa-bolt")),
                            "size": slider(20), "align": "left", "view": "default"},
                   globals_={"primary_color": color_ref(C["ink_primary"])}),
            _heading(b["title"], "h3", T["h_small"]),
            *( [_text(b["text"], small=True)] if b.get("text") else [] ),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(6),
            "width": slider(_track(2, 16), "%"),
            "width_mobile": slider(100, "%"),
            "padding": box(20),
            "border_radius": box(14),
            "background_background": "classic",
            **CARD_SHADOW_SOFT,
        }, globals_={"background_color": color_ref(C["white"])}))

    img_col = _col([
        _photo(props["image"], props.get("image_height", 380), radius=18),
        *( [_row(badges, gap_px=16)] if badges else [] ),
    ], w_img, extra={"flex_gap": gap(18)})

    body = _col([
        *( [_chip(props["eyebrow"], props.get("eyebrow_icon", "fas fa-thumbs-up"))]
           if props.get("eyebrow") else [] ),
        _heading(props["heading"], "h2", T["h_large"], tone="brand"),
        *( [_text(props["intro"])] if props.get("intro") else [] ),
        *( [_ticks(props["ticks"], columns=1)] if props.get("ticks") else [] ),
        *( [_button(props["cta"]["label"], props["cta"]["href"], "accent")]
           if props.get("cta") else [] ),
    ], w_body, extra={"flex_gap": gap(18), "flex_justify_content": "center"})

    return _section([_row([img_col, body], gap_px=48, align="center")],
                    bg=props.get("bg", "white"))


@block("process.split")
def process_split(props):
    """Numbered steps beside the pitch, on a dark ground."""
    w_left, w_right = _tracks([46, 54], 48)
    left = _col([
        *( [_chip(props["eyebrow"], props.get("eyebrow_icon", "fas fa-list-check"),
                  on_dark=True)] if props.get("eyebrow") else [] ),
        _heading(props["heading"], "h2", T["h_large"], on_dark=True),
        *( [_text(props["intro"], on_dark=True)] if props.get("intro") else [] ),
        *( [_button(props["cta"]["label"], props["cta"]["href"], "accent")]
           if props.get("cta") else [] ),
        *( [_photo(props["image"], props.get("image_height", 260), radius=16)]
           if props.get("image") else [] ),
    ], w_left, extra={"flex_gap": gap(18)})

    steps = []
    for n, st in enumerate(props["steps"], 1):
        steps.append(container([
            _chip(f"Step {n:02d}", "fas fa-circle-dot", on_dark=True),
            _heading(st["title"], "h3", T["h_small"], on_dark=True),
            _text(st["text"], on_dark=True, small=True),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(8),
            "padding": dims(22, 24, 24, 24),
            "border_radius": box(14),
            "border_border": "solid", "border_width": box(1),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(C["overlay"]),
                     "border_color": color_ref(C["rule_dark"])}))
    right = _col(steps, w_right, extra={"flex_gap": gap(14)})

    return _section([_row([left, right], gap_px=48, align="flex-start")],
                    bg="dark")


@block("marquee.strip")
def marquee_strip(props):
    """Scrolling band of repeated phrases between sections.

    Built from one text widget rather than an addon: the phrase list is
    duplicated in the markup and the track translated by exactly half its
    width, which is what makes the loop seamless. `reduced motion` is
    honoured because a permanently moving band is an accessibility problem.
    """
    sep = props.get("separator", "✳")
    items = props["items"]
    run = ("&nbsp;&nbsp;%s&nbsp;&nbsp;" % sep).join(items)
    # Duplicated twice so the -50% translation lands on an identical frame.
    html = (f'<span class="mq">{run}&nbsp;&nbsp;{sep}&nbsp;&nbsp;</span>'
            f'<span class="mq">{run}&nbsp;&nbsp;{sep}&nbsp;&nbsp;</span>')

    text = widget("text-editor", {"editor": html, "align": "left"},
                  globals_={
                      "text_color": color_ref(
                          C["on_accent"] if props.get("fill", "accent") == "accent"
                          else C["white"]),
                      "typography_typography": typo_ref(T["h_medium"]),
                  })
    text["settings"]["custom_css"] = css(
        "selector { overflow: hidden; }",
        "selector .elementor-widget-container { display: flex; width: max-content; "
        f"animation: forge-mq {props.get('seconds', 34)}s linear infinite; }}",
        "selector .mq { white-space: nowrap; }",
        "selector:hover .elementor-widget-container { animation-play-state: paused; }",
        "@media (prefers-reduced-motion: reduce) { selector "
        ".elementor-widget-container { animation: none; } }",
        "@keyframes forge-mq { from { transform: translateX(0); } "
        "to { transform: translateX(-50%); } }",
    )

    sec = _section([text], bg=props.get("bg", "primary"),
                   pad=dims(18, 0, 18, 0),
                   extra={"content_width": "full",
                          "padding_mobile": dims(14, 0, 14, 0)})
    sec["settings"]["__globals__"]["background_color"] = color_ref(
        props.get("fill", "accent"))
    return sec


@block("gallery.compare")
def gallery_compare(props):
    """Before / after with a draggable handle.

    Elementor has no comparison widget in core or Pro, so this is the one
    place the kit depends on an addon. Falls back to gallery.pairs when the
    plugin is absent.
    """
    cards = []
    w = _track(props.get("columns", 2), 22)
    for p in props["items"]:
        cmp_widget = widget("ha-image-compare", {
            "before_image": media(p["before"]["url"], p["before"]["alt"]),
            "after_image": media(p["after"]["url"], p["after"]["alt"]),
            "before_label": props.get("before_label", "Before"),
            "after_label": props.get("after_label", "After"),
            "orientation": "horizontal",
            "default_offset_pct": slider(0.5),
            "move_slider_on_hover": "yes",
        })
        cards.append(container([
            cmp_widget,
            *( [_text(p["caption"], small=True)] if p.get("caption") else [] ),
        ], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(12),
            "width": slider(w, "%"),
            "width_mobile": slider(100, "%"),
            "padding": box(14),
            "border_radius": box(18),
            "background_background": "classic",
            **CARD_SHADOW_SOFT,
        }, globals_={"background_color": color_ref(C["white"])}))

    return _section([_section_head(props), _row(cards, gap_px=22)],
                    bg=props.get("bg", "surface"))


@block("archive.posts")
def archive_posts(props):
    """Archive template — one document driving every post in a collection.

    The alternative is a page template per post, which turns 43 blog entries
    into 43 hand-maintained templates. An archive plus a single template is
    what Theme Builder exists for, and it keeps the content in WordPress
    where the client can edit it.
    """
    head = _col([
        widget("theme-archive-title", {"align": "center"}, globals_={
            "title_color": color_ref("secondary"),
            "typography_typography": typo_ref(T["h_large"]),
        }),
        *( [_text(props["intro"], align="center")] if props.get("intro") else [] ),
    ], extra={"flex_align_items": "center", "content_width": "boxed", "boxed_width": slider(820),
              "margin": dims(0, "auto", 44, "auto")})

    # No posts-per-page control: an archive widget renders the query WordPress
    # already resolved for that archive, so the count is a WP setting, not a
    # widget one.
    grid = widget("archive-posts", {
        "columns": str(props.get("columns", 3)),
        "show_read_more": "yes",
        "read_more_text": props.get("more_label", "Read More"),
        "pagination_type": "numbers",
        "item_gap": gap(28),
    }, globals_={
        "title_color": color_ref("secondary"),
        "title_typography_typography": typo_ref(T["h_medium"]),
        "excerpt_color": color_ref("text"),
        "excerpt_typography_typography": typo_ref(T["body_small"]),
    })
    return _section([head, grid], bg=props.get("bg", "surface"))


@block("single.post")
def single_post(props):
    """Single template. Every value is a dynamic binding, never literal copy —
    the document is a shell that WordPress fills per post."""
    hero = _section([
        _col([
            widget("theme-post-title", {"header_size": "h1", "align": "center"},
                   globals_={
                       "title_color": color_ref(C["white"]),
                       "typography_typography": typo_ref(T["h_large"]),
                   }),
            *( [widget("post-info", {
                "icon_align": "left",
                "view": "inline",
            }, globals_={"text_color": color_ref(C["on_dark"]),
                         "icon_color": color_ref(C["brand_on_dark"]),
                         "typography_typography": typo_ref(T["meta"])})]
               if props.get("show_meta", True) else [] ),
        ], extra={"flex_align_items": "center", "content_width": "boxed", "boxed_width": slider(880),
                  "margin": dims(0, "auto", 0, "auto")}),
    ], bg="dark", pad=dims(96, 24, 96, 24))

    featured = _section([
        container([widget("theme-post-featured-image", {
            "image_size": "large",
            "align": "center",
            "image_border_radius": box(16),
        })], {
            "content_width": "full", "flex_direction": "column",
            "margin": dims(-56, 0, 0, 0),
        }),
    ], bg=props.get("bg", "white"), pad=dims(0, 0, 40, 0))

    body = _section([
        _col([widget("theme-post-content", {}, globals_={
            "text_color": color_ref("text"),
            "typography_typography": typo_ref("text"),
        })], 74, extra={"margin": dims(0, "auto", 0, "auto")}),
    ], bg=props.get("bg", "white"), pad=dims(8, 0, 88, 0))

    out = [hero, featured, body]
    if props.get("cta"):
        out.append(render("cta.panel", {
            "heading": props["cta"]["heading"],
            "text": props["cta"].get("text", ""),
            "cta": props["cta"]["cta"],
            "bg": "surface",
        }))
    return container(out, {"content_width": "full", "flex_direction": "column",
                           "flex_gap": gap(0)})


# ───────────────── consolidated service + area architecture ─────────────────
#
# A client with 81 services and 53 cities does not want 134 pages, and Google
# does not reward them — near-duplicate thin pages get discounted, and a city
# page with nothing local to say is a doorway page. These factories put every
# service and every city on the page as its own anchored heading instead, so
# the keyword coverage is complete while the page count stays reviewable.


@block("services.sections")
def services_sections(props):
    """Every service in a category as its own anchored H2.

    `items`: [{name, slug, body}] — `name` is the client's exact wording,
    because that string is the keyword. `slug` becomes the CSS id, so a menu
    can deep-link /residential-hvac#air-conditioning-repair.
    """
    items = props["items"]
    w = _tracks([50, 50], 32)[0]

    cards = []
    for it in items:
        inner = [_heading(it["name"], "h2", T["h_small"], tone="dark")]
        if it.get("body"):
            inner.append(_text(it["body"], small=True))
        cards.append(_col(inner, w, extra={
            "_element_id": it["slug"],
            "background_background": "classic",
            "padding": dims(28, 28, 28, 28),
            "border_radius": box(8),
            "flex_gap": gap(10),
            **CARD_SHADOW_SOFT,
        }))

    head = []
    if props.get("eyebrow"):
        head.append(_eyebrow(props["eyebrow"]))
    head.append(_heading(props.get("heading", "What We Repair"), "h2",
                         T["h_large"], tone="brand"))
    if props.get("intro"):
        head.append(_text(props["intro"]))

    return _section([
        _col(head, extra={"margin": dims(0, 0, 40, 0)}),
        _row(cards, 32),
    ], bg=props.get("bg", "surface"))


@block("services.index")
def services_index(props):
    """The All Services page — every group, every service, as linked text.

    `groups`: [{name, slug, items: [{name, slug}]}]. Renders the complete
    catalogue in one screenful of scannable columns, each entry linking to its
    anchor on the category page.
    """
    groups = props["groups"]
    w = _tracks([50, 50], 32)[0]

    cols = []
    for g in groups:
        links = [repeater_item(
            text=it["name"],
            selected_icon=icon("fas fa-angle-right"),
            link=link(f"/{g['slug']}#{it['slug']}"),
        ) for it in g["items"]]
        cols.append(_col([
            _heading(f"{g['name']} ({len(g['items'])})", "h2", T["h_small"],
                     tone="brand"),
            widget("icon-list", {
                "icon_list": links,
                "space_between": slider(6),
                "icon_size": slider(13),
            }, globals_={
                "icon_color": color_ref(C["ink_primary"]),
                "text_color": color_ref("text"),
                "icon_typography_typography": typo_ref(T["body_small"]),
            }),
        ], w, extra={"flex_gap": gap(14), "margin": dims(0, 0, 36, 0)}))

    head = [_heading(props.get("heading", "Every Service We Offer"), "h2",
                     T["h_large"], align="center", tone="brand")]
    if props.get("intro"):
        head.append(_text(props["intro"], align="center"))

    return _section([
        _col(head, extra={"flex_align_items": "center",
                          "margin": dims(0, 0, 44, 0)}),
        _row(cols, 32),
    ], bg=props.get("bg", "white"))


@block("areas.counties")
def areas_counties(props):
    """All service cities, grouped by county, each an anchored entry.

    `counties`: [{name, slug, cities: [{name, slug}]}]. Replaces one thin page
    per city with one substantial page per county plus a complete on-page list.
    """
    blocks = []
    for c in props["counties"]:
        chips = [widget("button", {
            "text": city["name"],
            "link": link(f"/{c['slug']}#{city['slug']}"),
            "size": "sm",
            "border_radius": box(50),
            "button_padding": dims(9, 18, 9, 18),
            "align": "left",
            "_element_id": city["slug"],
        }, globals_={
            "button_text_color": color_ref("text"),
            "button_background_color": color_ref(C["white"]),
            "typography_typography": typo_ref(T["meta"]),
        }) for city in c["cities"]]

        blocks.append(_col([
            _heading(f"{c['name']} ({len(c['cities'])} cities)", "h3",
                     T["h_small"], tone="brand"),
            _row(chips, 10, extra={"flex_wrap": "wrap",
                                   "flex_direction_mobile": "row"}),
        ], extra={"flex_gap": gap(16), "margin": dims(0, 0, 34, 0)}))

    head = []
    if props.get("eyebrow"):
        head.append(_eyebrow(props["eyebrow"]))
    head.append(_heading(props.get("heading", "Areas We Serve"), "h2",
                         T["h_large"], tone="brand"))
    if props.get("intro"):
        head.append(_text(props["intro"]))

    return _section([
        _col(head, extra={"margin": dims(0, 0, 40, 0)}),
        _col(blocks),
    ], bg=props.get("bg", "surface"))


@block("brands.grid")
def brands_grid(props):
    """Manufacturer logo wall. Plain containers rather than an addon widget —
    a logo grid is not worth a plugin dependency on the client's site."""
    per_row = props.get("columns", 6)
    w = _tracks([1] * per_row, 20)[0]
    cells = [_col([widget("image", {
        "image": media(b["logo"], b.get("alt") or f"{b['name']} appliance and HVAC repair"),
        "align": "center",
        "width": slider(100, "%"),
    })], w, extra={
        "background_background": "classic",
        "padding": dims(18, 14, 18, 14),
        "border_radius": box(8),
        "flex_justify_content": "center",
    }) for b in props["brands"]]

    head = [_heading(props.get("heading", "We Service All Major Brands & Models"),
                     "h2", T["h_large"], align="center", tone="brand")]
    if props.get("intro"):
        head.append(_text(props["intro"], align="center"))

    return _section([
        _col(head, extra={"flex_align_items": "center",
                          "margin": dims(0, 0, 36, 0)}),
        _row(cells, 20),
    ], bg=props.get("bg", "white"))


@block("reviews.platforms")
def reviews_platforms(props):
    """Review-platform strip: rating, then one card per platform.

    Mirrors the reference, which runs this twice — once high on the page and
    once as a ratings band lower down.
    """
    w = _tracks([1] * max(1, len(props["platforms"])), 24)[0]
    cards = []
    for p in props["platforms"]:
        inner = []
        if p.get("logo"):
            inner.append(widget("image", {
                "image": media(p["logo"], f"{p['name']} reviews"),
                "align": "center", "width": slider(120),
            }))
        else:
            inner.append(_heading(p["name"], "h3", T["h_small"], align="center"))
        if p.get("rating"):
            inner.append(widget("star-rating", {
                "rating": p["rating"], "rating_scale": "5", "align": "center",
                "star_style": "star_fontawesome",
            }, globals_={"stars_color": color_ref("accent")}))
        if p.get("url"):
            inner.append(widget("button", {
                "text": props.get("link_label", "View Reviews"),
                "link": link(p["url"], external=True),
                "size": "sm", "align": "center",
                "border_radius": box(8),
                "button_padding": dims(11, 22, 11, 22),
            }, globals_={
                "button_background_color": color_ref("primary"),
                "button_text_color": color_ref(C["on_primary"]),
                "typography_typography": typo_ref(T["meta"]),
            }))
        cards.append(_col(inner, w, extra={
            "background_background": "classic",
            "padding": dims(26, 20, 26, 20),
            "border_radius": box(8),
            "flex_align_items": "center",
            "flex_gap": gap(12),
            **CARD_SHADOW_SOFT,
        }))

    head = []
    if props.get("average"):
        head.append(_heading(f"{props['average']} Average Rating", "h2",
                             T["h_large"], align="center", tone="brand"))
    else:
        head.append(_heading(props.get("heading", "Check Out Our Reviews"), "h2",
                             T["h_large"], align="center", tone="brand"))
    if props.get("intro"):
        head.append(_text(props["intro"], align="center"))

    return _section([
        _col(head, extra={"flex_align_items": "center",
                          "margin": dims(0, 0, 34, 0)}),
        _row(cards, 24, justify="center"),
    ], bg=props.get("bg", "white"))


@block("header.store")
def header_store(props):
    """Light header with a phone link beside the booking CTA.

    `header.simple` carries one CTA; the reference pairs a tappable phone
    number with a Book Now button, which is the shape that converts on a
    repair site. The logo falls through to Site Identity when no URL is set,
    so the client can upload it in WordPress without a rebuild.
    """
    logo = widget("theme-site-logo", {
        "align": "left", "width": slider(props.get("logo_width", 170)),
        **({"image": media(props["logo"], props.get("business", ""))}
           if props.get("logo") else {}),
    })
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal",
        "align_items": "end",
        "pointer": "underline",
        "menu_space_between": slider(22),
        "toggle_align": "right",
    }, globals_={
        "color_menu_item": color_ref("secondary"),
        "color_menu_item_hover": color_ref("primary"),
        "color_menu_item_active": color_ref("primary"),
        "menu_typography_typography": typo_ref("accent"),
    })

    actions = []
    if props.get("phone"):
        actions.append(widget("button", {
            "text": props.get("phone_display") or props["phone"],
            "link": link(f"tel:{props['phone']}"),
            "selected_icon": icon("fas fa-phone"),
            "icon_align": "left",
            "text_padding": dims(14, 18, 14, 18),
            "border_radius": box(8),
            "border_border": "solid",
            "border_width": box(1),
        }, globals_={
            "button_text_color": color_ref("secondary"),
            "background_color": color_ref(C["transparent"]),
            "border_color": color_ref(C["border"]),
            "hover_color": color_ref(C["white"]),
            "button_background_hover_color": color_ref("secondary"),
            "button_hover_border_color": color_ref("secondary"),
            "typography_typography": typo_ref("accent"),
        }))
    if props.get("cta"):
        actions.append(_button(props["cta"]["label"], props["cta"]["href"],
                               "accent", "fas fa-calendar-check"))

    w_logo, w_nav, w_cta = _tracks([16, 56, 28], 20)
    bar = container([
        _row([
            _col([logo], w_logo, extra={"flex_justify_content": "center"}),
            _col([nav], w_nav, extra={"flex_justify_content": "center"}),
            _col([_row(actions, 10, align="center", justify="flex-end",
                       extra={"flex_direction_mobile": "row"})], w_cta,
                 extra={"flex_justify_content": "center"}),
        ], gap_px=20, align="center")
    ], {
        "content_width": "boxed",
        "flex_direction": "row",
        "padding": dims(16, 0, 16, 0),
        "padding_mobile": dims(12, 20, 12, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"])})

    if not props.get("topbar"):
        return bar

    strip = container([
        widget("icon-list", {
            "icon_list": [repeater_item(
                text=i["text"],
                selected_icon=icon(i.get("icon", "fas fa-circle-info")),
                link=link(i.get("href", ""))) for i in props["topbar"]],
            "view": "inline",
            "space_between": slider(24),
            "icon_size": slider(13),
        }, globals_={
            "icon_color": color_ref(C["brand_on_dark"]),
            "text_color": color_ref(C["on_dark"]),
            "icon_typography_typography": typo_ref(T["meta"]),
        }),
    ], {
        "content_width": "boxed",
        "flex_direction": "row",
        "flex_justify_content": "space-between",
        "padding": dims(9, 0, 9, 0),
        "hide_mobile": "hidden-mobile",
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})

    return container([strip, bar], {"content_width": "full",
                                    "flex_direction": "column",
                                    "flex_gap": gap(0)})


@block("footer.light")
def footer_light(props):
    """Light footer. `footer.simple` is dark throughout; this is the variant
    for a brand whose logo carries a dark wordmark and cannot sit on black."""
    logo_w = (
        widget("image", {"image": media(props["logo"], props.get("business", "")),
                         "width": slider(160), "align": "left"})
        if props.get("logo") else
        widget("theme-site-logo", {"align": "left", "width": slider(170)})
    )
    groups = props.get("groups", [])
    has_map = bool(props.get("map_query"))
    ratios = [32] + [22] * len(groups) + ([24] if has_map else [])
    widths = _tracks(ratios, 32)
    w_brand, w_group = widths[0], widths[1:1 + len(groups)]

    brand = _col([
        logo_w,
        _text(props.get("blurb", ""), small=True),
        widget("social-icons", {
            "social_icon_list": [
                repeater_item(social_icon=icon(f"fab fa-{s['network']}"),
                              link=link(s["url"], external=True))
                for s in props.get("socials", [])],
            "align": "left", "icon_size": slider(16), "shape": "circle",
            "icon_spacing": slider(10),
        }) if props.get("socials") else widget("spacer", {"space": slider(0)}),
    ], w_brand, extra={"flex_gap": gap(14)})

    def col(title, items, width):
        return _col([
            _heading(title, "h4", T["h_small"], tone="dark"),
            widget("icon-list", {
                "icon_list": [repeater_item(
                    text=i["text"], link=link(i.get("href", "")),
                    selected_icon={"value": "", "library": ""}) for i in items],
                "space_between": slider(9),
            }, globals_={
                "text_color": color_ref("text"),
                "icon_typography_typography": typo_ref(T["body_small"]),
            }),
        ], width, extra={"flex_gap": gap(12)})

    cols = [brand] + [col(g["title"], g["items"], w)
                      for g, w in zip(groups, w_group)]
    if has_map:
        cols.append(_col([
            _heading(props.get("map_title", "Where We Work"), "h4",
                     T["h_small"], tone="dark"),
            widget("google_maps", {"address": props["map_query"],
                                   "zoom": slider(10),
                                   "height": slider(180)}),
        ], widths[-1], extra={"flex_gap": gap(12)}))

    # On a light ground the divider is a hairline in the border token — the
    # dark footer's white-at-16% rule would be invisible here.
    divider = widget("divider", {
        "weight": slider(1), "gap": slider(28), "style": "solid",
    }, globals_={"color": color_ref(C["border"])})

    legal = _text(props.get("legal", ""), align="center", small=True)

    return _section([_row(cols, 32), divider, legal],
                    bg="surface", pad=dims(72, 0, 34, 0))


# ═══════════════════ editorial set ═══════════════════
#
# A serif-display, zero-radius, wide-margin system. The distinguishing moves
# are a two-tone display heading, services as a numbered rule-separated list
# rather than cards, and a navy CTA band standing between content and a
# near-black footer.

ED_PAD = dims(120, 0, 120, 0)
ED_PAD_T = dims(84, 28, 84, 28)
ED_PAD_M = dims(60, 20, 60, 20)
ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]


# Which grounds are dark. Every editorial factory derives its text tone from
# this rather than assuming a light page — a near-black heading on a dark
# ground is invisible, and that failure mode has now shipped twice.
ED_BG = {
    "cream": (C["surface"], False), "sand": (C["surface_alt"], False),
    "white": (C["white"], False),
    "navy": ("primary", True), "ink": ("secondary", True),
    # dark-theme aliases
    "ground": (C["surface"], True), "panel": (C["surface_alt"], True),
    "deep": ("secondary", True), "accent": ("primary", True),
}


def _dk(bg, default="cream"):
    return ED_BG.get(bg or default, ED_BG[default])[1]


def _ed_section(children, bg="cream", pad=None, extra=None):
    token = ED_BG.get(bg, ED_BG["cream"])[0]
    s = {
        "content_width": "boxed", "flex_direction": "column",
        "padding": pad or ED_PAD, "padding_tablet": ED_PAD_T,
        "padding_mobile": ED_PAD_M, "background_background": "classic",
    }
    if extra:
        s.update(extra)
    return container(children, s, globals_={"background_color": color_ref(token)})


def _display(html, size="h2", token=None, align="left", on_dark=False):
    """Two-tone display heading.

    Elementor has no control for colouring part of a heading, so the emphasis
    word is a span coloured through the kit's own CSS variable — no literal,
    so a re-skin still moves it. Scoped to `selector`, per contract v2.
    """
    hl = "accent" if on_dark else "primary"
    return widget("heading", {
        "title": html, "header_size": size, "align": align,
        "custom_css": css(f"selector .hl {{ color: var(--e-global-color-{hl}); }}"),
    }, globals_={
        "title_color": color_ref(C["white"] if on_dark else "secondary"),
        "typography_typography": typo_ref(token or T["h_large"]),
    })


def _ed_eyebrow(text, number=None, on_dark=False):
    label = f"§ {number} / {text}" if number else text
    return widget("heading", {
        "title": label, "header_size": "div", "align": "inherit",
    }, globals_={
        "title_color": color_ref(C["brand_on_dark"] if on_dark else C["muted"]),
        "typography_typography": typo_ref(T["eyebrow"]),
    })


def _ed_button(label, href, style="navy"):
    """Square button with an arrow that nudges on hover."""
    base = {
        "text": label, "link": link(href),
        "selected_icon": icon("fas fa-arrow-right"),
        "icon_align": "right", "icon_indent": slider(12),
        "text_padding": dims(19, 38, 19, 38),
        "border_radius": box(0), "border_border": "solid", "border_width": box(1),
        "hover_animation": "grow",
    }
    if style == "navy":
        g = {"button_text_color": color_ref(C["white"]),
             "background_color": color_ref("primary"),
             "border_color": color_ref("primary"),
             "hover_color": color_ref("primary"),
             "button_background_hover_color": color_ref(C["white"]),
             "button_hover_border_color": color_ref("primary")}
    elif style == "white":
        # ink_primary is the brand darkened until it is readable on light. Using
        # the raw brand colour here breaks for any light brand: Cedar measures
        # 2.91:1 on white, Valeris navy measured 12.6:1 and hid the bug.
        g = {"button_text_color": color_ref(C["ink_primary"]),
             "background_color": color_ref(C["white"]),
             "border_color": color_ref(C["white"]),
             "hover_color": color_ref(C["white"]),
             "button_background_hover_color": color_ref(C["transparent"]),
             "button_hover_border_color": color_ref(C["white"])}
    else:  # gold
        g = {"button_text_color": color_ref(C["on_accent"]),
             "background_color": color_ref(C["accent_fill"]),
             "border_color": color_ref(C["accent_fill"]),
             "hover_color": color_ref(C["white"]),
             "button_background_hover_color": color_ref("primary"),
             "button_hover_border_color": color_ref("primary")}
    g["typography_typography"] = typo_ref("accent")
    return widget("button", base, globals_=g)


def _ed_link(label, href, on_dark=False):
    """Underlined text link with a trailing arrow — the reference's tertiary CTA."""
    return widget("button", {
        "text": label, "link": link(href),
        "selected_icon": icon("fas fa-arrow-right"),
        "icon_align": "right", "icon_indent": slider(10),
        # 13px vertical gives a 44px tap target. A text link is still a link on
        # a phone, and 38px is under the mobile minimum.
        "text_padding": dims(13, 0, 13, 0),
        "border_radius": box(0),
        "border_border": "solid", "border_width": dims(0, 0, 1, 0),
        "custom_css": css("selector a { background: transparent; }"),
    }, globals_={
        "button_text_color": color_ref(C["white"] if on_dark else "secondary"),
        "background_color": color_ref(C["transparent"]),
        "border_color": color_ref(C["border"] if not on_dark else C["rule_dark"]),
        "hover_color": color_ref("primary" if not on_dark else "accent"),
        "button_background_hover_color": color_ref(C["transparent"]),
        "button_hover_border_color": color_ref("primary" if not on_dark else "accent"),
        "typography_typography": typo_ref(T["meta"]),
    })


@block("hero.editorial")
def hero_editorial(props):
    """Full-bleed image, gradient scrim, oversized two-tone serif headline."""
    inner = []
    if props.get("eyebrow"):
        inner.append(_ed_eyebrow(props["eyebrow"], on_dark=True))
    inner.append(_display(props["h1"], "h1", T["hero"], on_dark=True))
    if props.get("intro"):
        inner.append(_text(props["intro"], on_dark=True))
    if props.get("trust"):
        inner.append(widget("icon-list", {
            "icon_list": [repeater_item(text=t, selected_icon={"value": "", "library": ""})
                          for t in props["trust"]],
            "view": "inline", "space_between": slider(22), "divider": "yes",
            "divider_style": "solid",
        }, globals_={"text_color": color_ref(C["on_dark"]),
                     "divider_color": color_ref(C["rule_dark"]),
                     "icon_typography_typography": typo_ref(T["meta"])}))
    if props.get("cta"):
        inner.append(_ed_button(props["cta"]["label"], props["cta"]["href"], "navy"))

    col = _col(inner, _tracks([54, 46], 40)[0], extra={"flex_gap": gap(24)})
    # A transparent header sits in normal flow and would otherwise push the
    # hero down. Pulling the hero up by exactly HEADER_H puts the image behind
    # the nav; the matching top padding keeps the headline clear of it.
    overlap = {"margin": dims(-HEADER_H, 0, 0, 0)} if props.get("overlap") else {}
    return container([_row([col], 40, align="flex-end")], {
        "content_width": "boxed",
        "flex_direction": "column",
        "min_height": slider(92, "vh"),
        "min_height_mobile": slider(78, "vh"),
        "padding": dims(140 + (HEADER_H if props.get("overlap") else 0), 0, 76, 0),
        "padding_mobile": dims(96 + (HEADER_H if props.get("overlap") else 0),
                               20, 56, 20),
        **overlap,
        "flex_justify_content": "flex-end",
        "background_background": "classic",
        "background_image": media(props["image"], props.get("image_alt", "")),
        "background_size": "cover",
        "background_position": "center center",
        "background_overlay_background": "gradient",
        "background_overlay_color": "#0D1117",
        "background_overlay_color_stop": slider(0),
        "background_overlay_color_b": "#0D111700",
        "background_overlay_color_b_stop": slider(78),
        "background_overlay_gradient_angle": slider(70),
        "background_overlay_opacity": slider(0.94),
    })


@block("statement.center")
def statement_center(props):
    """Centred page opener. Interior pages pass h1=True — this block is the
    page's title, and a document whose only headings are h2 has no h1 at all,
    which is the single most common avoidable on-page SEO fault."""
    dk = _dk(props.get("bg"), "cream")
    inner = []
    if props.get("eyebrow"):
        inner.append(_ed_eyebrow(props["eyebrow"], props.get("number"), on_dark=dk))
    inner.append(_display(props["heading"], "h1" if props.get("h1") else "h2",
                          T["h_large"], align="center", on_dark=dk))
    if props.get("body"):
        inner.append(_text(props["body"], align="center", on_dark=dk))
    if props.get("link"):
        inner.append(_ed_link(props["link"]["label"], props["link"]["href"],
                              on_dark=dk))
    return _ed_section([_col(inner, 74, extra={
        "flex_align_items": "center", "flex_gap": gap(22),
        "margin": dims(0, "auto", 0, "auto")})],
        bg=props.get("bg", "cream"))


@block("services.list")
def services_list(props):
    """Numbered rows separated by hairlines, each with a trailing arrow.

    The reference deliberately avoids cards here — a rule-separated list reads
    as a table of contents for the trade, which is calmer and scans faster.
    """
    dk = _dk(props.get("bg"), "sand")
    w_head, w_intro = _tracks([46, 54], 48)
    head = _col([_display(props["heading"], "h2", T["h_large"], on_dark=dk)], w_head)
    aside = [_text(props["intro"], on_dark=dk)] if props.get("intro") else []
    if props.get("link"):
        aside.append(_ed_link(props["link"]["label"], props["link"]["href"],
                              on_dark=dk))
    intro = _col(aside, w_intro, extra={"flex_justify_content": "flex-end",
                                        "flex_gap": gap(18)})

    rows = []
    for n, it in enumerate(props["items"]):
        w_num, w_name, w_arrow = _tracks([6, 84, 10], 16)
        rows.append(container([
            _col([widget("heading", {
                "title": ROMAN[n] + ".", "header_size": "div",
            }, globals_={"title_color": color_ref(C["muted"]),
                         "typography_typography": typo_ref(T["meta"])})], w_num),
            _col([_display(it["name"], "h3", T["h_medium"], on_dark=dk)], w_name),
            _col([widget("icon", {
                "selected_icon": icon("fas fa-arrow-right"),
                "view": "default", "size": slider(17), "align": "right",
            }, globals_={"primary_color": color_ref("primary")})], w_arrow,
                extra={"flex_align_items": "flex-end"}),
        ], {
            "content_width": "full", "flex_direction": "row",
            "flex_gap": gap(16), "flex_align_items": "center",
            "padding": dims(26, 8, 26, 8),
            "border_border": "solid", "border_width": dims(0, 0, 1, 0),
            "link": link(it["href"]),
            "_element_id": it.get("slug", ""),
        }, globals_={"border_color": color_ref(C["border"])}))

    return _ed_section([
        _row([head, intro], 48, extra={"margin": dims(0, 0, 46, 0)}),
        _col(rows, extra={"flex_gap": gap(0),
                          "border_border": "solid",
                          "border_width": dims(1, 0, 0, 0)}),
    ], bg=props.get("bg", "sand"))


@block("principles.grid")
def principles_grid(props):
    """2x2 cards, each capped by a navy rule and numbered in roman."""
    dk = _dk(props.get("bg"), "cream")
    w = _tracks([50, 50], 24)[0]
    cards = []
    for n, it in enumerate(props["items"]):
        cards.append(_col([
            widget("heading", {"title": ROMAN[n] + ".", "header_size": "div"},
                   globals_={"title_color": color_ref("primary"),
                             "typography_typography": typo_ref(T["meta"])}),
            _display(it["title"], "h3", T["h_small"], on_dark=dk),
            _text(it["text"], small=True, on_dark=dk),
        ], w, extra={
            "background_background": "classic",
            "padding": dims(30, 30, 34, 30),
            "border_border": "solid", "border_width": dims(2, 0, 0, 0),
            "flex_gap": gap(10),
        }, ))
        cards[-1]["settings"]["__globals__"] = {
            "background_color": color_ref("secondary" if dk else C["white"]),
            "border_color": color_ref("primary"),
        }
    head = []
    if props.get("eyebrow"):
        head.append(_ed_eyebrow(props["eyebrow"], props.get("number"), on_dark=dk))
    head.append(_display(props["heading"], "h2", T["h_large"], align="center",
                         on_dark=dk))
    return _ed_section([
        _col(head, extra={"flex_align_items": "center",
                          "margin": dims(0, 0, 44, 0), "flex_gap": gap(16)}),
        _row(cards, 24),
    ], bg=props.get("bg", "cream"))


@block("work.cards")
def work_cards(props):
    """Three project cards with the caption sitting on the image."""
    w = _tracks([1] * len(props["items"]), 22)[0]
    cards = []
    for n, it in enumerate(props["items"]):
        cards.append(_col([
            widget("image", {
                "image": media(it["image"], it.get("alt") or it["title"]),
                "width": slider(100, "%"), "hover_animation": "grow",
            }),
            _col([
                widget("heading", {"title": f"No. {n + 1:02d}", "header_size": "div"},
                       globals_={"title_color": color_ref(C["brand_on_dark"]),
                                 "typography_typography": typo_ref(T["meta"])}),
                _display(it["title"], "h3", T["h_small"], on_dark=True),
            ], extra={
                "position": "absolute", "_position": "absolute",
                "_offset_orientation_v": "end", "_offset_y": slider(22),
                "_offset_x": slider(22), "flex_gap": gap(4),
            }),
        ], w, extra={"position": "relative", "flex_gap": gap(0),
                     "overflow": "hidden"}))
    dkw = _dk(props.get("bg"), "sand")
    head = []
    if props.get("eyebrow"):
        head.append(_ed_eyebrow(props["eyebrow"], props.get("number"), on_dark=dkw))
    head.append(_display(props["heading"], "h2", T["h_large"], on_dark=dkw))
    top = [_col(head, _tracks([70, 30], 24)[0], extra={"flex_gap": gap(14)})]
    if props.get("link"):
        top.append(_col([_ed_link(props["link"]["label"], props["link"]["href"],
                                  on_dark=dkw)],
                        _tracks([70, 30], 24)[1],
                        extra={"flex_align_items": "flex-end",
                               "flex_justify_content": "flex-end"}))
    return _ed_section([
        _row(top, 24, align="flex-end", extra={"margin": dims(0, 0, 36, 0)}),
        _row(cards, 22),
    ], bg=props.get("bg", "sand"))


@block("service.split")
def service_split(props):
    """Alternating image/text split, one per trade."""
    dk = _dk(props.get("bg"), "cream")
    w_a, w_b = _tracks([46, 54], 56)
    body = [_ed_eyebrow(props["eyebrow"], props.get("number"), on_dark=dk),
            _display(props["heading"], "h2", T["h_medium"], on_dark=dk)]
    for para in props.get("paragraphs", []):
        body.append(_text(para, small=True, on_dark=dk))
    if props.get("link"):
        body.append(_ed_link(props["link"]["label"], props["link"]["href"],
                             on_dark=dk))
    text_col = _col(body, w_b, extra={"flex_gap": gap(16),
                                      "flex_justify_content": "center"})
    img_col = _col([widget("image", {
        "image": media(props["image"], props.get("image_alt", props["heading"])),
        "width": slider(100, "%"), "hover_animation": "grow",
    })], w_a)
    order = [img_col, text_col] if props.get("reverse") else [text_col, img_col]
    return _ed_section([_row(order, 56, align="center")],
                       bg=props.get("bg", "cream"),
                       extra={"_element_id": props.get("slug", "")})


@block("process.numbered")
def process_numbered(props):
    """Oversized serif numeral beside the step copy, grounds alternating."""
    out = []
    for n, st in enumerate(props["steps"], 1):
        w_num, w_body = _tracks([24, 76], 48)
        num = _col([widget("heading", {
            "title": f"{n:02d}", "header_size": "div", "align": "center",
        }, globals_={"title_color": color_ref("primary"),
                     "typography_typography": typo_ref(T["hero"])})], w_num,
            extra={"flex_justify_content": "center"})
        bg_a, bg_b = props.get("grounds", ("cream", "white"))
        bg = bg_a if n % 2 else bg_b
        dk = _dk(bg, "cream")
        body = [_display(st["title"], "h2", T["h_medium"], on_dark=dk)]
        for para in st.get("paragraphs", []):
            body.append(_text(para, small=True, on_dark=dk))
        out.append(_ed_section([_row([num, _col(body, w_body,
                                                extra={"flex_gap": gap(14)})],
                                     48, align="center")],
                               bg=bg, pad=dims(86, 0, 86, 0)))
    return container(out, {"content_width": "full", "flex_direction": "column",
                           "flex_gap": gap(0)})


@block("gallery.filter")
def gallery_filter(props):
    """Filter pills plus an honest empty state — the reference ships this
    rather than padding the page with stock photography."""
    pills = []
    for n, f in enumerate(props["filters"]):
        active = n == 0
        pills.append(widget("button", {
            "text": f["label"], "link": link(f.get("href", "#")), "size": "sm",
            "text_padding": dims(12, 24, 12, 24), "border_radius": box(0),
            "border_border": "solid", "border_width": box(1),
            "selected_icon": {"value": "", "library": ""},
            "hover_animation": "grow",
        }, globals_={
            "button_text_color": color_ref(C["white"] if active else "secondary"),
            "background_color": color_ref("primary" if active else C["transparent"]),
            "border_color": color_ref("primary" if active else C["border"]),
            "hover_color": color_ref(C["white"]),
            "button_background_hover_color": color_ref("primary"),
            "button_hover_border_color": color_ref("primary"),
            "typography_typography": typo_ref(T["meta"]),
        }))
    dk = _dk(props.get("bg"), "white")
    body = [_row(pills, 12, justify="center",
                 extra={"flex_direction_mobile": "row", "flex_wrap": "wrap"})]
    if props.get("empty_heading"):
        body.append(_col([
            _display(props["empty_heading"], "h3", T["h_medium"], align="center",
                     on_dark=dk),
            _text(props.get("empty_text", ""), align="center", on_dark=dk),
        ], extra={"flex_align_items": "center", "flex_gap": gap(12),
                  "padding": dims(96, 0, 96, 0)}))
    return _ed_section(body, bg=props.get("bg", "white"))


@block("contact.editorial")
def contact_editorial(props):
    """Expectations on the left, a bordered form card on the right."""
    dk = _dk(props.get("bg"), "cream")
    w_a, w_b = _tracks([44, 56], 56)
    left = [_ed_eyebrow(props.get("eyebrow", "What to Expect"), on_dark=dk),
            _display(props["heading"], "h2", T["h_medium"], on_dark=dk)]
    if props.get("quote"):
        left.append(_col([_text(props["quote"], on_dark=dk)], extra={
            "border_border": "solid", "border_width": dims(0, 0, 0, 2),
            "padding": dims(4, 0, 4, 20),
        }))
        left[-1]["settings"]["__globals__"] = {"border_color": color_ref("primary")}
    if props.get("points"):
        left.append(widget("icon-list", {
            "icon_list": [repeater_item(text=p, selected_icon=icon("fas fa-arrow-right"))
                          for p in props["points"]],
            "space_between": slider(16), "icon_size": slider(12),
        }, globals_={"icon_color": color_ref("primary"),
                     "text_color": color_ref(C["on_dark"] if dk else "text"),
                     "icon_typography_typography": typo_ref(T["body_small"])}))

    fields = [{
        "custom_id": f["id"], "field_type": f.get("type", "text"),
        "field_label": f["label"], "placeholder": f.get("placeholder", ""),
        "required": "true" if f.get("required") else "",
        "width": f.get("width", "100"),
        **({"field_options": "\n".join(f["options"])} if f.get("options") else {}),
        **({"rows": 4} if f.get("type") == "textarea" else {}),
    } for f in props["fields"]]
    form = widget("form", {
        "form_name": props.get("form_name", "Quote Request"),
        "form_fields": [repeater_item(**f) for f in fields],
        "button_text": props.get("submit", "Request Free Quote"),
        "button_size": "md",
        "button_align": "start",
        "label_typography_typography": "custom",
    }, globals_={
        "button_background_color": color_ref("primary"),
        "button_text_color": color_ref(C["white"]),
        "field_typography_typography": typo_ref("text"),
    })
    card = _col([form, _text(props.get("note", ""), small=True, on_dark=dk)],
                w_b, extra={
        "background_background": "classic",
        "padding": dims(40, 40, 40, 40),
        "border_border": "solid", "border_width": box(1),
        "border_radius": box(props.get("radius", 0)),
        "flex_gap": gap(18),
    })
    card["settings"]["__globals__"] = {
        "background_color": color_ref("secondary" if dk else C["white"]),
        "border_color": color_ref(C["rule_dark"] if dk else C["border"])}
    return _ed_section([_row([_col(left, w_a, extra={"flex_gap": gap(20)}), card],
                             56, align="flex-start")],
                       bg=props.get("bg", "cream"))


@block("areas.strip")
def areas_strip(props):
    """Service towns as a centred pill row. A short list of real towns is worth
    naming on the page — it is the local-intent signal — but it does not earn
    a page each."""
    dk = _dk(props.get("bg"), "panel")
    pills = [widget("button", {
        "text": a["name"], "link": link(a.get("href", "#")), "size": "sm",
        "text_padding": dims(11, 22, 11, 22), "border_radius": box(0),
        "border_border": "solid", "border_width": box(1),
        "selected_icon": {"value": "", "library": ""},
        "hover_animation": "grow",
    }, globals_={
        "button_text_color": color_ref(C["on_dark"] if dk else "secondary"),
        "background_color": color_ref(C["transparent"]),
        "border_color": color_ref(C["rule_dark"] if dk else C["border"]),
        "hover_color": color_ref(C["on_accent"]),
        "button_background_hover_color": color_ref("primary"),
        "button_hover_border_color": color_ref("primary"),
        "typography_typography": typo_ref(T["meta"]),
    }) for a in props["areas"]]

    head = []
    if props.get("eyebrow"):
        head.append(_ed_eyebrow(props["eyebrow"], on_dark=dk))
    head.append(_display(props["heading"], "h2", T["h_medium"],
                         align="center", on_dark=dk))
    if props.get("body"):
        head.append(_text(props["body"], align="center", on_dark=dk))

    return _ed_section([
        _col(head, extra={"flex_align_items": "center", "flex_gap": gap(16),
                          "margin": dims(0, 0, 34, 0)}),
        _row(pills, 12, justify="center",
             extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"}),
    ], bg=props.get("bg", "panel"), pad=dims(96, 0, 96, 0))


@block("cta.navy")
def cta_navy(props):
    """Full-width closing CTA.

    `bg` defaults to the brand ground but must be honourable — hardcoding it
    put white text and a brand-coloured eyebrow onto a brand-coloured band,
    which measured 2.91:1 and 1.00:1 for a light brand colour. Any ground whose
    own accent tokens sit on top of it needs to be dark, not the accent itself.
    """
    bg = props.get("bg", "navy")
    dk = _dk(bg, "navy")
    inner = []
    if props.get("eyebrow"):
        inner.append(_ed_eyebrow(props["eyebrow"], on_dark=dk))
    inner.append(_display(props["heading"], "h2", T["h_large"],
                          align="center", on_dark=dk))
    if props.get("text"):
        inner.append(_text(props["text"], align="center", on_dark=dk))
    inner.append(_ed_button(props["cta"]["label"], props["cta"]["href"],
                            "white" if dk else "navy"))
    return _ed_section([_col(inner, 70, extra={
        "flex_align_items": "center", "flex_gap": gap(20),
        "margin": dims(0, "auto", 0, "auto")})],
        bg=bg, pad=dims(104, 0, 104, 0))


HEADER_H = 88   # fixed so hero.editorial's overlap offset is deterministic


@block("header.editorial")
def header_editorial(props):
    """Sticky header. `transparent=True` floats it over a full-bleed hero with
    reversed type, then flips to solid white on scroll.

    Elementor Pro stamps `.elementor-sticky--effects` onto the element once the
    scroll passes `sticky_effects_offset`, so the scrolled state is styleable
    without a line of JavaScript. Height is pinned rather than left to content
    because the hero's negative offset is measured against it — a header whose
    height depends on its content is what slices a nav in half on a re-render.
    """
    clear = props.get("transparent", False)
    lw = slider(props.get("logo_width", 150))
    biz = props.get("business", "")

    # Logo strategy, best first.
    #
    # 1. `logo_light` supplied  -> two images swapped by the sticky class. The
    #    only approach that is correct regardless of what the logo file looks
    #    like, so it is the default whenever a reversed asset exists.
    # 2. filter fallback        -> brightness(0) invert(1) whitens every opaque
    #    pixel. That is right for a logo on TRANSPARENT background and wrong
    #    for one on a white background, where it whitens the whole rectangle
    #    and renders as a white square. Only used when no reversed asset is
    #    given, and it demands a transparent PNG or SVG.
    swap = clear and props.get("logo_light") and props.get("logo")
    if swap:
        logo = [
            widget("image", {"image": media(props["logo_light"], biz),
                             "width": lw, "align": "left",
                             "link_to": "custom", "link": link("/"),
                             "_element_id": "site-logo-reversed"}),
            widget("image", {"image": media(props["logo"], biz),
                             "width": lw, "align": "left",
                             "link_to": "custom", "link": link("/"),
                             "_element_id": "site-logo-colour"}),
        ]
    else:
        logo = [widget("theme-site-logo", {
            "align": "left", "width": lw,
            **({"image": media(props["logo"], biz)} if props.get("logo") else {}),
        })]
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"), "layout": "horizontal",
        "align_items": "center", "pointer": "underline",
        "menu_space_between": slider(30), "toggle_align": "right",
    }, globals_={
        "color_menu_item": color_ref(C["white"] if clear else "secondary"),
        "color_menu_item_hover": color_ref("accent" if clear else "primary"),
        "menu_typography_typography": typo_ref(T["meta"]),
    })
    cta = _ed_button(props["cta"]["label"], props["cta"]["href"],
                     "white" if clear else "navy")
    w_l, w_n, w_c = _tracks([16, 62, 22], 20)

    rules = ["selector { transition: background-color .28s ease, "
             "box-shadow .28s ease; }"]
    if clear:
        white, border, ink = C["white"], C["border"], "secondary"
        rules += [
            f"selector.elementor-sticky--effects"
            f" {{ background-color: var(--e-global-color-{white});"
            f" box-shadow: 0 1px 0 var(--e-global-color-{border}); }}",
            f"selector.elementor-sticky--effects .elementor-nav-menu a"
            f" {{ color: var(--e-global-color-{ink}); }}",
            f"selector.elementor-sticky--effects .elementor-button"
            f" {{ background-color: var(--e-global-color-primary);"
            f" border-color: var(--e-global-color-primary);"
            f" color: var(--e-global-color-{white}); }}",
        ]
        if swap:
            rules += [
                "selector #site-logo-colour { display: none; }",
                "selector.elementor-sticky--effects #site-logo-reversed"
                " { display: none; }",
                "selector.elementor-sticky--effects #site-logo-colour"
                " { display: block; }",
            ]
        else:
            # Fallback only — see the strategy note above. Requires the logo
            # file to have a transparent background; a white-boxed PNG renders
            # as a solid white square here.
            rules += [
                "selector .elementor-widget-theme-site-logo img"
                " { filter: brightness(0) invert(1);"
                " transition: filter .28s ease; }",
                "selector.elementor-sticky--effects"
                " .elementor-widget-theme-site-logo img { filter: none; }",
            ]

    settings = {
        "content_width": "boxed", "flex_direction": "row",
        "min_height": slider(HEADER_H),
        "padding": dims(0, 0, 0, 0), "padding_mobile": dims(0, 20, 0, 20),
        "flex_align_items": "center",
        "background_background": "classic",
        "sticky": "top",
        "sticky_on": ["desktop", "tablet", "mobile"],
        "sticky_offset": 0,
        "sticky_effects_offset": props.get("effects_offset", 60),
        "z_index": 99,
        "custom_css": css(*rules),
    }
    g = {}
    if clear:
        settings["background_color"] = "#00000000"
    else:
        settings["border_border"] = "solid"
        settings["border_width"] = dims(0, 0, 1, 0)
        g = {"background_color": color_ref(C["white"]),
             "border_color": color_ref(C["border"])}

    return container([_row([
        _col(logo, w_l, extra={"flex_justify_content": "center"}),
        _col([nav], w_n, extra={"flex_justify_content": "center"}),
        _col([cta], w_c, extra={"flex_justify_content": "center",
                                "flex_align_items": "flex-end"}),
    ], 20, align="center")], settings, globals_=g or None)


@block("footer.editorial")
def footer_editorial(props):
    # The footer ground is near-black, so a logo drawn in the brand's own dark
    # colours is invisible on it — Valeris navy measures 1.31:1 here. Use the
    # reversed asset when there is one, otherwise whiten the mark in place.
    # Same rule as the transparent header: the filter needs a transparent
    # background or it renders as a solid white block.
    biz = props.get("business", "")
    if props.get("logo_light"):
        logo = widget("image", {"image": media(props["logo_light"], biz),
                                "width": slider(150), "align": "left",
                                "link_to": "custom", "link": link("/")})
    elif props.get("logo"):
        logo = widget("image", {
            "image": media(props["logo"], biz), "width": slider(150),
            "align": "left", "link_to": "custom", "link": link("/"),
            "custom_css": css("selector img { filter: brightness(0) invert(1); }"),
        })
    else:
        logo = widget("theme-site-logo", {
            "align": "left", "width": slider(150),
            "custom_css": css("selector img { filter: brightness(0) invert(1); }"),
        })
    groups = props.get("groups", [])
    ratios = [34] + [22] * len(groups)
    widths = _tracks(ratios, 32)
    brand = _col([logo, _text(props.get("blurb", ""), on_dark=True, small=True)],
                 widths[0], extra={"flex_gap": gap(16)})

    def col(g, w):
        return _col([
            widget("heading", {"title": g["title"], "header_size": "div"},
                   globals_={"title_color": color_ref(C["brand_on_dark"]),
                             "typography_typography": typo_ref(T["eyebrow"])}),
            widget("icon-list", {
                "icon_list": [repeater_item(
                    text=i["text"], link=link(i.get("href", "")),
                    selected_icon={"value": "", "library": ""}) for i in g["items"]],
                "space_between": slider(11),
            }, globals_={"text_color": color_ref(C["on_dark"]),
                         "icon_typography_typography": typo_ref(T["body_small"])}),
        ], w, extra={"flex_gap": gap(16)})

    cols = [brand] + [col(g, w) for g, w in zip(groups, widths[1:])]
    rule = widget("divider", {"weight": slider(1), "gap": slider(30),
                              "style": "solid"},
                  globals_={"color": color_ref(C["rule_dark"])})
    w_a, w_b = _tracks([60, 40], 24)
    base = _row([
        _col([_text(props.get("legal", ""), on_dark=True, small=True)], w_a),
        _col([_text(props.get("tagline", ""), align="right", on_dark=True,
                    small=True)], w_b),
    ], 24)
    tail = [rule, base]
    if props.get("trademark"):
        tail.append(_text(props["trademark"], on_dark=True, small=True))
    return _ed_section([_row(cols, 32)] + tail, bg="ink",
                       pad=dims(88, 0, 44, 0))


# ═══════════════════ rounded set ═══════════════════
#
# A second dark system, and deliberately the opposite of the editorial set:
# heavy border-radius rather than none, centred letterspaced caps rather than
# left-aligned serif, stadium-shaped image panels, circular seals and a pill
# CTA. Do not mix the two on one site — the radius alone reads as two brands.

R_CARD = 24
R_PANEL = 32
R_PILL = 999


def _rd_section(children, bg="ground", pad=None, extra=None):
    token, _ = ED_BG.get(bg, ED_BG["ground"])
    s = {
        "content_width": "boxed", "flex_direction": "column",
        # One rhythm for the whole set: 112 / 80 / 60. Mixed section padding
        # is the most common reason a page reads as assembled rather than
        # designed, and it is invisible in a component-by-component review.
        "padding": pad or dims(112, 0, 112, 0),
        "padding_tablet": dims(80, 28, 80, 28),
        "padding_mobile": dims(60, 20, 60, 20),
        "background_background": "classic",
    }
    if extra:
        s.update(extra)
    return container(children, s, globals_={"background_color": color_ref(token)})


def _caps(text, size="h2", token=None, align="center", on_dark=True):
    return widget("heading", {
        "title": text, "header_size": size, "align": align,
    }, globals_={
        "title_color": color_ref(C["white"] if on_dark else "secondary"),
        "typography_typography": typo_ref(token or T["caps_hero"]),
    })


def _pill(label, href, style="accent"):
    """Fully rounded button. The label colour is measured, never assumed —
    white on this palette's cyan is 2.04:1."""
    g = {
        "accent": {"button_text_color": color_ref(C["on_accent"]),
                   "background_color": color_ref(C["accent_fill"]),
                   "border_color": color_ref(C["accent_fill"]),
                   "hover_color": color_ref(C["white"]),
                   "button_background_hover_color": color_ref("secondary"),
                   "button_hover_border_color": color_ref("secondary")},
        "outline": {"button_text_color": color_ref(C["white"]),
                    "background_color": color_ref(C["transparent"]),
                    "border_color": color_ref(C["rule_dark"]),
                    "hover_color": color_ref(C["on_accent"]),
                    "button_background_hover_color": color_ref("accent"),
                    "button_hover_border_color": color_ref("accent")},
    }[style]
    g["typography_typography"] = typo_ref(T["eyebrow"])
    return widget("button", {
        "text": label, "link": link(href),
        "selected_icon": {"value": "", "library": ""},
        "text_padding": dims(17, 40, 17, 40),
        "border_radius": box(R_PILL),
        "border_border": "solid", "border_width": box(1),
        "hover_animation": "grow",
    }, globals_=g)


@block("hero.centered")
def hero_centered(props):
    """Full-bleed image, centred wide-tracked caps headline, caps sub-line."""
    inner = [_caps(props["h1"], "h1", T["caps_hero"])]
    if props.get("sub"):
        inner.append(_caps(props["sub"], "div", T["caps_sub"]))
    if props.get("cta"):
        inner.append(_pill(props["cta"]["label"], props["cta"]["href"]))

    return container([
        _row([_col(inner, extra={"flex_align_items": "center",
                                 "flex_gap": gap(22)})], 0, justify="center"),
    ], {
        "content_width": "boxed", "flex_direction": "column",
        "min_height": slider(props.get("min_height", 82), "vh"),
        "min_height_mobile": slider(70, "vh"),
        "flex_justify_content": "center",
        "padding": dims(120 + (HEADER_H if props.get("overlap") else 0), 0, 120, 0),
        "padding_mobile": dims(96 + (HEADER_H if props.get("overlap") else 0),
                               20, 84, 20),
        **({"margin": dims(-HEADER_H, 0, 0, 0)} if props.get("overlap") else {}),
        "background_background": "classic",
        "background_image": media(props["image"], props.get("image_alt", "")),
        "background_size": "cover",
        "background_position": "center center",
        "background_overlay_background": "classic",
        "background_overlay_color": "#0F1922",
        "background_overlay_opacity": slider(props.get("scrim", 0.55)),
        "border_radius": box(props.get("radius", 0)),
    })


@block("wordmark.band")
def wordmark_band(props):
    """The brand name, very large and very widely tracked, as its own band."""
    return _rd_section(
        [_caps(props["text"], "div", T["wordmark"],
               align=props.get("align", "right"))],
        bg=props.get("bg", "deep"), pad=dims(44, 0, 56, 0))


@block("split.underline")
def split_underline(props):
    """Statement left with one phrase underlined, rounded image right.

    The underline is a span rather than a border on the heading — the reference
    underlines a single word inside the sentence, which no Elementor control
    can express.
    """
    dk = _dk(props.get("bg"), "ground")
    w_a, w_b = _tracks([46, 54], 56)
    body = []
    if props.get("eyebrow"):
        body.append(_ed_eyebrow(props["eyebrow"], on_dark=dk))
    body.append(widget("heading", {
        "title": props["heading"], "header_size": props.get("tag", "h2"),
        "align": "left",
        "custom_css": css(
            "selector .ul { text-decoration: underline; "
            "text-underline-offset: 6px; text-decoration-thickness: 1px; }"),
    }, globals_={
        "title_color": color_ref(C["white"] if dk else "secondary"),
        "typography_typography": typo_ref(T["h_large"]),
    }))
    for para in props.get("paragraphs", []):
        body.append(_text(para, small=True, on_dark=dk))
    if props.get("cta"):
        body.append(_pill(props["cta"]["label"], props["cta"]["href"],
                          "accent" if dk else "outline"))

    img = _col([widget("image", {
        "image": media(props["image"], props.get("image_alt", "")),
        "width": slider(100, "%"), "hover_animation": "grow",
        "image_border_radius": box(R_PANEL),
    })], w_b)
    text_col = _col(body, w_a, extra={"flex_gap": gap(18),
                                      "flex_justify_content": "center"})
    order = [img, text_col] if props.get("reverse") else [text_col, img]
    return _rd_section([_row(order, 56, align="center")],
                       bg=props.get("bg", "ground"))


@block("panel.stadium")
def panel_stadium(props):
    """The signature element: a fully rounded image panel carrying a centred
    statement, optionally fed by a thin vertical connector above it."""
    dk = True
    inner = []
    if props.get("eyebrow"):
        inner.append(_ed_eyebrow(props["eyebrow"], on_dark=dk))
    inner.append(_caps(props["heading"], "h2", T["h_medium"]))
    if props.get("text"):
        inner.append(_text(props["text"], align="center", on_dark=dk))
    if props.get("cta"):
        inner.append(_pill(props["cta"]["label"], props["cta"]["href"]))

    panel = container([_col(inner, 76, extra={
        "flex_align_items": "center", "flex_gap": gap(16),
        "margin": dims(0, "auto", 0, "auto")})], {
        "content_width": "full", "flex_direction": "column",
        "flex_justify_content": "center",
        "padding": dims(76, 64, 76, 64),
        "padding_mobile": dims(52, 26, 52, 26),
        "border_radius": box(R_PILL),
        "border_radius_mobile": box(R_PANEL),
        "background_background": "classic",
        "background_image": media(props["image"], props.get("image_alt", "")),
        "background_size": "cover",
        "background_position": "center center",
        "background_overlay_background": "classic",
        "background_overlay_color": "#0F1922",
        "background_overlay_opacity": slider(props.get("scrim", 0.72)),
        "overflow": "hidden",
    })

    kids = []
    if props.get("connector", True):
        # A 1px rule dropping into the panel — the reference uses it to link
        # the statement above to the panel below.
        kids.append(widget("divider", {
            "weight": slider(1), "gap": slider(0), "style": "solid",
            "width": slider(1, "px"), "align": "center",
            "custom_css": css("selector .elementor-divider-separator "
                              "{ height: 74px; border-left: 1px solid "
                              "var(--e-global-color-" + C["rule_dark"] + "); "
                              "border-top: 0; width: 0; margin: 0 auto; }"),
        }, globals_={"color": color_ref(C["rule_dark"])}))
    kids.append(panel)
    return _rd_section(kids, bg=props.get("bg", "ground"))


@block("testimonial.founder")
def testimonial_founder(props):
    """Centred quote on a textured dark panel, circular portrait beneath."""
    inner = [_text(props["quote"], align="center", on_dark=True)]
    if props.get("photo"):
        inner.append(widget("image", {
            "image": media(props["photo"], props.get("name", "")),
            "width": slider(84), "align": "center",
            "image_border_radius": box(R_PILL),
        }))
    inner.append(_caps(props["name"], "div", T["h_small"]))
    if props.get("role"):
        inner.append(widget("heading", {
            "title": props["role"], "header_size": "div", "align": "center",
        }, globals_={"title_color": color_ref("accent"),
                     "typography_typography": typo_ref(T["eyebrow"])}))

    return _rd_section([_col(inner, 74, extra={
        "flex_align_items": "center", "flex_gap": gap(16),
        "margin": dims(0, "auto", 0, "auto")})],
        bg=props.get("bg", "deep"),
        extra={"custom_css": css(
            # Fine diagonal texture. No control expresses a repeating gradient,
            # and the reference leans on it in every dark panel.
            "selector { background-image: repeating-linear-gradient("
            "115deg, rgba(255,255,255,.035) 0 1px, transparent 1px 46px); }")})


@block("logos.trusted")
def logos_trusted(props):
    """White strip: caps eyebrow, a serif line, then client logos."""
    # This block is always on white.  is tuned to the palette's own
    # grounds, so on a dark-theme brand it measures 2.69:1 here; ink_primary is
    # the brand derived to be readable on light.
    head = [widget("heading", {
        "title": props.get("eyebrow", "Trusted By"), "header_size": "div",
        "align": "center",
    }, globals_={"title_color": color_ref(C["ink_on_white"]),
                 "typography_typography": typo_ref(T["eyebrow"])})]
    head.append(widget("heading", {
        "title": props["heading"], "header_size": "h2", "align": "center",
    }, globals_={"title_color": color_ref("secondary"),
                 "typography_typography": typo_ref(T["h_medium"])}))

    # A client-logo wall is only honest when there are real client logos. With
    # none supplied, the same slot carries the service towns as text — the
    # alternative is inventing logos, which is not an option.
    if props.get("logos"):
        n = max(1, len(props["logos"]))
        w = _tracks([1] * n, 28)[0]
        cells = [_col([widget("image", {
            "image": media(l["logo"], l.get("alt") or l["name"]),
            "align": "center", "width": slider(100, "%"),
        })], w, extra={"flex_justify_content": "center"}) for l in props["logos"]]
    else:
        cells = [widget("heading", {
            "title": t, "header_size": "div", "align": "center",
        }, globals_={"title_color": color_ref("secondary"),
                     "typography_typography": typo_ref(T["caps_sub"])})
            for t in props.get("towns", [])]

    return _rd_section([
        _col(head, extra={"flex_align_items": "center", "flex_gap": gap(12),
                          "margin": dims(0, 0, 40, 0)}),
        _row(cells, 28, align="center", justify="center"),
    ], bg="white")


@block("quote.bubble")
def quote_bubble(props):
    """Speech-bubble testimonial with a tail, on the light strip."""
    bubble = _col([
        _text(f'"{props["quote"]}"', align="center", small=True),
        widget("heading", {
            "title": props["attribution"], "header_size": "div", "align": "center",
        }, globals_={"title_color": color_ref(C["muted"]),
                     "typography_typography": typo_ref(T["eyebrow"])}),
    ], 84, extra={
        "background_background": "classic",
        "padding": dims(30, 40, 30, 40),
        "border_radius": box(R_CARD),
        "flex_gap": gap(12),
        "margin": dims(0, "auto", 0, "auto"),
        "custom_css": css(
            "selector { position: relative; }",
            "selector::after { content: ''; position: absolute; left: 50%; "
            "bottom: -13px; width: 0; height: 0; transform: translateX(-50%); "
            "border-left: 13px solid transparent; "
            "border-right: 13px solid transparent; "
            "border-top: 14px solid var(--e-global-color-" + C["surface_alt"] + "); }"),
    })
    bubble["settings"]["__globals__"] = {
        "background_color": color_ref(C["surface_alt"])}
    return _rd_section([bubble], bg=props.get("bg", "white"),
                       pad=dims(0, 0, 96, 0))


@block("cta.rounded")
def cta_rounded(props):
    """Rounded dark panel: caps heading, pill CTA, then stacked value props."""
    head = [_caps(props["heading"], "h2", T["h_large"])]
    if props.get("eyebrow"):
        head.insert(0, _ed_eyebrow(props["eyebrow"], on_dark=True))
    if props.get("sub"):
        head.append(_caps(props["sub"], "div", T["caps_sub"]))
    head.append(_pill(props["cta"]["label"], props["cta"]["href"]))

    items = []
    for it in props.get("items", []):
        items.append(_col([
            _caps(it["title"], "h3", T["h_small"]),
            _text(it["text"], align="center", small=True, on_dark=True),
        ], extra={"flex_align_items": "center", "flex_gap": gap(6)}))

    panel = container([
        _col(head, 78, extra={"flex_align_items": "center", "flex_gap": gap(18),
                              "margin": dims(0, "auto", 34, "auto")}),
        _col(items, 82, extra={"flex_gap": gap(26),
                               "margin": dims(0, "auto", 0, "auto")}),
    ], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(72, 56, 72, 56),
        "padding_mobile": dims(48, 24, 48, 24),
        "border_radius": box(R_PANEL),
        "background_background": "classic",
        "custom_css": css(
            "selector { background-image: repeating-linear-gradient("
            "115deg, rgba(255,255,255,.035) 0 1px, transparent 1px 46px); }"),
    }, globals_={"background_color": color_ref("secondary")})

    return _rd_section([panel], bg=props.get("bg", "ground"))


# ── rounded set, part 2: the blocks the Cedar copy needs ──
#
# Spacing rhythm, applied consistently so the pages breathe the same way:
#   section 112 / 80 / 60   head->body 48   card padding 32   grid gap 28

RD_PAD = dims(112, 0, 112, 0)
RD_PAD_T = dims(80, 28, 80, 28)
RD_PAD_M = dims(60, 20, 60, 20)
HEAD_GAP = 48


def _rd_head(props, dk=True, align="center"):
    """Section header: eyebrow, caps title, optional lede. One shape, so every
    section starts at the same rhythm."""
    out = []
    if props.get("eyebrow"):
        out.append(_ed_eyebrow(props["eyebrow"], on_dark=dk))
    out.append(_caps(props["heading"], props.get("tag", "h2"),
                     props.get("token") or T["h_large"], align=align, on_dark=dk))
    if props.get("lede"):
        out.append(_text(props["lede"], align=align, on_dark=dk))
    return _col(out, props.get("head_width"), extra={
        "flex_align_items": "center" if align == "center" else "flex-start",
        "flex_gap": gap(14),
        "margin": dims(0, "auto", HEAD_GAP, "auto"),
    })


@block("features.grid")
def features_grid(props):
    """'Why homeowners choose us' — an even card grid, title plus one line."""
    dk = _dk(props.get("bg"), "panel")
    n = props.get("columns", min(4, len(props["items"])))
    w = _tracks([1] * n, 28)[0]
    cards = []
    for it in props["items"]:
        cards.append(_col([
            _caps(it["title"], "h3", T["h_small"], align="left", on_dark=dk),
            _text(it["text"], small=True, on_dark=dk),
        ], w, extra={
            "background_background": "classic",
            "padding": dims(32, 30, 34, 30),
            "border_radius": box(R_CARD),
            "flex_gap": gap(10),
        }))
        cards[-1]["settings"]["__globals__"] = {
            "background_color": color_ref("secondary" if dk else C["surface_alt"])}
    return _rd_section([_rd_head(props, dk), _row(cards, 28)],
                       bg=props.get("bg", "panel"), pad=RD_PAD)


@block("cards.services")
def services_cards(props):
    """'What We Build' — image card, title, description, link."""
    dk = _dk(props.get("bg"), "ground")
    n = max(1, len(props["items"]))
    w = _tracks([1] * n, 28)[0]
    cards = []
    for it in props["items"]:
        inner = []
        if it.get("image"):
            inner.append(widget("image", {
                "image": media(it["image"], it.get("alt") or it["title"]),
                "width": slider(100, "%"), "hover_animation": "grow",
                "image_border_radius": dims(R_CARD, R_CARD, 0, 0),
            }))
        body = [_caps(it["title"], "h3", T["h_medium"], align="left", on_dark=dk),
                _text(it["text"], small=True, on_dark=dk)]
        if it.get("href"):
            body.append(_ed_link(props.get("link_label", "Learn more"),
                                 it["href"], on_dark=dk))
        inner.append(_col(body, extra={"flex_gap": gap(12),
                                       "padding": dims(28, 30, 32, 30)}))
        cards.append(_col(inner, w, extra={
            "background_background": "classic",
            "border_radius": box(R_CARD),
            "flex_gap": gap(0),
            "overflow": "hidden",
        }))
        cards[-1]["settings"]["__globals__"] = {
            "background_color": color_ref("secondary" if dk else C["surface_alt"])}

    kids = [_rd_head(props, dk), _row(cards, 28, align="stretch")]
    if props.get("cta"):
        kids.append(_col([_pill(props["cta"]["label"], props["cta"]["href"])],
                         extra={"flex_align_items": "center",
                                "margin": dims(44, 0, 0, 0)}))
    return _rd_section(kids, bg=props.get("bg", "ground"), pad=RD_PAD)


@block("service.detail")
def service_detail(props):
    """A service: image, heading, body, a 'What's included' checklist, CTA."""
    dk = _dk(props.get("bg"), "ground")
    w_a, w_b = _tracks([48, 52], 56)
    body = []
    if props.get("eyebrow"):
        body.append(_ed_eyebrow(props["eyebrow"], on_dark=dk))
    body.append(_caps(props["heading"], props.get("tag", "h2"),
                      T["h_medium"], align="left", on_dark=dk))
    for para in props.get("paragraphs", []):
        body.append(_text(para, small=True, on_dark=dk))
    if props.get("included"):
        body.append(widget("heading", {
            "title": props.get("included_label", "What's included"),
            "header_size": "div", "align": "left",
        }, globals_={"title_color": color_ref("accent"),
                     "typography_typography": typo_ref(T["eyebrow"])}))
        body.append(widget("icon-list", {
            "icon_list": [repeater_item(text=t, selected_icon=icon("fas fa-check"))
                          for t in props["included"]],
            "space_between": slider(12), "icon_size": slider(12),
        }, globals_={
            "icon_color": color_ref("accent"),
            "text_color": color_ref(C["on_dark"] if dk else "text"),
            "icon_typography_typography": typo_ref(T["body_small"]),
        }))
    if props.get("cta"):
        body.append(_pill(props["cta"]["label"], props["cta"]["href"]))

    text_col = _col(body, w_b, extra={"flex_gap": gap(16),
                                      "flex_justify_content": "center"})
    img_col = _col([widget("image", {
        "image": media(props["image"], props.get("image_alt", "")),
        "width": slider(100, "%"), "hover_animation": "grow",
        "image_border_radius": box(R_PANEL),
    })], w_a)
    order = [img_col, text_col] if props.get("reverse") else [text_col, img_col]
    return _rd_section([_row(order, 56, align="center")],
                       bg=props.get("bg", "ground"), pad=RD_PAD,
                       extra={"_element_id": props.get("slug", "")})


@block("steps.numbered")
def process_steps(props):
    """Numbered steps in an even row — the copy's four-stage process."""
    dk = _dk(props.get("bg"), "panel")
    n = max(1, len(props["steps"]))
    w = _tracks([1] * n, 28)[0]
    cards = []
    for i, st in enumerate(props["steps"], 1):
        cards.append(_col([
            # The raw accent is chosen to glow on the dark ground and is
            # measured at 1.76:1 on surface_alt, which is what a light-ground
            # card uses — the numeral was invisible on every light `bg`.
            # ink_primary is the same hue darkened until it reads (7.41:1).
            widget("heading", {"title": f"{i:02d}", "header_size": "div",
                               "align": "left"},
                   globals_={
                       "title_color": color_ref("accent" if dk
                                                else C["ink_primary"]),
                       "typography_typography": typo_ref(T["h_medium"])}),
            _caps(st["title"], "h3", T["h_small"], align="left", on_dark=dk),
            _text(st["text"], small=True, on_dark=dk),
        ], w, extra={
            "background_background": "classic",
            "padding": dims(30, 28, 34, 28),
            "border_radius": box(R_CARD),
            "flex_gap": gap(8),
        }))
        cards[-1]["settings"]["__globals__"] = {
            "background_color": color_ref("secondary" if dk else C["surface_alt"])}
    return _rd_section([_rd_head(props, dk), _row(cards, 28, align="stretch")],
                       bg=props.get("bg", "panel"), pad=RD_PAD)


@block("areas.towns")
def areas_towns(props):
    """Service towns as pills, with the 'don't see your town' line beneath."""
    dk = _dk(props.get("bg"), "ground")
    pills = [widget("button", {
        "text": t, "link": link(props.get("href", "/contact")), "size": "sm",
        "text_padding": dims(13, 26, 13, 26), "border_radius": box(R_PILL),
        "border_border": "solid", "border_width": box(1),
        "selected_icon": {"value": "", "library": ""},
        "hover_animation": "grow",
    }, globals_={
        "button_text_color": color_ref(C["on_dark"] if dk else "secondary"),
        "background_color": color_ref(C["transparent"]),
        "border_color": color_ref(C["rule_dark"] if dk else C["border"]),
        "hover_color": color_ref(C["on_accent"]),
        "button_background_hover_color": color_ref("accent"),
        "button_hover_border_color": color_ref("accent"),
        "typography_typography": typo_ref(T["meta"]),
    }) for t in props["towns"]]

    kids = [_rd_head(props, dk),
            _row(pills, 12, justify="center",
                 extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"})]
    if props.get("note"):
        kids.append(_col([_text(props["note"], align="center", small=True,
                                on_dark=dk)],
                         extra={"flex_align_items": "center",
                                "margin": dims(30, 0, 0, 0)}))
    if props.get("cta"):
        kids.append(_col([_ed_link(props["cta"]["label"], props["cta"]["href"],
                                   on_dark=dk)],
                         extra={"flex_align_items": "center",
                                "margin": dims(22, 0, 0, 0)}))
    return _rd_section(kids, bg=props.get("bg", "ground"), pad=RD_PAD)


@block("cta.estimate")
def cta_estimate(props):
    """Closing CTA with a short estimate form. Sits on every page.

    Four fields is the ceiling for a cold-traffic form — every extra field
    costs completions, and the detail can be gathered on the callback.
    """
    fields = props.get("fields") or [
        {"id": "name", "label": "Name", "type": "text",
         "placeholder": "Your name", "required": True, "width": "33"},
        {"id": "phone", "label": "Phone", "type": "tel",
         "placeholder": "(336) 000-0000", "required": True, "width": "33"},
        {"id": "email", "label": "Email", "type": "email",
         "placeholder": "you@email.com", "required": True, "width": "34"},
        {"id": "project", "label": "Project Type", "type": "select",
         "options": ["Home Build", "Remodel", "Deck or Porch", "Other"],
         "required": True, "width": "100"},
    ]
    form = widget("form", {
        "form_name": props.get("form_name", "Free Estimate"),
        "form_fields": [repeater_item(**{
            "custom_id": f["id"], "field_type": f.get("type", "text"),
            "field_label": f["label"], "placeholder": f.get("placeholder", ""),
            "required": "true" if f.get("required") else "",
            "width": f.get("width", "100"),
            **({"field_options": "\n".join(f["options"])} if f.get("options") else {}),
        }) for f in fields],
        "button_text": props.get("submit", "Get A Free Estimate"),
        "button_size": "md",
        "button_align": "stretch",
        "button_border_radius": box(R_PILL),
        "form_fields_border_radius": box(10),
        "field_text_padding": dims(14, 16, 14, 16),
        "row_gap": slider(16),
    }, globals_={
        "button_background_color": color_ref(C["accent_fill"]),
        "button_text_color": color_ref(C["on_accent"]),
        "field_typography_typography": typo_ref(T["body_small"]),
    })

    head = [_caps(props["heading"], "h2", T["h_large"])]
    if props.get("eyebrow"):
        head.insert(0, _ed_eyebrow(props["eyebrow"], on_dark=True))
    if props.get("text"):
        head.append(_text(props["text"], align="center", on_dark=True))
    contact = []
    if props.get("phone_display"):
        contact.append(_pill(props["phone_display"],
                             f"tel:{props.get('phone', '')}", "outline"))

    panel = container([
        _col(head, 82, extra={"flex_align_items": "center", "flex_gap": gap(14),
                              "margin": dims(0, "auto", 34, "auto")}),
        _col([form], 72, extra={"margin": dims(0, "auto", 0, "auto")}),
    ] + ([_col(contact, extra={"flex_align_items": "center",
                               "margin": dims(26, 0, 0, 0)})] if contact else []), {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(72, 56, 76, 56),
        "padding_mobile": dims(48, 22, 52, 22),
        "border_radius": box(R_PANEL),
        "background_background": "classic",
        "custom_css": css(
            "selector { background-image: repeating-linear-gradient("
            "115deg, rgba(255,255,255,.035) 0 1px, transparent 1px 46px); }"),
    }, globals_={"background_color": color_ref("secondary")})

    return _rd_section([panel], bg=props.get("bg", "ground"), pad=RD_PAD)


# ══════════════════════════ heritage day tours ══════════════════════════
#
# A day-tour operator selling to an over-60s audience. Two requirements the
# existing library could not meet, both explicitly asked for by the client:
# a looping photographic cover, and a looping testimonial rail. The registry
# has known `image-carousel` and `testimonial-carousel` since it was remined
# from Elementor's source — there was simply never a factory for either, so
# the whole motion category was unreachable from the IR.

# Gold on navy is the brand's whole identity, and both are dark enough that
# the derived on_* tokens resolve sensibly. Heights are literal because the
# cover has to fill the viewport beside a fixed-height copy column.
HDT_COVER_H = 620
HDT_COVER_H_T = 420
HDT_COVER_H_M = 320


def _hdt_meta(text, icon_cls, on_dark=False):
    """Icon + label pair used on the tour cards' date / seats row."""
    return _row([
        widget("icon", {
            "selected_icon": icon(icon_cls), "size": slider(13),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref(
            C["brand_on_dark"] if on_dark else C["ink_primary"])}),
        widget("heading", {"title": text, "header_size": "div", "align": "left"},
               globals_={
                   "title_color": color_ref(C["muted"] if not on_dark else C["on_dark"]),
                   "typography_typography": typo_ref(T["meta"]),
               }),
    ], gap_px=8, align="center", extra={"flex_wrap": "nowrap",
                                        "flex_direction_mobile": "row"})


@block("header.heritage")
def header_heritage(props):
    """Navy bar, reversed nav, gold booking CTA.

    `header.simple` paints a white bar with dark links; every colour in it is
    wrong against a navy ground, and the active-item underline the mockup
    shows has no equivalent there. Separate factory rather than a `dark` flag,
    because the two share almost no settings once the ground flips.
    """
    logo = widget("theme-site-logo", {
        "align": "left", "width": slider(props.get("logo_width", 190)),
        **({"image": media(props["logo"], props.get("business", ""))}
           if props.get("logo") else {}),
    })
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal",
        "align_items": "center",
        "pointer": "underline",
        "menu_space_between": slider(props.get("menu_gap", 30)),
        "toggle_align": "right",
    }, globals_={
        # On a navy bar the resting link is white and the active one gold —
        # the reverse of the light header, where brand ink marks the active.
        "color_menu_item": color_ref(C["white"]),
        "color_menu_item_hover": color_ref("accent"),
        "color_menu_item_active": color_ref("accent"),
        "pointer_color_menu_item_hover": color_ref("accent"),
        "pointer_color_menu_item_active": color_ref("accent"),
        "menu_typography_typography": typo_ref(T["meta"]),
    })
    cta = _button(props["cta"]["label"], props["cta"]["href"], "accent",
                  props.get("cta_icon", "far fa-calendar"))
    w_logo, w_nav, w_cta = _tracks([21, 62, 17], 20)
    return container([
        _row([
            _col([logo], w_logo, extra={"flex_justify_content": "center"}),
            _col([nav], w_nav, extra={"flex_justify_content": "center",
                                      "flex_align_items": "flex-end"}),
            _col([cta], w_cta, extra={"flex_justify_content": "center",
                                      "flex_align_items": "flex-end"}),
        ], gap_px=20, align="center")
    ], {
        "content_width": "boxed",
        "flex_direction": "row",
        "padding": dims(14, 0, 14, 0),
        "padding_mobile": dims(12, 20, 12, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})


@block("hero.slideshow")
def hero_slideshow(props):
    """Copy on the left, a self-advancing photographic cover on the right.

    The client asked for the cover to cycle roughly ten scenic photographs.
    `image-carousel` is core rather than Pro, so this costs the kit no extra
    licence surface, and it fades rather than slides — a slide transition
    beside a static column reads as a glitch at this size.

    `pause_on_hover` is off deliberately. The audience is over 60 and the
    cover sits directly beside the primary CTA, so a cursor resting near the
    button would otherwise freeze the rotation for as long as it lingers.
    """
    imgs = props["images"]
    if not imgs:
        raise ValueError(
            "hero.slideshow needs at least one image. An empty carousel "
            "renders as a collapsed box, not as a placeholder.")

    w_left, w_right = _tracks([46, 54], 48)
    dark = props.get("dark", True)

    left = _col([
        *([_eyebrow(props["eyebrow"], on_dark=dark)] if props.get("eyebrow") else []),
        _heading(props["h1"], "h1", T["hero"], on_dark=dark),
        _text(props.get("intro", ""), on_dark=dark),
        _row([
            _button(props["cta"]["label"], props["cta"]["href"], "accent",
                    props.get("cta_icon", "far fa-calendar")),
            *([_button(props["cta2"]["label"], props["cta2"]["href"],
                       "ghost_dark", props.get("cta2_icon", "fas fa-phone"))]
              if props.get("cta2") else []),
        ], gap_px=16, extra={"flex_wrap": "wrap", "margin": dims(14, 0, 0, 0)}),
    ], w_left, extra={"flex_gap": gap(22), "flex_justify_content": "center"})

    # Pro `slides` rather than core `image-carousel`, for one reason: it owns a
    # real `slides_height` control. A fading carousel stacks every slide in one
    # box, so that box needs a height of its own, and image-carousel has no
    # control for it — it would take a CSS override of a Swiper internal, which
    # is exactly the kind of thing the contract exists to keep out. The kit
    # already requires Pro for nav-menu, so this costs no extra licence surface.
    #
    # Ken Burns is on: a still photograph beside static copy reads as a broken
    # slideshow between transitions, and a slow drift is what tells the visitor
    # the panel is alive. Each slide alternates direction so the motion does
    # not pulse in one direction for the whole loop.
    carousel = widget("slides", {
        "slides": [
            repeater_item(
                background_image=media(i["url"], i.get("alt", "")),
                background_size="cover",
                background_ken_burns="yes",
                zoom_direction="in" if n % 2 == 0 else "out",
                # Photographic panel only — the copy lives in the left column,
                # so every text field stays empty by design.
                heading="", description="", button_text="",
            )
            for n, i in enumerate(imgs)
        ],
        "slides_height": slider(props.get("cover_height", HDT_COVER_H)),
        "slides_height_tablet": slider(HDT_COVER_H_T),
        "slides_height_mobile": slider(HDT_COVER_H_M),
        "navigation": "dots",
        "autoplay": "yes",
        "autoplay_speed": props.get("dwell", 5000),
        "infinite": "yes",
        "transition": "fade",
        "transition_speed": 1200,
        # Off deliberately: the audience is over 60 and the cover sits directly
        # beside the primary CTA, so a cursor resting near the button would
        # otherwise freeze the rotation for as long as it lingers.
        "pause_on_hover": "no",
        "pause_on_interaction": "no",
        "dots_position": "inside",
        "dots_size": slider(7),
        "dots_gap": slider(5),
    }, globals_={
        "dots_color": color_ref("accent"),
        "dots_color_inactive": color_ref(C["rule_dark"]),
    })

    # The radius lives on the wrapper, not the widget: `slides` has no
    # border_radius control of its own, and V6 waves the key through on a
    # style-suffix exemption, so setting it there would be a silent no-op
    # rather than a build error.
    right = _col([carousel], w_right, extra={
        "border_radius": box(14),
        "overflow": "hidden",
    })
    inner = _row([left, right], gap_px=48, align="center")
    return _section([inner], bg="dark" if dark else "surface",
                    pad=dims(72, 0, 108, 0),
                    extra={"flex_justify_content": "center"})


@block("feature.panel")
def feature_panel(props):
    """Four icon + title + text columns on a single panel.

    Used twice on the home page in two tones: navy, tucked under the cover,
    and light, under the tour cards. `trust.bar` is a one-line icon list and
    cannot carry a description per item, which is what the mockup shows.
    """
    items = props["items"]
    on_dark = props.get("tone", "dark") == "dark"
    widths = _tracks([1] * len(items), 28)
    cols = []
    for it, w in zip(items, widths):
        cols.append(_col([
            _row([
                widget("icon", {
                    "selected_icon": icon(it.get("icon", "fas fa-star")),
                    "size": slider(props.get("icon_size", 26)),
                    "align": "left", "view": "default",
                }, globals_={"primary_color": color_ref(
                    "accent" if on_dark else C["ink_primary"])}),
                _col([
                    widget("heading", {
                        "title": it["title"], "header_size": "h3", "align": "left",
                    }, globals_={
                        "title_color": color_ref("accent" if on_dark else "secondary"),
                        "typography_typography": typo_ref(T["h_small"]),
                    }),
                    *([_text(it["text"], on_dark=on_dark, small=True)]
                      if it.get("text") else []),
                ], extra={"flex_gap": gap(4), "width": slider(76, "%")}),
            ], gap_px=14, align="flex-start",
                extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
        ], w))
    row = _row(cols, gap_px=28, align="stretch")

    panel = container([row], {
        "content_width": "full",
        "flex_direction": "column",
        "padding": dims(34, 40, 34, 40),
        "padding_mobile": dims(28, 22, 28, 22),
        "border_radius": box(4),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(
        "primary" if on_dark else C["surface_alt"])})

    # Pulled up over the section boundary above it, which is what makes the
    # panel read as a bridge between the cover and the page rather than as
    # another band. Only safe on the dark tone, which has a section above it.
    pad = dims(0, 0, 0, 0) if props.get("overlap") else dims(0, 0, 0, 0)
    sec = _section([panel], bg=props.get("bg", "white"), pad=pad,
                   extra={"z_index": 2})
    if props.get("overlap"):
        sec["settings"]["margin"] = dims(-56, 0, 0, 0)
        sec["settings"]["margin_mobile"] = dims(-24, 0, 0, 0)
    return sec


def _hdt_tour_card(t, width, width_t):
    """One tour card: photo, corner price flag, title, blurb, date + seats."""
    photo = container([
        widget("image", {
            "image": media(t["image"]["url"], t["image"]["alt"]),
            "image_size": "full",
            "width": slider(100, "%"),
        }),
    ], {
        "content_width": "full", "flex_direction": "column",
        # Elementor crops via registered thumbnail sizes, which a kit cannot
        # register, so a fixed-ratio card top has no control equivalent.
        "custom_css": css(
            "selector img { width:100%; height:210px; object-fit:cover; "
            "display:block; }"),
    })

    # The flag is a ribbon in the mockup's top-right corner. Elementor's
    # position controls could place it, but they would also need the
    # width-estimation hack _chip documents, since an absolutely positioned
    # container still defaults to width:100%. One scoped rule is less to break.
    flag = container([
        widget("heading", {
            "title": t["price_label"], "header_size": "div", "align": "center",
        }, globals_={
            "title_color": color_ref(C["on_accent"]),
            "typography_typography": typo_ref(T["meta"]),
        }),
    ], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(9, 15, 9, 15),
        "background_background": "classic",
        "custom_css": css(
            "selector { position:absolute; top:16px; right:0; z-index:3; width:auto; "
            "border-radius:3px 0 0 3px; box-shadow:0 4px 14px rgba(0,0,0,.20); }"),
    }, globals_={"background_color": color_ref(C["accent_fill"])})

    body = _col([
        _heading(t["title"], "h3", T["h_medium"]),
        _text(t["text"], small=True),
        container([], {"content_width": "full", "flex_direction": "column",
                       "padding": dims(4, 0, 0, 0),
                       "border_width": dims(1, 0, 0, 0),
                       "border_border": "solid"},
                  globals_={"border_color": color_ref(C["border"])}),
        _row([
            _hdt_meta(t["date"], "far fa-calendar"),
            _hdt_meta(t["seats"], "far fa-user"),
        ], gap_px=18, align="center",
            extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"}),
    ], extra={"padding": dims(22, 24, 24, 24), "flex_gap": gap(10)})

    card = container([photo, flag, body], {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(0),
        "width": slider(width, "%"),
        "width_tablet": slider(width_t, "%"),
        "width_mobile": slider(100, "%"),
        "border_radius": box(6),
        "border_border": "solid",
        "border_width": box(1),
        "overflow": "hidden",
        "background_background": "classic",
        "custom_css": css("selector { position:relative; }"),
        **CARD_SHADOW_SOFT,
    }, globals_={
        "background_color": color_ref(C["white"]),
        "border_color": color_ref(C["border"]),
    })
    return _hover_lift(card, 5)


@block("tours.cards")
def tours_cards(props):
    """Tour cards with a corner price flag, in two arrangements.

    Default is the home page's shape: a narrow intro column on the left and
    the featured tours beside it. `grid: true` drops the side column and lays
    every tour out `columns`-wide, which is what the tours index needs — the
    side-column form solves each card against the row, so a ten-tour index
    would compute cards seven percent wide.

    The client was explicit that the flag reads `ONLY £99 pp`, not `From
    £99` — so the factory takes the whole rendered label and never composes
    it from a number, which is how a stray `From` would creep back in.
    """
    tours = props["items"]
    width_t = _track(2, 24, TABLET_CONTAINER)

    if props.get("grid"):
        cols = props.get("columns", 3)
        width = _track(cols, 24)
        cards = [_hdt_tour_card(t, width, width_t) for t in tours]
        head = _section_head(props) if props.get("heading") else None
        rows = [_row(cards[i:i + cols], gap_px=24, align="stretch")
                for i in range(0, len(cards), cols)]
        body = _col(rows, extra={"flex_gap": gap(24)})
        return _section(([head] if head else []) + [body],
                        bg=props.get("bg", "surface"))

    intro_w, cards_w = _tracks([26, 74], 40)
    intro = _col([
        *([_eyebrow(props["eyebrow"])] if props.get("eyebrow") else []),
        _heading(props["heading"], "h2", T["h_large"], tone="brand"),
        *([_text(props["intro"])] if props.get("intro") else []),
        *([_row([_button(props["cta"]["label"], props["cta"]["href"], "primary", None)],
                extra={"margin": dims(8, 0, 0, 0)})] if props.get("cta") else []),
    ], intro_w, extra={"flex_gap": gap(18), "flex_justify_content": "center"})

    width = _track(len(tours), 24, container=int(KIT_CONTAINER * cards_w / 100))
    cards = [_hdt_tour_card(t, width, width_t) for t in tours]
    grid = _col([_row(cards, gap_px=24, align="stretch")], cards_w)
    return _section([_row([intro, grid], gap_px=40, align="center")],
                    bg=props.get("bg", "surface"))


@block("testimonials.carousel")
def testimonials_carousel(props):
    """Looping testimonial rail — the client asked for it under the cards.

    `reviews.grid` shows three at once and stops; this keeps moving, which is
    what "looping testimonial section" asks for. `loop` and `pause_on_hover`
    are both on: unlike the cover, a visitor hovering here is reading.
    """
    quotes = props["items"]
    head = _col([
        *([_eyebrow(props["eyebrow"])] if props.get("eyebrow") else []),
        _heading(props["heading"], "h2", T["h_large"], align="center", tone="brand"),
        *([_text(props["intro"], align="center")] if props.get("intro") else []),
    ], extra={"flex_align_items": "center", "content_width": "boxed", "boxed_width": slider(760),
              "margin": dims(0, "auto", 44, "auto")})

    per = min(props.get("per_view", 3), max(1, len(quotes)))
    rail = widget("testimonial-carousel", {
        "slides": [
            repeater_item(
                content=q["quote"],
                name=q["name"],
                title=q.get("meta", ""),
                **({"image": media(q["image"]["url"], q["image"]["alt"])}
                   if q.get("image") else {}),
            )
            for q in quotes
        ],
        "skin": "default",
        "layout": "image_above",
        "alignment": "center",
        "slides_per_view": str(per),
        "slides_to_scroll": "1",
        "autoplay": "yes",
        "autoplay_speed": props.get("dwell", 5200),
        "loop": "yes",
        "speed": 700,
        "effect": "slide",
        "pause_on_hover": "yes",
        "show_arrows": "yes",
        "image_size": "thumbnail",
        "content_gap": slider(14),
        "image_gap": slider(16),
        "image_border_radius": box(999),
    }, globals_={
        "content_color": color_ref("text"),
        "name_color": color_ref("secondary"),
        "title_color": color_ref(C["ink_primary"]),
        "content_typography_typography": typo_ref(T["body_small"]),
        "name_typography_typography": typo_ref(T["h_small"]),
        "title_typography_typography": typo_ref(T["meta"]),
        "arrows_color": color_ref(C["ink_primary"]),
    })
    return _section([head, rail], bg=props.get("bg", "white"))


# ══════════════════════════ greyson private wealth ══════════════════════════
#
# A tax-integrated wealth manager. The design was signed off in Adobe XD and
# the brief is to match it exactly, so these factories follow the comps rather
# than the house patterns — the palette is navy/gold/cream from the brand
# guide, and the type system is Playfair Display over Inter.
#
# The SOW asks for a reusable component library built once and shared, which
# is what this is: `hero.greyson`, `framework.donut`, `cta.greyson`,
# `icons.row`, `story.split` and `faq.aside` are all used by more than one
# page, and the ten pages still to come reuse them without new code.

GW_PAD = dims(96, 0, 96, 0)
GW_PAD_T = dims(72, 24, 72, 24)
GW_PAD_M = dims(56, 20, 56, 20)


def _gw_anim(props, name="fadeInUp", n=0, step=90):
    """Entrance animation as an opt-in prop.

    Off unless a page asks for it, so adding motion to a new page cannot
    quietly restyle pages that were already signed off. Elementor exposes
    these as Advanced -> Motion Effects, which keeps them editable rather
    than baked into markup.
    """
    if not props.get("animate"):
        return {}
    return {"animation": name, "animation_delay": step * min(n, 6)}


def _gw_section(children, bg="white", pad=None, extra=None):
    """Greyson section shell. Narrower rhythm than SECTION_PAD's 104px."""
    return _section(children, bg=bg, pad=pad or GW_PAD, extra={
        **({"padding_tablet": GW_PAD_T, "padding_mobile": GW_PAD_M}),
        **(extra or {}),
    })


def _gw_eyebrow(text, align="center"):
    """Gold, uppercase, wide-tracked. Brand guide 05: eyebrows are always gold.

    NOTE: gold on cream measures 2.23:1 and on white 2.56:1, both under the
    4.5:1 the same brand guide asks for. Built as designed because the comp is
    the spec; switching to the darkened `gold_ink` is a one-line change here.
    """
    return widget("heading", {
        "title": text, "header_size": "div", "align": align,
    }, globals_={
        "title_color": color_ref("accent"),
        "typography_typography": typo_ref(T["eyebrow"]),
    })


def _gw_head(props, on_dark=False, align="center", max_w=780):
    """Eyebrow + serif headline + optional standfirst, centred."""
    return _col([
        *([_gw_eyebrow(props["eyebrow"], align)] if props.get("eyebrow") else []),
        _heading(props["heading"], props.get("head_tag", "h2"), T["h_large"],
                 align=align, on_dark=on_dark),
        *([_text(props["intro"], align=align, on_dark=on_dark)]
          if props.get("intro") else []),
    ], extra={"flex_align_items": "center" if align == "center" else "flex-start",
              "content_width": "boxed", "boxed_width": slider(max_w), "flex_gap": gap(14),
              "margin": dims(0, "auto", 44, "auto")})


def _gw_rule(width=56, align="center"):
    """The short gold rule under a headline — the brand's recurring device."""
    return widget("divider", {
        "weight": slider(2), "gap": slider(18), "look": "line",
        "width": slider(width), "align": align,
    }, globals_={"color": color_ref("accent")})


@block("header.greyson")
def header_greyson(props):
    """Utility strip, then logo left / nav right / gold pill CTA.

    `header.simple` centres a three-column bar with the CTA as a bordered
    button; the comp runs a pill and a thin utility strip carrying Client
    Login and search. Kept as its own factory rather than more flags on
    `header.simple`, which already carries two.
    """
    strip = container([
        widget("icon-list", {
            "icon_list": [
                repeater_item(text=i["text"],
                              selected_icon=icon(i.get("icon", "fas fa-lock")),
                              link=link(i.get("href", "")))
                for i in props.get("utility", [])
            ],
            "view": "inline", "space_between": slider(22), "icon_size": slider(11),
        }, globals_={
            "icon_color": color_ref(C["muted"]),
            "text_color": color_ref(C["muted"]),
            "icon_typography_typography": typo_ref(T["meta"]),
        }),
    ], {
        "content_width": "boxed", "flex_direction": "row",
        "flex_justify_content": "flex-end", "flex_align_items": "center",
        "padding": dims(7, 0, 7, 0),
        "hide_mobile": "hidden-mobile",
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface"])})

    logo = widget("theme-site-logo", {
        "align": "left", "width": slider(props.get("logo_width", 200)),
        **({"image": media(props["logo"], props.get("business", ""))}
           if props.get("logo") else {}),
    })
    nav = widget("nav-menu", {
        "menu": props.get("menu", "main-menu"),
        "layout": "horizontal", "align_items": "center",
        "pointer": "none",
        "menu_space_between": slider(props.get("menu_gap", 30)),
        "toggle_align": "right",
    }, globals_={
        "color_menu_item": color_ref("secondary"),
        "color_menu_item_hover": color_ref("accent"),
        "color_menu_item_active": color_ref("accent"),
        "menu_typography_typography": typo_ref(T["meta"]),
    })
    # Pill, not the kit's 8px radius — the comp's CTA is fully rounded.
    cta = _button(props["cta"]["label"], props["cta"]["href"], "accent", None)
    cta["settings"]["border_radius"] = box(999)
    cta["settings"]["text_padding"] = dims(13, 26, 13, 26)

    w_logo, w_nav, w_cta = _tracks([22, 58, 20], 20)
    bar = container([
        _row([
            _col([logo], w_logo, extra={"flex_justify_content": "center"}),
            _col([nav], w_nav, extra={"flex_justify_content": "center",
                                      "flex_align_items": "flex-end"}),
            _col([cta], w_cta, extra={"flex_justify_content": "center",
                                      "flex_align_items": "flex-end"}),
        ], gap_px=20, align="center")
    ], {
        "content_width": "boxed", "flex_direction": "row",
        "padding": dims(16, 0, 16, 0),
        "padding_mobile": dims(12, 20, 12, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"])})

    if not props.get("utility"):
        return bar
    return container([strip, bar], {
        "content_width": "full", "flex_direction": "column", "flex_gap": gap(0),
    })


@block("hero.greyson")
def hero_greyson(props):
    """Full-bleed photograph, left-aligned copy, up to two CTAs.

    Two sizes via `pad`: the home hero runs tall, the inner-page hero short.
    `hero.banner` centres a lone title and `hero.split` puts the photo in its
    own column — neither is this shape.
    """
    body = _col([
        *([_gw_eyebrow(props["eyebrow"], "left")] if props.get("eyebrow") else []),
        _heading(props["h1"], "h1", T["hero"], on_dark=True),
        *([_text(props.get("intro"), on_dark=True)] if props.get("intro") else []),
        *([_row([
            _button(props["cta"]["label"], props["cta"]["href"], "accent", None),
            *([_button(props["cta2"]["label"], props["cta2"]["href"],
                       "ghost_dark", None)] if props.get("cta2") else []),
        ], gap_px=14, extra={"flex_wrap": "wrap", "margin": dims(18, 0, 0, 0)})]
          if props.get("cta") else []),
    ], props.get("width", 56), extra={"flex_gap": gap(18),
                                      **_gw_anim(props, "fadeInUp")})

    sec = _gw_section([_row([body], justify="flex-start")], bg="dark",
                      pad=dims(props.get("pad", 190), 0, props.get("pad", 190), 0),
                      extra={"flex_justify_content": "center",
                             "padding_mobile": dims(110, 20, 96, 20)})
    if props.get("image"):
        sec["settings"].update({
            "background_image": media(props["image"]["url"], props["image"]["alt"]),
            "background_position": "center center",
            "background_size": "cover",
            "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_opacity": slider(props.get("overlay", 0.55)),
        })
        sec["settings"]["__globals__"]["background_overlay_color"] = color_ref("secondary")
        _scrim(sec, props.get("scrim", "left"), 0.72)
    return sec


@block("credentials.bar")
def credentials_bar(props):
    """Navy strip of proof groups, hairline-separated.

    Each group is a stacked label/value pair rather than one line, because the
    middle group in the comp sets `50+` at display size against small caps.
    """
    items = props["items"]
    widths = _tracks([1] * len(items), 0)
    cols = []
    for n, it in enumerate(items):
        inner = [
            widget("heading", {
                "title": it["value"], "header_size": "div", "align": "center",
            }, globals_={
                "title_color": color_ref(C["white"]),
                "typography_typography": typo_ref(
                    T["h_large"] if it.get("display") else T["h_small"]),
            }),
            widget("heading", {
                "title": it["label"], "header_size": "div", "align": "center",
            }, globals_={
                "title_color": color_ref("accent"),
                "typography_typography": typo_ref(T["eyebrow"]),
            }),
        ]
        extra = {"flex_align_items": "center", "flex_gap": gap(6),
                 "padding": dims(4, 18, 4, 18),
                 **_gw_anim(props, "fadeInUp", n, step=110)}
        # Hairlines between groups, never before the first — a leading rule
        # reads as a broken edge against the section padding.
        if n:
            extra["border_border"] = "solid"
            extra["border_width"] = dims(0, 0, 0, 1)
        col = _col(inner, widths[n], extra=extra)
        if n:
            col["settings"]["__globals__"] = {"border_color": color_ref(C["rule_dark"])}
        cols.append(col)
    return _gw_section([_row(cols, gap_px=0, align="center")], bg="dark",
                       pad=dims(30, 0, 30, 0))


@block("icons.row")
def icons_row(props):
    """N columns of gold icon + title + copy, optionally with a link button.

    Covers both `Most advice has been delivered in pieces` (four plain gold
    glyphs) and `Who we're built for` (gold roundels over a Learn More). One
    factory because the only differences are the icon treatment and the
    button, and two near-identical factories drift apart on the next revision.
    """
    items = props["items"]
    cols_n = props.get("columns", len(items))
    width, width_t = _grid_widths(cols_n, 28)
    on_dark = props.get("tone") == "dark"
    circled = props.get("icon_style", "plain") == "circle"

    cols = []
    for it in items:
        glyph = widget("icon", {
            "selected_icon": icon(it.get("icon", "fas fa-circle")),
            "size": slider(props.get("icon_size", 26)),
            "align": "center",
            "view": "stacked" if circled else "default",
            **({"shape": "circle", "icon_padding": slider(18)} if circled else {}),
        }, globals_={
            "primary_color": color_ref("accent") if circled else color_ref("accent"),
            **({"secondary_color": color_ref(C["on_accent"])} if circled else {}),
        })
        parts = [
            glyph,
            _heading(it["title"], "h3", T["h_medium"], align="center",
                     on_dark=on_dark),
        ]
        if it.get("text"):
            parts.append(_text(it["text"], align="center", on_dark=on_dark,
                               small=True))
        if it.get("rule"):
            parts.append(_gw_rule(40))
        if it.get("href"):
            btn = _button(it.get("cta", "Learn More"), it["href"], "ghost", None)
            btn["settings"]["border_radius"] = box(999)
            btn["settings"]["text_padding"] = dims(11, 24, 11, 24)
            parts.append(_row([btn], justify="center",
                              extra={"margin": dims(6, 0, 0, 0)}))
        cols.append(_col(parts, width, extra={
            "flex_align_items": "center", "flex_gap": gap(12),
            "width_tablet": slider(width_t, "%"),
        }))

    head = _gw_head(props, on_dark=on_dark) if props.get("heading") else None
    return _gw_section(([head] if head else []) + [_row(cols, gap_px=28,
                                                        align="flex-start")],
                       bg=props.get("bg", "white"))


@block("story.split")
def story_split(props):
    """Centred headline over a text column beside a photograph.

    The Who We Are page runs this three times, alternating the photo side and
    the ground. `about.split` is close but hangs a tick-list off the copy and
    puts the heading inside the text column; here the headline is centred
    above the whole split, which is what makes the page read as a sequence of
    statements rather than a stack of cards.
    """
    reverse = props.get("reverse", False)
    w_a, w_b = _tracks([48, 52] if not reverse else [52, 48], 56)

    text_col = _col([
        *([_gw_eyebrow(props["eyebrow"], "left")] if props.get("eyebrow") else []),
        _text(props["body"]),
        *([widget("text-editor", {
            "editor": f"<p><strong>{props['emphasis']}</strong></p>",
            "align": "left",
        }, globals_={"text_color": color_ref("secondary"),
                     "typography_typography": typo_ref("text")})]
          if props.get("emphasis") else []),
    ], w_b if reverse else w_a, extra={"flex_gap": gap(14),
                                       "flex_justify_content": "center"})

    photo = _col([widget("image", {
        "image": media(props["image"]["url"], props["image"]["alt"]),
        "image_size": "full",
        "width": slider(100, "%"),
        "height": slider(props.get("image_height", 340)),
        "height_mobile": slider(230),
        "object-fit": "cover",
        "object-position": "center center",
        "image_border_radius": box(props.get("radius", 6)),
    })], w_a if reverse else w_b)

    row = _row([photo, text_col] if reverse else [text_col, photo],
               gap_px=56, align="center")
    head = _col([
        _heading(props["heading"], props.get("head_tag", "h2"), T["h_large"],
                 align="center"),
    ], extra={"flex_align_items": "center", "content_width": "boxed", "boxed_width": slider(860),
              "margin": dims(0, "auto", 40, "auto")}) if props.get("heading") else None

    return _gw_section(([head] if head else []) + [row],
                       bg=props.get("bg", "white"))


@block("cta.greyson")
def cta_greyson(props):
    """Navy closing band — headline, one line of copy, gold + ghost buttons.

    `cta.band` wraps Pro's call-to-action widget, which allows one button.
    The comp closes both pages with two, so this is built from parts.
    """
    btns = [_button(props["cta"]["label"], props["cta"]["href"], "accent", None)]
    if props.get("cta2"):
        btns.append(_button(props["cta2"]["label"], props["cta2"]["href"],
                            "ghost_dark", None))
    for b in btns:
        b["settings"]["border_radius"] = box(999)
        b["settings"]["text_padding"] = dims(15, 32, 15, 32)

    return _gw_section([_col([
        _heading(props["heading"], "h2", T["h_large"], align="center",
                 on_dark=True),
        *([_text(props["text"], align="center", on_dark=True)]
          if props.get("text") else []),
        _row(btns, gap_px=14, justify="center",
             extra={"flex_wrap": "wrap", "margin": dims(12, 0, 0, 0)}),
    ], extra={"flex_align_items": "center", "content_width": "boxed", "boxed_width": slider(820),
              "margin": dims(0, "auto", 0, "auto"), "flex_gap": gap(16),
              **_gw_anim(props, "fadeInUp")})],
        bg="dark", pad=dims(84, 0, 84, 0))


def _gw_ring(phases, active, navy, gold, ink_on_navy, centre_label):
    """SVG for the four-discipline ring. Returns markup, not a widget.

    Elementor has no segmented-donut widget and no plugin in the allowed tier
    draws one, so this is inline SVG in a core `html` widget. It is the one
    place in this kit where colour is a literal rather than a global: SVG fill
    attributes cannot reach the `__globals__` channel. The values are passed
    in from the brand rather than typed here, so a re-skin still flows from
    `tokens.py` through the IR — it just does not flow automatically.
    """
    cx = cy = 150.0
    r_out, r_in = 132.0, 78.0
    gap_deg = 1.6
    span = 360.0 / len(phases)

    def pt(r, deg):
        a = math.radians(deg)
        return f"{cx + r * math.cos(a):.2f} {cy + r * math.sin(a):.2f}"

    seg = []
    for i, ph in enumerate(phases):
        start = -90 - span / 2 + i * span + gap_deg / 2
        end = start + span - gap_deg
        large = 1 if (end - start) > 180 else 0
        d = (f"M {pt(r_out, start)} A {r_out} {r_out} 0 {large} 1 {pt(r_out, end)} "
             f"L {pt(r_in, end)} A {r_in} {r_in} 0 {large} 0 {pt(r_in, start)} Z")
        fill = gold if (i + 1) == active else navy
        label_fill = ink_on_navy if (i + 1) == active else "#FFFFFF"
        seg.append(f'<path d="{d}" fill="{fill}"/>')

        mid = start + (end - start) / 2
        lr = (r_out + r_in) / 2
        a = math.radians(mid)
        lx, ly = cx + lr * math.cos(a), cy + lr * math.sin(a)
        words = ph["label"].split()
        # Two lines at most; a three-word discipline name set on one line
        # overruns the band and collides with the segment edge.
        if len(words) > 2:
            lines = [" ".join(words[:len(words) // 2]), " ".join(words[len(words) // 2:])]
        else:
            lines = words
        dy0 = -(len(lines) - 1) * 7
        spans = "".join(
            f'<tspan x="{lx:.2f}" dy="{(dy0 if n == 0 else 14):.2f}">{ln}</tspan>'
            for n, ln in enumerate(lines))
        seg.append(
            f'<text x="{lx:.2f}" y="{ly:.2f}" text-anchor="middle" fill="{label_fill}" '
            f'font-family="Inter, sans-serif" font-size="11" font-weight="600" '
            f'letter-spacing="0.4">{spans}</text>')

    cl = centre_label.split()
    centre = "".join(
        f'<tspan x="{cx}" dy="{(0 if n == 0 else 13):.2f}">{w}</tspan>'
        for n, w in enumerate(cl))
    return (
        f'<svg viewBox="0 0 300 300" role="img" '
        f'aria-label="{centre_label}: {", ".join(p["label"] for p in phases)}" '
        f'style="width:100%;height:auto;max-width:400px;display:block;margin:0 auto">'
        f'{"".join(seg)}'
        f'<circle cx="{cx}" cy="{cy}" r="{r_in - 12}" fill="#FFFFFF"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r_in - 12}" fill="none" stroke="{navy}" '
        f'stroke-width="1.5"/>'
        f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" fill="{navy}" '
        f'font-family="Inter, sans-serif" font-size="11" font-weight="700" '
        f'letter-spacing="1.2">{centre}</text>'
        f'</svg>')


@block("framework.donut")
def framework_donut(props):
    """The four-discipline ring beside the active phase's detail panel.

    `active` selects which segment is gold and which phase the panel
    describes, so the four Framework pages still to be built (Tax Strategy,
    Institutional Portfolio Management, Risk Architecture, Estate & Legacy
    Engineering) each reuse this factory with a different `active` rather than
    getting a bespoke section.

    Clicking a segment to swap the panel needs JavaScript, which a Template
    Kit cannot carry — that is a change order under SOW section 12. The dots
    in the comp are rendered, but as a position indicator, not a control.
    """
    phases = props["phases"]
    active = props.get("active", 1)
    cur = phases[active - 1]

    ring = widget("html", {
        "html": _gw_ring(phases, active, props.get("navy", "#25313F"),
                         props.get("gold", "#D09748"),
                         props.get("ink_on_gold", "#25313F"),
                         props.get("centre", "ONE STRATEGY")),
    })

    bullets = widget("icon-list", {
        "icon_list": [repeater_item(text=b, selected_icon=icon("fas fa-check"),
                                    link=link("")) for b in cur["points"]],
        "space_between": slider(13),
        "icon_size": slider(13),
    }, globals_={
        "icon_color": color_ref("accent"),
        "text_color": color_ref("text"),
        "icon_typography_typography": typo_ref(T["body_small"]),
    })

    dots = _row([
        container([], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(7), "min_height": slider(7),
            "border_radius": box(999), "background_background": "classic",
        }, globals_={"background_color": color_ref(
            "accent" if (i + 1) == active else C["border"])})
        for i in range(len(phases))
    ], gap_px=7, extra={"flex_wrap": "nowrap", "margin": dims(22, 0, 0, 0),
                        "flex_direction_mobile": "row"})

    panel = _col([
        _gw_eyebrow(f"{cur['label'].upper()} · PHASE {cur.get('roman', active)}", "left"),
        _heading(cur["title"], "h3", T["h_medium"]),
        bullets,
        *([_row([_button(props.get("more_label", "READ MORE"), cur["href"],
                         "ghost", "fas fa-arrow-right")],
                extra={"margin": dims(8, 0, 0, 0)})] if cur.get("href") else []),
        dots,
    ], extra={"flex_gap": gap(14), "flex_justify_content": "center"})

    w_ring, w_panel = _tracks([48, 52], 56)
    return _gw_section([
        _gw_head(props),
        _row([_col([ring], w_ring), _col([panel], w_panel)],
             gap_px=56, align="center"),
    ], bg=props.get("bg", "white"))


@block("process.numbered3")
def process_numbered3(props):
    """Numbered circles on the dark ground, one column per step."""
    items = props["items"]
    width, width_t = _grid_widths(len(items), 32)
    cols = []
    for n, it in enumerate(items, 1):
        num = container([
            widget("heading", {"title": str(n), "header_size": "div",
                               "align": "center"},
                   globals_={"title_color": color_ref("accent"),
                             "typography_typography": typo_ref(T["h_medium"])}),
        ], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(58), "min_height": slider(58),
            "flex_justify_content": "center", "flex_align_items": "center",
            "border_radius": box(999), "border_border": "solid",
            "border_width": box(1),
        }, globals_={"border_color": color_ref("accent")})
        cols.append(_col([
            _row([num], justify="center"),
            _heading(it["title"], "h3", T["h_medium"], align="center", on_dark=True),
            _text(it["text"], align="center", on_dark=True, small=True),
        ], width, extra={"flex_align_items": "center", "flex_gap": gap(14),
                         "width_tablet": slider(width_t, "%")}))
    return _gw_section([_gw_head(props, on_dark=True),
                        _row(cols, gap_px=32, align="flex-start")], bg="dark")


@block("listcard.split")
def listcard_split(props):
    """White card of stacked claims beside a photograph, then a link grid.

    The claims are title + sentence pairs separated by hairlines, which no
    existing factory does — `checklist.split` circles an icon against each and
    `_ticks` drops the sentence entirely.
    """
    rows = []
    for n, it in enumerate(props["items"]):
        inner = _col([
            _heading(it["title"], "h3", T["h_small"]),
            *([_text(it["text"], small=True)] if it.get("text") else []),
        ], extra={"flex_gap": gap(4),
                  "padding": dims(16 if n else 0, 0, 16, 0)})
        if n:
            inner["settings"]["border_border"] = "solid"
            inner["settings"]["border_width"] = dims(1, 0, 0, 0)
            inner["settings"]["__globals__"] = {"border_color": color_ref(C["border"])}
        rows.append(inner)

    card = container(rows, {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(34, 36, 34, 36), "padding_mobile": dims(26, 22, 26, 22),
        "border_radius": box(6), "border_border": "solid", "border_width": box(1),
        "background_background": "classic", **CARD_SHADOW_SOFT,
    }, globals_={"background_color": color_ref(C["white"]),
                 "border_color": color_ref(C["border"])})

    w_card, w_img = _tracks([54, 46], 48)
    photo = _col([widget("image", {
        "image": media(props["image"]["url"], props["image"]["alt"]),
        "image_size": "full", "width": slider(100, "%"),
        "height": slider(props.get("image_height", 400)),
        "height_mobile": slider(240),
        "object-fit": "cover", "object-position": "center center",
        "image_border_radius": box(6),
    })], w_img)

    body = [_gw_head(props), _row([_col([card], w_card), photo], gap_px=48,
                                  align="center")]

    # The audience row underneath: label + arrow, two per line on tablet.
    if props.get("links"):
        lw, lw_t = _grid_widths(props.get("link_columns", 2), 24)
        cells = []
        for l in props["links"]:
            cells.append(_col([
                _row([
                    widget("icon", {"selected_icon": icon(l.get("icon", "fas fa-user")),
                                    "size": slider(18), "align": "center",
                                    "view": "default"},
                           globals_={"primary_color": color_ref("accent")}),
                    _heading(l["title"], "h3", T["h_small"]),
                ], gap_px=12, align="center",
                    extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                           "width": slider(66, "%")}),
                _row([_button(l.get("cta", "Learn More"), l["href"], "ghost",
                              "fas fa-arrow-right")], justify="flex-end"),
            ], lw, extra={
                "flex_direction": "row", "flex_align_items": "center",
                "flex_justify_content": "space-between",
                "padding": dims(16, 4, 16, 4),
                "border_border": "solid", "border_width": dims(0, 0, 1, 0),
                "width_tablet": slider(lw_t, "%"),
            }))
            cells[-1]["settings"]["__globals__"] = {
                "border_color": color_ref(C["border"])}
        body.append(_row(cells, gap_px=24, align="stretch",
                         extra={"margin": dims(44, 0, 0, 0)}))

    return _gw_section(body, bg=props.get("bg", "surface"))


@block("timeline.zigzag")
def timeline_zigzag(props):
    """Alternating entries down a dashed gold spine with ring nodes.

    Rebuilt from the hand-written HTML version of this section so the same
    design ships as editable Elementor containers: real `h3` + paragraph, all
    colour through globals, no inline `<style>`, no font `@import`, and the
    scroll reveal expressed as a normal Motion Effects entrance animation
    rather than a bespoke IntersectionObserver.

    Every entry has the same child order — spacer, rail, body. Left-hand
    entries flip with `row-reverse` instead of moving the body into the other
    column, which is what keeps the mobile stack consistent: dot, heading,
    copy, the same way down the whole list rather than alternating.

    Two details of the HTML original do not survive the conversion, both
    deliberately: the spine is straight rather than meandering (a curve needs
    an SVG path, which is not an editable widget), and the short stub joining
    each node to its heading is dropped (it needs absolute positioning, which
    would stop the section reflowing on mobile).
    """
    w_side, w_rail, w_body = _tracks([46, 8, 46], 0)
    items = props["items"]
    node = props.get("node_size", 22)
    rail_style = props.get("rail_style", "dashed")
    animate = props.get("animate", True)
    # The node is centred on the heading's first line, not on the top of the
    # column, so it needs the heading's half-line-height less its own radius.
    node_offset = props.get("node_offset", 7)

    def rail(last):
        """Ring node, then the dashed run down to the next node."""
        ring = container([
            container([], {
                "content_width": "full", "flex_direction": "column",
                "width": slider(round(node * 0.38)),
                "min_height": slider(round(node * 0.38)),
                "border_radius": box(999),
                "background_background": "classic",
            }, globals_={"background_color": color_ref("accent")}),
        ], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(node), "min_height": slider(node),
            "border_radius": box(999),
            "border_border": "solid", "border_width": box(2),
            "background_background": "classic",
            "flex_align_items": "center", "flex_justify_content": "center",
            "margin": dims(node_offset, 0, 0, 0),
        }, globals_={"background_color": color_ref(C["surface"]),
                     "border_color": color_ref("accent")})
        children = [ring]
        # No run below the final node — the spine ends on the last entry, the
        # way the drawn version does.
        if not last:
            children.append(container([], {
                "content_width": "full", "flex_direction": "column",
                "width": slider(0), "min_height": slider(24),
                "_flex_grow": 1,
                "border_border": rail_style, "border_width": dims(0, 0, 0, 2),
                "margin": dims(6, 0, 0, 0),
            }, globals_={"border_color": color_ref("accent")}))
        return container(children, {
            "content_width": "full", "flex_direction": "column",
            "width": slider(w_rail, "%"), "width_mobile": slider(100, "%"),
            "flex_align_items": "center",
            "flex_align_items_mobile": "flex-start",
            "flex_gap": gap(0),
        })

    entries = []
    for n, it in enumerate(items):
        left = n % 2 == 0
        side = "right" if left else "left"

        head = _heading(it["title"], "h3", T["h_medium"], align=side)
        head["settings"]["align_mobile"] = "left"
        copy = _text(it["text"], align=side, small=True)
        copy["settings"]["align_mobile"] = "left"

        # Measure is capped with padding on the OUTER edge, never `max_width`:
        # `max_width` is not a container control in Elementor and is silently
        # ignored. Padding the far side narrows the line length to roughly the
        # 440px the drawn version uses while leaving the inner edge locked to
        # the spine.
        body = _col([head, copy], w_body, extra={
            "flex_gap": gap(10),
            "padding": dims(0, 0, 34, 130) if left else dims(0, 130, 34, 0),
            "padding_tablet": dims(0, 0, 28, 0),
            "padding_mobile": dims(8, 0, 26, 34),
            **({"animation": "fadeInUp",
                "animation_delay": 90 * min(n, 4)} if animate else {}),
        })

        spacer = container([], {
            "content_width": "full", "flex_direction": "column",
            "width": slider(w_side, "%"), "width_mobile": slider(0, "%"),
        })

        entries.append(_row(
            [spacer, rail(last=n == len(items) - 1), body],
            gap_px=0, align="stretch",
            extra={"flex_direction": "row-reverse" if left else "row",
                   "flex_direction_mobile": "column",
                   "flex_gap": gap(0)}))

    # Zero gap between rows: consecutive rail columns have to touch or the
    # dashed spine breaks at every entry boundary. The breathing room is the
    # body column's own bottom padding instead.
    return _gw_section([_gw_head(props), _col(entries, extra={"flex_gap": gap(0)})],
                       bg=props.get("bg", "white"))


@block("partners.cards")
def partners_cards(props):
    """Portrait cards on the dark ground; one may carry a bio."""
    people = props["items"]
    width, width_t = _grid_widths(len(people), 28)
    cards = []
    for p in people:
        inner = [widget("image", {
            "image": media(p["image"]["url"], p["image"]["alt"]),
            "image_size": "full", "width": slider(100, "%"),
            "height": slider(props.get("photo_height", 300)),
            "height_mobile": slider(260),
            "object-fit": "cover", "object-position": "center top",
            "image_border_radius": box(4),
        })] if p.get("image") else []
        if p.get("bio"):
            inner = [container([_text(p["bio"], on_dark=True, small=True)], {
                "content_width": "full", "flex_direction": "column",
                "padding": box(22), "border_radius": box(4),
                "min_height": slider(props.get("photo_height", 300)),
                "background_background": "classic",
            }, globals_={"background_color": color_ref(C["overlay"])})]
        cards.append(_col(inner + [
            _heading(p["name"], "h3", T["h_small"], align="center", on_dark=True),
            widget("heading", {"title": p["role"], "header_size": "div",
                               "align": "center"},
                   globals_={"title_color": color_ref("accent"),
                             "typography_typography": typo_ref(T["meta"])}),
        ], width, extra={"flex_gap": gap(12), "width_tablet": slider(width_t, "%")}))
    return _gw_section([_gw_head(props, on_dark=True),
                        _row(cards, gap_px=28, align="flex-start")], bg="dark")


@block("testimonials.columns")
def testimonials_columns(props):
    """Three static quotes, gold mark above each. No carousel in this comp."""
    quotes = props["items"]
    width, width_t = _grid_widths(len(quotes), 32)
    cols = []
    for q in quotes:
        cols.append(_col([
            widget("icon", {"selected_icon": icon("fas fa-quote-left"),
                            "size": slider(20), "align": "left",
                            "view": "default"},
                   globals_={"primary_color": color_ref("accent")}),
            _text(q["quote"], small=True),
            widget("heading", {"title": q["name"], "header_size": "div",
                               "align": "left"},
                   globals_={"title_color": color_ref("accent"),
                             "typography_typography": typo_ref(T["eyebrow"])}),
            *([widget("heading", {"title": q["meta"], "header_size": "div",
                                  "align": "left"},
                      globals_={"title_color": color_ref(C["muted"]),
                                "typography_typography": typo_ref(T["meta"])})]
              if q.get("meta") else []),
        ], width, extra={"flex_gap": gap(10), "width_tablet": slider(width_t, "%")}))
    return _gw_section([_gw_head(props), _row(cols, gap_px=32, align="flex-start")],
                       bg=props.get("bg", "white"))


@block("engagement.cards")
def engagement_cards(props):
    """Three fee-structure cards; `featured` lifts one with a gold flag."""
    items = props["items"]
    width, width_t = _grid_widths(len(items), 26)
    cards = []
    for it in items:
        feat = it.get("featured")
        head = [
            widget("icon", {"selected_icon": icon(it.get("icon", "fas fa-circle")),
                            "size": slider(22), "align": "left",
                            "view": "default"},
                   globals_={"primary_color": color_ref("accent")}),
            widget("heading", {"title": it["eyebrow"], "header_size": "div",
                               "align": "left"},
                   globals_={"title_color": color_ref(C["muted"]),
                             "typography_typography": typo_ref(T["eyebrow"])}),
            _heading(it["title"], "h3", T["h_medium"]),
            *([_text(it["text"], small=True)] if it.get("text") else []),
            widget("icon-list", {
                "icon_list": [repeater_item(text=b, selected_icon=icon("fas fa-check"),
                                            link=link("")) for b in it["points"]],
                "space_between": slider(11), "icon_size": slider(12),
            }, globals_={"icon_color": color_ref("accent"),
                         "text_color": color_ref("text"),
                         "icon_typography_typography": typo_ref(T["body_small"])}),
        ]
        # "Most Popular" sits on the top border of the featured card, so it
        # has to leave the flow — same treatment as the tour price flag.
        if it.get("badge"):
            head.insert(0, container([
                widget("heading", {"title": it["badge"], "header_size": "div",
                                   "align": "center"},
                       globals_={"title_color": color_ref(C["on_accent"]),
                                 "typography_typography": typo_ref(T["eyebrow"])}),
            ], {
                "content_width": "full", "flex_direction": "column",
                "padding": dims(6, 14, 6, 14),
                "border_radius": box(999),
                "background_background": "classic",
                "custom_css": css(
                    "selector { position:absolute; top:-14px; right:22px; "
                    "z-index:3; width:auto; }"),
            }, globals_={"background_color": color_ref(C["accent_fill"])}))

        card = container(head, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(12),
            "width": slider(width, "%"), "width_tablet": slider(width_t, "%"),
            "width_mobile": slider(100, "%"),
            "padding": dims(30, 30, 32, 30),
            "border_radius": box(6), "border_border": "solid",
            "border_width": box(2 if feat else 1),
            "background_background": "classic",
            **({"custom_css": css("selector { position:relative; }")}
               if it.get("badge") else {}),
            **(CARD_SHADOW if feat else CARD_SHADOW_SOFT),
        }, globals_={
            "background_color": color_ref(C["white"]),
            "border_color": color_ref("accent" if feat else C["border"]),
        })
        cards.append(card)
    return _gw_section([_gw_head(props), _row(cards, gap_px=26, align="stretch")],
                       bg=props.get("bg", "surface"))


@block("faq.aside")
def faq_aside(props):
    """Accordion beside a photograph. Pro's FAQ schema comes from the plugin,
    not from this JSON — see the README on validating it after import."""
    w_faq, w_img = _tracks([56, 44], 48)
    photo = _col([widget("image", {
        "image": media(props["image"]["url"], props["image"]["alt"]),
        "image_size": "full", "width": slider(100, "%"),
        "height": slider(props.get("image_height", 380)),
        "height_mobile": slider(240),
        "object-fit": "cover", "object-position": "center center",
        "image_border_radius": box(6),
    })], w_img) if props.get("image") else None

    left = _col([_faq(props["items"], props.get("first_open", False))], w_faq)
    row = _row([left, photo] if photo else [left], gap_px=48, align="flex-start")
    return _gw_section([_gw_head(props), row], bg=props.get("bg", "white"))


@block("consult.aside")
def consult_aside(props):
    """Long-form reassurance copy beside a navy enquiry card.

    The shape a "book a first meeting" page wants: the reader works down an
    argument on the left while the form stays in view on the right.

    Child order is [form, content] with `row-reverse`, not [content, form]
    with a plain row. Both render content-left / form-right on desktop, but
    only this order puts the form FIRST when the row stacks on mobile —
    otherwise the one thing the page exists for sits below a screen and a half
    of prose.
    """
    w_body, w_form = _tracks([60, 34], 48)
    animate = props.get("animate", True)
    step = props.get("stagger", 90)

    def anim(name, n=0):
        if not animate:
            return {}
        return {"animation": name, "animation_delay": step * min(n, 6)}

    def ticks(items):
        return widget("icon-list", {
            "icon_list": [repeater_item(text=t, selected_icon=icon("fas fa-check"),
                                        link=link("")) for t in items],
            "space_between": slider(13),
            "icon_size": slider(13),
        }, globals_={"icon_color": color_ref("accent"),
                     "text_color": color_ref("text"),
                     "icon_typography_typography": typo_ref(T["body_small"])})

    # ── left: the argument ────────────────────────────────────────────────
    left = []
    n = 0
    if props.get("intro"):
        left.append(container([_text(p) for p in props["intro"]], {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(12), "padding": dims(0, 0, 30, 0),
            **anim("fadeInUp", n),
        }))
        n += 1

    for sec in props.get("sections", []):
        kids = [_heading(sec["heading"], sec.get("tag", "h2"), T["h_medium"],
                         tone="brand")]
        kids += [_text(p) for p in sec.get("paras", [])]
        if sec.get("ticks"):
            kids.append(ticks(sec["ticks"]))
        # Term-over-definition pairs — the "Clarity / Direction / Confidence"
        # shape. A real h3 rather than a bolded paragraph, so the outline holds.
        for d in sec.get("defs", []):
            kids.append(container([
                _heading(d["term"], "h3", T["h_small"]),
                _text(d["text"], small=True),
            ], {"content_width": "full", "flex_direction": "column",
                "flex_gap": gap(3),
                "border_border": "solid", "border_width": dims(0, 0, 0, 2),
                "padding": dims(2, 0, 2, 16)},
                globals_={"border_color": color_ref("accent")}))
        if sec.get("closing"):
            kids.append(_text(f"<p><strong>{sec['closing']}</strong></p>"))
        left.append(container(kids, {
            "content_width": "full", "flex_direction": "column",
            "flex_gap": gap(14), "padding": dims(0, 0, 34, 0),
            **anim("fadeInUp", n),
        }))
        n += 1

    body_col = _col(left, w_body, extra={"flex_gap": gap(0)})

    # ── right: the card ───────────────────────────────────────────────────
    f = props["form"]
    fields = []
    for fd in f["fields"]:
        item = {
            "custom_id": fd["id"],
            "field_type": fd.get("type", "text"),
            "field_label": fd["label"],
            "placeholder": fd.get("placeholder", ""),
            "required": "true" if fd.get("required") else "",
            "width": str(fd.get("width", 100)),
        }
        if fd.get("rows"):
            item["rows"] = fd["rows"]
        if fd.get("options"):
            item["field_options"] = chr(10).join(fd["options"])
        fields.append(repeater_item(**item))

    form = widget("form", {
        "form_name": f.get("form_name", "Assessment Request"),
        "submit_actions": ["email"],
        "form_fields": fields,
        "button_text": f.get("submit", "Schedule Your Assessment"),
        "button_size": "md",
        "button_width": "100",
        "input_size": "md",
        "show_labels": "",
        "mark_required": "yes",
        "row_gap": slider(13),
        "column_gap": slider(13),
        "success_message": f.get("success", ""),
        "email_to": f.get("email", ""),
        "email_subject": f.get("subject", "New assessment request"),
    }, globals_={
        "button_background_color": color_ref(C["accent_fill"]),
        "button_text_color": color_ref(C["on_accent"]),
        "field_background_color": color_ref(C["white"]),
        "field_text_color": color_ref("secondary"),
        "label_color": color_ref(C["white"]),
    })

    card_kids = [
        *([_gw_eyebrow(f["eyebrow"], "left")] if f.get("eyebrow") else []),
        _heading(f["heading"], f.get("tag", "h2"), T["h_small"], on_dark=True),
        *([_text(f["intro"], on_dark=True, small=True)] if f.get("intro") else []),
        form,
        *([_text(f["footnote"], on_dark=True, small=True)]
          if f.get("footnote") else []),
    ]
    card = container(card_kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(14),
        "padding": dims(30, 30, 32, 30),
        "padding_mobile": dims(24, 20, 26, 20),
        "border_radius": box(3),
        "background_background": "classic",
        **CARD_SHADOW,
    }, globals_={"background_color": color_ref("secondary")})

    form_col = container([card], {
        "content_width": "full", "flex_direction": "column",
        "width": slider(w_form, "%"), "width_mobile": slider(100, "%"),
        **anim("fadeInRight"),
    })

    return _gw_section([_row([form_col, body_col], gap_px=48, align="flex-start",
                             extra={"flex_direction": "row-reverse",
                                    "flex_direction_mobile": "column"})],
                       bg=props.get("bg", "white"))


@block("footer.greyson")
def footer_greyson(props):
    """Navy footer: brand block and map on top, links, then the disclosure.

    The compliance line is the reason this is not `footer.simple`. The SOW
    requires the LPL sentence to appear exactly once per page, in the footer,
    so it lives here and nowhere else — one factory, one occurrence.
    """
    logo_w = (widget("image", {"image": media(props["logo"], props.get("business", "")),
                               "width": slider(190), "align": "left"})
              if props.get("logo") else
              widget("theme-site-logo", {"align": "left", "width": slider(190)}))

    w_brand, w_map = _tracks([58, 42], 48)
    brand = _col([logo_w, _text(props.get("blurb", ""), on_dark=True, small=True)],
                 w_brand, extra={"flex_gap": gap(16)})
    mapc = _col([container([widget("google_maps", {
        "address": props["map_query"], "zoom": slider(props.get("map_zoom", 10)),
        "height": slider(170),
    })], {"content_width": "full", "flex_direction": "column",
          "border_radius": box(4), "overflow": "hidden"})], w_map) \
        if props.get("map_query") else None

    top = _row([brand, mapc] if mapc else [brand], gap_px=48, align="flex-start")

    links = _col([
        widget("heading", {"title": props.get("links_title", "EXPLORE"),
                           "header_size": "div", "align": "left"},
               globals_={"title_color": color_ref("accent"),
                         "typography_typography": typo_ref(T["eyebrow"])}),
        widget("icon-list", {
            "icon_list": [repeater_item(text=i["text"], link=link(i.get("href", "")),
                                        selected_icon={"value": "", "library": ""})
                          for i in props.get("links", [])],
            "view": "inline", "space_between": slider(26),
        }, globals_={"text_color": color_ref(C["on_dark"]),
                     "icon_typography_typography": typo_ref(T["body_small"])}),
    ], extra={"flex_gap": gap(12), "margin": dims(34, 0, 0, 0)})

    disclosure = widget("text-editor", {
        "editor": f"<p>{props['disclosure']}</p>", "align": "left",
    }, globals_={"text_color": color_ref(C["muted"]),
                 "typography_typography": typo_ref(T["meta"])})

    return container([
        top, links,
        widget("divider", {"weight": slider(1), "gap": slider(26), "look": "line"},
               globals_={"color": color_ref(C["rule_dark"])}),
        disclosure,
    ], {
        "content_width": "boxed", "flex_direction": "column",
        "padding": dims(64, 0, 40, 0), "padding_mobile": dims(48, 20, 32, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})


# ═════════════════════ heritage day tours — tour pages ═════════════════════
#
# The single-tour template and the tours index, built as WooCommerce Theme
# Builder documents rather than as hand-built pages. That is the whole point:
# the client asked to add tours, dates, prices, photographs and pick-up points
# themselves without a developer, and a `product` document renders every tour
# from one template. The ten hand-written cards on the existing `tours` page
# are a shop window; these are the shop.
#
# Two dependencies beyond Pro, both hard:
#
#   WooCommerce      registers the `product` and `product-archive` document
#                    types. Without it these two documents do not import.
#   Heritage Tours   the client's own plugin, which owns departures, seat
#                    counts, pick-up points and the mandatory independent-
#                    travel declaration. Its four widgets and four dynamic
#                    tags are declared in registry/plugin-widgets.json.
#
# The Heritage Tours widgets are third-party by the letter of contract §1.3,
# and allowed here for the same reason Happy Addons is: the ban exists to stop
# a kit depending on a plugin the client does not have and cannot install, so
# it is lifted exactly when the manifest declares the plugin and the client
# owns it. Both hold. What is NOT negotiable is that the booking logic stays
# in the plugin — no factory here re-implements a seat count or a price.

# The reference layout the client supplied runs a sticky booking rail beside a
# long content column. 64/36 is the split that leaves the rail wide enough for
# a date picker and two-up passenger fields without the prose column dropping
# under ~60 characters per line.
HDT_TOUR_SPLIT = (64, 36)
HDT_RAIL_GAP = 36
HDT_PANEL_PAD = dims(30, 32, 32, 32)
HDT_PANEL_PAD_M = dims(24, 20, 26, 20)

# Usable width inside a panel: the left column, less the panel's own side
# padding. Every grid *inside* a panel has to be solved against this and not
# against KIT_CONTAINER — a three-up computed against the full 1240 comes out
# at 31.9% each, which needs 102.8% of the real 730px track once the gaps are
# counted, and silently drops the third tile onto its own line. V11 cannot
# catch it, because the validator only knows the kit's container width.
# The main column is not 64% of the page: `_tracks` reserves the rail gap
# first and splits what is left, so it is 62.14%. Measuring the panel against
# the raw ratio overstates it by 23px, and the three spec tiles inside it —
# sized against that overstatement — no longer fit on their line.
HDT_PANEL_INNER = round(
    KIT_CONTAINER * _tracks(list(HDT_TOUR_SPLIT), HDT_RAIL_GAP)[0] / 100) - 64
# At tablet the rail drops below the main column, so the panel is the full
# content width — still less its own 64px of padding.
HDT_PANEL_INNER_T = TABLET_CONTAINER - 64


def _hdt_rule(width=52, align="left"):
    """Short gold rule under a panel heading — the brand's recurring device."""
    return widget("divider", {
        "weight": slider(3), "gap": slider(14), "look": "line",
        "width": slider(width), "align": align,
    }, globals_={"color": color_ref("accent")})


def _hdt_panel(title, children, anchor=None, bg="white", pad=None):
    """One card in the tour page's left column.

    Every content section on the page is one of these, so the rhythm is set
    once: heading, gold rule, content, hairline border, generous padding.
    `anchor` is what the sticky sub-nav scrolls to.
    """
    s = {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(16),
        "padding": pad or HDT_PANEL_PAD,
        "padding_mobile": HDT_PANEL_PAD_M,
        "border_radius": box(8),
        "border_border": "solid",
        "border_width": box(1),
        "background_background": "classic",
        # Scroll target for the sub-nav. `scroll-margin-top` keeps the heading
        # clear of the sticky bar that did the scrolling — without it the bar
        # covers the very heading the visitor just clicked.
        "custom_css": css("selector { scroll-margin-top: 96px; }"),
        **CARD_SHADOW_SOFT,
    }
    if anchor:
        s["_element_id"] = anchor
    head = []
    if title:
        head = [_heading(title, "h2", T["h_medium"]), _hdt_rule()]
    return container(head + list(children), s, globals_={
        "background_color": color_ref(C["white"] if bg == "white" else C["surface"]),
        "border_color": color_ref(C["border"]),
    })


def _hdt_spec(item):
    """One tile in the At a glance grid.

    `field` binds the value to a Heritage Tours meta field through the dynamic
    tag, so the tile reads from the tour the visitor is on. `value` is the
    literal fallback for facts that are the same on every tour — 'Executive
    coach', 'Light refreshments' — which do not belong in per-tour meta.
    """
    val = widget("heading", {
        "title": item.get("value", ""), "header_size": "div", "align": "left",
    }, globals_={
        "title_color": color_ref("secondary"),
        "typography_typography": typo_ref(T["h_small"]),
    })
    if item.get("field"):
        val["settings"]["__dynamic__"] = {
            "title": dynamic("hdt-tour-field", field=item["field"])}
    return _row([
        widget("icon", {
            "selected_icon": icon(item.get("icon", "fas fa-circle-check")),
            "size": slider(19), "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref("accent")}),
        _col([
            widget("heading", {
                "title": item["label"], "header_size": "div", "align": "left",
            }, globals_={
                "title_color": color_ref(C["muted"]),
                "typography_typography": typo_ref(T["eyebrow"]),
            }),
            val,
        ], extra={"flex_gap": gap(3)}),
    ], gap_px=13, align="flex-start",
        extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})


@block("tour.hero")
def tour_hero(props):
    """Full-bleed cover for one tour, with the title bound to the product.

    Every text value is a dynamic binding rather than copy — this document is
    a shell WordPress fills once per tour. The photograph is the product's own
    featured image, so the client changes it by changing the tour, which is
    exactly the "without a developer" requirement.

    A bottom scrim rather than the flat overlay `hero.banner` uses: the title
    sits low over the photograph and a flat wash would dim the landscape the
    tour is selling. The scrim clears off the top two-thirds of the frame.
    """
    crumb = widget("woocommerce-breadcrumb", {
        "alignment": "left",
    }, globals_={
        "text_color": color_ref(C["on_dark"]),
        "link_color": color_ref("accent"),
        "text_typography_typography": typo_ref(T["meta"]),
    })

    title = widget("woocommerce-product-title", {
        "header_size": "h1", "align": "left", "link": "",
    }, globals_={
        "title_color": color_ref(C["white"]),
        "typography_typography": typo_ref(T["hero"]),
    })

    # The three facts that decide whether an over-60s visitor reads on: when
    # it goes, how long it takes, and whether there is still a seat. All three
    # come from the plugin, so they cannot drift from the booking form below.
    facts = _row([
        _hdt_meta_tag(props.get("next_label", "Next departure"),
                      "far fa-calendar", "hdt-next-departure"),
        _hdt_meta_tag(props.get("duration_label", "Duration"),
                      "far fa-clock", "hdt-tour-field", field="duration"),
        _hdt_meta_tag(props.get("seats_label", "Availability"),
                      "far fa-user", "hdt-seats-remaining"),
    ], gap_px=34, align="center", extra={"flex_wrap": "wrap"})

    inner = _col([crumb, title, facts], extra={
        "flex_gap": gap(18), "content_width": "boxed", "boxed_width": slider(900),
    })

    sec = container([inner], {
        "content_width": "boxed",
        "flex_direction": "column",
        "flex_justify_content": "flex-end",
        "min_height": slider(props.get("height", 540)),
        "min_height_tablet": slider(430),
        "min_height_mobile": slider(380),
        "padding": dims(120, 0, 56, 0),
        "padding_tablet": dims(96, 24, 44, 24),
        "padding_mobile": dims(80, 20, 36, 20),
        "background_background": "classic",
        "background_size": "cover",
        "background_position": "center center",
    }, globals_={"background_color": color_ref("secondary")}, dynamic_={
        "background_image": dynamic("post-featured-image"),
    })
    return _scrim(sec, "bottom", 0.88)


def _hdt_meta_tag(label, icon_cls, tag_name, **tag_settings):
    """Icon + small label + dynamically bound value, for the hero fact row.

    The sibling of `_hdt_meta`, which takes a literal string. This one binds
    to a Heritage Tours dynamic tag instead, because on a product document
    there is no literal to write — the value differs per tour.
    """
    value = widget("heading", {
        "title": label, "header_size": "div", "align": "left",
    }, globals_={
        "title_color": color_ref(C["white"]),
        "typography_typography": typo_ref(T["h_small"]),
    }, dynamic_={"title": dynamic(tag_name, **tag_settings)})
    return _row([
        widget("icon", {
            "selected_icon": icon(icon_cls), "size": slider(17),
            "align": "center", "view": "default",
        }, globals_={"primary_color": color_ref("accent")}),
        _col([
            widget("heading", {
                "title": label, "header_size": "div", "align": "left",
            }, globals_={
                "title_color": color_ref(C["on_dark"]),
                "typography_typography": typo_ref(T["eyebrow"]),
            }),
            value,
        ], extra={"flex_gap": gap(2)}),
    ], gap_px=11, align="center",
        extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})


@block("tour.subnav")
def tour_subnav(props):
    """Sticky in-page nav across the tour page's sections.

    The reference site runs one and it earns its place here for a different
    reason: this page is long by necessity — itinerary, inclusions, pick-up
    points and the important-information panel are all things the client is
    contractually better off showing than hiding — and a visitor who has to
    scroll past four panels to reach the price is a visitor who leaves.

    `position: sticky` rather than Elementor's sticky effect, which is Pro's
    JS implementation and switches the element to `position: fixed`. Fixed
    lifts the bar out of the flow, so the content behind it jumps by the bar's
    height the moment it engages.
    """
    items = props["items"]
    nav = widget("icon-list", {
        "icon_list": [repeater_item(
            text=it["label"], link=link(f"#{it['anchor']}"),
            selected_icon=icon("")) for it in items],
        "view": "inline",
        "space_between": slider(0),
        "icon_size": slider(0),
    }, globals_={
        "text_color": color_ref("secondary"),
        "icon_typography_typography": typo_ref(T["eyebrow"]),
    })
    return container([nav], {
        "content_width": "boxed",
        "flex_direction": "row",
        "flex_justify_content": "center",
        "padding": dims(15, 0, 15, 0),
        "padding_mobile": dims(12, 16, 12, 16),
        "border_width": dims(0, 0, 1, 0),
        "border_border": "solid",
        "background_background": "classic",
        "custom_css": css(
            "selector { position: sticky; top: 0; z-index: 20; }",
            # The rail scrolls horizontally on a phone rather than wrapping to
            # three lines and eating the viewport.
            "selector .elementor-inline-items { flex-wrap: nowrap; overflow-x: auto; "
            "scrollbar-width: none; }",
            "selector .elementor-inline-items::-webkit-scrollbar { display: none; }",
            "selector .elementor-icon-list-item a:hover { color: inherit; }",
        ),
    }, globals_={
        "background_color": color_ref(C["white"]),
        "border_color": color_ref(C["border"]),
    })


def _hdt_booking_rail(props):
    """The sticky booking card: price, reassurance, then the plugin's form.

    Deliberately thin. Everything that decides whether a booking is legal —
    the mandatory independent-travel declaration, the pick-up dropdown that
    cannot be typed into, the seat count that stops an overbooking — is the
    plugin's, and rendering `hdt_booking_form` is what pulls all of it in. A
    factory that rebuilt any of that in Elementor controls would be a second
    implementation to keep in step with the first.
    """
    price = _col([
        widget("heading", {
            "title": props.get("price_label", "From"), "header_size": "div",
            "align": "left",
        }, globals_={
            "title_color": color_ref(C["on_dark"]),
            "typography_typography": typo_ref(T["eyebrow"]),
        }),
        _row([
            widget("heading", {
                "title": "£0.00", "header_size": "div", "align": "left",
            }, globals_={
                "title_color": color_ref("accent"),
                "typography_typography": typo_ref(T["h_large"]),
            }, dynamic_={"title": dynamic("hdt-lowest-price")}),
            widget("heading", {
                "title": props.get("per_label", "per person"),
                "header_size": "div", "align": "left",
            }, globals_={
                "title_color": color_ref(C["on_dark"]),
                "typography_typography": typo_ref(T["meta"]),
            }),
        ], gap_px=9, align="baseline",
            extra={"flex_wrap": "wrap", "flex_direction_mobile": "row"}),
    ], extra={"flex_gap": gap(4)})

    head = container([price], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(24, 26, 24, 26),
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})

    body_kids = [
        widget("hdt_booking_form", {
            "date_style": props.get("date_style", "cards"),
        }),
    ]
    if props.get("reassurance"):
        body_kids += [
            widget("divider", {"weight": slider(1), "gap": slider(6),
                               "look": "line"},
                   globals_={"color": color_ref(C["border"])}),
            widget("icon-list", {
                "icon_list": [repeater_item(
                    text=t, selected_icon=icon("fas fa-circle-check"),
                    link=link("")) for t in props["reassurance"]],
                "space_between": slider(11),
                "icon_size": slider(14),
            }, globals_={
                "icon_color": color_ref("accent"),
                "text_color": color_ref("text"),
                "icon_typography_typography": typo_ref(T["body_small"]),
            }),
        ]

    # Only renders once every date is gone, which is the plugin's own default —
    # so the card degrades from "book this" to "tell us when it runs again"
    # without the client touching the template.
    body_kids.append(widget("hdt_waitlist", {"only_when_full": "yes"}))

    if props.get("help"):
        body_kids += [
            widget("divider", {"weight": slider(1), "gap": slider(6),
                               "look": "line"},
                   globals_={"color": color_ref(C["border"])}),
            _heading(props["help"]["heading"], "h3", T["h_small"]),
            _text(props["help"]["text"], small=True),
            widget("icon-list", {
                "icon_list": [repeater_item(
                    text=d["text"], selected_icon=icon(d["icon"]),
                    link=link(d.get("href", ""))) for d in props["help"]["details"]],
                "space_between": slider(9),
                "icon_size": slider(14),
            }, globals_={
                "icon_color": color_ref(C["ink_primary"]),
                "text_color": color_ref("secondary"),
                "icon_typography_typography": typo_ref(T["body_small"]),
            }),
        ]

    body = container(body_kids, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(16),
        "padding": dims(24, 26, 28, 26),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["white"])})

    card = container([head, body], {
        "content_width": "full",
        "flex_direction": "column",
        "flex_gap": gap(0),
        "border_radius": box(10),
        "border_border": "solid",
        "border_width": box(1),
        "overflow": "hidden",
        # Sticks to the top of the viewport for as long as the content column
        # beside it is still scrolling, then travels with the page. 88px clears
        # the sticky sub-nav; the max-height + scroll is what stops a long form
        # from being cut off on a laptop-height viewport.
        "custom_css": css(
            "selector { position: sticky; top: 88px; max-height: calc(100vh - 108px); "
            "overflow-y: auto; scrollbar-width: thin; }",
            "@media (max-width: 1024px) { selector { position: static; "
            "max-height: none; overflow-y: visible; } }",
        ),
        **CARD_SHADOW,
    }, globals_={"border_color": color_ref(C["border"])})
    return card


@block("tour.body")
def tour_body(props):
    """The tour page proper: content column plus the sticky booking rail.

    One block rather than six stacked ones because the rail has to stick
    alongside *all* of the content — a rail inside its own section can only
    stick past that section, which is the usual way this layout is got wrong.
    So the panels are children of the left column, not sections of the page.

    Panels are declared in the IR, in order, and each one names its own
    anchor, so the sub-nav and the page cannot fall out of step.
    """
    w_main, w_rail = _tracks(list(HDT_TOUR_SPLIT), HDT_RAIL_GAP)
    panels = []

    for p in props["panels"]:
        kind = p["kind"]

        if kind == "overview":
            kids = [widget("woocommerce-product-short-description", {
                "text_align": "left",
            }, globals_={
                "text_color": color_ref("text"),
                "text_typography_typography": typo_ref("text"),
            })]
            if p.get("specs"):
                w = _track(3, 26, HDT_PANEL_INNER)
                w_t = _track(2, 26, HDT_PANEL_INNER_T)
                tiles = [_col([_hdt_spec(s)], w, extra={
                    "width_tablet": slider(w_t, "%")}) for s in p["specs"]]
                kids += [
                    container([], {"content_width": "full",
                                   "flex_direction": "column",
                                   "border_width": dims(1, 0, 0, 0),
                                   "border_border": "solid",
                                   "margin": dims(6, 0, 2, 0)},
                              globals_={"border_color": color_ref(C["border"])}),
                    _row(tiles, gap_px=26, align="flex-start"),
                ]

        elif kind == "content":
            # Straight passthrough of one Heritage Tours meta field. The
            # heading is the panel's, not the widget's, so the page keeps one
            # heading treatment rather than two competing ones.
            kids = [widget("hdt_tour_content", {"field": p["field"]})]

        elif kind == "included":
            # Included and excluded side by side. The client's brief calls out
            # "what's included" as its own requirement, and the exclusions are
            # what stop a refund argument on the day.
            w_half = _track(2, 26, HDT_PANEL_INNER)
            kids = [_row([
                _col([
                    _heading(p.get("included_label", "What's included"),
                             "h3", T["h_small"]),
                    widget("hdt_tour_content", {"field": "included"}),
                ], w_half, extra={"flex_gap": gap(10)}),
                _col([
                    _heading(p.get("excluded_label", "Not included"),
                             "h3", T["h_small"]),
                    widget("hdt_tour_content", {"field": "excluded"}),
                ], w_half, extra={"flex_gap": gap(10)}),
            ], gap_px=26, align="flex-start")]

        elif kind == "pickups":
            kids = [
                widget("hdt_tour_content", {"field": "meeting"}),
                widget("hdt_departures", {
                    "low_threshold": p.get("low_threshold", 6),
                    "show_pickups": "yes",
                }),
            ]
            if p.get("note"):
                kids.append(_hdt_note(p["note"]))

        elif kind == "faq":
            kids = [_faq(p["items"], p.get("first_open", True))]

        else:
            raise ValueError(
                f"tour.body: unknown panel kind {kind!r}. Legal: overview, "
                "content, included, pickups, faq.")

        panels.append(_hdt_panel(p.get("title"), kids, anchor=p.get("anchor")))

    main = _col(panels, w_main, extra={"flex_gap": gap(24)})
    rail = _col([_hdt_booking_rail(props["booking"])], w_rail)

    return _section([_row([main, rail], gap_px=HDT_RAIL_GAP, align="stretch")],
                    bg=props.get("bg", "surface"),
                    pad=dims(48, 0, 88, 0))


def _hdt_note(note):
    """Tinted caution panel — cancellation terms, walking level, a warning.

    Reads as advice rather than as body copy, which is the point: the things
    the client most needs a customer to have seen are the things a customer
    skims past when they are set in the same 15px grey as everything else.
    """
    return container([
        _row([
            widget("icon", {
                "selected_icon": icon(note.get("icon", "fas fa-circle-info")),
                "size": slider(17), "align": "center", "view": "default",
            }, globals_={"primary_color": color_ref(C["ink_primary"])}),
            _col([
                *([_heading(note["title"], "h4", T["h_small"])]
                  if note.get("title") else []),
                _text(note["text"], small=True),
            ], extra={"flex_gap": gap(4), "width": slider(93, "%")}),
        ], gap_px=12, align="flex-start",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
    ], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(18, 20, 18, 20),
        "border_radius": box(6),
        "border_width": dims(0, 0, 0, 3),
        "border_border": "solid",
        "background_background": "classic",
    }, globals_={
        "background_color": color_ref(C["surface_alt"]),
        "border_color": color_ref("accent"),
    })


@block("tour.related")
def tour_related(props):
    """You may also like — WooCommerce's own related-products query.

    Not `tours.cards`: that takes a hand-written list, and a hand-written list
    on a template rendered for every tour would show the same four tours on
    all of them, including on their own page.
    """
    grid = widget("woocommerce-product-related", {
        "columns": str(props.get("columns", 4)),
        "orderby": props.get("orderby", "rand"),
        "order": "asc",
        "column_gap": slider(24),
        "row_gap": slider(32),
    }, globals_={
        "title_color": color_ref("secondary"),
        "price_color": color_ref(C["ink_primary"]),
        "heading_color": color_ref("secondary"),
    })
    return _section([_section_head(props), grid], bg=props.get("bg", "white"))


@block("tour.archive")
def tour_archive(props):
    """The tours index, driven by the product archive rather than by hand.

    This is the template that replaces the ten hand-written cards: the client
    adds a tour in WordPress and it appears here, in the shop, with its own
    price and availability, without anyone opening Elementor.
    """
    banner = _scrim(container([
        _col([
            widget("theme-archive-title", {"align": "center"}, globals_={
                "title_color": color_ref(C["white"]),
                "typography_typography": typo_ref(T["h_large"]),
            }),
            *([_text(props["intro"], align="center", on_dark=True)]
              if props.get("intro") else []),
        ], extra={"flex_align_items": "center", "content_width": "boxed", "boxed_width": slider(760),
                  "margin": dims(0, "auto", 0, "auto")}),
    ], {
        "content_width": "boxed",
        "flex_direction": "column",
        "flex_justify_content": "center",
        "min_height": slider(props.get("height", 340)),
        "min_height_mobile": slider(240),
        "padding": dims(72, 0, 72, 0),
        "padding_mobile": dims(56, 20, 56, 20),
        "background_background": "classic",
        "background_size": "cover",
        "background_position": "center center",
        **({"background_image": media(props["image"]["url"], props["image"]["alt"])}
           if props.get("image", {}).get("url") else {}),
    }, globals_={"background_color": color_ref("secondary")}), "bottom", 0.72)

    grid = widget("woocommerce-archive-products", {
        "columns": str(props.get("columns", 3)),
        "rows": props.get("rows", 4),
        # Both off by default. A sort dropdown and a "showing 1–12 of 30" line
        # are shop furniture; on a ten-tour index they add two controls the
        # audience has to parse before reaching the first photograph.
        "allow_order": "yes" if props.get("allow_order") else "",
        "show_result_count": "yes" if props.get("show_count") else "",
        "nothing_found_message": props.get(
            "empty_message",
            "New dates are being confirmed. Please call us and we will let you "
            "know what is coming up."),
        "column_gap": slider(24),
        "row_gap": slider(34),
    }, globals_={
        "title_color": color_ref("secondary"),
        "price_color": color_ref(C["ink_primary"]),
        "nothing_found_color": color_ref("text"),
    })

    out = [banner, _section([grid], bg=props.get("bg", "surface"))]
    if props.get("cta"):
        out.append(render("cta.band", {
            "heading": props["cta"]["heading"],
            "text": props["cta"].get("text", ""),
            "cta": props["cta"]["cta"],
            "bg": "primary",
        }))
    return container(out, {"content_width": "full", "flex_direction": "column",
                           "flex_gap": gap(0)})


def render(block_name: str, props: dict) -> dict:
    if block_name not in BLOCKS:
        raise KeyError(
            f"Unknown block '{block_name}'. Available: {sorted(BLOCKS)}. "
            "Add a factory in blocks.py — never emit raw JSON from an agent."
        )
    return BLOCKS[block_name](props)


# ── store family ──────────────────────────────────────────────────────
#
# Imported at the bottom, after every helper and `render` above exists:
# these modules import from this one, so an import at the top would be
# circular. Importing them here is what registers their @block factories,
# so `render()` can find them.
from . import blocks_store        # noqa: E402,F401
from . import blocks_store_home   # noqa: E402,F401
from . import blocks_store_shop   # noqa: E402,F401
from . import blocks_store_pages  # noqa: E402,F401
from . import blocks_store_content # noqa: E402,F401
from . import blocks_statement    # noqa: E402,F401
from . import blocks_ameri       # noqa: E402,F401
from . import blocks_fatima     # noqa: E402,F401
from . import blocks_millbranch  # noqa: E402,F401
from . import blocks_dualcore  # noqa: E402,F401
from . import blocks_wasatch   # noqa: E402,F401
from . import blocks_magic     # noqa: E402,F401
from . import blocks_metroline # noqa: E402,F401
from . import blocks_plaunch # noqa: E402,F401
from . import blocks_elite # noqa: E402,F401
from . import blocks_genelee # noqa: E402,F401
from . import blocks_edit # noqa: E402,F401
from . import blocks_prorevive  # noqa: E402,F401
from . import blocks_desgroup  # noqa: E402,F401
from . import blocks_onsight  # noqa: E402,F401
from . import blocks_gk  # noqa: E402,F401
from . import blocks_truair  # noqa: E402,F401
from . import blocks_fatima_library  # noqa: E402,F401
from . import blocks_lightning  # noqa: E402,F401
from . import blocks_ww  # noqa: E402,F401
from . import blocks_ee  # noqa: E402,F401
from . import blocks_ll  # noqa: E402,F401
from . import blocks_bbl  # noqa: E402,F401
from . import blocks_wemockup  # noqa: E402,F401
from . import blocks_econ  # noqa: E402,F401
from . import blocks_ie  # noqa: E402,F401
from . import blocks_md  # noqa: E402,F401
from . import blocks_stt  # noqa: E402,F401
from . import blocks_prolific  # noqa: E402,F401
from . import blocks_vybe  # noqa: E402,F401
from . import blocks_mot  # noqa: E402,F401
from . import blocks_easy  # noqa: E402,F401
from . import blocks_lakes  # noqa: E402,F401
from . import blocks_mow  # noqa: E402,F401
