---
name: learn
description: Turn what this session learned into team knowledge - new traps for GOTCHAS.md, case files, validator rules, block factories or checklist items - as a reviewed change to the shared plugin repo. Use at the end of a project or after solving a problem that cost real time.
---

# Learn

The plugin is installed read-only for everyone, so new knowledge reaches the team as a change to the
`wpu-marketplace` repo, reviewed and merged, then shipped by auto-update.

1. Collect from this session (and `sites/<slug>/SITE-NOTES.md` "Traps found on this site"): what failed, why, the rule
   that would have prevented it. Only the non-obvious - never what the code already says.
2. For each, pick the home:
   - environment/platform trap -> `knowledge/GOTCHAS.md` entry: **symptom -> cause -> rule**, the date and the site,
     in the existing house style (lead with the decision, bold the rule, end with "How to apply")
   - a design or toolchain lesson -> `knowledge/handbook/06-CASE-FILES.md`
   - a check a machine can run -> a validator rule, an audit script or a `seo_plan.py` check (with a test)
   - a recurring section -> a block factory in `forge/src/forge/blocks.py` (and the regression build passes)
   - a step people skip -> the relevant checklist
3. Show the member the proposed additions first. Search GOTCHAS for an existing entry before adding a duplicate.
4. With their OK: in a clone of the marketplace repo, branch, edit, run the regression
   (`python forge/forge.py forge/examples/intake.example.json -o <tmp> --strict`, `python tools/seo/keyword_score.py`),
   commit, push, open a pull request. Bump `plugins/wpu/.claude-plugin/plugin.json` version so auto-update ships it.
