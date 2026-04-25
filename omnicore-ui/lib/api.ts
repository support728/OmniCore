export type AssistantExecution = {
  type: "copy_text" | "open_weather" | "web_search" | "youtube_search";
  query?: string;
  text?: string;
  city?: string;
  label?: string;
  success_summary?: string;
  success_insight?: string;
  failure_summary?: string;
  failure_insight?: string;
  blocked_summary?: string;
  blocked_insight?: string;
  tool?: string;
};

export type AssistantResponse = {
  type: string;
  summary?: string;
  data?: {
    intent?: string;
    tool?: string;
    query?: string;
    actions?: string[];
    results?: SearchResult[] | VideoResult[];
    city?: string;
    country?: string;
    description?: string;
    temperature?: number;
    temp?: number;
    feels_like?: number;
    humidity?: number;
    request_type?: string;
    forecast_days?: Array<Record<string, unknown>>;
    weather?: {
      city?: string;
      country?: string;
      description?: string;
      temperature?: number;
      temp?: number;
      feels_like?: number;
      humidity?: number;
      request_type?: string;
      forecast_days?: Array<Record<string, unknown>>;
    };
    articles?: Array<Record<string, unknown>>;
    insight?: string;
    tags?: string[];
    executions?: AssistantExecution[];
    confidence?: string;
    sections?: Array<{ title?: string; body?: string }>;
  };
  session_id?: string;
};

type SendMessageOptions = {
  timeoutMs?: number;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

const LAST_WEATHER_CITY_KEY = "omnicore-last-weather-city";

export type SearchResult = {
  title: string;
  link: string;
  snippet: string;
  source?: string;
};

export type SearchResponse = {
  type?: string;
  summary: string;
  results: SearchResult[];
};

export type VideoResult = {
  videoId: string;
  title: string;
  channel: string;
  thumbnail: string;
  url: string;
  embedUrl: string;
  snippet: string;
};

export type VideoResponse = {
  type?: string;
  summary: string;
  results: VideoResult[];
};

export async function sendMessage(
  query: string,
  sessionId: string,
  userId: string,
  preferredMediaPlatform: string | null,
  options?: SendMessageOptions,
) {
  const controller = new AbortController();
  const timeoutMs = options?.timeoutMs ?? 0;
  const timeoutId =
    timeoutMs > 0
      ? window.setTimeout(() => {
          controller.abort();
        }, timeoutMs)
      : null;


  let res: Response;
  try {
    res = await fetch("https://omnicore-backend.onrender.com/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      mode: "cors",
      body: JSON.stringify({
        message: query,
      }),
    });
  } catch (error) {
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
    }

    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(`Request timed out after ${timeoutMs}ms`);
    }

    throw error;
  }

  if (timeoutId !== null) {
    window.clearTimeout(timeoutId);
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Request failed");
  }

  return (await res.json()) as AssistantResponse;
}
