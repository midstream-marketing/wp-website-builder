"""
motion.py — scroll-reveal entrance animation as a compile stage.

Elementor gives every container an `animation` control that plays once as the
element scrolls into view. Nothing in the pipeline used it, so kits came out
completely static — which is a gap when the reference a client points at
reveals each section and staggers its cards on the way in.

This runs over compiled documents rather than inside the block factories, for
two reasons. A block factory sees one section and cannot know whether it is
the first on the page or the ninth, and stagger is a property of a row's
children as a set, not of any one card. Both are only knowable once the
document exists.

It is opt-in through `ir["motion"]`, so a kit built without it compiles
byte-identical to before.

    "motion": {"preset": "reveal"}

Rules that matter, all of them learned from how these animations go wrong:

- **The first section of a page is never animated.** An entrance animation
  starts from `opacity: 0`. Above the fold that is a visible flash of empty
  page before the hero appears, which reads as a slow site rather than a
  polished one.
- **Only one animation per branch.** Elementor animates a container and its
  children independently, so a fading section full of fading cards double-
  fades and the timings fight. A section that staggers its cards does not
  animate itself.
- **Headers and footers are left alone.** They are Theme Builder documents
  rendered on every page; an animated header re-runs its entrance on every
  navigation.
- **Fixed sections are left alone.** A sticky bottom call bar is on screen
  from the first paint, so a scroll-triggered entrance never fires and the
  bar simply stays invisible.
- **Delays stay short and bounded.** Past about half a second the last card in
  a row is still arriving after the reader has looked at it.
"""
from __future__ import annotations

# Stagger applied across the children of one row, in milliseconds. Capped so a
# wide grid does not leave its last card arriving long after the first.
STAGGER_MS = 120
MAX_DELAY_MS = 600

# Document types that render on every page and so must not animate.
CHROME = {"header", "footer"}

PRESETS = {
    # The default: sections rise into place, cards stagger across.
    "reveal": {"section": "fadeInUp", "child": "fadeInUp"},
    # Quieter — no vertical movement, for content-dense pages.
    "fade":   {"section": "fadeIn",   "child": "fadeIn"},
    "none":   {},
}


def _is_row(el: dict) -> bool:
    return (el.get("elType") == "container"
            and (el.get("settings") or {}).get("flex_direction") == "row")


def _card_row(el: dict) -> list | None:
    """The children of `el` if it is a row worth staggering, else None.

    A row of two is a split — staggering the two halves of a hero reads as a
    glitch rather than as motion. Three or more is a card grid, which is what
    stagger is for.
    """
    if not _is_row(el):
        return None
    kids = [k for k in (el.get("elements") or []) if k.get("elType") == "container"]
    return kids if len(kids) >= 3 else None


def _stagger(kids: list, animation: str) -> None:
    for i, k in enumerate(kids):
        s = k.setdefault("settings", {})
        s["animation"] = animation
        delay = min(i * STAGGER_MS, MAX_DELAY_MS)
        if delay:
            s["animation_delay"] = delay


def _first_card_row(el: dict, depth: int = 0):
    """Nearest descendant row that is a card grid, searched breadth-first.

    Depth-limited: a row buried deep inside a card is that card's internal
    layout, not the section's grid, and staggering it animates the wrong set.
    """
    if depth > 3:
        return None
    for child in (el.get("elements") or []):
        if _card_row(child) is not None:
            return child
    for child in (el.get("elements") or []):
        found = _first_card_row(child, depth + 1)
        if found is not None:
            return found
    return None


def apply_motion(docs: dict[str, dict], spec: dict | None) -> int:
    """Stamp entrance animations onto compiled documents. Returns the count."""
    if not spec:
        return 0
    name = spec.get("preset", "reveal")
    if name not in PRESETS:
        raise ValueError(
            f"Unknown motion preset {name!r}. Legal: {sorted(PRESETS)}")
    preset = PRESETS[name]
    if not preset:                       # "none" is a legal, empty preset
        return 0

    section_anim = spec.get("section", preset["section"])
    child_anim = spec.get("child", preset["child"])
    skip_first = spec.get("skip_first_section", True)
    n = 0

    for doc in docs.values():
        if doc.get("type") in CHROME:
            continue
        sections = doc.get("content", [])
        for i, sec in enumerate(sections):
            if skip_first and i == 0:
                continue
            # A fixed section — a sticky call bar — is already in the viewport
            # when the page loads, so a scroll-triggered entrance leaves it at
            # opacity 0 until something else scrolls past. It is chrome, like
            # a header, and the same rule applies.
            if (sec.get("settings") or {}).get("_position") == "fixed":
                continue
            row = _first_card_row(sec)
            if row is not None:
                # The cards carry the motion; the section stays still so the
                # two do not compound into a double fade.
                kids = _card_row(row)
                _stagger(kids, child_anim)
                n += len(kids)
            else:
                sec.setdefault("settings", {})["animation"] = section_anim
                n += 1
    return n
