"""
tokens.py — design tokens -> Elementor Global Kit (global.json).

This is the ONLY place colours and typography are defined. Every block
factory references these by token id through __globals__, never by hex.
Swap this file's output and the whole site re-skins.

Token ids: system ids are the four fixed strings Elementor reserves.
Custom ids are stable 7-char slugs so regenerating a site doesn't
invalidate previously exported templates.
"""
from __future__ import annotations

from .core import slider, dims, box, color_ref, typo_ref

# Stable custom token ids — DO NOT renumber, templates reference these.
C = {
    "white":       "fff0001",
    "surface":     "surf002",
    "surface_alt": "surf003",
    "border":      "bord004",
    "muted":       "mute005",
    "overlay":     "ovly006",
    "transparent": "tran007",
    "on_dark":     "ondk008",
    # Contrast-derived. Computed from the brand colours rather than picked,
    # so a light brand colour can't ship unreadable text.
    "on_accent":   "onac009",
    "on_primary":  "onpr010",
    "ink_primary": "inkp011",
    # A dark-on-dark rule is invisible; dividers inside dark panels use this.
    "rule_dark":   "rule012",
    # The brand colour, lightened enough to read on a dark section.
    "brand_on_dark": "bod0013",
    # The accent, adjusted if needed so a label can sit on it.
    "accent_fill":  "acfl014",
    # ink_primary is derived against surface_alt, which is correct for a light
    # theme and wrong for a dark one — there surface_alt is itself dark, so the
    # brand colour is never darkened and fails on any white section. This is
    # always derived against white, so it is safe in both themes.
    "ink_on_white": "inkw015",
}
T = {
    "hero":        "typo101",
    "h_large":     "typo102",
    "h_medium":    "typo103",
    "h_small":     "typo104",
    "eyebrow":     "typo105",
    "body_small":  "typo106",
    "meta":        "typo107",
    # Wide-tracked uppercase display. A centred, heavily letterspaced caps
    # headline is a different typographic system from a serif display size —
    # it needs large POSITIVE tracking, where a mixed-case display wants
    # negative. Additive ids, so existing kits are unaffected.
    "caps_hero":   "typo108",
    "caps_sub":    "typo109",
    "wordmark":    "typo110",
}

DEFAULTS = {
    "primary":   "#1B4DFF",
    "secondary": "#0B1220",
    "text":      "#3C414C",
    "accent":    "#FF6B35",
    # Neutrals. Overridable per brand — the stock set is cool/blue-tinted and
    # reads wrong under a warm or achromatic palette.
    "surface":     "#F7F9FC",
    "surface_alt": "#EEF3FB",
    "border":      "#DDE3EC",
    "muted":       "#6B7280",
    "heading_font": "Inter",
    "body_font": "Inter",
}


def _hex8(hexcolor: str, alpha_pct: int) -> str:
    """Bake opacity into 8-digit hex, the convention both reference kits use."""
    a = max(0, min(255, round(alpha_pct * 255 / 100)))
    return f"{hexcolor}{a:02X}"


# ───────────────────────── contrast-derived colour ─────────────────────────
#
# A brand colour is chosen to look right, not to be readable. Lime on white is
# 2.4:1 — well under the 4.5:1 small text needs — so eyebrows and links in the
# raw brand colour are unreadable, and white button labels on a lime fill are
# worse. These helpers derive the readable variants instead of guessing them.

def _rgb(hexcolor: str) -> tuple[int, int, int]:
    h = hexcolor.lstrip("#")[:6]
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _luminance(hexcolor: str) -> float:
    def chan(c):
        s = c / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in _rgb(hexcolor))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _shade(hexcolor: str, factor: float) -> str:
    r, g, b = _rgb(hexcolor)
    return "#%02X%02X%02X" % tuple(
        max(0, min(255, round(c * factor))) for c in (r, g, b))


def _ink(hexcolor: str, on: str = "#FFFFFF", target: float = 4.5) -> str:
    """Darkest-hue-preserving variant of `hexcolor` readable as small text."""
    f = 1.0
    while f >= 0.2:
        c = _shade(hexcolor, f)
        if contrast(c, on) >= target:
            return c
        f -= 0.04
    return "#1A1A1A"


def _tint(hexcolor: str, factor: float) -> str:
    r, g, b = _rgb(hexcolor)
    return "#%02X%02X%02X" % tuple(
        round(c + (255 - c) * factor) for c in (r, g, b))


def _lift(hexcolor: str, on: str, target: float = 4.5) -> str:
    """Lightest-hue-preserving variant readable on a dark ground.

    A brand colour dark enough to work as text on white is usually too dark
    to sit on a near-black section. Mixing toward white keeps the hue while
    clearing the threshold; a navy brand ends up near-white, which is correct.
    """
    f = 0.0
    while f <= 1.0:
        c = _tint(hexcolor, f)
        if contrast(c, on) >= target:
            return c
        f += 0.04
    return "#FFFFFF"


def _on(fill: str, dark: str, light: str = "#FFFFFF") -> str:
    """Whichever of `dark` / `light` reads better on top of `fill`."""
    return dark if contrast(fill, dark) >= contrast(fill, light) else light


def _fill(colour: str, dark: str, target: float = 4.5) -> str:
    """A version of `colour` a label can actually sit on.

    Mid-tone brands defeat both labels: #2697C3 gives 4.27:1 against near-black
    and 3.24:1 against white, so picking the better of the two still fails.
    When that happens the fill has to move, not the label — darkened until
    white clears, since a mid-tone lightened enough for dark text stops
    reading as the brand colour at all.
    """
    if max(contrast(colour, dark), contrast(colour, "#FFFFFF")) >= target:
        return colour
    f = 1.0
    while f >= 0.2:
        c = _shade(colour, f)
        if contrast(c, "#FFFFFF") >= target:
            return c
        f -= 0.04
    return dark


def build_kit(brand: dict, title: str = "Global Kit Styles") -> dict:
    colors = {**DEFAULTS, **(brand.get("colors") or {})}
    fonts = brand.get("fonts") or {}
    hf = fonts.get("heading", DEFAULTS["heading_font"])
    bf = fonts.get("body", DEFAULTS["body_font"])
    # Small headings default to the display face, which is right for most
    # brands. Some type systems deliberately hand the smallest heading step to
    # the body face instead — a high-contrast display serif stops working
    # around 18px, so the brand switches to the sans rather than shrinking it
    # further. Defaulting to hf keeps every existing kit unchanged.
    shf = fonts.get("small_heading", hf)

    # Type scale. Defaults to 1.0, so every kit built before this existed
    # compiles byte-identical. The reason it exists: the 16px body size below
    # is tuned for a general audience, and a site whose stated customer is
    # over 60 needs to start nearer 18px. That is a property of the brand, not
    # something a block factory can decide, and it must not be fixed by
    # editing the constants — that would silently reflow every other client.
    scale = float(brand.get("type_scale", 1.0))
    if not 0.8 <= scale <= 1.5:
        raise ValueError(
            f"brand.type_scale {scale} is outside 0.8-1.5. Beyond that the "
            "line-height and tracking values here stop holding and the "
            "headings collide.")

    def sz(v):
        """Scaled font size, rounded to the whole pixel Elementor stores."""
        return round(v * scale)

    primary = colors["primary"]
    secondary = colors["secondary"]

    system_colors = [
        {"_id": "primary",   "title": "Primary",   "color": primary},
        {"_id": "secondary", "title": "Secondary", "color": secondary},
        {"_id": "text",      "title": "Text",      "color": colors["text"]},
        {"_id": "accent",    "title": "Accent",    "color": colors["accent"]},
    ]
    # Derived tokens a brand may state outright.
    #
    # The derivations below are correct arithmetic on the primary, but a brand
    # colour is not always derivable from another one. This logo's on-dark
    # colour is the cream from the badge — lifting the navy primary toward
    # white gives a defensible grey-blue that is nonetheless not the brand.
    # Where the client states one of these, it wins; where they do not, the
    # derivation stands, so every existing kit is unchanged.
    #
    # The contrast floor still applies. An override is allowed to be
    # off-formula, not unreadable — that is the whole reason these were
    # derived rather than picked in the first place.
    def derived(name: str, computed: str, on: str, target: float = 4.5) -> str:
        stated = (brand.get("colors") or {}).get(name)
        if not stated:
            return computed
        if contrast(stated, on) < target:
            raise ValueError(
                f"brand.colors.{name} = {stated} gives "
                f"{contrast(stated, on):.2f}:1 against {on}, under the "
                f"{target}:1 small text needs. Pick a lighter or darker "
                f"variant, or drop the override and let it be derived.")
        return stated

    custom_colors = [
        {"_id": C["white"],       "title": "Full White",     "color": "#FFFFFF"},
        {"_id": C["surface"],     "title": "Surface",        "color": colors["surface"]},
        {"_id": C["surface_alt"], "title": "Surface Alt",    "color": colors["surface_alt"]},
        {"_id": C["border"],      "title": "Border",         "color": colors["border"]},
        {"_id": C["muted"],       "title": "Muted Text",     "color": colors["muted"]},
        {"_id": C["overlay"],     "title": "Dark Overlay",   "color": _hex8(secondary, 60)},
        {"_id": C["transparent"], "title": "Transparent",    "color": "#FFFFFF00"},
        {"_id": C["on_dark"],     "title": "Text on Dark",   "color": "#FFFFFFCC"},
        {"_id": C["accent_fill"], "title": "Accent Fill",
         "color": _fill(colors["accent"], secondary)},
        {"_id": C["on_accent"],   "title": "Text on Accent",
         "color": _on(_fill(colors["accent"], secondary), secondary)},
        {"_id": C["on_primary"],  "title": "Text on Primary",
         "color": _on(primary, secondary)},
        # Derived against the *darkest* light surface, so the same ink is safe
        # on white, surface and surface-alt alike.
        {"_id": C["ink_primary"], "title": "Primary Ink",
         "color": derived("ink_primary", _ink(primary, colors["surface_alt"]),
                          colors["surface_alt"])},
        {"_id": C["ink_on_white"], "title": "Brand Ink on White",
         "color": derived("ink_on_white", _ink(primary, "#FFFFFF"), "#FFFFFF")},
        {"_id": C["rule_dark"],   "title": "Rule on Dark", "color": "#FFFFFF29"},
        {"_id": C["brand_on_dark"], "title": "Brand on Dark",
         "color": derived("brand_on_dark", _lift(primary, secondary), secondary)},
    ]

    # Per-brand EXTRA colours, opt-in (added 2026-09-11 for elite-property).
    #
    # Some designs need semantic colours the four-role system cannot express:
    # a green "VERIFICATION PASSED" badge and a red warning mark on a
    # comparison table mean something, and borrowing the accent for them
    # would make the CTA and the status indistinguishable. Each entry states
    # its own stable 7-char id, so templates keep resolving across rebuilds.
    # Absent key = no change, so every existing kit compiles byte-identical.
    for x in brand.get("extra_colors") or []:
        if len(x.get("id", "")) != 7:
            _id = x.get("id", "")
            raise ValueError(
                f"extra_colors id {_id!r} is {len(_id)} chars; Elementor global "
                f"ids are exactly 7. Try {(_id + '000000')[:7]!r}.")
        custom_colors.append({"_id": x["id"], "title": x["title"],
                              "color": x["color"]})

    def typo(_id, title, family, size, weight, lh, mobile=None, tablet=None, extra=None):
        # Every size goes through sz(), including the tablet and mobile steps —
        # scaling only the desktop size would leave a large-type site snapping
        # back to the stock scale on the devices where it matters most.
        t = {
            "_id": _id, "title": title,
            "typography_typography": "custom",
            "typography_font_family": family,
            "typography_font_size": slider(sz(size)),
            "typography_font_weight": str(weight),
            "typography_line_height": slider(lh, "em"),
        }
        if tablet:
            t["typography_font_size_tablet"] = slider(sz(tablet))
        if mobile:
            t["typography_font_size_mobile"] = slider(sz(mobile))
        if extra:
            t.update(extra)
        return t

    # Display sizes carry slight negative tracking — at 40px+ the default
    # spacing reads loose. Body sizes keep neutral tracking.
    # Per-brand heading WEIGHT and section-title CASE (opt-in, 2026-09-11).
    # The stock scale sets display weights at 700-800 and section titles in
    # uppercase, which is right for a geometric sans and wrong for a classical
    # serif: Garamond at 800 reads as a poster, and uppercase Garamond at
    # section size reads as a law firm. Absent keys = unchanged output.
    hw = brand.get("heading_weight")
    title_case = brand.get("section_title_case", "uppercase")

    def w(default):
        return hw or default

    system_typography = [
        typo("primary",   "Heading",    hf, 40, w(700), 1.14, mobile=30,
             extra={"typography_letter_spacing": slider(-0.4)}),
        typo("secondary", "Subheading", hf, 26, 600, 1.25, mobile=22),
        typo("text",      "Body",       bf, 16, 400, 1.7),
        typo("accent",    "Accent",     bf, 14, 600, 1.2,
             extra={"typography_text_transform": "uppercase",
                    "typography_letter_spacing": slider(0.6)}),
    ]
    custom_typography = [
        typo(T["hero"],       "Hero Title",    hf, 62, w(800), 1.04, tablet=46, mobile=36,
             extra={"typography_letter_spacing": slider(-1.2)}),
        # Section titles are uppercase — the reference site's most recognisable
        # trait. Uppercase needs positive tracking, not the negative tracking a
        # mixed-case display size wants.
        typo(T["h_large"],    "Section Title", hf, 36, w(800), 1.16, tablet=31, mobile=27,
             extra={"typography_text_transform": title_case,
                    "typography_letter_spacing": slider(
                        0.4 if title_case == "uppercase" else -0.3)}),
        typo(T["h_medium"],   "Card Title",    hf, 24, w(700), 1.28, mobile=21,
             extra={"typography_letter_spacing": slider(-0.2)}),
        typo(T["h_small"],    "Small Title",   shf, 19, 600, 1.35),
        typo(T["eyebrow"],    "Eyebrow",       bf, 12, 700, 1.2,
             extra={"typography_text_transform": "uppercase",
                    "typography_letter_spacing": slider(1.6)}),
        typo(T["body_small"], "Body Small",    bf, 15, 400, 1.68),
        typo(T["meta"],       "Meta",          bf, 13, 500, 1.5,
             extra={"typography_letter_spacing": slider(0.2)}),
        typo(T["caps_hero"],  "Caps Display",  hf, 52, 500, 1.18, tablet=38, mobile=27,
             extra={"typography_text_transform": "uppercase",
                    "typography_letter_spacing": slider(6)}),
        typo(T["caps_sub"],   "Caps Sub",      bf, 14, 500, 1.6, mobile=12,
             extra={"typography_text_transform": "uppercase",
                    "typography_letter_spacing": slider(5)}),
        typo(T["wordmark"],   "Wordmark",      hf, 62, 300, 1.0, tablet=44, mobile=30,
             extra={"typography_text_transform": "uppercase",
                    "typography_letter_spacing": slider(18)}),
    ]

    page_settings = {
        "system_colors": system_colors,
        "custom_colors": custom_colors,
        "system_typography": system_typography,
        "custom_typography": custom_typography,
        "default_generic_fonts": "Sans-serif",
        "container_width": slider(1240),
        "container_padding": dims(0, 0, 0, 0, linked=True),
        "space_between_widgets": {"unit": "px", "size": 0, "column": "0", "row": "0", "isLinked": True},
        "paragraph_spacing": slider(1.4, "em"),
        "page_title_selector": "h1.entry-title",
        "viewport_md": 768,
        "viewport_lg": 1025,
        "activeItemIndex": 1,

        # Buttons — geometry literal, colour/type via globals
        "button_border_border": "solid",
        "button_border_width": box(1),
        "button_border_radius": box(8),
        "button_padding": dims(16, 32, 16, 32),
        "button_hover_border_border": "solid",
        "button_hover_border_width": box(1),
        "image_border_radius": box(12),

        # Headings — literal sizes so the theme still looks right outside widgets
        **{f"h{i}_typography_typography": "custom" for i in range(1, 7)},
        **{f"h{i}_typography_font_family": hf for i in range(1, 7)},
        "h1_typography_font_size": slider(sz(52)),
        "h2_typography_font_size": slider(sz(40)),
        "h3_typography_font_size": slider(sz(29)),
        "h4_typography_font_size": slider(sz(23)),
        "h5_typography_font_size": slider(sz(19)),
        "h6_typography_font_size": slider(sz(16)),
        **{f"h{i}_typography_font_weight": "700" for i in range(1, 5)},
        **{f"h{i}_typography_font_weight": "600" for i in range(5, 7)},
        "body_typography_typography": "custom",
        "body_typography_font_family": bf,
        "body_typography_font_size": slider(sz(16)),
        "body_typography_line_height": slider(1.65, "em"),
        "body_background_background": "classic",

        "__globals__": {
            **{f"h{i}_color": color_ref("secondary") for i in range(1, 7)},
            "body_color": color_ref("text"),
            # Links are small text on light — the raw brand colour fails 4.5:1.
            "link_normal_color": color_ref(C["ink_primary"]),
            "link_hover_color": color_ref("secondary"),
            "button_text_color": color_ref(C["on_primary"]),
            "button_background_color": color_ref("primary"),
            "button_border_color": color_ref("primary"),
            "button_hover_text_color": color_ref(C["white"]),
            "button_hover_background_color": color_ref("secondary"),
            "button_hover_border_color": color_ref("secondary"),
            "button_typography_typography": typo_ref("accent"),
            "body_background_color": color_ref(C["white"]),
        },
    }

    # Opt-in dark theme (added 2026-10-26 for Lakes Construction). The stock
    # Global Kit is a light theme: a white body, near-black theme headings and
    # a near-black link hover. On a dark site those surface wherever a widget
    # does not set its own colour - the body flashes white on overscroll, raw
    # headings vanish, inline links disappear on hover. Absent the key,
    # output is byte-identical.
    if brand.get("theme") == "dark":
        g = page_settings["__globals__"]
        g["body_background_color"] = color_ref(C["surface"])
        for i in range(1, 7):
            g[f"h{i}_color"] = color_ref(C["white"])
        g["link_normal_color"] = color_ref(C["brand_on_dark"])
        g["link_hover_color"] = color_ref(C["white"])

    return {
        "version": "0.4",
        "title": title,
        "type": "section",
        "metadata": {
            "template_type": "global-styles",
            "include_in_zip": "1",
            "elementor_pro_required": "1",
            "wp_page_template": "default",
            "additional_template_information": [
                "Import this FIRST. Apply via Site Settings before importing pages."
            ],
        },
        "content": [],
        "page_settings": page_settings,
    }


def token_ids(kit: dict) -> tuple[set[str], set[str]]:
    ps = kit["page_settings"]
    colors = {c["_id"] for c in ps["system_colors"]} | {c["_id"] for c in ps["custom_colors"]}
    typo = {t["_id"] for t in ps["system_typography"]} | {t["_id"] for t in ps["custom_typography"]}
    return colors, typo
