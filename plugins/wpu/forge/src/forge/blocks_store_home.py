"""
blocks_store_home.py — homepage sections for the RUO storefront.

Every factory here is list-shaped and prop-driven, so the same twelve blocks
compose the About, Quality & Testing, COA-lookup and FAQ pages later without
new Python. That is the extensibility contract: new page = new IR entry.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link, icon,
    gap, color_ref, typo_ref, css,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _track, _grid_widths, _heading, _text,
    _button, _scrim, _hover_lift, CARD_SHADOW, CARD_SHADOW_SOFT,
)
from .blocks_store import (
    _st_section, _st_head, _st_chip, _st_card, _st_icon, _st_iconcard,
    _st_rule, ST_PAD, ST_PAD_T, ST_PAD_M, R_CARD, R_PANEL, R_PILL,
)


@block("store.hero")
def store_hero(props):
    """Dark hero: eyebrow, two-tone headline, subheadline, two CTAs.

    The reference splits its H1 across two lines and colours the second in the
    brand blue. That is done here as one heading with an inline span rather
    than two stacked headings, so the line break is typographic rather than
    structural and the two halves cannot drift apart on a narrow screen.
    """
    head = props["heading"]
    if props.get("heading_accent"):
        head = head + ' <span style="color:var(--e-global-color-' + \
            C["brand_on_dark"] + ')">' + props["heading_accent"] + "</span>"

    inner = [
        _st_chip(props["eyebrow"], align="left", on_dark=True)
        if props.get("eyebrow") else None,
        widget("heading", {
            "title": head, "header_size": "h1", "align": "left",
        }, globals_={
            "title_color": color_ref(C["white"]),
            "typography_typography": typo_ref(T["hero"]),
        }),
        _text(props["text"], on_dark=True) if props.get("text") else None,
    ]
    ctas = [_button(props["cta"]["label"], props["cta"]["href"], "primary")] \
        if props.get("cta") else []
    if props.get("cta2"):
        ctas.append(_button(props["cta2"]["label"], props["cta2"]["href"],
                            "ghost_dark"))
    if ctas:
        inner.append(_row(ctas, 12, align="center",
                          extra={"flex_direction_mobile": "column",
                                 "flex_align_items_mobile": "stretch"}))

    body = _col([i for i in inner if i is not None], extra={
        "flex_gap": gap(20),
        "content_width": "boxed",
        "boxed_width": slider(props.get("measure", 620)),
    })

    sec = container([body], {
        "content_width": "boxed",
        "flex_direction": "column",
        "flex_justify_content": "center",
        "min_height": slider(props.get("height", 560)),
        "min_height_tablet": slider(460),
        "min_height_mobile": slider(420),
        "padding": dims(96, 0, 96, 0),
        "padding_tablet": dims(76, 24, 76, 24),
        "padding_mobile": dims(60, 20, 60, 20),
        "background_background": "classic",
        "background_size": "cover",
        "background_position": "center right",
        **({"background_image": media(props["image"]["url"],
                                      props["image"].get("alt", ""))}
           if props.get("image", {}).get("url") else {}),
    }, globals_={"background_color": color_ref("secondary")})

    # A left wedge rather than a flat wash: the reference runs lab glassware
    # down the right of the frame and a flat overlay would dim the one image
    # on the page that is doing any selling.
    return _scrim(sec, "left", props.get("scrim", 0.90))


@block("store.trustrow")
def store_trustrow(props):
    """Icon + label row floating in a white pill, overlapping the hero.

    The negative top margin lifts it onto the hero's bottom edge, which is the
    reference's move and the reason the row reads as a caption to the hero
    rather than as the first row of the next section.
    """
    items = props["items"]
    w = _track(len(items), 24)
    cells = [_col([
        _row([
            _st_icon(i.get("icon", "fas fa-circle-check"), size=20, boxed=False),
            _col([
                _heading(i["title"], "h4", T["h_small"]),
                *([_text(i["text"], small=True)] if i.get("text") else []),
            ], extra={"flex_gap": gap(2)}),
        ], gap_px=12, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
    ], w, extra={"width_tablet": {"unit": "%", "size": 50, "sizes": []}})
        for i in items]

    pill = _st_card([_row(cells, 24, align="center")], bg="white",
                    pad=dims(22, 34, 22, 34), radius=R_PILL, extra={
        "padding_mobile": dims(20, 20, 20, 20),
        "border_radius_mobile": R_PANEL,
        **CARD_SHADOW,
    })

    return _st_section([pill], bg=props.get("bg", "surface"), pad=dims(0, 0, 0, 0),
                       extra={
        "margin": dims(-46, 0, 0, 0),
        "margin_mobile": dims(-32, 0, 0, 0),
        "z_index": 5,
        "background_background": "",
        "padding_tablet": dims(0, 24, 0, 24),
        "padding_mobile": dims(0, 20, 0, 20),
    })


@block("store.panels")
def store_panels(props):
    """Two or more wide pale-blue panels, each heading + body + button.

    The reference's highest-contrast section and the one that does the most
    work: it states the two claims the whole site rests on before the visitor
    has scrolled to any product.
    """
    items = props["items"]
    g_px = props.get("gap", 26)
    w = _track(len(items), g_px)
    card_extra = {"flex_gap": gap(16), "flex_align_items": "flex-start"}
    if props.get("min_height"):
        card_extra["min_height"] = slider(props["min_height"])
    cards = [_col([_st_card([
        _heading(i["title"], "h2", T["h_medium"], tone="brand"),
        _text(i["text"]),
        *([_button(i["cta"]["label"], i["cta"]["href"], "primary")]
          if i.get("cta") else []),
    ], bg=props.get("card_bg", "alt"), pad=dims(34, 34, 34, 34), border=False,
        extra=dict(card_extra))], w,
        extra={"width_tablet": {"unit": "%", "size": 100, "sizes": []}})
        for i in items]

    body = [_row(cards, g_px, align="stretch")]
    if props.get("heading"):
        body.insert(0, _st_head(props, align=props.get("align", "center")))
    return _st_section(body, bg=props.get("bg", "white"),
                       extra={"flex_gap": gap(40)})


@block("store.categories")
def store_categories(props):
    """Shop-by-category tiles: image, name, and a Shop Now link.

    Tiles are hand-listed rather than pulled from product categories. A
    category widget would render every term including the empty ones, and the
    brief names an exact six in an exact order.
    """
    items = props["items"]
    cols = props.get("columns", 3)
    w, w_t = _grid_widths(cols, 26)

    def tile(i):
        img = widget("image", {
            "image": media(i.get("image", {}).get("url", ""),
                           i.get("image", {}).get("alt", i["title"])),
            "image_size": "medium_large",
            "align": "center",
            "width": slider(100, "%"),
        }) if i.get("image", {}).get("url") else container([], {
            # Empty slot: a fixed-height pale block, so an unfilled tile reads
            # as "photograph goes here" rather than as a broken layout.
            "content_width": "full",
            "min_height": slider(props.get("image_height", 190)),
            "border_radius": box(8),
            "background_background": "classic",
        }, globals_={"background_color": color_ref(C["surface_alt"])})

        return _hover_lift(_st_card([
            img,
            _heading(i["title"], "h3", T["h_small"]),
            *([_text(i["text"], small=True)] if i.get("text") else []),
            widget("button", {
                "text": i.get("cta_label", props.get("cta_label", "Shop Now")),
                "link": link(i["href"]),
                "selected_icon": icon("fas fa-arrow-right"),
                "icon_align": "right",
                "text_padding": dims(0, 0, 0, 0),
                "button_type": "default",
            }, globals_={
                "button_text_color": color_ref(C["ink_primary"]),
                "background_color": color_ref(C["transparent"]),
                "hover_color": color_ref("secondary"),
                "button_background_hover_color": color_ref(C["transparent"]),
                "typography_typography": typo_ref("accent"),
            }),
        ], bg="white", extra={"flex_gap": gap(13),
                              "flex_align_items": "flex-start"}))

    cells = [_col([tile(i)], w, extra={
        "width_tablet": {"unit": "%", "size": w_t, "sizes": []}}) for i in items]

    rows = []
    for n in range(0, len(cells), cols):
        rows.append(_row(cells[n:n + cols], 26, align="stretch"))

    return _st_section([_st_head(props)] + rows, bg=props.get("bg", "white"),
                       extra={"flex_gap": gap(40)})


@block("store.products")
def store_products(props):
    """A WooCommerce product grid — featured, recent, or a fixed category.

    `wc-products` rather than a hand-built card grid: the client adds a
    compound in WordPress and it appears here with its own price, stock state
    and add-to-cart, without anyone opening Elementor. That is the whole
    "I will be adding more products" requirement, and a hand-written list
    would defeat it on day one.
    """
    grid = widget("wc-products", {
        "columns": str(props.get("columns", 4)),
        "posts_per_page": str(props.get("count", 8)),
        "filter_by": props.get("filter_by", "featured"),
        "orderby": props.get("orderby", "date"),
        "order": props.get("order", "desc"),
        "show_onsale_flash": "yes" if props.get("sale_flash", True) else "",
        "column_gap": slider(24),
        "row_gap": slider(34),
        "align": "center",
        "automatically_align_buttons": "yes",
        "box_padding": dims(18, 18, 22, 18),
        "image_spacing": slider(16),
        "title_spacing": slider(8),
        "button_spacing": slider(16),
        "button_text_padding": dims(12, 20, 12, 20),
        "star_size": slider(13),
    }, globals_={
        "title_color": color_ref("secondary"),
        "title_typography_typography": typo_ref(T["h_small"]),
        "price_color": color_ref(C["ink_primary"]),
        "price_typography_typography": typo_ref(T["h_small"]),
        "old_price_color": color_ref(C["muted"]),
        "star_color": color_ref("primary"),
        "empty_star_color": color_ref(C["border"]),
        "box_bg_color": color_ref(C["white"]),
        "button_text_color": color_ref(C["on_primary"]),
        "button_background_color": color_ref("primary"),
        "button_hover_color": color_ref(C["white"]),
        "button_background_color_hover": color_ref("secondary"),
        "button_typography_typography": typo_ref("accent"),
        "onsale_text_color": color_ref(C["on_primary"]),
        "onsale_background_color": color_ref("primary"),
    })

    body = [_st_head(props), grid]
    if props.get("cta"):
        body.append(_col([
            _button(props["cta"]["label"], props["cta"]["href"],
                    props.get("cta_style", "ghost")),
        ], extra={"flex_align_items": "center"}))

    return _st_section(body, bg=props.get("bg", "surface"),
                       extra={"flex_gap": gap(40)})


@block("store.features")
def store_features(props):
    """N-column icon feature grid — 'Why researchers choose us'."""
    items = props["items"]
    cols = props.get("columns", 4)
    on_dark = props.get("bg") in ("dark", "primary")
    w, w_t = _grid_widths(cols, 24)
    cells = [_col([_st_iconcard(i, on_dark=on_dark,
                                bg=props.get("card_bg", "white"))], w,
                  extra={"width_tablet": {"unit": "%", "size": w_t, "sizes": []}})
             for i in items]
    rows = [_row(cells[n:n + cols], 24, align="stretch")
            for n in range(0, len(cells), cols)]
    return _st_section([_st_head(props, on_dark=on_dark)] + rows,
                       bg=props.get("bg", "white"), extra={"flex_gap": gap(40)})


@block("store.checklist")
def store_checklist(props):
    """Ticked claim list beside a feature grid — the reference's 'Our
    Standards' + 'Why Choose Us' pairing, which is one section, not two."""
    left = [_st_head({"heading": props["heading"],
                      "sub": props.get("sub", ""),
                      "eyebrow": props.get("eyebrow", "")}, align="left")]
    left.append(_col([
        _row([
            _st_icon("fas fa-circle-check", size=17, boxed=False),
            _text(t, small=True),
        ], gap_px=11, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row",
                   "padding": dims(11, 14, 11, 14),
                   "border_radius": box(8),
                   "background_background": "classic",
                   "__globals__": {"background_color": color_ref(C["surface"])}})
        for t in props["ticks"]], extra={"flex_gap": gap(9)}))

    items = props.get("items", [])
    cols = props.get("columns", 2)
    w_in, _ = _grid_widths(cols, 20)
    cells = [_col([_st_iconcard(i)], w_in,
                  extra={"width_tablet": {"unit": "%", "size": 100, "sizes": []}})
             for i in items]
    right = [_st_head({"heading": props["items_heading"]}, align="left")] if \
        props.get("items_heading") else []
    right += [_row(cells[n:n + cols], 20, align="stretch")
              for n in range(0, len(cells), cols)]

    w_l, w_r = _tracks(props.get("ratios", [36, 64]), 44)
    return _st_section([_row([
        _col(left, w_l, extra={"flex_gap": gap(24)}),
        _col(right, w_r, extra={"flex_gap": gap(20)}),
    ], 44, align="flex-start")], bg=props.get("bg", "white"))


@block("store.promise")
def store_promise(props):
    """Dark image band carrying the COA / quality promise plus a step strip.

    The reference runs its RUO panel and its three-step research process over
    one photograph. Keeping them in one band is deliberate: the promise is
    what makes the steps worth reading, and splitting them into two sections
    puts a fold between a claim and its evidence.
    """
    panel = _st_card([
        *([_st_chip(props["eyebrow"], align="left", on_dark=True)]
          if props.get("eyebrow") else []),
        _heading(props["heading"], "h2", T["h_large"], on_dark=True),
        _text(props["text"], on_dark=True),
        *([_button(props["cta"]["label"], props["cta"]["href"], "primary")]
          if props.get("cta") else []),
    ], bg="dark", pad=dims(36, 36, 36, 36), border=False, extra={
        "flex_gap": gap(18),
        "flex_align_items": "flex-start",
        "background_color_b": "",
        "background_background": "classic",
        "__globals__": {"background_color": color_ref(C["overlay"])},
    })

    steps = props.get("steps", [])
    step_cells = []
    if steps:
        w = _track(len(steps), 18)
        step_cells = [_col([_col([
            _st_icon(s.get("icon", "fas fa-flask"), size=19, on_dark=True),
            _heading(s["title"], "h4", T["h_small"], on_dark=True),
            _text(s["text"], on_dark=True, small=True),
        ], extra={"flex_gap": gap(10)})], w, extra={
            "width_tablet": {"unit": "%", "size": 100, "sizes": []}})
            for s in steps]

    right = []
    if props.get("steps_heading"):
        right.append(_heading(props["steps_heading"], "h3", T["h_medium"],
                              align="center", on_dark=True))
    if step_cells:
        right.append(_row(step_cells, 18, align="flex-start"))
    right_panel = _st_card(right, bg="dark", pad=dims(36, 30, 36, 30),
                           border=False, extra={
        "flex_gap": gap(24),
        "__globals__": {"background_color": color_ref(C["overlay"])},
    }) if right else None

    w_l, w_r = _tracks(props.get("ratios", [38, 62]), 26)
    row = _row([c for c in [
        _col([panel], w_l),
        _col([right_panel], w_r) if right_panel else None,
    ] if c is not None], 26, align="stretch")

    sec = container([row], {
        "content_width": "boxed",
        "flex_direction": "column",
        "flex_justify_content": "center",
        "padding": dims(96, 0, 96, 0),
        "padding_tablet": dims(72, 24, 72, 24),
        "padding_mobile": dims(56, 20, 56, 20),
        "background_background": "classic",
        "background_size": "cover",
        "background_position": "center center",
        **({"background_image": media(props["image"]["url"],
                                      props["image"].get("alt", ""))}
           if props.get("image", {}).get("url") else {}),
    }, globals_={"background_color": color_ref("secondary")})
    return _scrim(sec, "bottom", props.get("scrim", 0.72))


@block("store.steps")
def store_steps(props):
    """Numbered how-it-works strip."""
    items = props["items"]
    w = _track(len(items), 22)
    cells = []
    for n, i in enumerate(items, 1):
        cells.append(_col([_st_card([
            _col([widget("heading", {
                "title": str(n).zfill(2), "header_size": "div", "align": "center",
            }, globals_={
                "title_color": color_ref(C["on_primary"]),
                "typography_typography": typo_ref(T["h_small"]),
            })], extra={
                "width": slider(42), "min_height": slider(42), "_flex_grow": 0,
                "flex_justify_content": "center", "flex_align_items": "center",
                "_flex_align_self": "flex-start",
                "border_radius": R_PILL, "background_background": "classic",
                "__globals__": {"background_color": color_ref("primary")},
            }),
            _heading(i["title"], "h3", T["h_small"]),
            _text(i["text"], small=True),
        ], bg=props.get("card_bg", "white"),
            extra={"flex_gap": gap(13), "flex_align_items": "flex-start"})],
            w, extra={"width_tablet": {"unit": "%", "size": 50, "sizes": []}}))
    return _st_section([_st_head(props), _row(cells, 22, align="stretch")],
                       bg=props.get("bg", "surface"),
                       extra={"flex_gap": gap(40)})


@block("store.posts")
def store_posts(props):
    """Research Hub preview — the real post loop, not hand-written cards.

    `posts` with the cards skin: the brief wants this section to stay fresh
    for SEO, and a hand-written list goes stale the moment the client
    publishes anything.
    """
    grid = widget("posts", {
        "_skin": "cards",
        "cards_columns": str(props.get("columns", 3)),
        "cards_posts_per_page": str(props.get("count", 3)),
        "cards_show_excerpt": "yes",
        "cards_excerpt_length": props.get("excerpt", 18),
        "cards_show_read_more": "yes",
        "cards_read_more_text": props.get("read_more", "Read Article"),
        "cards_meta_separator": "  •  ",
        "cards_item_ratio": slider(0.6),
        "cards_row_gap": slider(30),
        "cards_column_gap": slider(26),
        "cards_card_border_radius": R_CARD,
        "cards_card_padding": dims(20, 20, 24, 20),
        "cards_show_badge": "",
        # Off on a homepage teaser, on where this block IS the blog index —
        # nine posts and no way forward is a dead end on the one page the
        # brief's whole SEO argument depends on.
        **({"pagination_type": props.get("paginate"),
            "pagination_align": "center"} if props.get("paginate") else {}),
    }, globals_={
        "cards_title_typography_typography": typo_ref(T["h_small"]),
        "cards_excerpt_color": color_ref("text"),
        "cards_excerpt_typography_typography": typo_ref(T["body_small"]),
        "cards_meta_color": color_ref(C["muted"]),
        "cards_meta_typography_typography": typo_ref(T["meta"]),
        "cards_read_more_typography_typography": typo_ref("accent"),
        "cards_card_bg_color": color_ref(C["white"]),
    })
    body = [_st_head(props), grid]
    if props.get("cta"):
        body.append(_col([_button(props["cta"]["label"], props["cta"]["href"],
                                  "ghost")], extra={"flex_align_items": "center"}))
    return _st_section(body, bg=props.get("bg", "white"),
                       extra={"flex_gap": gap(40)})


@block("store.reviews")
def store_reviews(props):
    """Testimonial cards — star rating, quote, attribution, verified tag."""
    items = props["items"]
    cols = props.get("columns", 3)
    w, w_t = _grid_widths(cols, 24)

    def card(i):
        return _st_card([
            widget("star-rating", {
                "rating": i.get("rating", 5), "star_style": "star_fontawesome",
                "rating_scale": "5", "icon_size": slider(15), "align": "left",
            }, globals_={
                "stars_color": color_ref("primary"),
                "stars_unmarked_color": color_ref(C["border"]),
            }),
            _text(i["quote"]),
            _row([
                _col([
                    _heading(i["name"], "h4", T["h_small"]),
                    *([_text(i["role"], small=True)] if i.get("role") else []),
                ], extra={"flex_gap": gap(2)}),
                *([_st_chip(i["tag"], align="left")] if i.get("tag") else []),
            ], gap_px=12, align="center", justify="space-between"),
        ], bg=props.get("card_bg", "white"),
            extra={"flex_gap": gap(15), "flex_align_items": "flex-start"})

    cells = [_col([card(i)], w, extra={
        "width_tablet": {"unit": "%", "size": w_t, "sizes": []}}) for i in items]
    rows = [_row(cells[n:n + cols], 24, align="stretch")
            for n in range(0, len(cells), cols)]
    return _st_section([_st_head(props)] + rows, bg=props.get("bg", "surface"),
                       extra={"flex_gap": gap(40)})


@block("store.compliance")
def store_compliance(props):
    """The mandatory Research Use Only notice.

    Bordered and left-aligned rather than centred prose: this is the block a
    payment processor or a regulator reads, and it has to look like a notice,
    not like marketing. The copy is passed through verbatim — no factory
    should ever paraphrase it.
    """
    body = [
        _row([
            _st_icon(props.get("icon", "fas fa-triangle-exclamation"), size=19),
            _heading(props["heading"], "h2", T["h_medium"], tone="brand"),
        ], gap_px=14, align="center",
            extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
        _text(props["text"]),
    ]
    if props.get("links"):
        body.append(widget("icon-list", {
            "icon_list": [repeater_item(
                text=l["text"], link=link(l["href"]),
                selected_icon=icon("fas fa-arrow-right")) for l in props["links"]],
            "view": "inline", "space_between": slider(22), "icon_size": slider(12),
        }, globals_={
            "icon_color": color_ref("primary"),
            "text_color": color_ref(C["ink_primary"]),
            "icon_typography_typography": typo_ref(T["meta"]),
        }))
    panel = _st_card(body, bg=props.get("card_bg", "surface"),
                     pad=dims(34, 36, 34, 36),
                     extra={"flex_gap": gap(16),
                            "border_width": dims(1, 1, 1, 4)})
    return _st_section([panel], bg=props.get("bg", "white"),
                       pad=dims(20, 0, 84, 0),
                       extra={"padding_tablet": dims(16, 24, 64, 24),
                              "padding_mobile": dims(12, 20, 48, 20)})


@block("store.newsletter")
def store_newsletter(props):
    """Email capture. The form is Elementor Pro's, so the client wires it to
    their own list in the widget rather than through a template rebuild."""
    form = widget("form", {
        "form_name": props.get("form_name", "Newsletter"),
        "form_fields": [repeater_item(
            custom_id="email", field_type="email",
            field_label="Email", placeholder=props.get(
                "placeholder", "Your Email Address"),
            required="true", width="70")],
        "button_text": props.get("button", "Subscribe"),
        "button_size": "md",
        "button_align": "stretch",
        "button_width": "30",
        "input_size": "md",
        "show_labels": "",
        "mark_required": "",
        "button_border_radius": box(8),
        "field_border_radius": box(8),
        "row_gap": slider(10),
        "success_message": props.get(
            "success", "Thank you. Please check your inbox to confirm."),
    }, globals_={
        "field_text_color": color_ref("secondary"),
        "field_background_color": color_ref(C["white"]),
        "field_border_color": color_ref(C["border"]),
        "field_typography_typography": typo_ref(T["body_small"]),
        "button_background_color": color_ref("primary"),
        "button_text_color": color_ref(C["on_primary"]),
        "button_typography_typography": typo_ref("accent"),
    })
    body = [_st_head(props), _col([form], extra={
        "content_width": "boxed", "boxed_width": slider(560),
        "margin": dims(0, "auto", 0, "auto"),
    })]
    if props.get("micro"):
        body.append(_text(props["micro"], align="center", small=True))
    return _st_section(body, bg=props.get("bg", "surface"),
                       extra={"flex_gap": gap(26)})


@block("store.split")
def store_split(props):
    """Image beside prose — About, founder message, testing process.

    A general-purpose two-column block kept here rather than in a page-
    specific module because every content page the client adds next needs one.
    """
    img = widget("image", {
        "image": media(props["image"]["url"], props["image"].get("alt", "")),
        "image_size": "large", "align": "center", "width": slider(100, "%"),
        "border_radius": R_PANEL,
    }) if props.get("image", {}).get("url") else container([], {
        "content_width": "full",
        "min_height": slider(props.get("image_height", 420)),
        "border_radius": R_PANEL,
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["surface_alt"])})

    text = [_st_head(props, align="left")]
    for para in props.get("paras", []):
        text.append(_text(para))
    if props.get("ticks"):
        text.append(widget("icon-list", {
            "icon_list": [repeater_item(
                text=t, selected_icon=icon("fas fa-circle-check"))
                for t in props["ticks"]],
            "space_between": slider(9), "icon_size": slider(14),
        }, globals_={
            "icon_color": color_ref("primary"),
            "text_color": color_ref("text"),
            "icon_typography_typography": typo_ref(T["body_small"]),
        }))
    if props.get("cta"):
        text.append(_button(props["cta"]["label"], props["cta"]["href"],
                            "primary"))

    w_a, w_b = _tracks(props.get("ratios", [46, 54]), 44)
    cols = [_col([img], w_a), _col(text, w_b, extra={"flex_gap": gap(16)})]
    if props.get("flip"):
        cols = [_col(text, w_b, extra={"flex_gap": gap(16)}), _col([img], w_a)]
    return _st_section([_row(cols, 44, align="center")],
                       bg=props.get("bg", "white"))
