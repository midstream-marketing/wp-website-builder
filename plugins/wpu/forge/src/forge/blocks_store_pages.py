"""
blocks_store_pages.py — content, support and policy page sections.

The storefront's long tail: order tracking, shipping, returns, FAQ, wholesale,
support, and the eight legal documents. These pages are mostly prose, and
prose is where a template library usually gives up and hands the client a
blank text widget — which is how policy pages end up as one unstyled wall of
text with no anchors and no way to find clause 7.

`store.prose` is the answer to that: a sectioned document with real `h2`s, a
sticky table of contents built from them, and callout/list variants. Every
policy page in the kit is one `store.prose` call, so they are all consistent
and a new policy is a data entry rather than a layout job.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, media, link, icon,
    gap, color_ref, typo_ref, css,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _track, _grid_widths, _heading, _text,
    _button, _scrim, _faq, _hover_lift, CARD_SHADOW, CARD_SHADOW_SOFT,
)
from .blocks_store import (
    _st_section, _st_head, _st_chip, _st_card, _st_icon, _st_iconcard,
    _st_rule, ST_PAD, ST_PAD_T, ST_PAD_M, R_CARD, R_PANEL, R_PILL,
)


@block("store.pagehero")
def store_pagehero(props):
    """Compact dark banner for a content page.

    Shorter than the homepage hero (260px against 560px) on purpose: on a
    policy or support page the visitor arrived with a specific question, and
    a full-height banner is one scroll between them and the answer.
    """
    body = []
    if props.get("eyebrow"):
        body.append(_st_chip(props["eyebrow"], align="center", on_dark=True))
    body.append(widget("heading", {
        "title": props["heading"], "header_size": "h1", "align": "center",
    }, globals_={
        "title_color": color_ref(C["white"]),
        "typography_typography": typo_ref(T["h_large"]),
    }))
    if props.get("sub"):
        body.append(_text(props["sub"], align="center", on_dark=True))

    sec = container([_col(body, extra={
        "flex_gap": gap(14), "flex_align_items": "center",
        "content_width": "boxed", "boxed_width": slider(props.get("measure", 780)),
        "margin": dims(0, "auto", 0, "auto"),
    })], {
        "content_width": "boxed",
        "flex_direction": "column",
        "flex_justify_content": "center",
        "min_height": slider(props.get("height", 260)),
        "min_height_mobile": slider(210),
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
        return _scrim(sec, "bottom", props.get("scrim", 0.80))
    return sec


@block("store.prose")
def store_prose(props):
    """A sectioned long-form document, optionally with a sticky contents rail.

    Every `h2` in the body is a real heading, which is what lets the Pro
    table-of-contents widget build itself — and what lets a support agent send
    a customer to `#refunds` instead of "scroll about halfway down".

    Section shapes, all optional per section: `paras` (prose), `list`
    (bulleted), `steps` (numbered), `note` (a bordered callout for the line
    that most often gets missed).
    """
    updated = props.get("updated")
    sections = props["sections"]

    body = []
    if updated:
        body.append(_st_card([_text(updated, small=True)], bg="surface",
                             pad=dims(12, 16, 12, 16), border=True,
                             extra={"flex_gap": gap(0)}))
    if props.get("intro"):
        body.append(_text(props["intro"]))

    for s in sections:
        block_out = []
        if s.get("heading"):
            h = _heading(s["heading"], "h2", T["h_medium"], tone="brand")
            # Anchor id so a policy clause can be linked to directly.
            if s.get("id"):
                h["settings"]["_element_id"] = s["id"]
            block_out.append(h)
        for p in s.get("paras", []):
            block_out.append(_text(p))
        if s.get("list"):
            block_out.append(widget("icon-list", {
                "icon_list": [repeater_item(
                    text=t, selected_icon=icon("fas fa-circle-check"))
                    for t in s["list"]],
                "space_between": slider(9), "icon_size": slider(13),
            }, globals_={
                "icon_color": color_ref("primary"),
                "text_color": color_ref("text"),
                "icon_typography_typography": typo_ref("text"),
            }))
        if s.get("steps"):
            ol = "<ol>" + "".join("<li>" + t + "</li>" for t in s["steps"]) + "</ol>"
            block_out.append(_text(ol))
        if s.get("note"):
            block_out.append(_st_card([_text(s["note"], small=True)],
                                      bg="alt", pad=dims(16, 20, 16, 20),
                                      border=True,
                                      extra={"flex_gap": gap(0),
                                             "border_width": dims(1, 1, 1, 3)}))
        body.append(_col(block_out, extra={"flex_gap": gap(12)}))

    if props.get("closing"):
        body.append(_st_card([_text(props["closing"], small=True)],
                             bg="surface", pad=dims(20, 22, 20, 22),
                             extra={"flex_gap": gap(0)}))

    prose = _col(body, extra={"flex_gap": gap(26)})

    if not props.get("toc", True):
        return _st_section([_col([prose], extra={
            "content_width": "boxed", "boxed_width": slider(820),
            "margin": dims(0, "auto", 0, "auto"),
        })], bg=props.get("bg", "white"))

    # `position: sticky` rather than Elementor's sticky effect, which is Pro's
    # JS implementation and switches the element to `position: fixed` — fixed
    # lifts it out of the flow and the prose column jumps left by the rail's
    # width the moment it engages.
    toc = widget("table-of-contents", {
        "headings_by_tags": ["h2"],
        "html_tag": "h4",
        "container": props.get("toc_title", "On this page"),
        "marker_view": "numbers",
        "hierarchical_view": "",
        "minimize_box": "",
        "border_width": box(1),
        "border_radius": box(10),
        "padding": dims(20, 20, 20, 20),
        "no_headings_message": "",
    }, globals_={
        "header_text_color": color_ref("secondary"),
        "header_typography_typography": typo_ref(T["h_small"]),
        "item_text_color_normal": color_ref("text"),
        "item_text_color_hover": color_ref(C["ink_primary"]),
        "item_text_color_active": color_ref(C["ink_primary"]),
        "list_typography_typography": typo_ref(T["body_small"]),
        "marker_color": color_ref("primary"),
        "border_color": color_ref(C["border"]),
    })
    rail = _col([toc], extra={
        "custom_css": css("selector { position: sticky; top: 24px; }"),
    })

    w_a, w_b = _tracks(props.get("ratios", [27, 73]), 44)
    return _st_section([_row([
        _col([rail], w_a),
        _col([prose], w_b),
    ], 44, align="flex-start")], bg=props.get("bg", "white"))


@block("store.faq")
def store_faq(props):
    """Grouped FAQ accordions.

    `faq_schema` is on: the brief's whole SEO argument for this site is
    ranking on compliant informational queries, and FAQ rich results are the
    cheapest version of that. It is only legitimate where the question and
    answer are both really on the page, which is the case here.
    """
    body = []
    if props.get("heading") or props.get("eyebrow"):
        body.append(_st_head(props))

    for grp in props["groups"]:
        acc = _faq(grp["faqs"], first_open=grp.get("first_open", False))
        acc["settings"]["faq_schema"] = "yes" if props.get("schema", True) else ""
        inner = []
        if grp.get("title"):
            inner.append(_heading(grp["title"], "h2", T["h_medium"],
                                  tone="brand"))
        inner.append(acc)
        body.append(_col(inner, extra={"flex_gap": gap(16)}))

    if props.get("cta"):
        body.append(_st_card([
            _heading(props["cta"]["heading"], "h3", T["h_small"]),
            *([_text(props["cta"]["text"], small=True)]
              if props["cta"].get("text") else []),
            _button(props["cta"]["label"], props["cta"]["href"], "primary"),
        ], bg="alt", border=False,
            extra={"flex_gap": gap(13), "flex_align_items": "flex-start"}))

    return _st_section([_col(body, extra={
        "flex_gap": gap(34),
        "content_width": "boxed", "boxed_width": slider(props.get("width", 880)),
        "margin": dims(0, "auto", 0, "auto"),
    })], bg=props.get("bg", "white"))


@block("store.form")
def store_form(props):
    """A form beside its supporting copy — wholesale, support, bulk enquiry.

    Field shapes come from the IR rather than being fixed here, because every
    one of these forms asks something different and a generic four-field
    fallback on a wholesale page collects none of what the client needs.
    """
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

    form = widget("form", {
        "form_name": props.get("form_name", "Enquiry"),
        "submit_actions": ["email"],
        "form_fields": fields,
        "button_text": props.get("submit_label", "Send Enquiry"),
        "button_size": "md",
        "button_width": "100",
        "input_size": "md",
        "show_labels": "yes",
        "mark_required": "yes",
        "row_gap": slider(14),
        "column_gap": slider(14),
        "field_border_radius": box(8),
        "button_border_radius": box(8),
        "success_message": props.get(
            "success_message", "Thank you — we'll be in touch shortly."),
        "email_to": props.get("email", ""),
        "email_subject": props.get("email_subject", "New enquiry"),
    }, globals_={
        "field_text_color": color_ref("secondary"),
        "field_background_color": color_ref(C["white"]),
        "field_border_color": color_ref(C["border"]),
        "field_typography_typography": typo_ref(T["body_small"]),
        "field_label_color": color_ref("secondary"),
        "button_background_color": color_ref("primary"),
        "button_text_color": color_ref(C["on_primary"]),
        "button_typography_typography": typo_ref("accent"),
    })
    form_card = _st_card([form], bg="white", pad=dims(30, 30, 30, 30),
                         extra={"flex_gap": gap(0), **CARD_SHADOW})

    aside = [_st_head(props, align="left")]
    for p in props.get("paras", []):
        aside.append(_text(p))
    if props.get("points"):
        aside.append(widget("icon-list", {
            "icon_list": [repeater_item(
                text=t, selected_icon=icon("fas fa-circle-check"))
                for t in props["points"]],
            "space_between": slider(10), "icon_size": slider(14),
        }, globals_={
            "icon_color": color_ref("primary"),
            "text_color": color_ref("text"),
            "icon_typography_typography": typo_ref("text"),
        }))
    if props.get("note"):
        aside.append(_st_card([_text(props["note"], small=True)], bg="alt",
                              pad=dims(16, 18, 16, 18), border=True,
                              extra={"flex_gap": gap(0),
                                     "border_width": dims(1, 1, 1, 3)}))

    w_a, w_b = _tracks(props.get("ratios", [44, 56]), 44)
    return _st_section([_row([
        _col(aside, w_a, extra={"flex_gap": gap(18)}),
        _col([form_card], w_b),
    ], 44, align="flex-start")], bg=props.get("bg", "white"))


@block("store.shortcode")
def store_shortcode(props):
    """A shortcode in a card — order tracking, a chat embed, a COA lookup.

    These are all plugin-owned interfaces. Wrapping rather than rebuilding is
    deliberate: WooCommerce's order-tracking form already validates an order
    id against an email, and a second implementation in Elementor controls
    would be a second thing to keep in step with it.
    """
    inner = []
    if props.get("heading"):
        inner.append(_heading(props["heading"], "h2", T["h_medium"],
                              tone="brand"))
    if props.get("text"):
        inner.append(_text(props["text"]))
    inner.append(widget("shortcode", {"shortcode": props["shortcode"]}))
    if props.get("note"):
        inner.append(_text(props["note"], small=True))

    card = _st_card(inner, bg=props.get("card_bg", "white"),
                    pad=dims(32, 34, 32, 34),
                    extra={"flex_gap": gap(16), **CARD_SHADOW_SOFT})

    return _st_section([_col([card], extra={
        "content_width": "boxed", "boxed_width": slider(props.get("width", 760)),
        "margin": dims(0, "auto", 0, "auto"),
    })], bg=props.get("bg", "surface"))


@block("store.cards")
def store_cards(props):
    """Linked icon cards — contact routes, a policy index, support channels.

    The generic tile grid. `href` turns a card into a link; without one it is
    an information tile, which is why this one factory serves both the
    'how to reach us' grid and the legal-document index.
    """
    items = props["items"]
    cols = props.get("columns", 3)
    w, w_t = _grid_widths(cols, 24)

    def card(i):
        inner = [
            _st_icon(i.get("icon", "fas fa-circle-info")),
            _heading(i["title"], "h3", T["h_small"]),
        ]
        if i.get("text"):
            inner.append(_text(i["text"], small=True))
        if i.get("href"):
            inner.append(widget("button", {
                "text": i.get("cta_label", props.get("cta_label", "Open")),
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
            }))
        c = _st_card(inner, bg=props.get("card_bg", "white"),
                     extra={"flex_gap": gap(12),
                            "flex_align_items": "flex-start"})
        return _hover_lift(c) if i.get("href") else c

    cells = [_col([card(i)], w, extra={
        "width_tablet": {"unit": "%", "size": w_t, "sizes": []}}) for i in items]
    rows = [_row(cells[n:n + cols], 24, align="stretch")
            for n in range(0, len(cells), cols)]

    body = ([_st_head(props)] if props.get("heading") else []) + rows
    return _st_section(body, bg=props.get("bg", "white"),
                       extra={"flex_gap": gap(40)})


@block("store.ctaband")
def store_ctaband(props):
    """Closing call to action. Narrower and quieter than `store.promise` —
    these pages end in a question, not a pitch."""
    inner = [
        _heading(props["heading"], "h2", T["h_medium"], align="center",
                 on_dark=True),
    ]
    if props.get("text"):
        inner.append(_text(props["text"], align="center", on_dark=True))
    btns = []
    if props.get("cta"):
        btns.append(_button(props["cta"]["label"], props["cta"]["href"],
                            "primary"))
    if props.get("cta2"):
        btns.append(_button(props["cta2"]["label"], props["cta2"]["href"],
                            "ghost_dark"))
    if btns:
        inner.append(_row(btns, 12, align="center", justify="center",
                          extra={"flex_direction_mobile": "column"}))

    panel = _st_card(_col_wrap(inner), bg="dark", pad=dims(44, 40, 44, 40),
                     border=False, radius=R_PANEL,
                     extra={"flex_gap": gap(0)})
    return _st_section([panel], bg=props.get("bg", "white"),
                       pad=dims(20, 0, 84, 0),
                       extra={"padding_tablet": dims(16, 24, 64, 24),
                              "padding_mobile": dims(12, 20, 48, 20)})


def _col_wrap(children):
    return [_col(children, extra={
        "flex_gap": gap(16), "flex_align_items": "center",
        "content_width": "boxed", "boxed_width": slider(680),
        "margin": dims(0, "auto", 0, "auto"),
    })]
