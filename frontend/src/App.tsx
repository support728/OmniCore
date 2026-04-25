import { useState } from 'react'


export default function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([]);

  const sendMessage = async () => {
    console.log("API CALL STARTING");
    const response = await fetch("http://127.0.0.1:8000/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: input,
      }),
    });

    const data = await response.json();
    setMessages((prev) => [
      ...prev,
      { role: "bot", text: data.response },
    ]);
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>Chat Test</h1>

      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type message"
      />

      <button onClick={sendMessage}>Send</button>

      <div style={{ marginTop: 20 }}>
        {messages.map((msg, idx) => (
          <div key={idx}>{msg.role}: {msg.text}</div>
        ))}
      </div>
    </div>
  );
}
  prompt: string;
};

type ChatIntent = "weather" | "news" | "sports" | "email" | "web_search" | "youtube_search" | "general";

type MemoryState = {
  name: string | null;
  lastIntent: ChatIntent | null;
  lastCity: string | null;
  lastTopic: string | null;
};

type MemoryUpdates = Partial<MemoryState>;

type PersistedMemory = {
  sessionId: string | null;
  memory: MemoryState;
};

const DEFAULT_MEMORY: MemoryState = {
  name: null,
  lastIntent: null,
  lastCity: null,
  lastTopic: null,
};

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function createAndPersistSessionId() {
  const nextSessionId = crypto.randomUUID();
  window.localStorage.setItem(SESSION_STORAGE_KEY, nextSessionId);
  return nextSessionId;
}

function normalizeStoredMessages(rawMessages: unknown): Message[] {
  if (!Array.isArray(rawMessages)) {
    return [INITIAL_MESSAGE];
  }

  const normalized: Array<Message | null> = rawMessages.map((item, index) => {
    if (!item || typeof item !== "object") {
      return null;
    }

    const record = item as Partial<Message>;
    if ((record.role !== "user" && record.role !== "ai") || typeof record.content !== "string") {
      return null;
    }

    return {
      id: typeof record.id === "string" && record.id ? record.id : `restored-${Date.now()}-${index}`,
      role: record.role,
      content: record.content,
      response:
        record.response && typeof record.response === "object" && !Array.isArray(record.response)
          ? (record.response as AssistantResponse)
          : null,
      timestamp:
        typeof record.timestamp === "number" && Number.isFinite(record.timestamp)
          ? record.timestamp
          : Date.now() + index,
    } satisfies Message;
  });

  const filtered = normalized.filter((item) => item !== null) as Message[];

  return filtered.length > 0 ? filtered : [INITIAL_MESSAGE];
}

function renderStructuredResponse(response: AssistantResponse | null | undefined) {
  if (!response) {
    return null;
  }

  const results = Array.isArray(response.data?.results) ? response.data.results : [];

  if (response.type === "weather") {
    const city = response.data?.city || "that location";
    const temp = response.data?.temperature ?? response.data?.temp;
    const description = response.data?.description || "current conditions";
    return (
      <div style={{ marginTop: 12, border: "1px solid #d9e1ec", borderRadius: 16, background: "#f8fbff", padding: 16, color: "#172033" }}>
        <div style={{ fontWeight: 700, marginBottom: 6 }}>{city}</div>
        <div style={{ fontSize: 14, lineHeight: 1.6 }}>{temp !== undefined ? `${temp}° · ${description}` : description}</div>
      </div>
    );
  }

  if (response.type === "web_search" || response.type === "youtube_search" || response.type === "news") {
    return results.length ? (
      <div style={{ marginTop: 12, display: "grid", gap: 12 }}>
        {results.map((result, index) => (
          <div key={`${result.link || result.url || result.title || "result"}-${index}`} style={{ border: "1px solid #d9e1ec", borderRadius: 16, background: "#fff", padding: 16 }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: "#172033", marginBottom: 8 }}>{result.title || result.link || result.url || "Result"}</div>
            {result.snippet ? <div style={{ fontSize: 14, lineHeight: 1.6, color: "#425874" }}>{result.snippet}</div> : null}
            {response.type === "youtube_search" && (result.link || result.url) && isYouTubeUrl(result.link || result.url || "")
              ? renderEmbeddedYouTube(result.link || result.url || "", `search-youtube-${index}`)
              : null}
            {(result.link || result.url) ? (
              <a href={result.link || result.url} className="message-link" target="_blank" rel="noreferrer" style={{ marginTop: 10, display: "inline-block", fontSize: 12, wordBreak: "break-all" }}>
                {result.link || result.url}
              </a>
            ) : null}
          </div>
        ))}
      </div>
    ) : null;
  }

  if (response.type === "image" && response.data?.url) {
    return (
      <div className="generated-image-card">
        <img src={response.data.url} alt={response.data.prompt || "Generated image"} className="generated-image" loading="lazy" />
        {response.data.prompt ? <div className="generated-image-caption">{response.data.prompt}</div> : null}
      </div>
    );
  }

  return null;
}

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatDateLabel(timestamp: number): string {
  const messageDate = new Date(timestamp);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);

  const isSameDay = (left: Date, right: Date) =>
    left.getFullYear() === right.getFullYear() &&
    left.getMonth() === right.getMonth() &&
    left.getDate() === right.getDate();

  if (isSameDay(messageDate, today)) {
    return "Today";
  }

  if (isSameDay(messageDate, yesterday)) {
    return "Yesterday";
  }

  return messageDate.toLocaleDateString([], {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function wait(delayMs: number) {
  return new Promise((resolve) => window.setTimeout(resolve, delayMs));
}

function getProgressiveChunks(text: string) {
  const normalized = text.replace(/\r\n/g, "\n");

  if (/^\s*(#{1,3}\s+|[-*+]\s+|\d+\.\s+)/m.test(normalized)) {
    const lines = normalized.split("\n");

    return lines
      .map((line, index) => `${line}${index < lines.length - 1 ? "\n" : ""}`)
      .filter((chunk) => chunk.length > 0);
  }

  if (normalized.includes("\n")) {
    const lines = normalized.split("\n");

    return lines
      .map((line, index) => `${line}${index < lines.length - 1 ? "\n" : ""}`)
      .filter((chunk) => chunk.length > 0);
  }

  const sentenceChunks = normalized.match(/[^.!?\n]+[.!?]+\s*|[^.!?\n]+$/g)?.filter(Boolean) ?? [];
  if (sentenceChunks.length > 1) {
    return sentenceChunks;
  }

  return normalized.match(/.{1,28}/g) ?? [normalized];
}

function sanitizeMarkdown(content: string) {
  return content
    .replace(/\r\n/g, "\n")
    .replace(/([^\n])\s*(#{2,6})\s+/g, "$1\n\n$2 ")
    .replace(/(#{2,6}\s.*)/g, "\n\n$1\n")
    .replace(/#{3,}/g, (match) => (match.length > 3 ? "###" : match))
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function getArticleTitleChunks(title: string) {
  const chunks: string[] = [];

  for (let index = 0; index < title.length; index += ARTICLE_TITLE_STEP_CHARS) {
    chunks.push(title.slice(index, index + ARTICLE_TITLE_STEP_CHARS));
  }

  return chunks.length > 0 ? chunks : [title];
}

function cleanArticleTitle(value: string) {
  return value.replace(/^\s*[-•]\s*/, "").trim();
}

function getArticleDomain(value: string) {
  try {
    return new URL(value).hostname.replace(/^www\./i, "");
  } catch {
    return value;
  }
}

function getSourceInitial(value: string) {
  const trimmed = value.trim();
  return trimmed ? trimmed.charAt(0).toUpperCase() : "?";
}

function createAssistantMessage(content: string): Message {
  return {
    id: createMessageId(),
    role: "ai",
    content,
    timestamp: Date.now(),
  };
}

function getSpeakableMessageText(text: string) {
  const blocks = parseMessageBlocks(text);

  return blocks
    .map((block) => {
      if (block.type === "text") {
        return block.content;
      }

      if (block.type === "article") {
        return `${block.title}. Source ${block.source}.`;
      }

      return `Email draft. To ${block.recipient}. Subject ${block.subject}. ${block.body}`;
    })
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

function getInitialAssistantMessage(memory: MemoryState): Message {
  return createAssistantMessage(
    memory.name
      ? `Welcome back, ${memory.name}. What would you like to check today?`
      : "You can call me Amico. How can I assist you today?"
  );
}

function normalizePersonName(value: string) {
  return value
    .trim()
    .replace(/[.!?,]+$/g, "")
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function extractTopic(text: string) {
  const weatherMatch = text.match(/weather in\s+(.+)$/i);
  if (weatherMatch?.[1]) {
    return weatherMatch[1].trim().replace(/[.!?]+$/g, "");
  }

  const newsMatch = text.match(/news\s+(?:about|on|for)?\s*(.+)$/i);
  if (newsMatch?.[1]) {
    return newsMatch[1].trim().replace(/[.!?]+$/g, "");
  }

  const sportsMatch = text.match(/(?:sports?|football|nba|scores?)\s+(?:about|on|for)?\s*(.+)$/i);
  if (sportsMatch?.[1]) {
    return sportsMatch[1].trim().replace(/[.!?]+$/g, "");
  }

  const emailDraft = extractEmailDraftRequest(text);
  if (emailDraft?.topic) {
    return emailDraft.topic;
  }

  return null;
}

function toTitleCase(value: string) {
  return value
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatDraftForComposer(draft: EmailDraftBlock) {
  return [`Email ${draft.recipient} about ${draft.subject}`, "", `Body:`, draft.body].join("\n");
}

function extractEmailDraftRequest(text: string) {
  const editedDraftMatch = text.match(/^Email\s+(.+?)\s+about\s+(.+?)\s*\n\s*\n?Body:\s*\n([\s\S]+)$/i);
  if (editedDraftMatch?.[1] && editedDraftMatch?.[2] && editedDraftMatch?.[3]) {
    return {
      recipient: normalizePersonName(editedDraftMatch[1]),
      topic: editedDraftMatch[2].trim(),
      body: editedDraftMatch[3].trim(),
    };
  }

  const emailMatch = text.match(/\bemail\b\s*(.+)$/i);
  if (!emailMatch?.[1]) {
    return null;
  }

  const remainder = emailMatch[1].trim().replace(/[.!?]+$/g, "");
  if (!remainder) {
    return null;
  }

  const detailedMatch = remainder.match(/^(?:to\s+)?(.+?)\s+(?:about|regarding|on|for)\s+(.+)$/i);
  if (detailedMatch?.[1] && detailedMatch?.[2]) {
    return {
      recipient: normalizePersonName(detailedMatch[1]),
      topic: detailedMatch[2].trim(),
      body: null,
    };
  }

  const [recipient, ...topicParts] = remainder.split(/\s+/);
  if (!recipient) {
    return null;
  }

  return {
    recipient: normalizePersonName(recipient),
    topic: topicParts.join(" ").trim() || "General Update",
    body: null,
  };
}

function buildEmailDraft(recipient: string, topic: string, senderName: string | null, bodyOverride?: string | null) {
  const normalizedTopic = topic.trim() || "General Update";
  const subject = toTitleCase(normalizedTopic);
  const closingName = senderName ?? "OmniCore User";
  const body =
    bodyOverride?.trim() ||
    `Hi ${recipient},\n\nI wanted to share a quick update regarding ${normalizedTopic}. Please let me know if you have any questions or if you'd like to discuss it in more detail.\n\nBest,\n${closingName}`;

  return {
    recipient,
    subject,
    body,
  };
}

function formatEmailDraftMessage(recipient: string, subject: string, body: string) {
  return [`📧 Email Draft`, `To: ${recipient}`, `Subject: ${subject}`, body].join("\n");
}

function extractMemory(text: string): MemoryUpdates {
  const lower = text.toLowerCase();
  const updates: MemoryUpdates = {};

  const nameMatch = text.match(/my name is\s+(.+)$/i);
  if (nameMatch?.[1]) {
    const name = normalizePersonName(nameMatch[1]);
    if (name) {
      updates.name = name;
    }
  }

  const weatherMatch = text.match(/weather in\s+(.+)$/i);
  if (weatherMatch?.[1]) {
    const city = weatherMatch[1].trim().replace(/[.!?]+$/g, "");
    if (city) {
      updates.lastCity = city;
      updates.lastTopic = city;
    }
  }

  if (lower.includes("weather") || lower.includes("temperature") || lower.includes("forecast")) {
    updates.lastIntent = "weather";
  } else if (lower.includes("news") || lower.includes("headline")) {
    updates.lastIntent = "news";
  } else if (lower.includes("sport") || lower.includes("football") || lower.includes("nba") || lower.includes("score")) {
    updates.lastIntent = "sports";
  } else if (lower.includes("email")) {
    updates.lastIntent = "email";
  }

  const topic = extractTopic(text);
  if (topic) {
    updates.lastTopic = topic;
  }

  return updates;
}

function mergeMemory(current: MemoryState, updates: MemoryUpdates): MemoryState {
  return {
    ...current,
    ...Object.fromEntries(Object.entries(updates).filter(([, value]) => value !== undefined)),
  } as MemoryState;
}

function detectWeatherCity(text: string) {
  const match = text.match(/\bin\s+([A-Za-z][A-Za-z\s.'-]*?)(?:,\s*[A-Z]{2})?(?:[.!?]|$)/);
  return match?.[1]?.trim() ?? null;
}

function getIntent(text: string): ChatIntent {
  const lowerText = text.toLowerCase();

  if (lowerText.includes("youtube")) {
    return "youtube_search";
  }

  if (lowerText.includes("weather") || lowerText.includes("temperature") || lowerText.includes("forecast")) {
    return "weather";
  }

  if (lowerText.includes("news") || lowerText.includes("headline") || lowerText.includes("headlines")) {
    return "news";
  }

  if (
    lowerText.includes("sport") ||
    lowerText.includes("sports") ||
    lowerText.includes("football") ||
    lowerText.includes("nba") ||
    lowerText.includes("score") ||
    lowerText.includes("scores")
  ) {
    return "sports";
  }

  if (lowerText.includes("email")) {
    return "email";
  }

  if (lowerText.includes("search") || lowerText.includes("internet") || lowerText.includes("google") || lowerText.includes("find")) {
    return "web_search";
  }

  return "general";
}

function getSuggestions(intent: ChatIntent, lastUserMessage: string): FollowUpSuggestion[] {
  const city = intent === "weather" ? detectWeatherCity(lastUserMessage) : null;
  const cleanedQuery = lastUserMessage.trim();

  switch (intent) {
    case "weather":
      return [
        {
          label: "Tomorrow",
          prompt: city ? `What will the weather be tomorrow in ${city}?` : "What will the weather be tomorrow?",
        },
        {
          label: "Another city",
          prompt: city ? "What is the weather in New York?" : "What is the weather in another city?",
        },
        {
          label: "Weekend outlook",
          prompt: city ? `Give me the weekend weather outlook for ${city}` : "Give me the weekend weather outlook",
        },
      ];
    case "news":
      return [
        { label: "More headlines", prompt: "Show me more headlines" },
        { label: "AI news", prompt: "Show me the latest AI news" },
        { label: "Business news", prompt: "Show me the latest business news" },
      ];
    case "web_search":
      return [
        { label: "Summarize this", prompt: cleanedQuery ? `Summarize the search results for ${cleanedQuery}` : "Summarize this" },
        { label: "Show top result", prompt: cleanedQuery ? `Show the top result for ${cleanedQuery}` : "Show top result" },
        { label: "Related search", prompt: cleanedQuery ? `Search the internet for topics related to ${cleanedQuery}` : "Related search" },
      ];
    case "youtube_search":
      return [
        { label: "Show more videos", prompt: cleanedQuery ? `Search YouTube for more ${cleanedQuery}` : "Show more videos" },
        { label: "Another topic", prompt: "Search YouTube for another topic" },
        { label: "Open best match", prompt: cleanedQuery ? `Open the best YouTube match for ${cleanedQuery}` : "Open best match" },
      ];
    case "sports":
      return [
        { label: "Football", prompt: "Show me the latest football news" },
        { label: "NBA", prompt: "Show me the latest NBA news" },
        { label: "Latest scores", prompt: "Show me the latest sports scores" },
      ];
    case "email":
      return [
        { label: "Project update", prompt: "Email John about project update" },
        { label: "Meeting update", prompt: "Email Sarah about meeting update" },
        { label: "Follow-up", prompt: "Email Alex regarding follow-up from today" },
      ];
    default:
      return [
        { label: "Show more", prompt: "Show me more details" },
        { label: "Summarize", prompt: "Summarize that" },
        { label: "Related", prompt: "Show me something related" },
      ];
  }
}

function getLoadingLabel(intent: ChatIntent) {
  if (intent === "weather") {
    return "Looking up the forecast...";
  }

  if (intent === "news") {
    return "Checking the latest headlines...";
  }

  if (intent === "web_search") {
    return "Searching the web...";
  }

  if (intent === "youtube_search") {
    return "Searching YouTube...";
  }

  return "Thinking...";
}

function polishAssistantText(text: string) {
  return text
    .replace(/\bAs an AI[^.?!]*[.?!]?\s*/gi, "")
    .replace(/\bI can't browse the internet[^.?!]*[.?!]?\s*/gi, "")
    .replace(/\bI don't have the ability[^.?!]*[.?!]?\s*/gi, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function extractYouTubeId(url: string) {
  const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&?/]+)/i);
  return match ? match[1] : "";
}

function isYouTubeUrl(url: string) {
  return /(?:youtube\.com|youtu\.be)/i.test(url);
}

function getImagePromptFromMessage(message: string) {
  const trimmed = (message || "").trim();
  const match = trimmed.match(/^(?:create image|create an image|generate image|generate an image|make a picture|make an image|create a picture)\s+(?:of\s+)?(.+)$/i);
  if (!match?.[1]) {
    return null;
  }

  return match[1].trim().replace(/[.!?]+$/g, "");
}

function renderEmbeddedYouTube(url: string, key: string) {
  const videoId = extractYouTubeId(url);
  if (!videoId) {
    return (
      <a key={key} href={url} className="message-link" target="_blank" rel="noreferrer">
        {url}
      </a>
    );
  }

  return (
    <div key={key} className="youtube-embed-card">
      <iframe
        className="youtube-embed-frame"
        src={`https://www.youtube.com/embed/${videoId}`}
        title="YouTube video preview"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
      <a href={url} className="message-link youtube-embed-link" target="_blank" rel="noreferrer">
        Watch on YouTube
      </a>
    </div>
  );
}

type SourceBadgeProps = {
  source: string;
  domain: string;
  faviconUrl: string;
};

function SourceBadge({ source, domain, faviconUrl }: SourceBadgeProps) {
  const [faviconFailed, setFaviconFailed] = useState(false);

  return (
    <span className="source-badge" title={domain}>
      {faviconFailed ? (
        <span className="favicon-fallback" aria-hidden="true">
          {getSourceInitial(source)}
        </span>
      ) : (
        <img
          className="favicon"
          src={faviconUrl}
          alt=""
          aria-hidden="true"
          onError={() => setFaviconFailed(true)}
        />
      )}
      <span>{source}</span>
      <span className="source-domain">· {domain}</span>
    </span>
  );
}

function renderTextWithLinks(text: string) {
  const prepared = sanitizeMarkdown(text);

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ children }) => <h1 className="markdown-heading markdown-heading-1">{children}</h1>,
        h2: ({ children }) => <h2 className="markdown-heading markdown-heading-2">{children}</h2>,
        h3: ({ children }) => <h3 className="markdown-heading markdown-heading-3">{children}</h3>,
        p: ({ children }) => <div className="markdown-paragraph">{children}</div>,
        ul: ({ children }) => <ul className="markdown-list markdown-list-unordered">{children}</ul>,
        ol: ({ children }) => <ol className="markdown-list markdown-list-ordered">{children}</ol>,
        li: ({ children }) => <li className="markdown-list-item">{children}</li>,
        strong: ({ children }) => <strong className="markdown-strong">{children}</strong>,
        em: ({ children }) => <em className="markdown-emphasis">{children}</em>,
        a: ({ href, children }) =>
          href && isYouTubeUrl(href) ? renderEmbeddedYouTube(href, href) : (
            <a href={href} className="message-link" target="_blank" rel="noreferrer">
              {children}
            </a>
          ),
        img: ({ src, alt }) =>
          src ? <img src={src} alt={alt || "Assistant generated"} className="embedded-image" loading="lazy" /> : null,
        code: ({ children }) => <code className="markdown-inline-code">{children}</code>,
      }}
    >
      {prepared}
    </ReactMarkdown>
  );
}

function parseMessageBlocks(text: string): MessageBlock[] {
  const sanitizedText = sanitizeMarkdown(text);
  const emailLines = sanitizedText.split("\n").map((line) => line.trimEnd());
  const emailHeader = emailLines[0]?.trim();
  const emailToLine = emailLines.find((line) => /^To:\s+/i.test(line));
  const emailSubjectLine = emailLines.find((line) => /^Subject:\s+/i.test(line));

  if (emailHeader === "📧 Email Draft" && emailToLine && emailSubjectLine) {
    const recipient = emailToLine.replace(/^To:\s+/i, "").trim();
    const subject = emailSubjectLine.replace(/^Subject:\s+/i, "").trim();
    const bodyStartIndex = emailLines.findIndex((line) => /^Subject:\s+/i.test(line)) + 1;
    const body = emailLines.slice(bodyStartIndex).join("\n").trim();

    if (recipient && subject && body) {
      return [
        {
          type: "email",
          recipient,
          subject,
          body,
        },
      ];
    }
  }

  const blocks = sanitizedText.split(/\n\s*\n/);

  return blocks.reduce<MessageBlock[]>((parsedBlocks, block) => {
    const lines = block
      .split("\n")
      .map((line) => line.trimEnd())
      .filter((line) => line.trim().length > 0);

    const sourceLine = lines.find((line) => SOURCE_LINE_PATTERN.test(line));
    const linkLine = lines.find((line) => LINK_LINE_PATTERN.test(line));

    if (sourceLine && linkLine) {
      const sourceMatch = sourceLine.match(SOURCE_LINE_PATTERN);
      const linkMatch = linkLine.match(LINK_LINE_PATTERN);
      const titleLines = lines.filter((line) => line !== sourceLine && line !== linkLine);

      if (sourceMatch && linkMatch && titleLines.length > 0) {
        const articleUrl = linkMatch[1];
        const articleDomain = getArticleDomain(articleUrl);

        parsedBlocks.push({
          type: "article",
          title: cleanArticleTitle(titleLines.join(" ")),
          source: sourceMatch[1].trim(),
          domain: articleDomain,
          faviconUrl: `https://www.google.com/s2/favicons?domain=${encodeURIComponent(articleDomain)}&sz=32`,
          url: articleUrl,
        });

        return parsedBlocks;
      }
    }

    parsedBlocks.push({ type: "text", content: block });
    return parsedBlocks;
  }, []);
}

function renderBlocks(
  blocks: MessageBlock[],
  options?: {
    streamedTitles?: string[];
    activeArticleIndex?: number | null;
    onEditEmailDraft?: (draft: EmailDraftBlock) => void;
    onReviewEmailDraft?: (draft: EmailDraftBlock) => void;
  }
) {
  let articleIndex = -1;

  return blocks.map((block, blockIndex) => {
    if (block.type === "article") {
      articleIndex += 1;
      const streamedTitle = options?.streamedTitles?.[articleIndex];
      const displayedTitle = streamedTitle ?? block.title;
      const isStreamingCard = options?.activeArticleIndex === articleIndex;

      return (
        <div className="article-card" key={`article-${blockIndex}-${block.url}`}>
          <div className={`article-title${streamedTitle !== undefined ? " streaming" : ""}`}>
            {displayedTitle || "\u00A0"}
            {isStreamingCard ? <span className="typing-cursor" aria-hidden="true" /> : null}
          </div>
          <div className="article-source-row">
            <SourceBadge source={block.source} domain={block.domain} faviconUrl={block.faviconUrl} />
          </div>
          <a className="article-link-row message-link" href={block.url} target="_blank" rel="noreferrer">
            {block.url}
          </a>
        </div>
      );
    }

    if (block.type === "email") {
      return (
        <div className="email-card" key={`email-${blockIndex}-${block.recipient}-${block.subject}`}>
          <div className="email-card-header">
            <span className="email-card-kicker">📧 Email Draft</span>
          </div>
          <div className="email-meta-row">
            <span className="email-meta-label">To:</span>
            <span className="email-meta-value">{block.recipient}</span>
          </div>
          <div className="email-meta-row">
            <span className="email-meta-label">Subject:</span>
            <span className="email-meta-value">{block.subject}</span>
          </div>
          <div className="email-body">{renderTextWithLinks(block.body)}</div>
          <div className="email-actions" aria-label="Email draft actions">
            <button
              className="email-action-button interactive"
              type="button"
              onClick={() => options?.onReviewEmailDraft?.(block)}
            >
              Send
            </button>
            <button
              className="email-action-button secondary interactive"
              type="button"
              onClick={() => options?.onEditEmailDraft?.(block)}
            >
              Edit
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="message-block" key={`text-${blockIndex}`}>
        {renderTextWithLinks(block.content)}
      </div>
    );
  });
}

function renderMessageContent(
  text: string,
  options?: {
    onEditEmailDraft?: (draft: EmailDraftBlock) => void;
    onReviewEmailDraft?: (draft: EmailDraftBlock) => void;
  }
) {
  return renderBlocks(parseMessageBlocks(text), options);
}

function App() {
  const apiBaseUrl = "http://127.0.0.1:8000";
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [memory, setMemory] = useState<MemoryState>(DEFAULT_MEMORY);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [showTypingIndicator, setShowTypingIndicator] = useState(false);
  const [loadingLabel, setLoadingLabel] = useState("Thinking...");
  const [requestError, setRequestError] = useState<string | null>(null);
  const [lastFailedUserMessage, setLastFailedUserMessage] = useState<string | null>(null);
  const [animatedAssistantState, setAnimatedAssistantState] = useState<AnimatedAssistantState | null>(null);
  const [editingDraftLabel, setEditingDraftLabel] = useState<string | null>(null);
  const [activeSpokenMessageId, setActiveSpokenMessageId] = useState<string | null>(null);
  const [autoSpeakEnabled, setAutoSpeakEnabled] = useState(true);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const suppressAbortFeedbackRef = useRef(false);
  const animationIntervalRef = useRef<number | null>(null);
  const availableVoicesRef = useRef<SpeechSynthesisVoice[]>([]);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const storedAutoSpeakEnabled = window.localStorage.getItem(AUTO_SPEAK_STORAGE_KEY);
    if (storedAutoSpeakEnabled === "false") {
      setAutoSpeakEnabled(false);
    }

    const storedSessionId = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (storedSessionId) {
      setSessionId(storedSessionId);
    } else {
      setSessionId(createAndPersistSessionId());
    }

    let restoredMemory = DEFAULT_MEMORY;
    const storedMemory = window.localStorage.getItem(MEMORY_STORAGE_KEY);
    if (storedMemory) {
      try {
        const parsed = JSON.parse(storedMemory) as PersistedMemory | MemoryUpdates;
        const parsedMemory =
          parsed && typeof parsed === "object" && "memory" in parsed
            ? (parsed as PersistedMemory)
            : { sessionId: storedSessionId, memory: parsed as MemoryUpdates };

        if (parsedMemory.sessionId === storedSessionId) {
          restoredMemory = mergeMemory(DEFAULT_MEMORY, parsedMemory.memory);
          setMemory(restoredMemory);
        } else {
          window.localStorage.removeItem(MEMORY_STORAGE_KEY);
        }
      } catch {
        window.localStorage.removeItem(MEMORY_STORAGE_KEY);
      }
    }

    const storedMessages = window.localStorage.getItem(MESSAGES_STORAGE_KEY);
    if (!storedMessages) {
      setMessages([getInitialAssistantMessage(restoredMemory)]);
      return;
    }

    try {
      setMessages(normalizeStoredMessages(JSON.parse(storedMessages)));
    } catch {
      window.localStorage.removeItem(MESSAGES_STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(MESSAGES_STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    const persistedMemory: PersistedMemory = {
      sessionId,
      memory,
    };
    window.localStorage.setItem(MEMORY_STORAGE_KEY, JSON.stringify(persistedMemory));
  }, [memory, sessionId]);

  useEffect(() => {
    window.localStorage.setItem(AUTO_SPEAK_STORAGE_KEY, String(autoSpeakEnabled));
  }, [autoSpeakEnabled]);

  useEffect(() => {
    if (!loading) {
      setShowTypingIndicator(false);
      return;
    }

    const timer = window.setTimeout(() => {
      setShowTypingIndicator(true);
    }, TYPING_INDICATOR_DELAY_MS);

    return () => window.clearTimeout(timer);
  }, [loading]);

  useEffect(() => {
    return () => {
      if (animationIntervalRef.current !== null) {
        window.clearInterval(animationIntervalRef.current);
      }
      window.speechSynthesis?.cancel();
      abortControllerRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    const speechSynthesis = window.speechSynthesis;
    if (!speechSynthesis) {
      return;
    }

    const loadVoices = () => {
      availableVoicesRef.current = speechSynthesis.getVoices();
    };

    loadVoices();
    speechSynthesis.onvoiceschanged = loadVoices;

    return () => {
      if (speechSynthesis.onvoiceschanged === loadVoices) {
        speechSynthesis.onvoiceschanged = null;
      }
    };
  }, []);

  const stopAssistantAnimation = () => {
    if (animationIntervalRef.current !== null) {
      window.clearInterval(animationIntervalRef.current);
      animationIntervalRef.current = null;
    }

    setAnimatedAssistantState(null);
  };

  const addAssistantMessage = (content: string) => {
    const assistantMessage = createAssistantMessage(content);
    setMessages((prev) => [...prev, assistantMessage]);
    startAssistantAnimation(assistantMessage.id, content);
    if (autoSpeakEnabled) {
      speakText(content, assistantMessage.id);
    }
  };

  const stopSpeaking = () => {
    window.speechSynthesis?.cancel();
    setActiveSpokenMessageId(null);
  };

  const getPreferredVoice = () => {
    const speechSynthesis = window.speechSynthesis;
    if (!speechSynthesis) {
      return null;
    }

    const voices = availableVoicesRef.current.length > 0 ? availableVoicesRef.current : speechSynthesis.getVoices();
    return voices.find((voice) => voice.name.includes("Female") || voice.name.includes("Google US English")) || null;
  };

  const speakText = (text: string, messageId?: string) => {
    const speechSynthesis = window.speechSynthesis;
    if (!speechSynthesis) {
      return;
    }

    const speakableText = getSpeakableMessageText(text);
    if (!speakableText) {
      return;
    }

    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(speakableText);
    const voice = getPreferredVoice();

    utterance.lang = voice?.lang || "en-US";
    utterance.voice = voice || null;
    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.volume = 1;
    utterance.onend = () => {
      if (messageId) {
        setActiveSpokenMessageId((current) => (current === messageId ? null : current));
      }
    };
    utterance.onerror = () => {
      if (messageId) {
        setActiveSpokenMessageId((current) => (current === messageId ? null : current));
      }
    };

    console.log("VOICE USED:", voice?.name || "default");
    if (messageId) {
      setActiveSpokenMessageId(messageId);
    }
    speechSynthesis.speak(utterance);
  };

  const toggleMessageSpeech = (message: Message) => {
    if (activeSpokenMessageId === message.id) {
      stopSpeaking();
      return;
    }

    speakText(message.content, message.id);
  };

  const loadEmailDraftIntoComposer = (draft: EmailDraftBlock, label: string) => {
    const formattedDraft = formatDraftForComposer(draft);

    setEditingDraftLabel(label);
    setInput(formattedDraft);

    window.requestAnimationFrame(() => {
      inputRef.current?.focus();
      const nextValueLength = formattedDraft.length;
      inputRef.current?.setSelectionRange(nextValueLength, nextValueLength);
    });
  };

  const handleEditEmailDraft = (draft: EmailDraftBlock) => {
    loadEmailDraftIntoComposer(draft, `Editing draft for ${draft.recipient}`);
  };

  const handleReviewEmailDraft = (draft: EmailDraftBlock) => {
    loadEmailDraftIntoComposer(draft, `Review draft for ${draft.recipient}`);
  };

  const cancelDraftEditing = () => {
    setEditingDraftLabel(null);
    setInput("");
    window.requestAnimationFrame(() => {
      inputRef.current?.focus();
    });
  };

  const startAssistantAnimation = (messageId: string, fullText: string) => {
    stopAssistantAnimation();

    const sanitizedText = sanitizeMarkdown(fullText);

    const parsedBlocks = parseMessageBlocks(sanitizedText);
    const articleBlocks = parsedBlocks.filter((block): block is ArticleBlock => block.type === "article");
    const hasEmailBlock = parsedBlocks.some((block) => block.type === "email");

    if (hasEmailBlock) {
      return;
    }

    if (articleBlocks.length > 0) {
      const titleChunks = articleBlocks.map((block) => getArticleTitleChunks(block.title));
      const displayedTitles = articleBlocks.map(() => "");
      let nextArticleIndex = 0;
      let nextChunkIndex = 0;

      setAnimatedAssistantState({
        messageId,
        mode: "articles",
        blocks: parsedBlocks,
        displayedTitles: [...displayedTitles],
        activeArticleIndex: 0,
      });

      animationIntervalRef.current = window.setInterval(() => {
        if (nextArticleIndex >= titleChunks.length) {
          stopAssistantAnimation();
          return;
        }

        displayedTitles[nextArticleIndex] += titleChunks[nextArticleIndex][nextChunkIndex] ?? "";
        nextChunkIndex += 1;

        const hasMoreChunksInCurrentTitle = nextChunkIndex < titleChunks[nextArticleIndex].length;
        const upcomingArticleIndex = hasMoreChunksInCurrentTitle ? nextArticleIndex : nextArticleIndex + 1;

        setAnimatedAssistantState({
          messageId,
          mode: "articles",
          blocks: parsedBlocks,
          displayedTitles: [...displayedTitles],
          activeArticleIndex: upcomingArticleIndex < titleChunks.length ? upcomingArticleIndex : null,
        });

        if (!hasMoreChunksInCurrentTitle) {
          nextArticleIndex += 1;
          nextChunkIndex = 0;
        }

        if (nextArticleIndex >= titleChunks.length) {
          stopAssistantAnimation();
        }
      }, RESPONSE_CHUNK_DELAY_MS);

      return;
    }

    const chunks = getProgressiveChunks(sanitizedText);
    if (chunks.length <= 1) {
      return;
    }

    let nextChunkIndex = 0;
    let nextText = "";

    setAnimatedAssistantState({
      messageId,
      mode: "text",
      displayedText: "",
    });

    animationIntervalRef.current = window.setInterval(() => {
      nextText += chunks[nextChunkIndex] ?? "";
      nextChunkIndex += 1;
      setAnimatedAssistantState({
        messageId,
        mode: "text",
        displayedText: nextText,
      });

      if (nextChunkIndex >= chunks.length) {
        stopAssistantAnimation();
      }
    }, RESPONSE_CHUNK_DELAY_MS);
  };

  const startNewChat = () => {
    const confirmed = window.confirm(
      "Start a new chat? This clears the current conversation and creates a brand new session immediately."
    );

    if (!confirmed) {
      return;
    }

    suppressAbortFeedbackRef.current = true;
    const nextSessionId = createAndPersistSessionId();
    stopAssistantAnimation();
    stopSpeaking();
    setSessionId(nextSessionId);
    setMemory(DEFAULT_MEMORY);
    setMessages([getInitialAssistantMessage(DEFAULT_MEMORY)]);
    setInput("");
    setEditingDraftLabel(null);
    setRequestError(null);
    setLastFailedUserMessage(null);
    abortControllerRef.current?.abort();
    window.localStorage.removeItem(MESSAGES_STORAGE_KEY);
    window.localStorage.setItem(
      MEMORY_STORAGE_KEY,
      JSON.stringify({ sessionId: nextSessionId, memory: DEFAULT_MEMORY } satisfies PersistedMemory)
    );
  };

  const sessionLabel = sessionId ? "Session active" : "New session on next message";
  const shortSessionId = sessionId ? sessionId.slice(0, 8) : null;
  const statusLabel = retrying
    ? "Retrying once"
    : loading
      ? "Waiting for response"
      : animatedAssistantState
        ? "Rendering response"
      : requestError
        ? requestError
        : activeSpokenMessageId
          ? "Speaking answer"
          : "Connected";
  const statusToneClass = retrying
    ? "status-pill loading"
    : loading
      ? "status-pill loading"
      : animatedAssistantState
        ? "status-pill loading"
      : requestError
        ? "status-pill error"
        : activeSpokenMessageId
          ? "status-pill loading"
          : "status-pill ready";

  const postChatMessage = async (messageText: string, signal: AbortSignal) => {
    // Session ID logic is not needed for backend, only send message
    const requestBody = { message: messageText };
    console.log("Sending message:", messageText);

    for (let attempt = 1; attempt <= 2; attempt += 1) {
      try {
        const res = await fetch(`${apiBaseUrl}/api/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
          signal,
        });

        if (!res.ok) {
          if (attempt === 1 && RETRYABLE_STATUS_CODES.has(res.status)) {
            setRetrying(true);
            await wait(RETRY_DELAY_MS);
            continue;
          }

          throw new Error("Server error");
        }

        const data = await res.json();
        if (!data || typeof data !== "object") {
          throw new Error("Invalid server response");
        }

        if (data.type === "error") {
          throw new Error(typeof data.response === "string" && data.response.trim() ? data.response : "Server error");
        }

        return data;
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          throw error;
        }

        console.error("FETCH ERROR:", error);
        const isNetworkFailure = error instanceof TypeError;
        if (attempt === 1 && isNetworkFailure) {
          setRetrying(true);
          await wait(RETRY_DELAY_MS);
          continue;
        }

        throw error;
      }
    }

    throw new Error("Request failed after retry.");
  };

  const postImageMessage = async (prompt: string) => {
    const response = await fetch(`${apiBaseUrl}/api/image`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ prompt }),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(typeof data?.response === "string" && data.response.trim() ? data.response : "Image generation failed");
    }

    return data;
  };

  const sendMessage = async (overrideMessage?: string) => {
    if (loading) {
      return;
    }

    const rawMessageText = (overrideMessage ?? input).trim();
    if (!rawMessageText) return;
    const imagePrompt = getImagePromptFromMessage(rawMessageText);

    let effectiveMessageText = rawMessageText;
    const followUpCityMatch = rawMessageText.match(/what about\s+(.+)$/i);

    if (followUpCityMatch?.[1] && memory.lastIntent === "weather") {
      const city = followUpCityMatch[1].trim().replace(/[.!?]+$/g, "");
      if (city) {
        effectiveMessageText = `weather in ${city}`;
      }
    }

    const memoryUpdates: MemoryUpdates = {
      ...extractMemory(rawMessageText),
      ...extractMemory(effectiveMessageText),
    };
    const nextMemory = mergeMemory(memory, memoryUpdates);

    const userMessage: Message = {
      id: createMessageId(),
      role: "user",
      content: rawMessageText,
      timestamp: Date.now(),
    };
    stopSpeaking();
    setMessages((prev) => [...prev, userMessage]);
    setMemory(nextMemory);
    setInput("");
    setEditingDraftLabel(null);
    setRequestError(null);
    setLastFailedUserMessage(null);
    stopAssistantAnimation();

    const emailDraftRequest = extractEmailDraftRequest(rawMessageText);
    if (emailDraftRequest) {
      const draft = buildEmailDraft(
        emailDraftRequest.recipient,
        emailDraftRequest.topic,
        nextMemory.name,
        emailDraftRequest.body
      );
      addAssistantMessage(
        formatEmailDraftMessage(draft.recipient, draft.subject, draft.body)
      );
      return;
    }

    setLoading(true);
    setRetrying(false);
    setLoadingLabel(imagePrompt ? "Generating image..." : getLoadingLabel(getIntent(effectiveMessageText)));
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const data = imagePrompt
        ? await postImageMessage(imagePrompt)
        : await postChatMessage(effectiveMessageText, abortController.signal);

      if (data.session_id && data.session_id !== sessionId) {
        setSessionId(data.session_id);
        window.localStorage.setItem(SESSION_STORAGE_KEY, data.session_id);
      }

      setRequestError(null);

      const assistantReply = polishAssistantText(
        (typeof data?.summary === "string" && data.summary.trim()) ||
        (typeof data?.message === "string" && data.message.trim()) ||
        (typeof data?.reply === "string" && data.reply.trim()) ||
        (typeof data?.error === "string" && data.error.trim()) ||
        ""
      );

      if (!assistantReply) {
        return;
      }

      const assistantMessageId = createMessageId();

      setMessages((prev) => [
        ...prev,
        {
          id: assistantMessageId,
          role: "ai",
          content: assistantReply,
          response: data && typeof data === "object" ? (data as AssistantResponse) : null,
          timestamp: Date.now(),
        },
      ]);
      startAssistantAnimation(assistantMessageId, assistantReply);
      if (autoSpeakEnabled) {
        speakText(assistantReply, assistantMessageId);
      }
    } catch (err) {
      const wasAborted = err instanceof DOMException && err.name === "AbortError";
      if (wasAborted && suppressAbortFeedbackRef.current) {
        return;
      }

      const errorMessage = wasAborted
        ? "Request canceled."
        : err instanceof TypeError
          ? "Connection failed"
          : err instanceof Error && err.message === "Server error"
            ? "Connection failed"
            : err instanceof Error && err.message.trim()
              ? err.message
              : "Connection failed";
      setRequestError(errorMessage);
      setLastFailedUserMessage(rawMessageText);
      setMessages((prev) => {
        if (wasAborted) {
          return prev;
        }

        return [
          ...prev,
          {
            id: createMessageId(),
            role: "ai",
            content: errorMessage,
            timestamp: Date.now(),
          },
        ];
      });
    } finally {
      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
      }
      suppressAbortFeedbackRef.current = false;
      setLoading(false);
      setLoadingLabel("Thinking...");
      setRetrying(false);
    }
  };

  const cancelRequest = () => {
    abortControllerRef.current?.abort();
  };

  const resendLastFailedMessage = () => {
    if (!lastFailedUserMessage || loading) {
      return;
    }

    void sendMessage(lastFailedUserMessage);
  };

  const handleSuggestionClick = (prompt: string) => {
    if (loading) {
      return;
    }

    setInput(prompt);
    void sendMessage(prompt);
  };

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <div className="header-copy">
            <h1 className="title">OmniCore AI</h1>
            <div className="session-meta">
              <p className="session-indicator">{sessionLabel}</p>
              {shortSessionId ? <span className="session-chip">ID {shortSessionId}</span> : null}
              <span className={statusToneClass}>{statusLabel}</span>
            </div>
          </div>
          <div className="header-actions">
            <label className="speech-setting-toggle">
              <input
                type="checkbox"
                checked={autoSpeakEnabled}
                onChange={(event) => setAutoSpeakEnabled(event.target.checked)}
              />
              <span>Auto-read</span>
            </label>
            {loading ? (
              <button className="secondary-button cancel-button" onClick={cancelRequest} type="button">
                Cancel reply
              </button>
            ) : null}
            <button className="secondary-button" onClick={startNewChat} type="button">
              New chat
            </button>
          </div>
        </div>
        <div className="chat-box">
          {messages.map((msg, index) => {
            const previousMessage = index > 0 ? messages[index - 1] : null;
            const currentDateLabel = formatDateLabel(msg.timestamp);
            const previousDateLabel = previousMessage ? formatDateLabel(previousMessage.timestamp) : null;
            const shouldRenderDateDivider = currentDateLabel !== previousDateLabel;
            const assistantAnimation =
              msg.role === "ai" && animatedAssistantState?.messageId === msg.id ? animatedAssistantState : null;
            const isLatestAssistantMessage =
              msg.role === "ai" && messages.slice(index + 1).every((message) => message.role !== "ai");
            const lastUserMessage =
              messages
                .slice(0, index)
                .reverse()
                .find((message) => message.role === "user")?.content ?? "";
            const suggestions = isLatestAssistantMessage
              ? getSuggestions(getIntent(lastUserMessage), lastUserMessage).slice(0, 3)
              : [];

            return (
              <Fragment key={msg.id}>
                {shouldRenderDateDivider ? <div className="date-divider">{currentDateLabel}</div> : null}
                <div className={`message ${msg.role === "user" ? "user" : "ai"}`}>
                  <div className="message-header-row">
                    <div className="message-time">{formatTime(msg.timestamp)}</div>
                    {msg.role === "ai" ? (
                      <button
                        className={`message-audio-button${activeSpokenMessageId === msg.id ? " active" : ""}`}
                        type="button"
                        onClick={() => toggleMessageSpeech(msg)}
                      >
                        {activeSpokenMessageId === msg.id ? "■ Stop" : "🔊 Listen"}
                      </button>
                    ) : null}
                  </div>
                  {assistantAnimation?.mode === "text"
                    ? renderTextWithLinks(assistantAnimation.displayedText)
                    : assistantAnimation?.mode === "articles"
                      ? renderBlocks(assistantAnimation.blocks, {
                          streamedTitles: assistantAnimation.displayedTitles,
                          activeArticleIndex: assistantAnimation.activeArticleIndex,
                          onEditEmailDraft: handleEditEmailDraft,
                          onReviewEmailDraft: handleReviewEmailDraft,
                        })
                      : renderMessageContent(msg.content, {
                          onEditEmailDraft: handleEditEmailDraft,
                          onReviewEmailDraft: handleReviewEmailDraft,
                        })}
                  {msg.role === "ai" ? renderStructuredResponse(msg.response) : null}
                  {assistantAnimation?.mode === "text" ? <span className="typing-cursor" aria-hidden="true" /> : null}
                  {msg.role === "ai" && !assistantAnimation && suggestions.length > 0 ? (
                    <div className="suggestions" role="group" aria-label="Suggested follow-up questions">
                      {suggestions.map((suggestion) => (
                        <button
                          key={`${msg.id}-${suggestion.label}`}
                          className="suggestion-chip"
                          type="button"
                          onClick={() => handleSuggestionClick(suggestion.prompt)}
                        >
                          {suggestion.label}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              </Fragment>
            );
          })}
          {showTypingIndicator && <div className="message ai loading-bubble">{loadingLabel}</div>}
          {requestError && lastFailedUserMessage ? (
            <div className="retry-banner">
              <span>{requestError === "Request canceled." ? "Last message was canceled." : "Last message failed to send."}</span>
              <button className="secondary-button retry-button" onClick={resendLastFailedMessage} type="button">
                Resend
              </button>
            </div>
          ) : null}
          <div ref={chatEndRef} />
        </div>
        <ChatInput
          key={sessionId ?? "chat-input"}
          value={input}
          isLoading={loading}
          inputRef={inputRef}
          editingDraftLabel={editingDraftLabel}
          onCancelDraft={cancelDraftEditing}
          onChange={setInput}
          onSend={sendMessage}
        />
      </div>
    </div>
  );
}

export default App;
