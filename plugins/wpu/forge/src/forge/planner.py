"""
planner.py — intake + copy -> IR.

This is the deterministic floor. It guarantees every requested page
compiles to something sane even if no agent ever runs. The layout agent
overrides the block sequence per page; when it does, it emits the same
IR shape and everything downstream is unchanged.
"""
from __future__ import annotations


def _img(brand, role, fallback_subject=""):
    for i in (brand.get("images") or []):
        if i.get("role") == role:
            return {"url": i["url"], "alt": i.get("subject", fallback_subject)}
    imgs = brand.get("images") or []
    if imgs:
        return {"url": imgs[0]["url"], "alt": imgs[0].get("subject", fallback_subject)}
    # No third-party placeholder service: via.placeholder.com has since shut
    # down, and a dead URL in a delivered kit is worse than no image. An empty
    # url lets Elementor show its own placeholder, which is the honest signal
    # that a photo is still owed.
    return {"url": "", "alt": fallback_subject}


def _imgs(brand, role):
    """Every image tagged with `role`, in intake order."""
    out = []
    for i in (brand.get("images") or []):
        if i.get("role") != role:
            continue
        item = {"url": i["url"], "alt": i.get("subject", "")}
        if i.get("caption"):
            item["caption"] = i["caption"]
        out.append(item)
    return out


def _copy(copy, page, slot, default=""):
    return (copy.get(page, {}) or {}).get(slot, default)


def _merged(copy, flag):
    """Site-level layout switches, e.g. folding About into Home when the
    client wants a three-page site instead of five."""
    return bool((copy.get("_site", {}) or {}).get(flag))


def _service_cards(services, copy_key=None):
    """Photo cards when every service carries an image, icon cards otherwise.
    A mixed list would render as a ragged grid, so it falls back wholesale."""
    return all(s.get("image") for s in services)


def _services_block(services, heading, intro="", eyebrow="", columns=3, bg=None,
                    caption_only=False, limit=None):
    # A home page that leads with every service reads as a catalogue. `limit`
    # shows the flagship few there and leaves the full set to the services
    # page; unset, the whole list renders as before.
    if limit:
        services = services[:limit]
    if _service_cards(services):
        block = "services.cards"
        items = [{"title": s["name"], "text": s.get("summary", ""),
                  "image": {"url": s["image"], "alt": s.get("image_alt", s["name"])},
                  "href": f"/services/{s['slug']}" if s.get("own_page") else ""}
                 for s in services]
    else:
        block = "services.grid"
        items = [{"title": s["name"], "text": s.get("summary", ""),
                  "icon": s.get("icon", "fas fa-wrench"),
                  "href": f"/services/{s['slug']}" if s.get("own_page") else ""}
                 for s in services]
    props = {"heading": heading, "columns": columns, "items": items}
    if eyebrow:
        props["eyebrow"] = eyebrow
    if intro:
        props["intro"] = intro
    if bg:
        props["bg"] = bg
    if caption_only and block == "services.cards":
        props["caption_only"] = True
        props["image_height"] = 260
    return {"block": block, "props": props}


def plan(intake: dict, copy: dict | None = None) -> dict:
    copy = copy or {}
    biz = intake["business"]
    brand = intake.get("brand", {}) or {}
    contact = intake["contact"]
    services = intake["services"]
    areas = intake.get("areas_served", []) or []
    cta = {"label": biz.get("primary_cta", "Get a Free Quote"), "href": "/contact"}
    call = {"label": contact.get("phone_display") or contact["phone"],
            "href": f"tel:{contact['phone']}"}

    # Shared content pools. Empty pools simply drop their block, so a client
    # who supplies no reviews still gets a coherent page.
    gallery_imgs = _imgs(brand, "gallery")
    gallery_pairs = copy.get("gallery", {}).get("pairs", [])
    reviews = copy.get("reviews", {}).get("items", [])
    faqs = copy.get("faq", {}).get("faqs", [])
    finance_tiers = copy.get("financing", {}).get("tiers", [])
    way_points = copy.get("home", {}).get("way_points", [])
    # Shared media for the two sections the reference site repeats on every
    # page: the process band and the closing estimate split.
    cta_img = _img(brand, "team", f"{biz['name']} crew on site")
    proc_bg = _img(brand, "background", f"{biz['name']} work in progress")
    # A shortcode slot beats authored testimonials: the page shows real
    # reviews or nothing at all.
    reviews_shortcode = (copy.get("_site", {}) or {}).get("reviews_shortcode", "")
    # Third-party proof marks the client actually holds, supplied as images.
    trust_badges = (copy.get("_site", {}) or {}).get("badges", [])
    # Addon widgets are opt-in: a kit built without them stays installable on
    # a site that has only Elementor and Pro.
    use_addon = bool((copy.get("_site", {}) or {}).get("addons"))
    before_after = copy.get("gallery", {}).get("compare", [])
    # The repeating band between sections. Defaults to the CTA plus the trust
    # points, which is what the reference sites put in theirs.
    marquee_items = copy.get("home", {}).get("marquee") or (
        [biz.get("primary_cta", "Get a Free Quote")]
        + [u for u in (biz.get("usp") or [])[:3]]
        if _merged(copy, "layout_impact") else [])

    def home_feature():
        """Photographic hero + capture form + chip-led sections.

        Selected with `_site.layout: "feature"`. Sections with no supplied
        content are dropped rather than filled — a brand-logo strip or a
        testimonial row with nothing real behind it is worse than its absence.
        """
        k = "home"
        return [
            {"block": "hero.feature", "props": {
                "eyebrow": _copy(copy, k, "eyebrow", ""),
                "eyebrow_icon": "fas fa-location-dot",
                "h1": _copy(copy, k, "h1", biz["type"]),
                "intro": _copy(copy, k, "intro", biz["description"]),
                "ticks": (biz.get("usp") or [])[:4],
                "cta": cta, "cta2": call,
                "image": _img(brand, "hero", f"{biz['name']} owner")
            }},
            *( [{"block": "form.bar", "props": {
                "heading": _copy(copy, k, "form_heading", biz.get("primary_cta", "Get a Quote")),
                "ticks": copy.get(k, {}).get("form_ticks", []),
                "fields": copy.get(k, {})["quick_fields"],
                "email": contact["email"], "business": biz["name"],
                "form_name": "Quick Quote",
                "submit_label": _copy(copy, k, "form_submit", "Submit"),
                "success_message": _copy(copy, "contact", "success_message", "")
            }}] if copy.get(k, {}).get("quick_fields") else [] ),
            *( [{"block": "about.collage", "props": {
                "eyebrow": _copy(copy, k, "story_eyebrow", "About"),
                "heading": _copy(copy, k, "story_heading", f"About {biz['name']}"),
                "body": _copy(copy, k, "story_body", ""),
                "images": _imgs(brand, "about") + _imgs(brand, "team") + _imgs(brand, "service"),
                "cta": cta
            }}] if _copy(copy, k, "story_body") else [] ),
            _services_block(
                services,
                _copy(copy, k, "services_heading", "Our Services"),
                intro=_copy(copy, k, "services_intro", ""),
                eyebrow="Our Services", caption_only=False),
            *( [{"block": "why.panel", "props": {
                "eyebrow": "Why Choose Us",
                "heading": _copy(copy, k, "about_heading", f"Why choose {biz['name']}"),
                "intro": _copy(copy, k, "why_intro", ""),
                "highlight": copy.get(k, {}).get("highlight", {}),
                "items": way_points,
                "image": _img(brand, "service", f"{biz['name']} at work")
            }}] if way_points and copy.get(k, {}).get("highlight") else [] ),
            *( [{"block": "areas.chips", "props": {
                "eyebrow": "Service Areas",
                "heading": _copy(copy, k, "areas_heading", "Areas We Serve"),
                "intro": _copy(copy, k, "areas_intro", ""),
                "areas": [{"name": a["name"]} for a in areas],
                "map_query": contact.get("map_query", ""),
                "zoom": 9, "bg": "surface"
            }}] if areas else [] ),
            *( [{"block": "faq.split", "props": {
                "eyebrow": "FAQs",
                "heading": _copy(copy, k, "faq_heading", "Frequently Asked Questions"),
                "intro": _copy(copy, k, "faq_intro", ""),
                "items": faqs, "cta": cta, "bg": "white"
            }}] if faqs else [] ),
            *( [{"block": "gallery.grid", "props": {
                "eyebrow": "Our Work",
                "heading": _copy(copy, k, "gallery_heading", "Recent Work"),
                "intro": _copy(copy, k, "gallery_intro", ""),
                "columns": 3, "items": gallery_imgs, "bg": "surface"
            }}] if gallery_imgs else [] ),
            {"block": "cta.panel", "props": {
                "heading": _copy(copy, k, "cta_heading", "Ready to get started?"),
                "text": _copy(copy, k, "cta_text", ""),
                "image": cta_img,
                "cta": cta, "cta2": call,
                "bg": "white"
            }},
        ]

    def home_impact():
        """Dark-ground layout: heavy hero, proof split, dark step band, map
        panel, a real-reviews slot, FAQ and a photographic closing CTA."""
        k = "home"
        return [
            {"block": "hero.impact", "props": {
                "eyebrow": _copy(copy, k, "eyebrow", ""),
                "h1": _copy(copy, k, "h1", biz["type"]),
                "intro": _copy(copy, k, "intro", biz["description"]),
                "badges": copy.get(k, {}).get("badges", []),
                "cta": cta, "cta2": call,
                "image": _img(brand, "hero", f"{biz['name']} plumber at work")
            }},
            # Proof strip directly under the hero. `badges.strip` wants logo
            # images; `credentials.bar` states facts as text, which is what a
            # trade with a licence number and no third-party marks actually
            # has to show.
            *( [{"block": "credentials.bar", "props": {
                "items": (copy.get("_site", {}) or {})["credentials"],
            }}] if (copy.get("_site", {}) or {}).get("credentials") else [] ),
            # Capture form high on the page, the way the lead-gen references
            # place it. Only when the copy supplies the fields.
            *( [{"block": "form.bar", "props": {
                "heading": _copy(copy, k, "form_heading", biz.get("primary_cta", "Get a Quote")),
                "ticks": copy.get(k, {}).get("form_ticks", []),
                "fields": copy.get(k, {})["quick_fields"],
                "email": contact["email"], "business": biz["name"],
                "form_name": "Quick Quote",
                "submit_label": _copy(copy, k, "form_submit", "Submit"),
                "success_message": _copy(copy, "contact", "success_message", "")
            }}] if copy.get(k, {}).get("quick_fields") else [] ),
            *( [{"block": "badges.strip", "props": {
                "heading": _copy(copy, k, "badges_heading", ""),
                "items": trust_badges,
                "use_addon": use_addon,
                "bg": "white",
            }}] if trust_badges else [] ),
            *( [{"block": "why.split", "props": {
                "eyebrow": "Why Choose Us",
                "heading": _copy(copy, k, "about_heading", f"Why choose {biz['name']}"),
                "intro": _copy(copy, k, "why_intro", ""),
                "ticks": copy.get(k, {}).get("why_ticks", []),
                "badges": copy.get(k, {}).get("why_badges", []),
                "image": _img(brand, "about", f"{biz['name']} at work"),
                "cta": cta
            }}] if copy.get(k, {}).get("why_ticks") else [] ),
            *( [{"block": "marquee.strip", "props": {
                "items": marquee_items, "fill": "accent",
            }}] if marquee_items else [] ),
            _services_block(
                services,
                _copy(copy, k, "services_heading", "Our Services"),
                intro=_copy(copy, k, "services_intro", ""),
                eyebrow="Services We Provide",
                limit=(copy.get("_site", {}) or {}).get("home_services_limit")),
            {"block": "process.split", "props": {
                "eyebrow": "How It Works",
                "heading": _copy(copy, k, "process_heading", "How It Works"),
                "intro": _copy(copy, k, "process_intro", ""),
                "image": _img(brand, "service", f"{biz['name']} on site"),
                "cta": cta,
                "steps": copy.get(k, {}).get("steps", [])
            }},
            *( [{"block": "gallery.grid", "props": {
                "eyebrow": "Project Gallery",
                "heading": _copy(copy, k, "gallery_heading", "Our Recent Work"),
                "intro": _copy(copy, k, "gallery_intro", ""),
                "columns": 3, "items": gallery_imgs[:6],
                "cta": {"label": "View the full gallery", "href": "/gallery"}
            }}] if gallery_imgs else [] ),
            *( [{"block": "areas.chips", "props": {
                "eyebrow": "Service Areas",
                "heading": _copy(copy, k, "areas_heading", "Areas We Serve"),
                "intro": _copy(copy, k, "areas_intro", ""),
                "areas": [{"name": a["name"]} for a in areas],
                "map_query": contact.get("map_query", ""),
                "zoom": 9, "panel": "dark", "bg": "surface",
                "cta": {"label": "Explore service areas", "href": "/areas"}
            }}] if areas else [] ),
            *( [{"block": "reviews.embed", "props": {
                "eyebrow": "Testimonials",
                "heading": _copy(copy, k, "reviews_heading", "What Our Customers Say"),
                "intro": _copy(copy, k, "reviews_intro", ""),
                "shortcode": reviews_shortcode,
                "note": _copy(copy, k, "reviews_note", ""),
                "bg": "white"
            }}] if reviews_shortcode else [] ),
            *( [{"block": "faq.accordion", "props": {
                "heading": _copy(copy, k, "faq_heading", "Frequently Asked Questions"),
                "items": faqs[:8], "bg": "surface"
            }}] if faqs else [] ),
            {"block": "cta.panel", "props": {
                "heading": _copy(copy, k, "cta_heading", "Ready to get started?"),
                "text": _copy(copy, k, "cta_text", ""),
                "background": _img(brand, "background", f"{biz['name']} work"),
                "cta": cta, "cta2": call,
                "bg": "white"
            }},
        ]

    pages = []

    for p in intake["pages"]:
        key, ptype = p["key"], p["type"]
        blocks = []

        if ptype == "archive":
            # One document per collection, not per entry. Display conditions
            # (which post type it applies to) live in post meta and are set by
            # the importer, not in the template JSON.
            blocks = [{"block": "archive.posts", "props": {
                "intro": _copy(copy, key, "intro", ""),
                "columns": copy.get(key, {}).get("columns", 3),
                "per_page": copy.get(key, {}).get("per_page", 9),
                "more_label": _copy(copy, key, "more_label", "Read More"),
            }}]

        elif ptype == "single-post":
            blocks = [{"block": "single.post", "props": {
                "show_meta": copy.get(key, {}).get("show_meta", True),
                "cta": {"heading": _copy(copy, key, "cta_heading",
                                         f"Work with {biz['name']}"),
                        "text": _copy(copy, key, "cta_text", ""),
                        "cta": cta},
            }}]

        elif ptype == "header":
            strip = []
            if _merged(copy, "layout_feature"):
                if intake.get("seo", {}).get("primary_location"):
                    strip.append({"text": intake["seo"]["primary_location"],
                                  "icon": "fas fa-location-dot"})
                for h in contact.get("hours", [])[:1]:
                    strip.append({"text": h, "icon": "far fa-clock"})
                strip.append({"text": contact["email"], "icon": "fas fa-envelope",
                              "href": f"mailto:{contact['email']}"})
            blocks = [{"block": "header.simple", "props": {
                "logo": brand.get("logo", ""), "business": biz["name"],
                "menu": "main-menu", "cta": call,
                "topbar": strip}}]

        elif ptype == "footer":
            groups = [
                {"title": "Services", "items": [
                    {"text": s["name"], "href": f"/services/{s.get('slug','')}"} for s in services[:6]]},
            ]
            if areas:
                groups.append({"title": "Areas We Serve", "items": [
                    {"text": a["name"], "href": f"/areas/{a.get('slug','')}"} for a in areas[:6]]})
            groups.append({"title": "Contact", "items": [
                {"text": contact.get("phone_display") or contact["phone"],
                 "href": f"tel:{contact['phone']}"},
                {"text": contact["email"], "href": f"mailto:{contact['email']}"},
                *( [{"text": contact["address"], "href": ""}] if contact.get("address") else [] ),
            ]})
            blocks = [{"block": "footer.simple", "props": {
                "logo": brand.get("logo_light") or brand.get("logo", ""),
                "business": biz["name"],
                "blurb": _copy(copy, key, "blurb", biz["description"][:180]),
                "socials": contact.get("socials", []),
                "groups": groups,
                "map_query": contact.get("map_query", ""),
                "map_title": _copy(copy, key, "map_title", "Where We Work"),
                "copyright": f"© {biz['name']}. All rights reserved."
            }}]

        elif key == "home" and _merged(copy, "layout_impact"):
            blocks = home_impact()

        elif key == "home" and _merged(copy, "layout_feature"):
            blocks = home_feature()

        elif key == "home":
            blocks = [
                # `hero_style: split` puts a person beside the headline — used
                # when the owner is the proof, not the finished work.
                ({"block": "hero.split", "props": {
                    "eyebrow": _copy(copy, key, "eyebrow", ""),
                    "h1": _copy(copy, key, "h1", biz["type"]),
                    "intro": _copy(copy, key, "intro", biz["description"]),
                    "cta": cta, "cta2": call,
                    "image": _img(brand, "hero", f"{biz['name']} owner"),
                    "dark": True
                 }} if _merged(copy, "hero_split") else
                 {"block": "hero.banner", "props": {
                    "h1": _copy(copy, key, "banner", biz["name"]),
                    "image": _img(brand, "hero", f"{biz['name']} finished work"),
                    "pad": 170, "overlay": 0.34
                 }}),
                *( [{"block": "intro.split", "props": {
                    "statement": _copy(copy, key, "statement", ""),
                    "badges": copy.get(key, {}).get("badges", []),
                    "heading": _copy(copy, key, "position_heading", biz["type"]),
                    "body": _copy(copy, key, "position_body", ""),
                    "cta": cta, "cta2": call
                }}] if _copy(copy, key, "position_body") else [] ),
                {"block": "trust.bar", "props": {"items": [
                    {"text": u, "icon": "fas fa-circle-check"} for u in (biz.get("usp") or [])[:4]
                ] or [{"text": c, "icon": "fas fa-award"} for c in (biz.get("credentials") or [])[:4]]}},
                _services_block(
                    services,
                    _copy(copy, key, "services_heading", "Our Services"),
                    intro=_copy(copy, key, "services_intro", ""),
                    eyebrow="What We Do", caption_only=True),
                # The reference layout leads with a photo beside circled-check
                # points rather than a plain bulleted split.
                ({"block": "checklist.split", "props": {
                    "eyebrow": "Why Us",
                    "heading": _copy(copy, key, "about_heading", f"The {biz['name']} Way"),
                    "intro": _copy(copy, key, "about_body", ""),
                    "items": way_points,
                    "image": _img(brand, "about", f"{biz['name']} at work"),
                    "cta": cta
                }} if way_points else
                 {"block": "about.split", "props": {
                    "eyebrow": "Why Us",
                    "heading": _copy(copy, key, "about_heading", f"Why choose {biz['name']}"),
                    "body": _copy(copy, key, "about_body", biz["description"]),
                    "points": biz.get("credentials", [])[:5],
                    "image": _img(brand, "about", f"{biz['name']} at work"),
                    "cta": cta
                 }}),
                {"block": "process.band", "props": {
                    "heading": _copy(copy, key, "process_heading", "Our Installation Process"),
                    "background": _img(brand, "background", "Finished turf lawn"),
                    "steps": copy.get(key, {}).get("steps", [
                        {"title": "Get in touch", "text": "Call or send the form and tell us what you need."},
                        {"title": "Free assessment", "text": "We assess the job and give you a clear written quote."},
                        {"title": "Work done right", "text": "Licensed, insured, and tidy — finished on schedule."},
                    ])
                }},
                *( [{"block": "faq.accordion", "props": {
                    "heading": _copy(copy, key, "faq_heading", "Frequently Asked Questions"),
                    "items": faqs[:8], "bg": "white"
                }}] if faqs else [] ),
                # Counts are only emitted when the client supplies real ones.
                # A default here would publish invented figures.
                *( [{"block": "stats.band", "props": {
                    "background": _img(brand, "background", f"{biz['name']} work in progress"),
                    "items": copy.get(key, {})["stats"]}}]
                   if copy.get(key, {}).get("stats") else [] ),
                *( [{"block": "gallery.grid", "props": {
                    "eyebrow": "Our Work",
                    "heading": _copy(copy, key, "gallery_heading", "Recent Installs"),
                    "intro": _copy(copy, key, "gallery_intro", ""),
                    "columns": 3, "items": gallery_imgs[:6],
                    "cta": {"label": "See the full gallery", "href": "/gallery"}
                }}] if gallery_imgs else [] ),
                *( [{"block": "reviews.grid", "props": {
                    "eyebrow": "Reviews",
                    "heading": _copy(copy, key, "reviews_heading", "What Our Customers Say"),
                    "columns": 3,
                    "items": reviews[:3]
                }}] if reviews else [] ),
                *( [{"block": "areas.chips" if _merged(copy, "layout_feature")
                     else "areas.grid", "props": {
                    "eyebrow": "Service Area",
                    "heading": _copy(copy, key, "areas_heading", "Areas We Serve"),
                    "intro": _copy(copy, key, "areas_intro", ""),
                    "areas": [{"name": a["name"],
                               "href": f"/areas/{a['slug']}" if a.get("own_page") else ""}
                              for a in areas],
                    "map_query": contact.get("map_query", ""),
                    "columns": 4, "bg": "white"
                }}] if areas and not _merged(copy, "areas_into_services") else [] ),
                # About merged into the home page when the site has no
                # separate About route.
                *( [{"block": "about.split", "props": {
                    "eyebrow": _copy(copy, key, "story_eyebrow", "About"),
                    "heading": _copy(copy, key, "story_heading", f"About {biz['name']}"),
                    "body": _copy(copy, key, "story_body", ""),
                    "points": copy.get(key, {}).get("story_points", []),
                    "image": _img(brand, "team", f"{biz['name']} owner at work"),
                    "reverse": True, "bg": "surface"
                }}] if _copy(copy, key, "story_body") else [] ),
                *( [{"block": "note.panel", "props": {
                    "heading": _copy(copy, key, "standard_heading", "Our standard"),
                    "text": _copy(copy, key, "standard_text", ""),
                    "bg": "surface"
                }}] if _copy(copy, key, "standard_text") else [] ),
                {"block": "cta.split", "props": {
                    "eyebrow": biz.get("primary_cta", "Get a Free Quote"),
                    "heading": _copy(copy, key, "cta_heading", "Ready to get started?"),
                    "text": _copy(copy, key, "cta_text", ""),
                    "image": _img(brand, "team", f"{biz['name']} crew on site"),
                    "cta": cta, "cta2": call
                }},
            ]

        elif key == "about":
            blocks = [
                {"block": "hero.banner", "props": {
                    "h1": _copy(copy, key, "h1", f"About {biz['name']}"),
                    "intro": _copy(copy, key, "intro", biz["description"]),
                    "cta": cta,
                    "image": _img(brand, "team", f"{biz['name']} team"),
                    "dark": True
                }},
                {"block": "about.split", "props": {
                    "heading": _copy(copy, key, "story_heading", "Our story"),
                    "body": _copy(copy, key, "story_body", biz["description"]),
                    "points": biz.get("credentials", []),
                    "image": _img(brand, "about", f"{biz['name']} workshop"),
                    "reverse": True
                }},
                # Counts are claims about the business, not layout. Emitted
                # only when the client supplies real figures — a default here
                # publishes invented ones on a live site.
                *( [{"block": "stats.band", "props": {
                    "background": proc_bg,
                    "items": copy.get(key, {})["stats"]}}]
                   if copy.get(key, {}).get("stats") else [] ),
                {"block": "cta.panel" if _merged(copy, "layout_feature") else "cta.split",
                 "props": {"image": cta_img, "cta2": call,
                    "heading": _copy(copy, key, "cta_heading", "Work with us"),
                    "cta": cta}},
            ]

        elif key == "services":
            blocks = [
                {"block": "hero.banner", "props": {
                    "h1": _copy(copy, key, "h1", "Our Services"),
                    "intro": _copy(copy, key, "intro", ""),
                    "cta": cta, "image": _img(brand, "service"), "dark": True}},
                # Photo cards are the overview; when the brief supplies detailed
                # bulleted categories they cover the same ground, so only one
                # runs. `_site.keep_services_grid` opts into both, for a client
                # whose photographs are the selling point and whose category
                # lists exist to prove breadth rather than to repeat them.
                *( [_services_block(
                    services,
                    _copy(copy, key, "grid_heading", "What we offer"),
                    intro=_copy(copy, key, "grid_intro", ""),
                    columns=3, bg="white")]
                   if not copy.get(key, {}).get("categories")
                   or _merged(copy, "keep_services_grid") else [] ),
                # Category cards with bullet lists, when the brief supplies them.
                *( [{"block": "list.cards", "props": {
                    "heading": _copy(copy, key, "categories_heading", ""),
                    "intro": _copy(copy, key, "categories_intro", ""),
                    "columns": 2,
                    "items": copy.get(key, {})["categories"],
                    "bg": "surface"
                }}] if copy.get(key, {}).get("categories") else [] ),
                *( [{"block": "note.panel", "props": {
                    "heading": _copy(copy, key, "note_heading", "Scope note"),
                    "text": _copy(copy, key, "note_text", ""),
                    "bg": "surface"
                }}] if _copy(copy, key, "note_text") else [] ),
                # Service Area merged in when the site has no separate route.
                *( [{"block": "areas.chips" if _merged(copy, "layout_feature")
                     else "areas.grid", "props": {
                    "eyebrow": "Service Area",
                    "heading": _copy(copy, key, "areas_heading", "Where We Work"),
                    "intro": _copy(copy, key, "areas_intro", ""),
                    "areas": [{"name": a["name"], "href": ""} for a in areas],
                    "map_query": contact.get("map_query", ""),
                    "columns": 4, "bg": "white", "zoom": 9
                }}] if areas and _merged(copy, "areas_into_services") else [] ),
                {"block": "process.band", "props": {"background": proc_bg,
                    "heading": _copy(copy, key, "process_heading", "How It Works"),
                    "steps": copy.get("home", {}).get("steps", [
                        {"title": "Get in touch", "text": "Tell us what you need."},
                        {"title": "Free assessment", "text": "A clear written quote before any work."},
                        {"title": "Work done right", "text": "Finished on schedule, cleaned up after."},
                    ])}},
                # The feature layout carries the FAQ on the home page, so a
                # second copy here would just repeat it.
                *( [{"block": "faq.accordion", "props": {
                    "heading": "Common questions", "items": faqs[:6]}}]
                   if faqs and not _merged(copy, "layout_feature") else [] ),
                {"block": "cta.panel" if _merged(copy, "layout_feature") else "cta.split",
                 "props": {"image": cta_img, "cta2": call,
                    "heading": _copy(copy, key, "cta_heading", "Not sure what you need?"),
                    "cta": cta}},
            ]

        elif key == "gallery":
            blocks = [
                {"block": "hero.banner", "props": {
                    "eyebrow": "Our Work",
                    "h1": _copy(copy, key, "h1", "Gallery"),
                    "intro": _copy(copy, key, "intro", ""),
                    "cta": cta, "cta2": call,
                    "image": _img(brand, "hero"), "dark": True}},
                # A real comparison slider when the addon is available;
                # side-by-side pairs otherwise. Four of eight references show
                # before/after, and it is the most persuasive proof a trade
                # site has once the photos are real.
                *( [{"block": "gallery.compare", "props": {
                    "eyebrow": "Transformations",
                    "heading": _copy(copy, key, "pairs_heading", "Before & After"),
                    "intro": _copy(copy, key, "pairs_intro", ""),
                    "items": before_after,
                }}] if before_after and use_addon else [] ),
                *( [{"block": "gallery.pairs", "props": {
                    "eyebrow": "Transformations",
                    "heading": _copy(copy, key, "pairs_heading", "Before & After"),
                    "intro": _copy(copy, key, "pairs_intro", ""),
                    "items": gallery_pairs}}] if gallery_pairs else [] ),
                *( [{"block": "gallery.grid", "props": {
                    "heading": _copy(copy, key, "grid_heading", "Recent Projects"),
                    "columns": 3, "items": gallery_imgs, "bg": "white"}}]
                   if gallery_imgs else [] ),
                {"block": "cta.panel" if _merged(copy, "layout_feature") else "cta.split",
                 "props": {"image": cta_img, "cta2": call,
                    "heading": _copy(copy, key, "cta_heading", "Want yours to look like this?"),
                    "text": _copy(copy, key, "cta_text", ""),
                    "cta": cta}},
            ]

        elif key == "financing":
            blocks = [
                {"block": "hero.banner", "props": {
                    "eyebrow": "Financing",
                    "h1": _copy(copy, key, "h1", "Financing Options"),
                    "intro": _copy(copy, key, "intro", ""),
                    "cta": cta, "cta2": call,
                    "image": _img(brand, "about"), "dark": True}},
                *( [{"block": "pricing.cards", "props": {
                    "heading": _copy(copy, key, "tiers_heading", "Ways to pay"),
                    "intro": _copy(copy, key, "tiers_intro", ""),
                    "items": finance_tiers}}] if finance_tiers else [] ),
                {"block": "process.band", "props": {"background": proc_bg,
                    "heading": _copy(copy, key, "process_heading", "How approval works"),
                    "steps": copy.get(key, {}).get("steps", [
                        {"title": "Apply online", "text": "A short application, no impact on your credit score to check."},
                        {"title": "Get a decision", "text": "Most applicants hear back in minutes."},
                        {"title": "Book your install", "text": "Approved funds go straight to your project."},
                    ])}},
                *( [{"block": "faq.accordion", "props": {
                    "heading": "Financing questions",
                    "items": copy.get(key, {}).get("faqs", []), "bg": "white"}}]
                   if copy.get(key, {}).get("faqs") else [] ),
                {"block": "cta.panel" if _merged(copy, "layout_feature") else "cta.split",
                 "props": {"image": cta_img, "cta2": call,
                    "heading": _copy(copy, key, "cta_heading", "Find out what you qualify for"),
                    "cta": cta}},
            ]

        elif key == "reviews":
            blocks = [
                {"block": "hero.banner", "props": {
                    "eyebrow": "Reviews",
                    "h1": _copy(copy, key, "h1", "What Our Customers Say"),
                    "intro": _copy(copy, key, "intro", ""),
                    "cta": cta, "cta2": call,
                    "image": _img(brand, "team"), "dark": True}},
                *( [{"block": "stats.band", "props": {
                    "background": proc_bg,
                    "items": copy.get(key, {})["stats"]}}]
                   if copy.get(key, {}).get("stats") else [] ),
                *( [{"block": "reviews.grid", "props": {
                    "heading": _copy(copy, key, "grid_heading", "Verified customer reviews"),
                    "columns": 3, "items": reviews}}] if reviews else [] ),
                # A live review widget beats authored cards: the page shows
                # what the business actually received, or nothing.
                *( [{"block": "reviews.embed", "props": {
                    "heading": _copy(copy, key, "grid_heading", "Client Reviews"),
                    "intro": _copy(copy, key, "grid_intro", ""),
                    "shortcode": reviews_shortcode,
                    "note": _copy(copy, key, "reviews_note", ""),
                    "bg": "white"}}]
                   if reviews_shortcode and not reviews else [] ),
                {"block": "cta.panel" if _merged(copy, "layout_feature") else "cta.split",
                 "props": {"image": cta_img, "cta2": call,
                    "heading": _copy(copy, key, "cta_heading", "Join them"),
                    "cta": cta}},
            ]

        elif key in ("estimate", "schedule", "booking"):
            details = [
                {"text": contact.get("phone_display") or contact["phone"],
                 "icon": "fas fa-phone", "href": f"tel:{contact['phone']}"},
                {"text": contact["email"], "icon": "fas fa-envelope",
                 "href": f"mailto:{contact['email']}"},
            ]
            for h in contact.get("hours", []):
                details.append({"text": h, "icon": "far fa-clock"})
            blocks = [
                {"block": "hero.banner", "props": {
                    "eyebrow": "Free Estimate",
                    "h1": _copy(copy, key, "h1", biz.get("primary_cta", "Get a Free Quote")),
                    "intro": _copy(copy, key, "intro", ""),
                    "cta": call, "image": _img(brand, "hero"), "dark": True}},
                {"block": "trust.bar", "props": {"items": [
                    {"text": u, "icon": "fas fa-circle-check"} for u in (biz.get("usp") or [])[:4]
                ]}},
                {"block": "contact.block", "props": {
                    "eyebrow": "Tell us about the project",
                    "heading": _copy(copy, key, "form_heading", "Request your free estimate"),
                    "intro": _copy(copy, key, "form_intro", ""),
                    "details": details,
                    "email": contact["email"],
                    "business": biz["name"],
                    "form_name": "Free Estimate",
                    "submit_label": _copy(copy, key, "form_submit",
                                          biz.get("primary_cta", "Send Request")),
                    # Without these two the page silently fell back to the
                    # generic four-field form and the default success message,
                    # discarding whatever the brief specified for the one page
                    # whose entire job is the form.
                    "fields": copy.get(key, {}).get("fields", []),
                    "success_message": _copy(copy, key, "success_message",
                                             "Thanks — we'll be in touch shortly."),
                    "bg": "white"}},
                {"block": "process.band", "props": {"background": proc_bg,
                    "heading": _copy(copy, key, "process_heading", "What happens next"),
                    "steps": copy.get(key, {}).get("steps", [
                        {"title": "We call you back", "text": "Usually the same business day."},
                        {"title": "On-site measure", "text": "We measure, photograph and talk through options."},
                        {"title": "Fixed written quote", "text": "Itemised, with no obligation to proceed."},
                    ])}},
                {"block": "cta.panel" if _merged(copy, "layout_feature") else "cta.split",
                 "props": {"image": cta_img, "cta2": call,
                    "heading": _copy(copy, key, "cta_heading", "Prefer to talk it through?"),
                    "cta": call}},
            ]

        elif key.startswith("service:"):
            slug = key.split(":", 1)[1]
            svc = next((s for s in services if s.get("slug") == slug), {"name": slug})
            blocks = [
                {"block": "hero.banner", "props": {
                    "eyebrow": "Service",
                    "h1": _copy(copy, key, "h1", svc["name"]),
                    "intro": _copy(copy, key, "intro", svc.get("summary", "")),
                    "cta": cta, "cta2": call,
                    "image": _img(brand, "service", svc["name"]), "dark": True}},
                *( [{"block": "about.split", "props": {
                    "heading": _copy(copy, key, "detail_heading", f"About our {svc['name'].lower()}"),
                    "body": _copy(copy, key, "detail_body", svc.get("detail", svc.get("summary", ""))),
                    "points": biz.get("credentials", [])[:4],
                    "image": _img(brand, "service", svc["name"]), "cta": cta}}]
                   if _copy(copy, key, "detail_body") or not copy.get(key, {}).get("categories")
                   else [] ),
                # A trade page whose scope is a long list of named jobs reads
                # far better grouped than as prose — and every one of those
                # job names is a search term worth having on the page.
                *( [{"block": "list.cards", "props": {
                    "heading": _copy(copy, key, "categories_heading", ""),
                    "intro": _copy(copy, key, "categories_intro", ""),
                    "columns": copy.get(key, {}).get("columns", 2),
                    "items": copy.get(key, {})["categories"],
                    "bg": "surface"}}]
                   if copy.get(key, {}).get("categories") else [] ),
                {"block": "process.band", "props": {"background": proc_bg,
                    "heading": "How we work",
                    "steps": [
                        {"title": "Book a visit", "text": "Pick a time that suits you."},
                        {"title": "Clear quote", "text": "Fixed pricing before any work starts."},
                        {"title": "Job complete", "text": "Guaranteed workmanship, cleaned up after."},
                    ]}},
                {"block": "faq.accordion", "props": {
                    "heading": "Common questions",
                    "items": copy.get(key, {}).get("faqs", [
                        {"q": f"How much does {svc['name'].lower()} cost?",
                         "a": "Pricing depends on scope. We give a written quote before starting."},
                    ])}},
                {"block": "cta.panel" if _merged(copy, "layout_feature") else "cta.split",
                 "props": {"image": cta_img, "cta2": call,
                    "heading": _copy(copy, key, "cta_heading", f"Book {svc['name'].lower()} today"),
                    "cta": cta}},
            ]

        elif key.startswith("area:"):
            slug = key.split(":", 1)[1]
            area = next((a for a in areas if a.get("slug") == slug), {"name": slug})
            blocks = [
                {"block": "hero.banner", "props": {
                    "eyebrow": "Service Area",
                    "h1": _copy(copy, key, "h1", f"{biz['type']} in {area['name']}"),
                    "intro": _copy(copy, key, "intro", ""),
                    "cta": cta, "cta2": call,
                    "image": _img(brand, "hero", area["name"]), "dark": True}},
                {"block": "services.grid", "props": {
                    "heading": _copy(copy, key, "services_heading", f"What we do in {area['name']}"),
                    "columns": 3,
                    "items": [{"title": s["name"], "text": s.get("summary", ""),
                               "icon": s.get("icon", "fas fa-wrench"), "href": ""}
                              for s in services]}},
                {"block": "about.split", "props": {
                    "heading": _copy(copy, key, "local_heading", f"Local to {area['name']}"),
                    "body": _copy(copy, key, "local_body", ""),
                    "points": area.get("landmarks", [])[:5],
                    "image": _img(brand, "about", area["name"]), "reverse": True}},
                {"block": "cta.panel" if _merged(copy, "layout_feature") else "cta.split",
                 "props": {"image": cta_img, "cta2": call,
                    "heading": _copy(copy, key, "cta_heading", f"Serving {area['name']} today"),
                    "cta": cta}},
            ]

        elif key == "areas":
            blocks = [
                {"block": "hero.banner", "props": {
                    "h1": _copy(copy, key, "h1", "Areas We Serve"),
                    "intro": _copy(copy, key, "intro", ""),
                    "cta": cta, "image": _img(brand, "hero"), "dark": True}},
                {"block": "areas.chips" if _merged(copy, "layout_impact")
                 else "areas.grid", "props": {
                    "heading": _copy(copy, key, "grid_heading", "Where we work"),
                    "intro": _copy(copy, key, "grid_intro", ""),
                    "areas": [{"name": a["name"],
                               "href": f"/areas/{a['slug']}" if a.get("own_page") else ""}
                              for a in areas],
                    "map_query": contact.get("map_query", ""), "columns": 4,
                    "zoom": 9,
                    **({"panel": "dark"} if _merged(copy, "layout_impact") else {})}},
                {"block": "cta.panel" if _merged(copy, "layout_feature") else "cta.split",
                 "props": {"image": cta_img, "cta2": call,
                    "heading": "Not sure if we cover you?", "cta": call}},
            ]

        elif key == "faq":
            blocks = [
                {"block": "hero.banner", "props": {
                    "h1": _copy(copy, key, "h1", "Frequently Asked Questions"),
                    "intro": _copy(copy, key, "intro", ""),
                    "cta": cta, "image": _img(brand, "hero"), "dark": True}},
                {"block": "faq.accordion", "props": {
                    "heading": _copy(copy, key, "grid_heading", "Answers"),
                    "items": faqs or [
                        {"q": "Are you licensed and insured?", "a": "Yes — fully licensed and insured."},
                    ]}},
                {"block": "cta.panel" if _merged(copy, "layout_feature") else "cta.split",
                 "props": {"image": cta_img, "cta2": call,"heading": "Still have a question?", "cta": call}},
            ]

        elif key == "contact":
            details = [
                {"text": contact.get("phone_display") or contact["phone"],
                 "icon": "fas fa-phone", "href": f"tel:{contact['phone']}"},
                {"text": contact["email"], "icon": "fas fa-envelope",
                 "href": f"mailto:{contact['email']}"},
            ]
            if contact.get("address"):
                details.append({"text": contact["address"], "icon": "fas fa-location-dot"})
            for h in contact.get("hours", []):
                details.append({"text": h, "icon": "far fa-clock"})
            blocks = [
                {"block": "hero.banner", "props": {
                    "h1": _copy(copy, key, "banner", p.get("title", "Contact")),
                    "image": _img(brand, "hero", f"{biz['name']} finished installation")
                }},
                {"block": "contact.block", "props": {
                    "eyebrow": "Contact",
                    "heading": _copy(copy, key, "h1", "Get in touch"),
                    "intro": _copy(copy, key, "intro", ""),
                    "details": details,
                    "email": contact["email"],
                    "business": biz["name"],
                    "submit_label": biz.get("primary_cta", "Send Request"),
                    "fields": copy.get(key, {}).get("fields", []),
                    "success_message": _copy(copy, key, "success_message",
                                             "Thanks — we'll be in touch shortly.")
                }},
                *( [{"block": "areas.chips" if _merged(copy, "layout_feature")
                     else "areas.grid", "props": {
                    "eyebrow": "Service Area",
                    "heading": _copy(copy, key, "areas_heading", "Where we work"),
                    "intro": _copy(copy, key, "areas_intro", ""),
                    "areas": [{"name": a["name"],
                               "href": f"/areas/{a['slug']}" if a.get("own_page") else ""}
                              for a in areas],
                    "map_query": contact.get("map_query", ""),
                    "columns": 4, "bg": "white"}}] if areas else [] ),
                {"block": "cta.panel" if _merged(copy, "layout_feature") else "cta.split",
                 "props": {"image": cta_img, "cta2": call,
                    "heading": _copy(copy, key, "cta_heading", "Prefer to call?"),
                    "cta": call}},
            ]

        else:
            blocks = [
                {"block": "hero.banner", "props": {
                    "h1": _copy(copy, key, "h1", p.get("title", key.title())),
                    "intro": _copy(copy, key, "intro", ""),
                    "cta": cta, "image": _img(brand, "hero"), "dark": True}},
                {"block": "cta.panel" if _merged(copy, "layout_feature") else "cta.split",
                 "props": {"image": cta_img, "cta2": call,"heading": "Get in touch", "cta": cta}},
            ]

        pages.append({
            "key": key,
            "type": ptype,
            "title": p.get("title") or key.replace(":", " ").title(),
            "seo": {
                "target_keyword": p.get("target_keyword", ""),
                "meta_title": _copy(copy, key, "meta_title", ""),
                "meta_description": _copy(copy, key, "meta_description", ""),
            },
            "blocks": blocks,
        })

    return {"site": biz["name"], "pages": pages}
