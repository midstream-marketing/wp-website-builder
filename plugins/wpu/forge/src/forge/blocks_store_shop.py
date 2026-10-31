"""
blocks_store_shop.py — product archive and single product templates.

Both documents are shells WordPress fills per product. Nothing in here writes
a product name, a price or a batch number: every such value comes from a
WooCommerce widget bound to the product being viewed. A literal in one of
these factories renders the same compound on every URL, which is the single
worst defect class in this domain because it looks like the client's data
entry rather than like a template bug.

Only widgets whose control sets are present in the mined registry are used.
`loop-grid` is deliberately avoided: its query group controls and the
WooCommerce dynamic tags are not in the registry, so a custom product card
could not be verified before shipping. See the client README.
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
    _st_section, _st_head, _st_chip, _st_card, _st_icon, _st_iconcard,
    _st_rule, ST_PAD, ST_PAD_T, ST_PAD_M, R_CARD, R_PANEL, R_PILL,
)

# Shared styling for the two product grids, so the shop and the archive can
# never drift apart. Colour goes through globals; geometry stays literal.
_GRID_GEOM = {
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
    "show_onsale_flash": "yes",
}
_GRID_COLOR = {
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
    # Was `button_background_color_hover`, which is not a control on
    # woocommerce-products, wc-products OR woocommerce-archive-products.
    "button_hover_background_color": color_ref("secondary"),
    "button_typography_typography": typo_ref("accent"),
    "onsale_text_color": color_ref(C["on_primary"]),
    "onsale_background_color": color_ref("primary"),
}


# ═══════════════════════════ product archive ═══════════════════════════

@block("store.archive.banner")
def store_archive_banner(props):
    """Archive header bound to the term being viewed.

    `theme-archive-title` rather than a literal heading: this one document
    serves Shop and every product category, so a written title would label the
    peptide-blends archive 'Shop All Peptides'.
    """
    crumb = widget("woocommerce-breadcrumb", {"alignment": "center"}, globals_={
        "text_color": color_ref(C["on_dark"]),
        "link_color": color_ref(C["brand_on_dark"]),
        "text_typography_typography": typo_ref(T["meta"]),
    })
    title = widget("theme-archive-title", {"align": "center"}, globals_={
        "title_color": color_ref(C["white"]),
        "typography_typography": typo_ref(T["h_large"]),
    })
    body = [crumb, title]
    if props.get("intro"):
        body.append(_text(props["intro"], align="center", on_dark=True))
    else:
        # The category's own description, so the client writes archive copy in
        # WooCommerce rather than asking for a template edit per category.
        body.append(widget("woocommerce-archive-description", {}, globals_={
            "text_color": color_ref(C["on_dark"]),
            "typography_typography": typo_ref("text"),
        }))

    sec = container([_col(body, extra={
        "flex_gap": gap(14), "flex_align_items": "center",
        "content_width": "boxed", "boxed_width": slider(760),
        "margin": dims(0, "auto", 0, "auto"),
    })], {
        "content_width": "boxed",
        "flex_direction": "column",
        "flex_justify_content": "center",
        "min_height": slider(props.get("height", 300)),
        "min_height_mobile": slider(230),
        "padding": dims(72, 0, 72, 0),
        "padding_tablet": dims(60, 24, 60, 24),
        "padding_mobile": dims(48, 20, 48, 20),
        "background_background": "classic",
        "background_size": "cover",
        "background_position": "center center",
        **({"background_image": media(props["image"]["url"],
                                      props["image"].get("alt", ""))}
           if props.get("image", {}).get("url") else {}),
    }, globals_={"background_color": color_ref("secondary")})
    return _scrim(sec, "bottom", props.get("scrim", 0.78))


@block("store.archive.chips")
def store_archive_chips(props):
    """Category quick-links above the grid.

    Hand-listed for the same reason the homepage tiles are: a term list widget
    would surface every empty category, and the order here is a merchandising
    decision rather than an alphabetical one.
    """
    lst = widget("icon-list", {
        "icon_list": [repeater_item(
            text=i["text"], link=link(i["href"]),
            selected_icon={"value": "", "library": ""})
            for i in props["items"]],
        "view": "inline",
        "space_between": slider(10),
        "icon_size": slider(0),
    }, globals_={
        "text_color": color_ref("secondary"),
        "text_color_hover": color_ref(C["ink_primary"]),
        "icon_typography_typography": typo_ref("accent"),
    })
    return _st_section([lst], bg=props.get("bg", "white"),
                       pad=dims(28, 0, 4, 0),
                       extra={"flex_align_items": "center",
                              "padding_tablet": dims(24, 24, 4, 24),
                              "padding_mobile": dims(20, 20, 4, 20)})


@block("store.archive.grid")
def store_archive_grid(props):
    """The shop itself.

    `woocommerce-archive-products` obeys the archive query it is rendered in,
    so this one grid serves /shop/ and every category and tag archive. Sorting
    and the result count are on by default here — unlike a ten-item tour index,
    a peptide catalogue is browsed by people comparing options.
    """
    grid = widget("woocommerce-archive-products", {
        "columns": str(props.get("columns", 3)),
        "rows": props.get("rows", 4),
        "allow_order": "yes" if props.get("allow_order", True) else "",
        "show_result_count": "yes" if props.get("show_count", True) else "",
        "nothing_found_message": props.get(
            "empty_message",
            "No compounds match that filter yet. Browse the full catalogue or "
            "contact us about availability."),
        **_GRID_GEOM,
    }, globals_={**_GRID_COLOR,
                 "nothing_found_color": color_ref("text")})
    return _st_section([grid], bg=props.get("bg", "white"),
                       pad=dims(40, 0, 84, 0),
                       extra={"padding_tablet": dims(32, 24, 64, 24),
                              "padding_mobile": dims(26, 20, 48, 20)})


# ═══════════════════════════ single product ═══════════════════════════

@block("store.product.main")
def store_product_main(props):
    """Gallery beside the buy box.

    The right column is ordered the way a research buyer decides: what it is,
    what it costs, whether it is in stock, the short description, then the
    add-to-cart, then the reassurance strip. The COA line sits above the
    button rather than below it because verifying purity before purchase is
    the whole proposition of the site.
    """
    gallery = widget("woocommerce-product-images", {
        "sale_flash": "yes",
        "image_border_radius": R_PANEL,
        "thumbs_border_radius": box(8),
        "spacing_thumbs": slider(10),
    })

    crumb = widget("woocommerce-breadcrumb", {"alignment": "left"}, globals_={
        "text_color": color_ref(C["muted"]),
        "link_color": color_ref(C["ink_primary"]),
        "text_typography_typography": typo_ref(T["meta"]),
    })
    title = widget("woocommerce-product-title", {
        "header_size": "h1", "align": "left", "link": "",
    }, globals_={
        "title_color": color_ref("secondary"),
        "typography_typography": typo_ref(T["h_large"]),
    })
    rating = widget("woocommerce-product-rating", {
        "alignment": "left",
    }, globals_={
        "star_color": color_ref("primary"),
        "empty_star_color": color_ref(C["border"]),
        "link_color": color_ref(C["muted"]),
    })
    price = widget("woocommerce-product-price", {
        "text_align": "left",
    }, globals_={
        "price_color": color_ref(C["ink_primary"]),
        "sale_price_color": color_ref(C["ink_primary"]),
        "typography_typography": typo_ref(T["h_large"]),
    })
    stock = widget("woocommerce-product-stock", {}, globals_={
        "text_color": color_ref("primary"),
        "text_typography_typography": typo_ref("accent"),
    })
    short = widget("woocommerce-product-short-description", {
        "text_align": "left",
    }, globals_={
        "text_color": color_ref("text"),
        "text_typography_typography": typo_ref("text"),
    })
    cart = widget("woocommerce-product-add-to-cart", {
        "show_quantity": "yes",
        "alignment": "justify",
        "button_border_radius": box(8),
        "quantity_border_radius": box(8),
        "button_padding": dims(16, 30, 16, 30),
    }, globals_={
        # These three were `button_background_color`,
        # `button_hover_text_color` and `button_hover_background_color`,
        # none of which is a control on woocommerce-product-add-to-cart —
        # so the Add to Cart button on EVERY single-product template built
        # here has been rendering in Elementor's default colours rather
        # than the kit's. __globals__ keys are never validated, so nothing
        # reported it. The real names are below.
        "button_text_color": color_ref(C["on_primary"]),
        "button_bg_color": color_ref("primary"),
        "button_text_color_hover": color_ref(C["white"]),
        "button_bg_color_hover": color_ref("secondary"),
        "button_typography_typography": typo_ref("accent"),
        "quantity_text_color": color_ref("secondary"),
        "quantity_border_color": color_ref(C["border"]),
    })
    meta = widget("woocommerce-product-meta", {
        "view": "stacked",
    }, globals_={
        "text_color": color_ref(C["muted"]),
        "link_color": color_ref(C["ink_primary"]),
        "divider_color": color_ref(C["border"]),
        "text_typography_typography": typo_ref(T["body_small"]),
    })

    right = [crumb, title, rating, price, stock, short]

    # COA callout. The link is a site-wide lookup page rather than a per-batch
    # URL: a template cannot know the batch, and a dead per-product link is
    # worse than one extra click on the page that sells verification.
    if props.get("coa"):
        right.append(_st_card([
            _row([
                _st_icon(props["coa"].get("icon", "fas fa-file-circle-check"),
                         size=18, boxed=False),
                _col([
                    _heading(props["coa"]["title"], "h4", T["h_small"]),
                    _text(props["coa"]["text"], small=True),
                ], extra={"flex_gap": gap(3)}),
            ], gap_px=12, align="flex-start",
                extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"}),
            *([_button(props["coa"]["cta"]["label"],
                       props["coa"]["cta"]["href"], "ghost")]
              if props["coa"].get("cta") else []),
        ], bg="alt", pad=dims(18, 20, 18, 20), border=False,
            extra={"flex_gap": gap(12), "flex_align_items": "flex-start"}))

    right.append(cart)

    if props.get("assurances"):
        right.append(_st_rule_light())
        right.append(widget("icon-list", {
            "icon_list": [repeater_item(
                text=a["text"],
                selected_icon=icon(a.get("icon", "fas fa-circle-check")))
                for a in props["assurances"]],
            "space_between": slider(8), "icon_size": slider(13),
        }, globals_={
            "icon_color": color_ref("primary"),
            "text_color": color_ref("text"),
            "icon_typography_typography": typo_ref(T["body_small"]),
        }))

    right.append(meta)

    if props.get("notice"):
        right.append(_st_card([_text(props["notice"], small=True)],
                              bg="surface", pad=dims(14, 16, 14, 16),
                              extra={"border_width": dims(1, 1, 1, 3)}))

    w_l, w_r = _tracks(props.get("ratios", [50, 50]), 48)
    return _st_section([_row([
        _col([gallery], w_l),
        _col(right, w_r, extra={"flex_gap": gap(14)}),
    ], 48, align="flex-start")], bg=props.get("bg", "white"),
        pad=dims(40, 0, 64, 0),
        extra={"padding_tablet": dims(32, 24, 52, 24),
               "padding_mobile": dims(26, 20, 44, 20)})


def _st_rule_light():
    return widget("divider", {
        "weight": slider(1), "gap": slider(6), "style": "solid",
    }, globals_={"color": color_ref(C["border"])})


@block("store.product.tabs")
def store_product_tabs(props):
    """WooCommerce's own data tabs — description, additional information,
    reviews, and any tab a plugin adds.

    Deliberately the native widget rather than a hand-built accordion: the COA
    tab the brief asks for is registered by a plugin or a snippet against
    `woocommerce_product_tabs`, and only the native widget picks that up.
    """
    tabs = widget("woocommerce-product-data-tabs", {
        "tab_border_radius": box(8),
        "panel_border_radius": box(8),
        "panel_border_width": dims(1, 1, 1, 1),
    }, globals_={
        "tabs_title_normal_color": color_ref("text"),
        "tabs_title_active_color": color_ref(C["ink_primary"]),
        "tabs_border_color": color_ref(C["border"]),
        "active_tabs_border_color": color_ref("primary"),
        "tabs_title_typography_typography": typo_ref("accent"),
        "content_typography_typography": typo_ref("text"),
        "content_heading_typography_typography": typo_ref(T["h_medium"]),
        "content_color": color_ref("text"),
        "content_heading_color": color_ref("secondary"),
    })
    return _st_section([tabs], bg=props.get("bg", "surface"),
                       pad=dims(56, 0, 56, 0),
                       extra={"padding_tablet": dims(48, 24, 48, 24),
                              "padding_mobile": dims(40, 20, 40, 20)})


@block("store.product.assurance")
def store_product_assurance(props):
    """Full-width trust band under the buy box — the four claims restated
    where a hesitating buyer actually is."""
    items = props["items"]
    w = _track(len(items), 24)
    cells = [_col([_row([
        _st_icon(i.get("icon", "fas fa-shield-halved"), size=20, boxed=False),
        _col([
            _heading(i["title"], "h4", T["h_small"]),
            *([_text(i["text"], small=True)] if i.get("text") else []),
        ], extra={"flex_gap": gap(3)}),
    ], gap_px=12, align="flex-start",
        extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})], w,
        extra={"width_tablet": {"unit": "%", "size": 50, "sizes": []}})
        for i in items]
    return _st_section([_row(cells, 24, align="flex-start")],
                       bg=props.get("bg", "white"),
                       pad=dims(0, 0, 56, 0),
                       extra={"padding_tablet": dims(0, 24, 48, 24),
                              "padding_mobile": dims(0, 20, 40, 20)})


@block("store.product.related")
def store_product_related(props):
    """WooCommerce's own related-products query.

    Not a hand-written list: on a template rendered for every product a fixed
    list would show the same four compounds everywhere, including on their own
    page.
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
        "heading_typography_typography": typo_ref(T["h_large"]),
    })
    body = []
    if props.get("heading"):
        body.append(_st_head(props))
    body.append(grid)
    return _st_section(body, bg=props.get("bg", "white"),
                       extra={"flex_gap": gap(32)})
