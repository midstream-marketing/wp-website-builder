"""
blocks_store_content.py — company pages and the Research Hub blog.

The brief's SEO argument for this site rests entirely on the Research Hub:
compliant educational content is what ranks an RUO peptide store without
making a prohibited claim. That means the blog cannot be a landing page with
nothing behind it — a `single-post` template and an `archive` template are
what make the articles render in the kit's design rather than in whatever the
theme happens to do.

Also here: the founder/pull-quote panel the reference runs, which is the one
piece of the approved design the storefront modules had no home for.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link, icon,
    gap, color_ref, typo_ref, dynamic, css,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _track, _grid_widths, _heading, _text,
    _button, _scrim, CARD_SHADOW, CARD_SHADOW_SOFT,
)
from .blocks_store import (
    _st_section, _st_head, _st_chip, _st_card, _st_icon, _st_rule,
    ST_PAD, ST_PAD_T, ST_PAD_M, R_CARD, R_PANEL, R_PILL,
)


@block("store.quote")
def store_quote(props):
    """Founder message / pull quote in a wide tinted panel.

    The reference runs 'A Message From The Founder' as a full-width pale-blue
    band, and it is the one place on that site where a person speaks rather
    than the brand. Worth keeping: on a store selling verification, a named
    human standing behind it is the point.
    """
    inner = []
    if props.get("eyebrow"):
        inner.append(_st_chip(props["eyebrow"], align="left"))
    if props.get("heading"):
        inner.append(_heading(props["heading"], "h2", T["h_large"],
                              tone="brand"))
    for p in props.get("paras", []):
        inner.append(_text(p))

    if props.get("name"):
        attribution = [_heading(props["name"], "h4", T["h_medium"],
                                tone="brand")]
        if props.get("role"):
            attribution.append(_text(props["role"], small=True))
        inner.append(_col(attribution, extra={"flex_gap": gap(2),
                                              "margin": dims(8, 0, 0, 0)}))

    panel = _st_card(inner, bg=props.get("card_bg", "alt"),
                     pad=dims(44, 46, 44, 46), border=False, radius=R_PANEL,
                     extra={"flex_gap": gap(15),
                            "flex_align_items": "flex-start"})
    return _st_section([panel], bg=props.get("bg", "white"))


@block("store.postarchive")
def store_postarchive(props):
    """The Research Hub archive — one document for the blog index, every
    category, every tag and search results.

    `archive-posts` renders the query WordPress already resolved for the
    archive it is on, which is why there is no posts-per-page control here:
    that count is a WordPress setting, not a widget one.
    """
    crumb = widget("theme-archive-title", {"align": "center"}, globals_={
        "title_color": color_ref(C["white"]),
        "typography_typography": typo_ref(T["h_large"]),
    })
    head = [crumb]
    if props.get("intro"):
        head.append(_text(props["intro"], align="center", on_dark=True))

    banner = container([_col(head, extra={
        "flex_gap": gap(14), "flex_align_items": "center",
        "content_width": "boxed", "boxed_width": slider(780),
        "margin": dims(0, "auto", 0, "auto"),
    })], {
        "content_width": "boxed",
        "flex_direction": "column",
        "flex_justify_content": "center",
        "min_height": slider(props.get("height", 280)),
        "min_height_mobile": slider(220),
        "padding": dims(64, 0, 64, 0),
        "padding_tablet": dims(54, 24, 54, 24),
        "padding_mobile": dims(44, 20, 44, 20),
        "background_background": "classic",
        "background_size": "cover",
        "background_position": "center center",
        **({"background_image": media(props["image"]["url"],
                                      props["image"].get("alt", ""))}
           if props.get("image", {}).get("url") else {}),
    }, globals_={"background_color": color_ref("secondary")})
    if props.get("image", {}).get("url"):
        banner = _scrim(banner, "bottom", 0.78)

    grid = widget("archive-posts", {
        "columns": str(props.get("columns", 3)),
        "thumbnail": "yes",
        "thumbnail_size_size": "medium_large",
        "show_excerpt": "yes",
        "excerpt_length": props.get("excerpt", 22),
        "show_read_more": "yes",
        "read_more_text": props.get("more_label", "Read Article"),
        "meta_data": ["date"],
        "meta_separator": "  •  ",
        "pagination_type": "numbers",
        "column_gap": slider(26),
        "row_gap": slider(34),
        "image_border_radius": box(8),
        "nothing_found_message": props.get(
            "empty_message",
            "No articles here yet. New research guidance is published "
            "regularly — check back soon."),
    }, globals_={
        "title_color": color_ref("secondary"),
        "title_typography_typography": typo_ref(T["h_small"]),
        "excerpt_color": color_ref("text"),
        "excerpt_typography_typography": typo_ref(T["body_small"]),
        "meta_color": color_ref(C["muted"]),
        "meta_typography_typography": typo_ref(T["meta"]),
    })

    return container([banner, _st_section([grid], bg=props.get("bg", "white"))],
                     {"content_width": "full", "flex_direction": "column",
                      "flex_gap": gap(0)})


@block("store.post")
def store_post(props):
    """Single article template.

    Every value is a dynamic binding — this document is a shell WordPress
    fills once per article. A literal headline here would put the same title
    on every post in the Research Hub.

    The RUO notice is not optional furniture on this template. Educational
    content about research compounds is exactly where an implied-use reading
    can creep in, so every article carries the disclaimer under the body.
    """
    title = widget("theme-post-title", {
        "header_size": "h1", "align": "center", "link": "",
    }, globals_={
        "title_color": color_ref(C["white"]),
        "typography_typography": typo_ref(T["h_large"]),
    })
    meta = widget("post-info", {
        "view": "inline",
        "icon_align": "left",
        "show_icon": "yes",
        "icon_size": slider(13),
        "space_between": slider(20),
    }, globals_={
        "text_color": color_ref(C["on_dark"]),
        "icon_color": color_ref(C["brand_on_dark"]),
        "icon_typography_typography": typo_ref(T["meta"]),
    })

    hero = container([_col([title, meta], extra={
        "flex_gap": gap(16), "flex_align_items": "center",
        "content_width": "boxed", "boxed_width": slider(860),
        "margin": dims(0, "auto", 0, "auto"),
    })], {
        "content_width": "boxed",
        "flex_direction": "column",
        "flex_justify_content": "center",
        "padding": dims(84, 0, 96, 0),
        "padding_tablet": dims(70, 24, 84, 24),
        "padding_mobile": dims(56, 20, 70, 20),
        "background_background": "classic",
    }, globals_={"background_color": color_ref("secondary")})

    # Pulled up over the dark hero — the reference's move, and it stops the
    # article opening with a flat band of near-black.
    featured = _st_section([
        container([widget("theme-post-featured-image", {
            "image_size": "large", "align": "center",
            "image_border_radius": R_PANEL,
        })], {
            "content_width": "full", "flex_direction": "column",
            "margin": dims(-64, 0, 0, 0),
            "margin_mobile": dims(-44, 0, 0, 0),
        }),
    ], bg="white", pad=dims(0, 0, 32, 0),
        extra={"padding_tablet": dims(0, 24, 28, 24),
               "padding_mobile": dims(0, 20, 24, 20)})

    body_col = [widget("theme-post-content", {}, globals_={
        "text_color": color_ref("text"),
        "typography_typography": typo_ref("text"),
    })]

    if props.get("share", True):
        body_col.append(_st_rule_light())
        body_col.append(widget("share-buttons", {
            "share_buttons": [
                repeater_item(button="x-twitter"),
                repeater_item(button="linkedin"),
                repeater_item(button="facebook"),
                repeater_item(button="email"),
            ],
            "view": "icon", "shape": "circle", "columns": "0",
            "alignment": "left", "button_size": slider(0.9),
        }))

    if props.get("notice"):
        body_col.append(_st_card([_text(props["notice"], small=True)],
                                 bg="surface", pad=dims(16, 20, 16, 20),
                                 extra={"flex_gap": gap(0),
                                        "border_width": dims(1, 1, 1, 3)}))

    body = _st_section([_col(body_col, extra={
        "flex_gap": gap(22),
        "content_width": "boxed", "boxed_width": slider(props.get("measure", 800)),
        "margin": dims(0, "auto", 0, "auto"),
    })], bg="white", pad=dims(8, 0, 56, 0),
        extra={"padding_tablet": dims(8, 24, 48, 24),
               "padding_mobile": dims(8, 20, 40, 20)})

    out = [hero, featured, body]

    if props.get("author", True):
        out.append(_st_section([_col([widget("author-box", {
            "source": "current", "show_avatar": "yes", "show_name": "yes",
            "show_biography": "yes", "avatar_size": slider(72),
            "layout": "left",
        }, globals_={
            "name_color": color_ref("secondary"),
            "bio_color": color_ref("text"),
            "name_typography_typography": typo_ref(T["h_small"]),
            "bio_typography_typography": typo_ref(T["body_small"]),
        })], extra={
            "content_width": "boxed", "boxed_width": slider(800),
            "margin": dims(0, "auto", 0, "auto"),
            "padding": dims(26, 28, 26, 28),
            "border_radius": R_CARD, "border_border": "solid",
            "border_width": box(1), "background_background": "classic",
            "__globals__": {
                "background_color": color_ref(C["surface"]),
                "border_color": color_ref(C["border"])},
        })], bg="white", pad=dims(0, 0, 40, 0),
            extra={"padding_tablet": dims(0, 24, 36, 24),
                   "padding_mobile": dims(0, 20, 32, 20)}))

    if props.get("nav", True):
        out.append(_st_section([_col([widget("post-navigation", {
            "show_label": "yes", "show_title": "yes", "show_borders": "yes",
            "prev_label": props.get("prev_label", "Previous Article"),
            "next_label": props.get("next_label", "Next Article"),
        }, globals_={
            "label_color": color_ref(C["muted"]),
            "hover_color": color_ref(C["ink_primary"]),
            "sep_color": color_ref(C["border"]),
            "label_typography_typography": typo_ref(T["meta"]),
            "title_typography_typography": typo_ref(T["h_small"]),
        })], extra={
            "content_width": "boxed", "boxed_width": slider(800),
            "margin": dims(0, "auto", 0, "auto"),
        })], bg="white", pad=dims(0, 0, 56, 0),
            extra={"padding_tablet": dims(0, 24, 48, 24),
                   "padding_mobile": dims(0, 20, 40, 20)}))

    return container(out, {"content_width": "full", "flex_direction": "column",
                           "flex_gap": gap(0)})


def _st_rule_light():
    return widget("divider", {
        "weight": slider(1), "gap": slider(6), "style": "solid",
    }, globals_={"color": color_ref(C["border"])})
