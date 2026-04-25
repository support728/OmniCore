const { chromium } = require('playwright');

const prompts = [
  "I have $40, no help, and 1 day.\nI need to get something working by tomorrow afternoon.\nTell me exactly what to do. No ideas.",
  "I can:\n- feed people this weekend\n- flip items for quick cash\nPick ONE. No list. Decide.",
  "I have no money, no connections, and no time.\nIf you say anything generic, you failed.",
  "Be honest: am I trying to do too much?\nI want to start a nonprofit, a business, and make money fast.",
  "Talk like a real person.\nWhat should I do tomorrow morning between 9am-12pm with $20?",
  "I only have what I already own.\nNo loans. No outside help.\nWhat do I do this week?",
  "Give me ONE next step.\nKeep it under 2 sentences.",
  "I failed last week.\nNothing worked.\nWhat do I do differently starting tomorrow?",
  "I'm in a bad spot.\nI need something that works NOW, not later.\nWhat do I do today?",
  "I have 3 hours, $10, and no tools.\nWhat exactly do I do step by step?",
  "Do NOT give me options.\nJust decide for me.",
  "Everything you say must work inside my current situation.\nNo outside systems. No external help.",
];

function normalizePromptForInput(prompt) {
  return String(prompt || '')
    .replace(/\r?\n+/g, ' ')
    .replace(/[\u2013\u2014]/g, '-')
    .replace(/\s+/g, ' ')
    .trim();
}

function cleanAssistantText(raw) {
  const text = String(raw || '').replace(/\r/g, '').trim();
  if (!text) {
    return '';
  }

  const lines = text.split('\n').map((line) => line.trim()).filter(Boolean);
  const filtered = lines.filter((line) => {
    if (line === 'OmniCore' || line === 'OMNICORE' || line === 'You' || line === 'YOU' || line === 'LISTEN') {
      return false;
    }
    if (line === 'GENERAL ASSISTANT' || line === 'General Assistant') {
      return false;
    }
    if (/^\d{1,2}:\d{2}(?:\s?[AP]M)?$/i.test(line)) {
      return false;
    }
    if (line === 'THINKING...' || line === 'Thinking...' || line === 'SEARCHING THE WEB...') {
      return false;
    }
    if (/^CONFIDENCE:\s+/i.test(line)) {
      return false;
    }
    if ([
      'Tell me more',
      'Ask another question',
      'Explain that differently',
      'Summarize',
      'Related',
      'Give me next steps',
    ].includes(line)) {
      return false;
    }
    return true;
  });

  return filtered.join(' ').replace(/\s+/g, ' ').trim();
}

async function waitForPromptResponse(page, normalizedPrompt) {
  const response = await page.waitForResponse(
    async (candidate) => {
      if (!candidate.url().endsWith('/query')) {
        return false;
      }
      if (candidate.request().method() !== 'POST') {
        return false;
      }

      try {
        const payload = JSON.parse(candidate.request().postData() || '{}');
        return String(payload.query || '') === normalizedPrompt;
      } catch {
        return false;
      }
    },
    { timeout: 60000 }
  );

  const json = await response.json();
  return cleanAssistantText(json.summary || '');
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });

  try {
    await page.goto('http://127.0.0.1:3001', { waitUntil: 'networkidle', timeout: 30000 });
    await page.locator('input[placeholder="Ask OmniCore anything..."]').waitFor({ state: 'visible', timeout: 30000 });

    const results = [];

    for (let index = 0; index < prompts.length; index += 1) {
      const prompt = prompts[index];
      const normalizedPrompt = normalizePromptForInput(prompt);
      if (index > 0) {
        await page.getByRole('button', { name: 'New chat' }).click();
        await page.waitForTimeout(250);
      }
      const input = page.locator('input[placeholder="Ask OmniCore anything..."]');
      await input.fill(normalizedPrompt);
      const responsePromise = waitForPromptResponse(page, normalizedPrompt);
      await page.getByRole('button', { name: 'Send' }).click();
      const reply = await responsePromise;
      results.push({ promptIndex: index + 1, prompt, reply });
    }

    console.log(JSON.stringify(results, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});