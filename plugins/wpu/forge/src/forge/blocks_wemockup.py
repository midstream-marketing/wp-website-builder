"""
blocks_wemockup.py — Web Elite Digital, "Free Website Mockup" landing page.

Three factories, and only three, because the rest of the page is built from
the kit's existing vocabulary (`services.grid`, `steps.numbered`,
`cards.services`, `features.grid`, `faq.accordion`, `cta.band`). A landing
page that invents its own version of every section stops looking like the
site it sits on, which is the one thing it must not do.

    wm.leadhero    dark hero: offer copy one side, the multi-step
                   qualification form the other, in the first screen
    wm.offerpanel  dark band: what the free mockup includes, beside a
                   $0 "ticket" summarising the terms
    wm.stickycta   fixed bottom bar on phone and tablet, one action

What the source HTML did and this does differently
--------------------------------------------------
The HTML prototype ran the six questions as a JavaScript quiz with a live
homepage preview redrawing beside it, a client-side budget gate that split
visitors into two result screens, and a WhatsApp deep link pre-filled with
their answers. Those are a script, and the build here uses the Elementor Pro
Form widget instead, so the whole page stays editable in the canvas and
submissions land in Elementor's Submissions table rather than in a webhook
that has to be wired up separately.

Three consequences, all handled on the page rather than left as gaps:

  * **No live preview.** The right-hand column is the form itself, which is
    what the visitor is there to fill in. The preview was decoration that
    cost a 400-line script.
  * **No branching result screen.** The budget floor is stated as an HTML
    field on the budget step instead of being enforced after submission —
    the visitor finds out before they spend another thirty seconds, which is
    the honest ordering.
  * **No pre-filled WhatsApp message.** A plain WhatsApp button and a booking
    button sit under the form, available from the first second rather than
    only after submitting.
"""
from __future__ import annotations

from .core import (
    container, widget, repeater_item, slider, dims, box, link,
    gap, color_ref, typo_ref, icon,
)
from .tokens import C, T
from .blocks import (
    block, _row, _col, _tracks, _button, _heading, _text, _display, _chip,
    _eyebrow, _ticks, CARD_SHADOW, KIT_CONTAINER,
)

WM_PAD = dims(96, 0, 96, 0)
WM_PAD_T = dims(72, 24, 72, 24)
WM_PAD_M = dims(56, 20, 56, 20)


def _sec(children, dark=True, pad=None, anchor=None, extra=None):
    s = {
        "content_width": "boxed",
        "flex_direction": "column",
        "padding": pad or WM_PAD,
        "padding_tablet": WM_PAD_T,
        "padding_mobile": WM_PAD_M,
        "background_background": "classic",
    }
    if anchor:
        s["_element_id"] = anchor
    if extra:
        s.update(extra)
    return container(children, s, globals_={
        "background_color": color_ref("secondary" if dark else C["white"])})


def _rule(on_dark=True):
    return widget("divider", {"weight": slider(1), "gap": slider(14),
                              "look": "line"},
                  globals_={"color": color_ref(
                      C["rule_dark"] if on_dark else C["border"])})


# ───────────────────────────── the form ─────────────────────────────────────

def _fields(spec):
    """IR field dicts -> Elementor form_fields repeater items.

    `type: "step"` is the Pro Form's own step divider: every field after one
    belongs to that step until the next. It is the whole reason this page can
    ask six questions without a script.
    """
    out = []
    for f in spec:
        item = {
            "custom_id": f["id"],
            "field_type": f.get("type", "text"),
            "field_label": f.get("label", ""),
            "width": str(f.get("width", 100)),
        }
        if f.get("placeholder"):
            item["placeholder"] = f["placeholder"]
        if f.get("required"):
            item["required"] = "true"
        if f.get("options"):
            item["field_options"] = "\n".join(f["options"])
        if f.get("inline"):
            item["inline_list"] = "elementor-subgroup-inline"
        if f.get("html"):
            item["field_html"] = f["html"]
        if f.get("rows"):
            item["rows"] = f["rows"]
        if f.get("acceptance_text"):
            item["acceptance_text"] = f["acceptance_text"]
        out.append(repeater_item(**item))
    return out


def _form(props):
    """The qualification form. Multi-step, progress bar, email on submit."""
    return widget("form", {
        "form_name": props.get("form_name", "Free Mockup Application"),
        "form_fields": _fields(props["fields"]),
        "submit_actions": props.get("submit_actions", ["email"]),
        "email_to": props.get("email", ""),
        "email_subject": props.get("email_subject", "Free mockup application"),
        "button_text": props.get("submit_label", "Get my free mockup"),
        "button_size": "md",
        "button_width": "100",
        "button_align": "center",
        "button_border_radius": box(999),
        "button_text_padding": dims(17, 28, 17, 28),
        "input_size": "md",
        "show_labels": "yes",
        "mark_required": "yes",
        "label_spacing": slider(6),
        "row_gap": slider(16),
        "column_gap": slider(14),
        "field_border_radius": box(10),
        "field_border_width": box(1),
        # Step chrome. A visitor who cannot see how much is left abandons a
        # six-step form at step two; the bar is the only thing that makes the
        # "about 60 seconds" promise legible while they are in it.
        "step_type": "progress_bar",
        "display_percentage": "yes",
        "step_next_label": props.get("next_label", "Continue"),
        "step_previous_label": props.get("back_label", "Back"),
        "step_progress_bar_height": slider(5),
        "step_progress_bar_border_radius": slider(999),
        "steps_gap": slider(22),
        "success_message": props.get("success_message",
                                     "Thanks — your mockup slot is reserved. "
                                     "We'll be in touch within one business "
                                     "day to collect your logo and brief."),
        "required_field_message": "Please answer this one so we can design "
                                  "the right thing.",
        "invalid_message": "Something above needs another look.",
    }, globals_={
        "button_background_color": color_ref(C["accent_fill"]),
        "button_text_color": color_ref(C["on_accent"]),
        "button_background_hover_color": color_ref("primary"),
        "button_hover_color": color_ref(C["on_primary"]),
        "button_typography_typography": typo_ref("accent"),
        "label_color": color_ref("secondary"),
        "label_typography_typography": typo_ref(T["meta"]),
        "field_text_color": color_ref("secondary"),
        "field_border_color": color_ref(C["border"]),
        "field_typography_typography": typo_ref(T["body_small"]),
        "html_color": color_ref(C["muted"]),
        "html_typography_typography": typo_ref(T["body_small"]),
        "step_active_primary_color": color_ref("primary"),
        "step_completed_primary_color": color_ref("primary"),
        "step_inactive_primary_color": color_ref(C["border"]),
        "step_progress_bar_color": color_ref("primary"),
        "step_progress_bar_background_color": color_ref(C["surface_alt"]),
        "step_progress_bar_percentage_color": color_ref(C["muted"]),
        "success_message_color": color_ref(C["ink_primary"]),
    })


@block("wm.leadhero")
def wm_leadhero(props):
    """Offer-first hero with the form in the first screen.

    The form is not below the fold and not on another page. Every other CTA
    on this template is an anchor back to `props["anchor"]`, so the page has
    exactly one destination.
    """
    w_left, w_right = _tracks([52, 48], 48)

    left = _col([
        *([_chip(props["eyebrow"], props.get("eyebrow_icon",
                                             "fas fa-location-dot"),
                 on_dark=True)] if props.get("eyebrow") else []),
        # `_display` colours a `.hl` span with the accent, which is how the
        # prototype's highlighter pen on "before you pay a cent" survives
        # without a literal colour anywhere in the output.
        _display(props["h1"], "h1", T["hero"], on_dark=True),
        *([_text(props["intro"], on_dark=True)] if props.get("intro") else []),
        *([_ticks(props["chips"], on_dark=True,
                  columns=len(props["chips"]))] if props.get("chips") else []),
    ], w_left, extra={"flex_gap": gap(22), "flex_justify_content": "center"})

    card = [
        _heading(props.get("form_heading", "Get your free mockup"), "h2",
                 T["h_small"]),
        *([_text(props["form_note"], small=True)]
          if props.get("form_note") else []),
        _form(props),
    ]
    if props.get("privacy"):
        card.append(widget("icon-list", {
            "icon_list": [repeater_item(text=props["privacy"],
                                        selected_icon=icon("fas fa-lock"),
                                        link=link(""))],
            "space_between": slider(0), "icon_size": slider(12),
        }, globals_={"icon_color": color_ref(C["muted"]),
                     "text_color": color_ref(C["muted"]),
                     "icon_typography_typography": typo_ref(T["meta"])}))

    # The prototype only offered WhatsApp and a booking link after a
    # successful submit. Without a branching result screen there is nowhere to
    # put them, and burying them is worse than showing them: a visitor who
    # would rather talk than type is a better lead than one who abandons.
    talk = [c for c in (props.get("whatsapp"), props.get("call")) if c]
    if talk:
        card.append(_rule(on_dark=False))
        card.append(_text(props.get("talk_label",
                                    "Prefer to talk first?"), small=True))
        card.append(_col([
            _button(talk[0]["label"], talk[0]["href"], "accent",
                    "fab fa-whatsapp"),
            *([_button(talk[1]["label"], talk[1]["href"], "ghost", None)]
              if len(talk) > 1 else []),
        ], extra={"flex_gap": gap(10)}))

    right = container(card, {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(14),
        "width": slider(w_right, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
        "padding": dims(28, 26, 30, 26),
        "padding_mobile": dims(22, 18, 24, 18),
        "border_radius": box(20),
        "background_background": "classic",
        **CARD_SHADOW,
    }, globals_={"background_color": color_ref(C["white"])})

    kids = [_row([left, right], gap_px=48, align="flex-start")]

    # The three promises that sat under the prototype's mockup preview. They
    # are the only part of that column worth keeping, so they run full width
    # beneath the row rather than competing with the form beside it.
    if props.get("notes"):
        panels = []
        w = _tracks([1] * len(props["notes"]), 16)[0]
        for n in props["notes"]:
            panels.append(_col([
                _eyebrow(n["label"], on_dark=True),
                _text(n["text"], small=True, on_dark=True),
            ], w, extra={
                "flex_gap": gap(4),
                "padding": dims(16, 18, 18, 18),
                "border_radius": box(12),
                "border_border": "solid", "border_width": box(1),
                "background_background": "classic",
            }))
            panels[-1]["settings"]["__globals__"] = {
                "background_color": color_ref(C["overlay"]),
                "border_color": color_ref(C["rule_dark"]),
            }
        kids.append(_row(panels, gap_px=16,
                         extra={"margin": dims(36, 0, 0, 0)}))

    return _sec(kids, dark=True, pad=dims(76, 0, 88, 0),
                anchor=props.get("anchor", "free-mockup-form"))


@block("wm.offerpanel")
def wm_offerpanel(props):
    """What the free mockup includes, beside a $0 ticket stating the terms.

    The ticket is the device that makes "free" believable: it lists what is
    not being asked for (payment details, obligation) in the same table as
    what is being given, so the reader can see the whole deal at once.
    """
    w_left, w_right = _tracks([54, 46], 48)

    rows = []
    for i, it in enumerate(props["items"]):
        rows.append(_row([
            widget("icon", {"selected_icon": icon("fas fa-circle-check"),
                            "size": slider(18), "align": "left",
                            "view": "default"},
                   globals_={"primary_color": color_ref(C["brand_on_dark"])}),
            _col([
                _heading(it["title"], "h3", T["h_small"], on_dark=True),
                _text(it["text"], small=True, on_dark=True),
            ], _tracks([8, 92], 14)[1], extra={"flex_gap": gap(4)}),
        ], gap_px=14, align="flex-start", extra={
            "padding": dims(18, 0, 18, 0),
            "border_border": "solid",
            "border_width": dims(1, 0, 0, 0) if i else dims(0, 0, 0, 0),
            "flex_wrap": "nowrap",
            "flex_direction_mobile": "row",
        }))
        if i:
            rows[-1]["settings"]["__globals__"] = {
                "border_color": color_ref(C["rule_dark"])}

    left = _col([
        *([_eyebrow(props["eyebrow"], on_dark=True)]
          if props.get("eyebrow") else []),
        _display(props["heading"], "h2", T["h_large"], on_dark=True),
        *([_text(props["intro"], on_dark=True)] if props.get("intro") else []),
        *rows,
    ], w_left, extra={"flex_gap": gap(14)})

    t = props["ticket"]
    ticket_rows = []
    for r in t["rows"]:
        ticket_rows.append(_row([
            _col([_text(r["label"], small=True, on_dark=True)],
                 _tracks([54, 46], 12)[0]),
            _col([widget("heading", {"title": r["value"], "header_size": "div",
                                     "align": "right"},
                         globals_={"title_color": color_ref(C["white"]),
                                   "typography_typography": typo_ref(T["meta"])})],
                 _tracks([54, 46], 12)[1]),
        ], gap_px=12, align="center", extra={"flex_wrap": "nowrap",
                                             "flex_direction_mobile": "row"}))

    right = container([
        _eyebrow(t.get("label", "Homepage mockup"), on_dark=True),
        _display(t["price"], "div", T["hero"], on_dark=True),
        _rule(),
        *ticket_rows,
        _button(t["cta"]["label"], t["cta"]["href"], "accent"),
        *([_text(t["note"], small=True, on_dark=True)]
          if t.get("note") else []),
    ], {
        "content_width": "full", "flex_direction": "column",
        "flex_gap": gap(12),
        "width": slider(w_right, "%"),
        "width_tablet": slider(100, "%"),
        "width_mobile": slider(100, "%"),
        "padding": dims(30, 28, 32, 28),
        "border_radius": box(20),
        "border_border": "solid", "border_width": box(1),
        "background_background": "classic",
    }, globals_={"background_color": color_ref(C["overlay"]),
                 "border_color": color_ref(C["rule_dark"])})

    return _sec([_row([left, right], gap_px=48, align="flex-start")],
                dark=True)


@block("wm.stickycta")
def wm_stickycta(props):
    """Fixed bottom bar, phone and tablet only, one action.

    Desktop keeps the form in view beside the copy; a phone scrolls it off in
    one flick, which is the whole case for this bar. Hidden on desktop so it
    cannot cover the footer on the screen that does not need it.
    """
    return container([_row([
        _button(props["cta"]["label"], props["cta"]["href"], "accent"),
    ], gap_px=10, align="center", justify="center",
        extra={"flex_wrap": "nowrap", "flex_direction_mobile": "row"})], {
        "content_width": "full", "flex_direction": "column",
        "padding": dims(10, 14, 10, 14),
        "background_background": "classic",
        "hide_desktop": "hidden-desktop",
        "_position": "fixed",
        "_offset_orientation_v": "end",
        "_offset_y_end": slider(0),
        "_offset_x": slider(0),
        "width": slider(100, "%"),
        "_z_index": 998,
        "border_border": "solid", "border_width": dims(1, 0, 0, 0),
    }, globals_={"background_color": color_ref("secondary"),
                 "border_color": color_ref(C["rule_dark"])})
