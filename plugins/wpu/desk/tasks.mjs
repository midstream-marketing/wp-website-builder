// What each Desk button does: the form it shows and the prompt it sends to Claude Code.
// Every prompt runs one of the plugin's /wpu: skills, so the Desk does exactly what the
// plugin does in a terminal - nothing more, nothing less.

export const TASKS = [
	{
		id: 'build', label: 'Build', group: 'Create',
		desc: 'Website, landing page, store page or new section from a design, reference sites or a brief',
		fields: [
			{ id: 'what', label: 'What to build', type: 'select', options: ['Whole website', 'Landing page', 'One page', 'New section on a page', 'WooCommerce store pages'] },
			{ id: 'source', label: 'Design or reference (Claude Design link, Figma/XD link, reference URLs, or a path to screenshots)', type: 'textarea' },
			{ id: 'brief', label: 'Brief: pages, content, style, anything the client said', type: 'textarea' },
		],
		prompt: (f) => `/wpu:build ${f.what || ''}.\nDesign / references: ${f.source || 'none given'}\nBrief: ${f.brief || 'none given'}`,
	},
	{
		id: 'doctor', label: 'Fix / health check', group: 'Maintain',
		desc: 'Find and fix layout, mobile, image, font and plugin problems, or work through a client revision list',
		fields: [{ id: 'issue', label: 'What is wrong (or leave empty for a full health check)', type: 'textarea' }],
		prompt: (f) => `/wpu:doctor ${f.issue || 'Full health check of the site.'}`,
	},
	{
		id: 'seo', label: 'SEO', group: 'Grow',
		desc: 'DataForSEO research, keyword map, Rank Math / Yoast titles, descriptions, schema - with rollback',
		fields: [
			{ id: 'scope', label: 'Pages or services to focus on', type: 'textarea' },
			{ id: 'location', label: 'Target location (city, state, country)', type: 'text' },
		],
		prompt: (f) => `/wpu:seo Focus: ${f.scope || 'all main pages'}. Location: ${f.location || 'as in site notes'}.`,
	},
	{
		id: 'posts', label: 'Blog posts', group: 'Grow',
		desc: 'Plan, write and upload posts as drafts with categories, images and SEO fields',
		fields: [
			{ id: 'topics', label: 'Topics, keywords or the client\'s own articles (paste or give paths)', type: 'textarea' },
			{ id: 'count', label: 'How many posts', type: 'text' },
			{ id: 'status', label: 'Upload as', type: 'select', options: ['Drafts (recommended)', 'Publish after my approval'] },
		],
		prompt: (f) => `/wpu:posts ${f.count || '1'} post(s). Topics: ${f.topics || 'from the SEO keyword map'}. Upload as: ${f.status || 'drafts'}.`,
	},
	{
		id: 'speed', label: 'Speed', group: 'Maintain',
		desc: 'PageSpeed before/after, one settings group at a time, automatic rollback if it gets worse',
		fields: [{ id: 'pages', label: 'Pages to test (empty = home page)', type: 'text' }],
		prompt: (f) => `/wpu:speed ${f.pages || 'home page'}`,
	},
	{
		id: 'secure', label: 'Security', group: 'Maintain',
		desc: 'Outside scan, inside audit, hardening switches (applied only with approval)',
		fields: [{ id: 'notes', label: 'Anything specific (hack suspected, before handover, ...)', type: 'textarea' }],
		prompt: (f) => `/wpu:secure ${f.notes || ''}`,
	},
	{
		id: 'updates', label: 'Plugin & theme updates', group: 'Maintain',
		desc: 'Dry run, then update with live-page checks before and after; anything that breaks a page is rolled back',
		fields: [{ id: 'scope', label: 'This site, or "all" for every connected site', type: 'select', options: ['This site', 'All connected sites'] }],
		prompt: (f, slug) => `/wpu:updates ${f.scope === 'All connected sites' ? 'all' : slug || ''}`,
	},
	{
		id: 'theme', label: 'Theme builder', group: 'Build',
		desc: 'Draft block theme from a design or brief, with a private preview link; goes live only when you say',
		fields: [{ id: 'source', label: 'Design link, reference sites or brief', type: 'textarea' }],
		prompt: (f, slug) => `/wpu:theme ${slug || ''} ${f.source || ''}`,
	},
	{
		id: 'rescue', label: 'Rescue (site down)', group: 'Maintain',
		desc: 'White screen, critical error, stuck maintenance - fix through SFTP/SSH or cPanel',
		fields: [{ id: 'symptom', label: 'What do you see on the site?', type: 'textarea' }],
		prompt: (f) => `/wpu:rescue ${f.symptom || 'The site is down.'}`,
	},
	{
		id: 'plugin', label: 'Custom plugin', group: 'Create',
		desc: 'Calculators, custom post types, Elementor widgets, WooCommerce tweaks - spec first, security-reviewed',
		fields: [{ id: 'spec', label: 'What should it do?', type: 'textarea' }],
		prompt: (f) => `/wpu:plugin ${f.spec || ''}`,
	},
	{
		id: 'handover', label: 'Handover', group: 'Finish',
		desc: 'Launch checklist, final backup, bridge removal, credential clean-up',
		fields: [{ id: 'notes', label: 'Notes for the launch', type: 'textarea' }],
		prompt: (f) => `/wpu:handover ${f.notes || ''}`,
	},
	{
		id: 'learn', label: 'Save lessons', group: 'Finish',
		desc: 'Turn what this project taught into team knowledge (traps, rules, checklists)',
		fields: [{ id: 'notes', label: 'What did we learn?', type: 'textarea' }],
		prompt: (f) => `/wpu:learn ${f.notes || ''}`,
	},
	{
		id: 'custom', label: 'Ask anything', group: 'Other',
		desc: 'Any other instruction for this site, in plain English',
		fields: [{ id: 'text', label: 'Instruction', type: 'textarea' }],
		prompt: (f) => `${f.text || ''}`,
	},
];

export const NEW_SITE = {
	fields: [
		{ id: 'slug', label: 'Short name (letters, numbers, dashes)', type: 'text' },
		{ id: 'url', label: 'Site URL (staging or live)', type: 'text' },
		{ id: 'details', label: 'Anything else: client, hosting, SEO plugin, notes', type: 'textarea' },
	],
	prompt: (f) => `/wpu:new-site ${f.slug} ${f.url}\n${f.details || ''}`,
};

/** Added in front of every prompt, so the skills behave well without a terminal. */
export function preface(slug) {
	return [
		'You are running inside WPU Desk, a local dashboard. The member cannot see a terminal and cannot answer interactive prompts.',
		slug ? `The selected site is "${slug}" (WPU_SITE is already set).` : 'No site is selected yet.',
		'- Approvals: tool calls that change a live site are shown to the member in the Desk as an approval card. Just run them; the Desk asks.',
		`- Secrets: never ask for a password, key or token in the conversation and never run wpu-secret.ps1 yourself. When one is missing, tell the member to open the Desk's Secrets panel and save scope "${slug || 'global'}" with the exact name (key, apppassword, adminpass, sftp_pass, sftp_keypass, cpanel_token, or global dataforseo_login / dataforseo_password / pagespeed_key), then stop and wait.`,
		'- Questions: if you need information or a decision, end your turn with a short, numbered question. The member replies in the Desk and you continue.',
		'- When a step needs the member to do something in wp-admin or a browser, give short numbered steps.',
		'- Finish with a short summary: what changed, what is left, and any file the member should look at (path relative to the workspace).',
		'',
	].join('\n');
}
