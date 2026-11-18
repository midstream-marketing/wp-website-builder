#!/usr/bin/env node
// WPU Desk approval bridge: a tiny MCP server that Claude Code calls (--permission-prompt-tool)
// whenever a tool call needs the member's permission. It forwards the request to the local Desk
// server and waits for the member's Approve / Reject. No dependencies; stdio JSON-RPC only.
//
// Env (set by the Desk when it starts a job): DESK_URL, DESK_HELPER_TOKEN, DESK_JOB.
import http from 'node:http';
import { createInterface } from 'node:readline';

const { DESK_URL = '', DESK_HELPER_TOKEN = '', DESK_JOB = '' } = process.env;
const send = (o) => process.stdout.write(JSON.stringify(o) + '\n');

function askDesk(payload) {
	return new Promise((resolve) => {
		let u;
		try { u = new URL('/api/internal/approval', DESK_URL); } catch { return resolve({ behavior: 'deny', message: 'WPU Desk is not reachable.' }); }
		if (u.hostname !== '127.0.0.1') return resolve({ behavior: 'deny', message: 'WPU Desk must run on 127.0.0.1.' });
		const body = JSON.stringify({ job: DESK_JOB, ...payload });
		const req = http.request(u, {
			method: 'POST',
			headers: { 'content-type': 'application/json', 'x-desk-helper': DESK_HELPER_TOKEN, 'content-length': Buffer.byteLength(body) },
			timeout: 0, // the member may take a while to decide
		}, (res) => {
			let data = '';
			res.on('data', (c) => { data += c; });
			res.on('end', () => {
				try {
					const d = JSON.parse(data);
					if (d.behavior === 'allow') return resolve({ behavior: 'allow', updatedInput: payload.input });
					return resolve({ behavior: 'deny', message: d.message || 'Rejected by the member in WPU Desk.' });
				} catch { resolve({ behavior: 'deny', message: 'WPU Desk gave no decision.' }); }
			});
		});
		req.on('error', () => resolve({ behavior: 'deny', message: 'WPU Desk is not reachable, so nothing was run.' }));
		req.end(body);
	});
}

const rl = createInterface({ input: process.stdin });
rl.on('line', async (line) => {
	let m;
	try { m = JSON.parse(line); } catch { return; }
	if (m.method === 'initialize') {
		send({ jsonrpc: '2.0', id: m.id, result: { protocolVersion: m.params?.protocolVersion || '2025-06-18', capabilities: { tools: {} }, serverInfo: { name: 'wpu_desk', version: '1.0.0' } } });
	} else if (m.method === 'tools/list') {
		send({ jsonrpc: '2.0', id: m.id, result: { tools: [{
			name: 'approve',
			description: 'Asks the member in WPU Desk to approve or reject a tool call. Used only as the permission prompt tool.',
			inputSchema: { type: 'object', properties: { tool_name: { type: 'string' }, input: { type: 'object' }, tool_use_id: { type: 'string' } }, required: ['tool_name', 'input'] },
		}] } });
	} else if (m.method === 'tools/call') {
		const a = m.params?.arguments || {};
		const decision = await askDesk({ tool_name: String(a.tool_name || ''), input: a.input || {}, tool_use_id: String(a.tool_use_id || '') });
		send({ jsonrpc: '2.0', id: m.id, result: { content: [{ type: 'text', text: JSON.stringify(decision) }] } });
	} else if (m.id !== undefined) {
		send({ jsonrpc: '2.0', id: m.id, result: {} });
	}
});
