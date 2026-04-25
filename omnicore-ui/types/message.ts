export type MessageRole = "user" | "system";

export type MessageType =
  | "summary"
  | "analysis"
  | "recommendation"
  | "web_search"
  | "youtube_search"
  | "weather"
  | "news"
  | "general"
  | "error";

export type MessageTool = "news" | "finance" | "weather" | "search" | "general" | "multi";

export type MessageSection = {
  title?: string;
  body?: string;
};

export type MessageExecution = {
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

export type AnalysisContent = {
  summary?: string;
  insight?: string;
  actions?: string[];
  tags?: string[];
  executions?: MessageExecution[];
  confidence?: string;
  sections?: MessageSection[];
};

export type SearchResultItem = {
  title: string;
  link: string;
  snippet: string;
  source?: string;
};

export type SearchResultsContent = {
  data: SearchResultItem[];
  query?: string;
  summary?: string;
  insight?: string;
  actions?: string[];
};

export type WebSearchContent = SearchResultsContent;

export type VideoResultItem = {
  videoId: string;
  title: string;
  channel: string;
  thumbnail: string;
  url: string;
  embedUrl: string;
  snippet: string;
};

export type VideoResultsContent = {
  data: VideoResultItem[];
  query?: string;
  summary?: string;
  insight?: string;
  actions?: string[];
};

export type YouTubeSearchContent = VideoResultsContent;

export type WeatherForecastDay = {
  date?: string;
  day?: string;
  condition?: string;
  description?: string;
  summary?: string;
  temp?: number;
  temperature?: number;
  min_temp?: number;
  max_temp?: number;
  humidity?: number;
};

export type WeatherContent = {
  summary?: string;
  insight?: string;
  actions?: string[];
  city?: string;
  country?: string;
  description?: string;
  temperature?: number;
  temp?: number;
  feels_like?: number;
  humidity?: number;
  request_type?: string;
  forecast_days?: WeatherForecastDay[];
};

export type NewsContent = {
  data: SearchResultItem[];
  query?: string;
  summary?: string;
  insight?: string;
  actions?: string[];
};

export type GeneralContent = AnalysisContent;

export type ErrorContent = {
  message?: string;
  summary?: string;
  insight?: string;
  actions?: string[];
  confidence?: string;
};

export type MessageContent =
  | string
  | string[]
  | AnalysisContent
  | SearchResultsContent
  | VideoResultsContent
  | WeatherContent
  | NewsContent
  | GeneralContent
  | ErrorContent
  | Record<string, unknown>
  | null;

export type Message = {
  id: string;
  role: MessageRole;
  type: MessageType;
  content: MessageContent;
  metadata?: {
    tool?: MessageTool;
    followUp?: boolean;
    statuses?: string[];
  };
  timestamp: number;
};