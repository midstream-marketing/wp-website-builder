=== WPU Bridge ===
Contributors: webelitedigital
Requires at least: 6.0
Requires PHP: 7.4
Stable tag: 2.0.0
License: GPLv2 or later

TEMPORARY build-time bridge for the WP Ultimate Build toolkit. Delete it at handover.

== Description ==

Lets the WP Ultimate Build toolkit (run from Claude Code by the agency's team)
build, fix and optimise this site over an authenticated REST namespace,
wpu/v1, with no hosting access:

* /doctor   - host preflight
* /run      - run a maintenance script (administrators only)
* /file     - read/write under wp-content, PHP parse-checked, previous version kept
* /log      - tail the error log
* /audit    - the last 50 calls: who, which team member, when, what
* /media    - add a file to the Media Library
* /template - import an Elementor template export
* /seo      - read/write SEO title, description, focus keyword, canonical,
              noindex and schema for Rank Math or Yoast, with backup and rollback
* /posts    - create or update blog posts (drafts by default)

Safety:

* Administrator capability on every route
* Per-member connection keys (Tools > WPU Bridge) or Application Passwords
* HTTPS only
* Switches itself off 30 days after activation (WPU_BRIDGE_DAYS to change)
* Kill switch: define( 'WPU_BRIDGE_DISABLE', true ); in wp-config.php
* Deactivating deletes every connection key

== Handover ==

1. Delete this plugin.
2. Revoke any Application Password made for the toolkit (Users > Profile).
3. Keep the mu-plugin wpu-seo-schema.php if the site uses schema from the toolkit.
