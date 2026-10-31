---
name: posts
description: Plan, write and publish blog posts on a WordPress site - from the client's own articles or from the SEO keyword map - as drafts with categories, tags, featured images and Rank Math/Yoast fields, through the bridge. Use for blog content, article uploads and content calendars.
argument-hint: "[topics | path to client articles]"
---

# Posts

Load `core`; read `${CLAUDE_PLUGIN_ROOT}/knowledge/handbook/02-COPY-AND-SEO.md`. Input: `$ARGUMENTS`.
Posts are prepared in `sites/<slug>/posts/<slug-of-post>/post.json` (+ images).

## Client-supplied articles

Split the client's copy on its own headings - don't rewrite their words unless asked. Format as block markup
(`<!-- wp:heading -->` / `<!-- wp:paragraph -->`...), add internal links to the money pages, an FAQ block when the
article answers questions, alt text on images.

## New articles (from the keyword map)

1. Content plan: pillars per service + supporting posts from `seo/plan.json` / `seo/gap.json` - a table the member
   edits before writing starts.
2. Brief per post: target keyword, intent, what the SERP's top pages cover (`dataforseo.py serp`), and what THIS
   business can say that others can't (its process, its area, facts the client gave).
3. `content-writer` agent drafts; `editor` agent checks claims, removes filler, flags any fact needing the client.
   Never invent stats, quotes, prices, testimonials or credentials. Default cap: 5 posts per run.

## Upload

```
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rmedia.ps1" sites/<slug>/posts/<p>/featured.webp "<alt text>"
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rposts.ps1" push sites/<slug>/posts/<p>/post.json          # draft
powershell -File "${CLAUDE_PLUGIN_ROOT}/scripts/rposts.ps1" push sites/<slug>/posts/<p>/post.json update   # revise
```

`post.json` carries an optional `seo` block (title, description, focus_keyword) written right after the post.
Scheduling: `"status": "future", "date": "<ISO date>"`. **Publishing now** (`... publish`) only after the member
has read the preview link and said yes - the guard will ask them too.

## Verify

Open each preview (`shot.mjs <preview url>`) at 390 and 1440; `audit/seo.mjs <path>` once published.
