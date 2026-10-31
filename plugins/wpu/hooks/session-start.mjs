// SessionStart: tell Claude where it is - which client sites exist in this
// workspace and which one is selected - and nothing else. Keeps context small.
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ws = process.env.WPU_WORKSPACE || process.cwd();
const sitesDir = path.join(ws, 'sites');
const lines = [];
const root = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
lines.push(`WPU plugin folder (use for script paths you show the member): ${root}`);

if (existsSync(sitesDir)) {
	const sites = readdirSync(sitesDir).filter((d) => existsSync(path.join(sitesDir, d, 'site.json')));
	const sel = process.env.WPU_SITE || '';
	lines.push(`WP Ultimate Build workspace: ${ws}`);
	lines.push(`Client sites (${sites.length}): ${sites.slice(0, 60).join(', ')}${sites.length > 60 ? ' ...' : ''}`);
	if (sel && sites.includes(sel)) {
		const notes = path.join(sitesDir, sel, 'SITE-NOTES.md');
		lines.push(`Selected site: ${sel}. Read sites/${sel}/SITE-NOTES.md before changing anything${existsSync(notes) ? ` (${Math.round(statSync(notes).size / 1024)} KB - search it, do not read it whole if large)` : ' (none yet)'}.`);
	} else {
		lines.push('No site selected. Before any script: set WPU_SITE=<slug> for the command (PowerShell: $env:WPU_SITE = "<slug>").');
	}
	lines.push('Working method: load the wpu:core skill before any WordPress work.');
} else {
	lines.push(`WP Ultimate Build is installed, but ${ws} has no sites/ folder. Run /wpu:new-site to set up a client, or open Claude Code in the team workspace folder.`);
}

process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext: lines.join('\n') } }));
