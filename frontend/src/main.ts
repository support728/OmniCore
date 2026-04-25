import './style.css';

const API_URL = 'http://localhost:8000';

const app = document.querySelector<HTMLDivElement>('#app');

type SearchResult = {
	title: string;
	link: string;
	snippet: string;
};

type AssistantResponse = {
	type?: string;
	summary?: string;
	message?: string;
	reply?: string;
	data?: {
		results?: SearchResult[];
		city?: string;
		temperature?: number;
		temp?: number;
		description?: string;
	};
};

function escapeHtml(value: string) {
	return value
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#39;');
}

function renderStructuredResponse(data: AssistantResponse) {
	const results = Array.isArray(data.data?.results) ? data.data.results : [];
	if (data.type === 'weather') {
		const temp = data.data?.temperature ?? data.data?.temp;
		const description = data.data?.description ?? '';
		const city = data.data?.city ?? 'that location';
		return `<div style="margin-top: 12px; border: 1px solid #d9e1ec; border-radius: 16px; background: #f8fbff; color: #172033; padding: 16px;">${escapeHtml(String(city))}${temp !== undefined ? ` · ${escapeHtml(String(temp))}°` : ''}${description ? ` · ${escapeHtml(String(description))}` : ''}</div>`;
	}

	if (data.type === 'web_search' || data.type === 'youtube_search' || data.type === 'news') {
		const cards = results
			.map(
				(result) => `
					<div style="border: 1px solid #d9e1ec; border-radius: 16px; background: #fff; padding: 16px; text-align: left;">
						<div style="font-size: 16px; font-weight: 700; color: #172033; margin-bottom: 8px;">${escapeHtml(result.title || result.link || 'Result')}</div>
						<div style="font-size: 14px; line-height: 1.6; color: #425874;">${escapeHtml(result.snippet || '')}</div>
						<div style="margin-top: 10px; font-size: 12px; color: #7a889c; word-break: break-all;">${escapeHtml(result.link || '')}</div>
					</div>
				`
			)
			.join('');

		return cards ? `<div style="display: grid; gap: 12px; margin-top: 12px;">${cards}</div>` : '';
	}

	return '';
}

function renderUI() {
	if (!app) return;
	app.innerHTML = `
		<div style="display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh; background: #fff; padding: 24px; box-sizing: border-box;">
			<h1 style="font-size: 3rem; font-weight: 700; letter-spacing: 2px; color: #222; margin: 0;">OmniCore AI</h1>
			<p style="font-size: 1.25rem; color: #666; margin-top: 1rem;">Welcome to the future of intelligence</p>
			<form id="chat-form" style="margin-top: 2rem; display: flex; gap: 0.5rem;">
				<input id="user-input" type="text" placeholder="Type your message..." style="padding: 0.75rem 1rem; font-size: 1rem; border: 1px solid #ccc; border-radius: 6px; width: 260px;" required />
				<button type="submit" style="padding: 0.75rem 1.5rem; font-size: 1rem; background: #aa3bff; color: #fff; border: none; border-radius: 6px; cursor: pointer;">Send</button>
			</form>
			<div id="chat-response" style="margin-top: 1.5rem; min-height: 2.5rem; color: #222; font-size: 1.1rem; text-align: center;"></div>
		</div>
	`;
}

async function sendMessage(message: string) {
	const responseDiv = document.getElementById('chat-response');
	if (responseDiv) responseDiv.textContent = 'Thinking...';
	try {
		const res = await fetch(`${API_URL}/api/chat`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ message }),
		});
		const data = (await res.json()) as AssistantResponse;
		const responseMessage =
			(typeof data?.summary === 'string' && data.summary.trim()) ||
			(typeof data?.message === 'string' && data.message.trim()) ||
			(typeof data?.reply === 'string' && data.reply.trim()) ||
			'';

		if (responseDiv) {
			responseDiv.innerHTML = `<div>${escapeHtml(responseMessage)}</div>${renderStructuredResponse(data)}`;
		}
	} catch (e) {
		if (responseDiv) responseDiv.textContent = 'Error connecting to OmniCore AI.';
	}
}

renderUI();

document.addEventListener('submit', (e) => {
	const form = e.target as HTMLFormElement;
	if (form && form.id === 'chat-form') {
		e.preventDefault();
		const input = document.getElementById('user-input') as HTMLInputElement;
		if (input && input.value.trim()) {
			sendMessage(input.value.trim());
			input.value = '';
		}
	}
});
