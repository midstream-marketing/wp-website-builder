---
name: desk
description: Start or set up WPU Desk, the local browser dashboard for WP Ultimate Build - sites, task buttons, live progress, approvals, replies, results and secrets, without a terminal. Use when the member asks for the dashboard, the Desk, a UI, or a way to work without Claude Code or VS Code.
---

# WPU Desk

WPU Desk is a local web dashboard. It runs the official Claude Code, signed in with the member's own
Claude account, with this plugin. Every task is the same `/wpu:` skill, and approvals for live-site
changes appear as Approve/Reject cards. It listens only on 127.0.0.1 and never sees the member's
Claude login.

Tell the member, with the real plugin folder from the session context filled in:

1. **One time:** make a Desktop shortcut (in their own PowerShell window):
   ```
   powershell -ExecutionPolicy Bypass -File "<plugin folder>\scripts\wpu-desk.ps1" -InstallShortcut -Workspace "<their workspace folder>"
   ```
2. **Every day:** double-click **WPU Desk** on the Desktop. A window opens (keep it open) and the
   browser opens the dashboard with a one-time sign-in link. Pressing Enter in that window gives a
   fresh link. Closing the window stops the Desk.

Suggest a workspace inside the member's user folder (Desktop\WPU-Work is the default).

Requirements: Node.js, Claude Code installed and signed in once (`claude` in a terminal, then log in).

To run it without the shortcut: `node "<plugin folder>/desk/server.mjs" "<workspace>"`, then open the
one-time link it prints. How the Desk is protected: `desk/SECURITY.md`.

Rules that still apply in the Desk:
- Secrets are saved through the Desk's **Secrets** panel, not in a chat.
- Each member runs their own Desk with their own Claude seat. Never share one Desk or one Claude
  login between people.
