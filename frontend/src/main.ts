import './style.css';

const API_URL = 'http://localhost:8000';

const app = document.querySelector<HTMLDivElement>('#app');

function renderUI() {
	if (!app) return;
	app.innerHTML = `
		<div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; background: #fff;">
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
		const data = await res.json();
		if (responseDiv) responseDiv.textContent = data.response || 'No response.';
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
