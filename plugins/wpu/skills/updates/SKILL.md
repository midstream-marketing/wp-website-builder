---
name: updates
description: Update plugins and themes on one or many client sites through the WPU Bridge's typed tools, with a dry run, checks of the live pages before and after each update, automatic rollback if a page breaks, and a report. Use for "update the plugins", monthly maintenance, or updating every client site.
argument-hint: "[site slug | all]"
---

# Plugin and theme updates (one site or all of them)

Works through the **WPU Bridge** (2.1+) with `scripts/rtool.ps1` (see `core`). The tools: `updates_check`,
`updates_apply`, `site_health_check`, `change_undo`. Pick the site with `$env:WPU_SITE = '<slug>'` before each
site's commands.

What `updates_apply` does for every item: copies the plugin or theme folder to private storage, updates it with
WordPress's own upgrader, loads the key pages again (home, newest post and page, shop and cart), and if a page
that worked before now fails, puts the old folder back. A successful update returns a `change_id`, and
`change_undo` goes back to the previous version. WordPress core is reported, never updated.

## Steps

1. **Which sites.** `$ARGUMENTS` is a slug or `all`. For all, go through `sites/*/site.json` one site at a time. A site whose bridge
   does not answer (`rdoctor.ps1`), has expired, or is older than 2.1: say so and skip it.
2. **Check, per site.** `updates_check` (refresh true). Note `blocked` (DISALLOW_FILE_MODS or FTP-only
   hosts can't update from here), anything not `compatible` with the site's PHP or WordPress, and premium
   plugins without a package (licence not active).
3. **Show the plan** as one table per site: name, current -> new, active, notes. Leave out
   incompatible items and say why. Ask once: "Update these?" Big jumps (WooCommerce, Elementor, a major
   version) go last and alone.
4. **Dry run.** `rtool.ps1 updates_apply <args.json>` with `"dry_run": true` for the batch (no `apply` needed). If `already_broken` lists pages, report
   them. They are not caused by the update, and the check ignores them. If `checks_possible` is false, the
   site can't load its own pages. Stop and ask before using `allow_without_checks`.
5. **Apply.** At most 3 items per call (`"dry_run": false`, and the word `apply`; the member approves each call), cheapest and safest first. One site at a time.
   If any result is `rolled_back`, stop updates on that site and report which page broke and why
   (`why`, `broken_pages`). Don't retry it. If any result is `rollback_failed`, stop everything: the
   site may be down. Use `/wpu:rescue` straight away.
6. **After.** `site_health_check` once more. Then report per site: updated, rolled back, skipped, with
   change_ids so any update can be undone with `change_undo`.
7. Write one line per site into `sites/<slug>/SITE-NOTES.md`: date, what was updated, anything rolled back.

## Rules

- Never update during a site's busy hours if the notes say so (shops: avoid sale days).
- The bridge does not update itself through its own tools: it refuses. Upload the new bridge zip in wp-admin.
- A rollback is a finding, not a failure to hide: tell the person which plugin and which page.
