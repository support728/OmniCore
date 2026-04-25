import { Fragment, useEffect, useRef, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import { ProgressiveText } from "@/components/progressive-text";
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import type {
  AnalysisContent,
  ErrorContent,
  GeneralContent,
  Message,
  MessageExecution,
  NewsContent,
  SearchResultsContent,
  VideoResultItem,
  VideoResultsContent,
  WeatherContent,
  WeatherForecastDay,
} from "@/types/message";

const URL_PATTERN = /(https?:\/\/[^\s<]+)/gi;
const SOURCE_LINE_PATTERN = /^\s*Source:\s+(.+)$/i;
const LINK_LINE_PATTERN = /^\s*Link:\s+(https?:\/\/\S+)$/i;

function sanitizeMarkdown(content: string) {
  return content
    .replace(/\r\n/g, "\n")
    .replace(/([^\n])\s*(#{2,6})\s+/g, "$1\n\n$2 ")
    .replace(/(#{2,6}\s.*)/g, "\n\n$1\n")
    .replace(/#{3,}/g, (match) => (match.length > 3 ? "###" : match))
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function prepareMarkdownForDisplay(text: string) {
  return convertPlainUrlsToAnchors(sanitizeMarkdown(text))
    .replace(/^###\s+(.+)$/gm, "<h3>$1</h3>")
    .replace(/^##\s+(.+)$/gm, "<h2>$1</h2>")
    .replace(/^#\s+(.+)$/gm, "<h1>$1</h1>");
}

function convertPlainUrlsToAnchors(text: string) {
  return text.replace(URL_PATTERN, (match) => {
    const { url, trailing } = splitUrlSuffix(match);
    if (!url) {
      return match;
    }

    return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>${trailing}`;
  });
}

function renderMarkdownBlock(
  text: string,
  options?: {
    textClassName?: string;
    linkClassName?: string;
  }
) {
  const textClassName = options?.textClassName ?? "text-[15px] leading-[1.6] text-slate-600";
  const linkClassName =
    options?.linkClassName ?? "text-sky-700 underline underline-offset-4 break-all transition hover:text-sky-800";

  return (
    <ReactMarkdown
      rehypePlugins={[rehypeRaw]}
      components={{
        h1: ({ children }) => <h1 className="text-[15px] font-semibold leading-7 text-slate-800">{children}</h1>,
        h2: ({ children }) => <h2 className="text-[15px] font-semibold leading-7 text-slate-800">{children}</h2>,
        h3: ({ children }) => <h3 className="text-[15px] font-semibold leading-7 text-slate-700">{children}</h3>,
        p: ({ children }) => <p className={`${textClassName} mb-2 last:mb-0`}>{children}</p>,
        ul: ({ children }) => <ul className="space-y-1 pl-4 text-[15px] leading-[1.6] text-slate-600 list-disc">{children}</ul>,
        ol: ({ children }) => <ol className="space-y-1 pl-4 text-[15px] leading-[1.6] text-slate-600 list-decimal">{children}</ol>,
        li: ({ children }) => <li className="pl-0.5 marker:text-slate-400">{children}</li>,
        strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
        em: ({ children }) => <em className="italic text-slate-700">{children}</em>,
        a: ({ href, children }) => (
          <a href={href} className={linkClassName} target="_blank" rel="noreferrer">
            {children}
          </a>
        ),
      }}
    >
      {prepareMarkdownForDisplay(text)}
    </ReactMarkdown>
  );
}

function splitUrlSuffix(value: string) {
  let url = value;
  let trailing = "";

  while (url.length > 0 && /[),.!?:;]$/.test(url)) {
    trailing = `${url.slice(-1)}${trailing}`;
    url = url.slice(0, -1);
  }

  return { url, trailing };
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

type SourceBadgeProps = {
  source: string;
  domain: string;
  faviconUrl: string;
};

function SourceBadge({ source, domain, faviconUrl }: SourceBadgeProps) {
  const [faviconFailed, setFaviconFailed] = useState(false);

  return (
    <span
      className="inline-flex min-h-6 items-center gap-1 rounded-full border border-slate-200 bg-slate-100 px-2 py-1 text-[11px] font-semibold tracking-[0.01em] text-slate-600"
      title={domain}
    >
      {faviconFailed ? (
        <span
          className="flex h-[14px] w-[14px] items-center justify-center rounded-full bg-slate-200 text-[10px] text-slate-600"
          aria-hidden="true"
        >
          {getSourceInitial(source)}
        </span>
      ) : (
        <img
          className="h-[14px] w-[14px]"
          src={faviconUrl}
          alt=""
          aria-hidden="true"
          onError={() => setFaviconFailed(true)}
        />
      )}
      <span>{source}</span>
      <span className="ml-0.5 text-[11px] font-medium text-slate-400">· {domain}</span>
    </span>
  );
}

type SearchResultsPanelProps = {
  message: Message;
  content: SearchResultsContent;
  title: string;
  kicker: string;
  activeClassName: string;
  hoverClassName: string;
  onActionClick?: (message: Message, action: string) => void;
  animateSummary?: boolean;
  actions?: string[];
  showActionChips?: boolean;
};

function ActionChips({
  message,
  actions,
  onActionClick,
  show = true,
}: {
  message: Message;
  actions?: string[];
  onActionClick?: (message: Message, action: string) => void;
  show?: boolean;
}) {
  if (!show || !actions?.length) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2.5 pt-1">
      {actions.map((action) => (
        <button
          key={action}
          type="button"
          onClick={() => onActionClick?.(message, action)}
          className="rounded-full border border-slate-300 bg-white px-3.5 py-2 text-xs font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-100"
        >
          {action}
        </button>
      ))}
    </div>
  );
}

function SearchResultsPanel({ message, content, title, kicker, activeClassName, hoverClassName, onActionClick, animateSummary = false, actions, showActionChips = true }: SearchResultsPanelProps) {
  const results = Array.isArray(content.data) ? content.data : [];
  const sanitizedSummary = content.summary ? sanitizeMarkdown(content.summary) : "";
  const [activeLink, setActiveLink] = useState<string | null>(results[0]?.link ?? null);

  useEffect(() => {
    if (!results.length) {
      setActiveLink(null);
      return;
    }

    if (!results.some((result) => result.link === activeLink)) {
      setActiveLink(results[0]?.link ?? null);
    }
  }, [activeLink, results]);

  const activeResult = results.find((result) => result.link === activeLink) ?? results[0] ?? null;
  const activeDomain = activeResult ? getArticleDomain(activeResult.link) : "";
  const activeSource = activeResult?.source?.trim() || activeDomain;
  const activeFaviconUrl = activeDomain
    ? `https://www.google.com/s2/favicons?domain=${encodeURIComponent(activeDomain)}&sz=32`
    : "";

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-5 shadow-sm">
      <div className="space-y-4 text-sm leading-7 text-slate-700">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">{kicker}</p>
        {content.query ? (
          <div className="text-xl font-bold leading-8 text-slate-950">{title} for “{content.query}”</div>
        ) : null}
        {sanitizedSummary ? (
          <ProgressiveText
            text={sanitizedSummary}
            animate={animateSummary}
            renderText={(value) => renderStructuredText(value)}
          />
        ) : null}
        {activeResult ? (
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
            <div className="space-y-3">
              <div className="space-y-2">
                <p className="text-base font-semibold leading-6 text-slate-950">{activeResult.title?.trim() || activeResult.link}</p>
                {activeSource ? (
                  <SourceBadge
                    source={activeSource}
                    domain={activeDomain}
                    faviconUrl={activeFaviconUrl}
                  />
                ) : null}
              </div>
              <div className="text-sm leading-6 text-slate-600">{renderTextWithLinks(activeResult.snippet)}</div>
              <a
                href={activeResult.link}
                target="_blank"
                rel="noopener noreferrer"
                className="break-all text-xs font-medium text-sky-700 underline underline-offset-4 transition hover:text-sky-800"
              >
                {activeResult.link}
              </a>
            </div>
          </div>
        ) : null}
        {results.length ? (
          <div className="grid gap-3">
            {results.map((result) => {
              const isActive = result.link === activeResult?.link;
              const domain = getArticleDomain(result.link);
              const source = result.source?.trim() || domain;
              const faviconUrl = `https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=32`;

              return (
                <button
                  key={`${result.link}-${result.title}`}
                  type="button"
                  onClick={() => setActiveLink(result.link)}
                  className={`rounded-2xl border bg-white p-4 text-left transition ${hoverClassName} ${
                    isActive ? activeClassName : "border-slate-200"
                  }`}
                >
                  <div className="space-y-2.5">
                    <p className="text-sm font-semibold leading-6 text-slate-950">{result.title?.trim() || result.link}</p>
                    {source ? (
                      <div>
                        <SourceBadge source={source} domain={domain} faviconUrl={faviconUrl} />
                      </div>
                    ) : null}
                    <div className="text-sm leading-6 text-slate-600">{renderTextWithLinks(result.snippet)}</div>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-slate-500">No search results were returned.</p>
        )}
        <ActionChips message={message} actions={actions ?? content.actions} onActionClick={onActionClick} show={showActionChips} />
      </div>
    </div>
  );
}

type VideoResultsPanelProps = {
  message: Message;
  content: VideoResultsContent;
  onActionClick?: (message: Message, action: string) => void;
  animateSummary?: boolean;
  actions?: string[];
  showActionChips?: boolean;
};

function VideoResultsPanel({ message, content, onActionClick, animateSummary = false, actions, showActionChips = true }: VideoResultsPanelProps) {
  const results = Array.isArray(content.data) ? content.data : [];
  const sanitizedSummary = content.summary ? sanitizeMarkdown(content.summary) : "";
  const [activeVideoId, setActiveVideoId] = useState<VideoResultItem["videoId"] | null>(results[0]?.videoId ?? null);

  useEffect(() => {
    if (!results.length) {
      setActiveVideoId(null);
      return;
    }

    if (!results.some((result) => result.videoId === activeVideoId)) {
      setActiveVideoId(results[0]?.videoId ?? null);
    }
  }, [activeVideoId, results]);

  const activeVideo = results.find((result) => result.videoId === activeVideoId) ?? results[0] ?? null;

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-5 shadow-sm">
      <div className="space-y-4 text-sm leading-7 text-slate-700">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">Video Results</p>
        {content.query ? (
          <div className="text-xl font-bold leading-8 text-slate-950">YouTube videos for “{content.query}”</div>
        ) : null}
        {sanitizedSummary ? (
          <ProgressiveText
            text={sanitizedSummary}
            animate={animateSummary}
            renderText={(value) => renderStructuredText(value)}
          />
        ) : null}
        {activeVideo ? (
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
            <div className="grid gap-4 p-4 md:grid-cols-[220px_minmax(0,1fr)]">
              <div className="overflow-hidden rounded-2xl bg-slate-100">
                <img src={activeVideo.thumbnail} alt={activeVideo.title} className="h-full w-full object-cover" />
              </div>
              <div className="space-y-3">
                <p className="text-lg font-semibold leading-7 text-slate-950">{activeVideo.title}</p>
                {activeVideo.channel ? (
                  <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">{activeVideo.channel}</p>
                ) : null}
                <div className="text-sm leading-6 text-slate-600">{renderTextWithLinks(activeVideo.snippet)}</div>
                <a
                  href={activeVideo.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="break-all text-xs font-medium text-sky-700 underline underline-offset-4 transition hover:text-sky-800"
                >
                  {activeVideo.url}
                </a>
              </div>
            </div>
          </div>
        ) : null}
        {results.length ? (
          <div className="grid gap-3">
            {results.map((result) => {
              const isActive = result.videoId === activeVideo?.videoId;

              return (
                <button
                  key={result.videoId}
                  type="button"
                  onClick={() => setActiveVideoId(result.videoId)}
                  className={`grid grid-cols-[120px_minmax(0,1fr)] gap-4 rounded-2xl border bg-white p-3 text-left transition hover:border-rose-300 hover:bg-rose-50/30 ${
                    isActive ? "border-rose-300 ring-1 ring-rose-200" : "border-slate-200"
                  }`}
                >
                  <div className="overflow-hidden rounded-xl bg-slate-200">
                    <img src={result.thumbnail} alt={result.title} className="h-full w-full object-cover" />
                  </div>
                  <div className="min-w-0 space-y-1.5">
                    <p className="text-sm font-semibold leading-6 text-slate-950">{result.title}</p>
                    {result.channel ? <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">{result.channel}</p> : null}
                    <div className="text-sm leading-6 text-slate-600">{renderTextWithLinks(result.snippet)}</div>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-slate-500">No YouTube results were returned.</p>
        )}
        <ActionChips message={message} actions={actions ?? content.actions} onActionClick={onActionClick} show={showActionChips} />
      </div>
    </div>
  );
}

function formatWeatherValue(value?: number) {
  return typeof value === "number" ? `${Math.round(value)}°F` : "--";
}

function formatForecastLabel(day: WeatherForecastDay, index: number) {
  if (typeof day.day === "string" && day.day.trim()) {
    return day.day;
  }
  if (typeof day.date === "string" && day.date.trim()) {
    return day.date;
  }
  return `Day ${index + 1}`;
}

type WeatherPanelProps = {
  message: Message;
  content: WeatherContent;
  onActionClick?: (message: Message, action: string) => void;
  animateSummary?: boolean;
  actions?: string[];
  showActionChips?: boolean;
};

function WeatherPanel({ message, content, onActionClick, animateSummary = false, actions, showActionChips = true }: WeatherPanelProps) {
  const forecastDays = Array.isArray(content.forecast_days) ? content.forecast_days : [];
  const temperature = content.temperature ?? content.temp;
  const sanitizedSummary = content.summary ? sanitizeMarkdown(content.summary) : "";

  return (
    <div className="rounded-2xl border border-cyan-200 bg-cyan-50/60 px-5 py-5 shadow-sm">
      <div className="space-y-4 text-sm leading-7 text-slate-700">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-cyan-700">Weather</p>
        {content.city ? (
          <div className="flex flex-wrap items-end justify-between gap-4 rounded-2xl border border-cyan-200 bg-white px-4 py-4">
            <div>
              <p className="text-xl font-bold leading-8 text-slate-950">
                {content.city}
                {content.country ? `, ${content.country}` : ""}
              </p>
              {content.description ? <p className="text-sm leading-6 text-slate-600">{content.description}</p> : null}
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold text-slate-950">{formatWeatherValue(temperature)}</p>
              {content.request_type ? (
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-cyan-700">{content.request_type}</p>
              ) : null}
            </div>
          </div>
        ) : null}
        {sanitizedSummary ? (
          <ProgressiveText
            text={sanitizedSummary}
            animate={animateSummary}
            renderText={(value) => renderStructuredText(value)}
          />
        ) : null}
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/80 bg-white px-4 py-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">Temperature</p>
            <p className="mt-1 text-lg font-semibold text-slate-950">{formatWeatherValue(temperature)}</p>
          </div>
          <div className="rounded-2xl border border-white/80 bg-white px-4 py-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">Feels Like</p>
            <p className="mt-1 text-lg font-semibold text-slate-950">{formatWeatherValue(content.feels_like)}</p>
          </div>
          <div className="rounded-2xl border border-white/80 bg-white px-4 py-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">Humidity</p>
            <p className="mt-1 text-lg font-semibold text-slate-950">
              {typeof content.humidity === "number" ? `${Math.round(content.humidity)}%` : "--"}
            </p>
          </div>
        </div>
        {forecastDays.length ? (
          <div className="space-y-3 rounded-2xl border border-cyan-200 bg-white px-4 py-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-700">Forecast</p>
            <div className="grid gap-3 md:grid-cols-3">
              {forecastDays.map((day, index) => (
                <div key={`${formatForecastLabel(day, index)}-${index}`} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <p className="text-sm font-semibold text-slate-950">{formatForecastLabel(day, index)}</p>
                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    {day.summary ?? day.description ?? day.condition ?? "Forecast available"}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-3 text-xs font-medium text-slate-500">
                    <span>High {formatWeatherValue(day.max_temp ?? day.temperature ?? day.temp)}</span>
                    <span>Low {formatWeatherValue(day.min_temp)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
        <ActionChips message={message} actions={actions ?? content.actions} onActionClick={onActionClick} show={showActionChips} />
      </div>
    </div>
  );
}

type GeneralPanelProps = {
  message: Message;
  content: GeneralContent;
  label: string;
  statuses: string[];
  isSpeaking: boolean;
  activeExecutionKey: string | null;
  onToggleAudio?: (message: Message) => void;
  onActionClick?: (message: Message, action: string) => void;
  onExecutionClick?: (message: Message, execution: MessageExecution) => void;
  setActiveExecutionKey: Dispatch<SetStateAction<string | null>>;
  resetTimerRef: { current: number | null };
  animateSummary?: boolean;
  actions?: string[];
  showActionChips?: boolean;
};

function GeneralPanel({
  message,
  content,
  label,
  statuses,
  isSpeaking,
  activeExecutionKey,
  onToggleAudio,
  onActionClick,
  onExecutionClick,
  setActiveExecutionKey,
  resetTimerRef,
  animateSummary = false,
  actions,
  showActionChips = true,
}: GeneralPanelProps) {
  const executions = content.executions ?? [];
  const tags = content.tags ?? [];
  const sanitizedSummary = content.summary ? sanitizeMarkdown(content.summary) : "";

  const handleExecutionClick = (execution: MessageExecution, key: string) => {
    onExecutionClick?.(message, execution);
    setActiveExecutionKey(key);

    if (resetTimerRef.current !== null) {
      window.clearTimeout(resetTimerRef.current);
    }

    resetTimerRef.current = window.setTimeout(() => {
      setActiveExecutionKey((current: string | null) => (current === key ? null : current));
      resetTimerRef.current = null;
    }, 1800);
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-5 shadow-sm">
      <div className="space-y-4 text-sm leading-7 text-slate-700">
        {message.role === "system" ? (
          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => onToggleAudio?.(message)}
              className="rounded-full border border-slate-300 bg-white px-3.5 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-600 transition hover:border-slate-400 hover:bg-slate-100"
            >
              {isSpeaking ? "Stop" : "Listen"}
            </button>
          </div>
        ) : null}
        {statuses.length ? (
          <div className="space-y-1.5">
            {statuses.slice(-3).map((status) => (
              <p
                key={status}
                className="animate-fade-in text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400"
              >
                {status}
              </p>
            ))}
          </div>
        ) : null}
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</p>
        {sanitizedSummary ? (
          <ProgressiveText
            text={sanitizedSummary}
            animate={animateSummary}
            className="animate-fade-in whitespace-pre-wrap text-xl font-bold leading-8 text-slate-950"
            renderText={(value) =>
              renderStructuredText(value, {
                textClassName: "text-xl font-bold leading-8 text-slate-950",
                linkClassName: "text-sky-700 underline underline-offset-4 break-all transition hover:text-sky-800",
              })
            }
          />
        ) : null}
        {content.insight ? <div className="animate-fade-in">{renderStructuredText(content.insight)}</div> : null}
        {tags.length ? (
          <div className="animate-fade-in flex flex-wrap gap-2">
            {tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-[11px] font-semibold tracking-[0.02em] text-violet-800"
              >
                {tag}
              </span>
            ))}
          </div>
        ) : null}
        {content.sections?.length ? (
          <div className="animate-fade-in space-y-4 rounded-xl border border-slate-200 bg-white p-4">
            {content.sections.map((section) => (
              <div key={`${section.title}-${section.body}`} className="space-y-1.5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                      {section.title}
                    </p>
                    {getSectionProviderBadge(section.title) ? (
                      <span className="inline-flex items-center rounded-full border border-sky-200 bg-sky-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-sky-700">
                        {getSectionProviderBadge(section.title)}
                      </span>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {getSectionQuickActions(section.title, executions).map((execution) => {
                      const executionKey = `section-${section.title}-${execution.label ?? execution.query ?? execution.text ?? execution.city}`;
                      const isActive = activeExecutionKey === executionKey;

                      return (
                        <button
                          key={executionKey}
                          type="button"
                          onClick={() => handleExecutionClick(execution, executionKey)}
                          className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold transition ${
                            isActive
                              ? "border-slate-900 bg-slate-900 text-white hover:border-slate-900 hover:bg-slate-900"
                              : "border-slate-200 bg-slate-100 text-slate-700 hover:border-slate-300 hover:bg-slate-200"
                          }`}
                        >
                          {isActive ? getExecutionSuccessLabel(execution) : getExecutionLabel(execution)}
                        </button>
                      );
                    })}
                  </div>
                </div>
                <div>{renderStructuredText(section.body ?? "")}</div>
              </div>
            ))}
          </div>
        ) : null}
        {showActionChips && (actions ?? content.actions)?.length ? (
          <div className="animate-fade-in flex flex-wrap gap-2.5 pt-1">
            {(actions ?? content.actions)?.map((action) => (
              <button
                key={action}
                type="button"
                onClick={() => onActionClick?.(message, action)}
                className="rounded-full border border-slate-300 bg-white px-3.5 py-2 text-xs font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-100"
              >
                {action}
              </button>
            ))}
          </div>
        ) : null}
        {executions.length ? (
          <div className="animate-fade-in flex flex-wrap gap-2.5 pt-1">
            {executions.map((execution, index) => {
              const appearance = getExecutionAppearance(execution);
              const executionKey = `${execution.type}-${execution.label ?? execution.query ?? execution.text ?? execution.city ?? index}`;
              const isActive = activeExecutionKey === executionKey;

              return (
                <button
                  key={executionKey}
                  type="button"
                  onClick={() => handleExecutionClick(execution, executionKey)}
                  className={`inline-flex items-center gap-2 rounded-full border px-3.5 py-2 text-xs font-medium transition ${
                    isActive
                      ? "border-slate-900 bg-slate-900 text-white hover:border-slate-900 hover:bg-slate-900"
                      : appearance.className
                  }`}
                >
                  <span
                    className={`rounded-full px-1.5 py-0.5 text-[10px] font-bold tracking-[0.16em] ${
                      isActive ? "bg-white/20 text-white" : "bg-white/80"
                    }`}
                  >
                    {isActive ? "DONE" : appearance.badge}
                  </span>
                  <span>{isActive ? getExecutionSuccessLabel(execution) : getExecutionLabel(execution)}</span>
                </button>
              );
            })}
          </div>
        ) : null}
        {content.confidence ? (
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
            Confidence: {content.confidence}
          </p>
        ) : null}
      </div>
    </div>
  );
}

function renderTextWithLinks(
  text: string,
  linkClassName = "text-sky-700 underline underline-offset-4 break-all transition hover:text-sky-800"
) {
  const lines = text.split("\n");

  return lines.map((line, lineIndex) => {
    const parts = line.split(URL_PATTERN);

    return (
      <Fragment key={`line-${lineIndex}-${line}`}>
        {parts.map((part, partIndex) => {
          if (!/^https?:\/\//i.test(part)) {
            return <Fragment key={`text-${lineIndex}-${partIndex}`}>{part}</Fragment>;
          }

          const { url, trailing } = splitUrlSuffix(part);
          if (!url) {
            return <Fragment key={`text-${lineIndex}-${partIndex}`}>{part}</Fragment>;
          }

          return (
            <Fragment key={`link-${lineIndex}-${partIndex}`}>
              <a href={url} className={linkClassName} target="_blank" rel="noopener noreferrer">
                {url}
              </a>
              {trailing}
            </Fragment>
          );
        })}
        {lineIndex < lines.length - 1 ? <br /> : null}
      </Fragment>
    );
  });
}

function renderStructuredText(
  text: string,
  options?: {
    textClassName?: string;
    linkClassName?: string;
  }
) {
  const blocks = text.split(/\n\s*\n/);
  return (
    <div className="space-y-2">
      {blocks.map((block, blockIndex) => {
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
            const articleTitle = cleanArticleTitle(titleLines.join(" "));
            const articleSource = sourceMatch[1].trim();
            const articleDomain = getArticleDomain(articleUrl);
            const faviconUrl = `https://www.google.com/s2/favicons?domain=${encodeURIComponent(articleDomain)}&sz=32`;

            return (
              <div
                key={`article-${blockIndex}`}
                className="rounded-3xl border border-sky-100 bg-white/95 px-5 py-4 shadow-sm shadow-slate-200/70 transition duration-200 hover:-translate-y-0.5 hover:border-sky-200 hover:bg-white hover:shadow-md hover:shadow-slate-200/80"
              >
                <div className="space-y-2.5">
                  <div className="block text-[16px] font-medium leading-7 text-slate-950">
                    {articleTitle}
                  </div>
                  <div>
                    <SourceBadge source={articleSource} domain={articleDomain} faviconUrl={faviconUrl} />
                  </div>
                  <a
                    href={articleUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="break-all text-xs font-medium text-sky-700 underline underline-offset-4 transition hover:text-sky-800"
                  >
                    {articleUrl}
                  </a>
                </div>
              </div>
            );
          }
        }

        return (
          <div key={`text-block-${blockIndex}`}>
            {renderMarkdownBlock(block, options)}
          </div>
        );
      })}
    </div>
  );
}

type ResponseRendererProps = {
  message: Message;
  onActionClick?: (message: Message, action: string) => void;
  onExecutionClick?: (message: Message, execution: MessageExecution) => void;
  onToggleAudio?: (message: Message) => void;
  isSpeaking?: boolean;
  animateSummary?: boolean;
  actions?: string[];
  showActionChips?: boolean;
};

function getExecutionLabel(execution: MessageExecution) {
  if (execution.label?.trim()) {
    return execution.label.trim();
  }

  if (execution.type === "youtube_search") {
    return "Show YouTube results";
  }

  if (execution.type === "web_search") {
    return "Show web results";
  }

  if (execution.type === "copy_text") {
    return "Copy text";
  }

  if (execution.type === "open_weather") {
    return "Get weather";
  }

  return "Run action";
}

function getExecutionAppearance(execution: MessageExecution) {
  if (execution.type === "copy_text") {
    return {
      badge: "COPY",
      className:
        "border-emerald-200 bg-emerald-50 text-emerald-800 hover:border-emerald-300 hover:bg-emerald-100",
    };
  }

  if (execution.type === "open_weather") {
    return {
      badge: "WX",
      className:
        "border-cyan-200 bg-cyan-50 text-cyan-800 hover:border-cyan-300 hover:bg-cyan-100",
    };
  }

  if (execution.type === "youtube_search") {
    return {
      badge: "YT",
      className:
        "border-rose-200 bg-rose-50 text-rose-800 hover:border-rose-300 hover:bg-rose-100",
    };
  }

  if (execution.type === "web_search") {
    return {
      badge: "WEB",
      className:
        "border-indigo-200 bg-indigo-50 text-indigo-800 hover:border-indigo-300 hover:bg-indigo-100",
    };
  }

  return {
    badge: "ACT",
    className:
      "border-sky-200 bg-sky-50 text-sky-800 hover:border-sky-300 hover:bg-sky-100",
  };
}

function getExecutionSuccessLabel(execution: MessageExecution) {
  if (execution.type === "copy_text") {
    return "Copied";
  }

  if (execution.type === "open_weather") {
    return "Fetched";
  }

  return "Handled";
}

function getSectionQuickActions(sectionTitle: string | undefined, executions: MessageExecution[]) {
  const normalizedTitle = (sectionTitle ?? "").toLowerCase();

  if (normalizedTitle.includes("image prompt")) {
    return executions.filter((execution) => {
      const label = execution.label?.toLowerCase() ?? "";
      return label === "copy image prompt" || label === "copy negative prompt";
    });
  }

  if (normalizedTitle.includes("video prompt")) {
    return executions.filter((execution) => {
      const label = execution.label?.toLowerCase() ?? "";
      return label === "copy video prompt" || label === "copy camera notes" || label === "copy lens notes";
    });
  }

  if (normalizedTitle.includes("copy strategy")) {
    return executions.filter((execution) => (execution.label?.toLowerCase() ?? "") === "copy all prompts");
  }

  return [];
}

function getSectionProviderBadge(sectionTitle: string | undefined) {
  const normalizedTitle = (sectionTitle ?? "").toLowerCase();

  if (normalizedTitle.includes("midjourney")) {
    return "Midjourney";
  }
  if (normalizedTitle.includes("flux")) {
    return "Flux";
  }
  if (normalizedTitle.includes("runway")) {
    return "Runway";
  }
  if (normalizedTitle.includes("kling")) {
    return "Kling";
  }
  if (normalizedTitle.includes("sora")) {
    return "Sora";
  }

  return null;
}

export function ResponseRenderer({
  message,
  onActionClick,
  onExecutionClick,
  onToggleAudio,
  isSpeaking = false,
  animateSummary = false,
  actions,
  showActionChips = true,
}: ResponseRendererProps) {
  const statuses = message.metadata?.statuses ?? [];
  const [activeExecutionKey, setActiveExecutionKey] = useState<string | null>(null);
  const resetTimerRef = useRef<number | null>(null);
  const label =
    message.metadata?.tool === "multi"
      ? "Multi Analysis"
      : message.metadata?.tool === "news"
      ? "News Analysis"
      : message.metadata?.tool === "weather"
        ? "Weather Analysis"
      : message.metadata?.tool === "search"
        ? "Web Search"
      : message.metadata?.tool === "finance"
        ? "Finance Analysis"
        : "General Assistant";

  if (message.type === "summary") {
    return (
      <div className="space-y-2">
        {message.metadata?.followUp ? (
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">
            Follow-up question
          </p>
        ) : null}
        <div className="text-base font-semibold">{renderStructuredText(String(message.content), { textClassName: "text-base font-semibold", linkClassName: "text-sky-600 underline underline-offset-4 break-all transition hover:text-sky-700" })}</div>
      </div>
    );
  }

  if (message.type === "analysis" || message.type === "general") {
    const content = (message.content ?? {}) as GeneralContent | AnalysisContent;
    return (
      <GeneralPanel
        message={message}
        content={content}
        label={message.type === "general" ? "General Response" : label}
        statuses={statuses}
        isSpeaking={isSpeaking}
        activeExecutionKey={activeExecutionKey}
        onToggleAudio={onToggleAudio}
        onActionClick={onActionClick}
        onExecutionClick={onExecutionClick}
        setActiveExecutionKey={setActiveExecutionKey}
        resetTimerRef={resetTimerRef}
        animateSummary={animateSummary}
        actions={actions}
        showActionChips={showActionChips}
      />
    );
  }

  if (message.type === "web_search") {
    const content = (message.content ?? { data: [] }) as SearchResultsContent;
    return <SearchResultsPanel message={message} content={content} title="Web results" kicker="Web Search" hoverClassName="hover:border-sky-300 hover:bg-sky-50/30" activeClassName="border-sky-300 ring-1 ring-sky-200" onActionClick={onActionClick} animateSummary={animateSummary} actions={actions} showActionChips={showActionChips} />;
  }

  if (message.type === "news") {
    const content = (message.content ?? { data: [] }) as NewsContent;
    return <SearchResultsPanel message={message} content={content} title="News coverage" kicker="News" hoverClassName="hover:border-emerald-300 hover:bg-emerald-50/30" activeClassName="border-emerald-300 ring-1 ring-emerald-200" onActionClick={onActionClick} animateSummary={animateSummary} actions={actions} showActionChips={showActionChips} />;
  }

  if (message.type === "youtube_search") {
    const content = (message.content ?? { data: [] }) as VideoResultsContent;
    return <VideoResultsPanel message={message} content={content} onActionClick={onActionClick} animateSummary={animateSummary} actions={actions} showActionChips={showActionChips} />;
  }

  if (message.type === "weather") {
    const content = (message.content ?? {}) as WeatherContent;
    return <WeatherPanel message={message} content={content} onActionClick={onActionClick} animateSummary={animateSummary} actions={actions} showActionChips={showActionChips} />;
  }

  if (message.type === "error") {
    const content = (message.content ?? {}) as ErrorContent;

    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {message.role === "system" ? (
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => onToggleAudio?.(message)}
                  className="rounded-full border border-rose-200 bg-white px-3.5 py-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-rose-700 transition hover:border-rose-300 hover:bg-rose-100"
                >
                  {isSpeaking ? "Stop" : "Listen"}
                </button>
              </div>
            ) : null}
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-red-500">{label}</p>
        {renderStructuredText(content.summary ?? content.message ?? "Unexpected error", { textClassName: "text-sm text-red-700", linkClassName: "text-red-700 underline underline-offset-4 break-all transition hover:text-red-800" })}
      </div>
    );
  }

  if (message.type === "recommendation") {
    const items = Array.isArray(message.content) ? message.content : [];
    return (
      <ul className="list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">
        {items.map((item: string) => (
          <li key={item}>{renderStructuredText(item)}</li>
        ))}
      </ul>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
      <pre className="whitespace-pre-wrap break-words">{JSON.stringify(message.content, null, 2)}</pre>
    </div>
  );
}
