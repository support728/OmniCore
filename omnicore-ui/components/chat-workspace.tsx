"use client";

import { useEffect, useRef, useState } from "react";

import { ChatInput } from "@/components/chat-input";
import { ResponseRenderer } from "@/components/response-renderer";
import {
  sendMessage,
  type AssistantResponse,
  type AssistantExecution,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { useMessageStore } from "@/store/message-store";
import type {
  AnalysisContent,
  GeneralContent,
  Message,
  MessageExecution,
  MessageTool,
  NewsContent,
  SearchResultsContent,
  VideoResultsContent,
  WeatherContent,
} from "@/types/message";

const MEDIA_PLATFORM_OPTIONS = [
  { id: "", label: "Auto" },
  { id: "midjourney", label: "Midjourney" },
  { id: "flux", label: "Flux" },
  { id: "runway", label: "Runway" },
  { id: "kling", label: "Kling" },
  { id: "sora", label: "Sora" },
];

const USERNAME_STORAGE_KEY = "username";

type SendOptions = {
  autoSpeakReply?: boolean;
  rethrowOnError?: boolean;
  timeoutMs?: number;
};

function extractDeclaredName(prompt: string) {
  const match = prompt.match(/\bmy name is\s+([A-Za-z][A-Za-z'-]{0,49})\b/i);
  return match?.[1] ?? null;
}

function normalizeTool(tool?: string): MessageTool {
  if (
    tool === "news" ||
    tool === "finance" ||
    tool === "weather" ||
    tool === "search" ||
    tool === "multi"
  ) {
    return tool;
  }

  return "general";
}

function getSpeakableMessageText(message: Message) {
  if (typeof message.content === "string") {
    return message.content.trim();
  }

  if (!message.content || typeof message.content !== "object" || Array.isArray(message.content)) {
    return "";
  }

  const content = message.content as AnalysisContent & {
    message?: string;
    summary?: string;
    insight?: string;
    actions?: string[];
    sections?: Array<{ title?: string; body?: string }>;
  };
  const parts = [
    content.summary,
    content.insight,
    content.message,
    ...(content.sections ?? []).flatMap((section) => [section.title, section.body]),
    ...(content.actions ?? []),
  ]
    .map((part) => String(part ?? "").trim())
    .filter(Boolean);

  return parts.join(" ");
}

function buildExecutionPrompt(execution: AssistantExecution | MessageExecution) {
  if (execution.type === "web_search") {
    return execution.query ? `search the internet for ${execution.query}` : "search the internet";
  }

  if (execution.type === "youtube_search") {
    return execution.query ? `search YouTube for ${execution.query}` : "search YouTube";
  }

  if (execution.type === "open_weather") {
    return execution.city ? `weather in ${execution.city}` : "weather";
  }

  return "";
}

type PromptIntent = "weather" | "news" | "web_search" | "youtube_search" | "general";

function detectPromptIntent(prompt: string): PromptIntent {
  const lower = prompt.trim().toLowerCase();

  if (lower.includes("youtube")) {
    return "youtube_search";
  }

  if (
    lower.includes("weather") ||
    lower.includes("forecast") ||
    lower.includes("temperature") ||
    lower.includes("rain") ||
    lower.includes("snow")
  ) {
    return "weather";
  }

  if (
    lower.includes("news") ||
    lower.includes("headline") ||
    lower.includes("today") ||
    lower.includes("latest") ||
    lower.includes("current events")
  ) {
    return "news";
  }

  if (lower.includes("search") || lower.includes("internet") || lower.includes("google") || lower.includes("find")) {
    return "web_search";
  }

  return "general";
}

function getLoadingLabel(intent: PromptIntent) {
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

function polishAssistantCopy(text: string) {
  return text
    .replace(/\bAs an AI[^.?!]*[.?!]?\s*/gi, "")
    .replace(/\bI can't browse the internet[^.?!]*[.?!]?\s*/gi, "")
    .replace(/\bI do not have the ability[^.?!]*[.?!]?\s*/gi, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function getConversationalActions(message: Message) {
  if (message.role !== "system") {
    return [] as string[];
  }

  const contentActions =
    message.content && typeof message.content === "object" && !Array.isArray(message.content)
      ? (message.content as { actions?: string[] }).actions ?? []
      : [];

  if (contentActions.length) {
    return contentActions;
  }

  if (message.type === "weather") {
    return ["Tomorrow", "Weekend outlook", "Another city"];
  }

  if (message.type === "news") {
    return ["More headlines", "AI news", "Business news"];
  }

  if (message.type === "web_search") {
    return ["Summarize this", "Show top result", "Related search"];
  }

  if (message.type === "youtube_search") {
    return ["Show more videos", "Another topic", "Open best match"];
  }

  return [] as string[];
}

export function ChatWorkspace() {
  const [isMounted, setIsMounted] = useState(false);
  const [draft, setDraft] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true);
  const [preferredMediaPlatform, setPreferredMediaPlatform] = useState("");
  const [loadingLabel, setLoadingLabel] = useState("Thinking...");
  const [animatedMessageId, setAnimatedMessageId] = useState<string | null>(null);
  const { messages, isLoading, addMessage, clearMessages, updateMessage, mergeMessage, setLoading } =
    useMessageStore();
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const executeAssistantExecution = async (
    messageId: string,
    execution: AssistantExecution | MessageExecution
  ) => {
    try {
      if (execution.type === "web_search" || execution.type === "youtube_search" || execution.type === "open_weather") {
        if (!sessionId) {
          throw new Error("Session is not ready yet.");
        }

        const executionPrompt = buildExecutionPrompt(execution);
        if (!executionPrompt) {
          return;
        }

        if (!userId) {
          throw new Error("User is not ready yet.");
        }

        const response = await sendMessage(executionPrompt, sessionId, userId, preferredMediaPlatform || null);
        applyAssistantResponse(messageId, response);
        return;
      }

      if (execution.type === "copy_text") {
        if (!execution.text) {
          return;
        }

        if (!navigator.clipboard?.writeText) {
          throw new Error("Clipboard API unavailable");
        }

        await navigator.clipboard.writeText(execution.text);
        updateMessage(messageId, {
          metadata: {
            tool: normalizeTool(execution.tool),
          },
          content: {
            summary: execution.success_summary ?? "Copied to clipboard.",
            insight: execution.success_insight ?? `Copied: "${execution.text}".`,
          },
        });
        return;
      }

    } catch (error) {
      updateMessage(messageId, {
        metadata: {
          tool: normalizeTool(execution.tool),
        },
        content: {
          summary:
            execution.failure_summary ??
            execution.blocked_summary ??
            (error instanceof Error ? error.message : "The requested action failed."),
          insight:
            execution.failure_insight ??
            execution.blocked_insight ??
            "The assistant could not complete the requested execution.",
        },
      });
    }
  };

  const handleSuggestedAction = async (message: Message, action: string) => {
    const content =
      message.content && typeof message.content === "object" && !Array.isArray(message.content)
        ? (message.content as AnalysisContent & SearchResultsContent & VideoResultsContent & WeatherContent & NewsContent)
        : undefined;
    const matchingExecution = (content?.executions ?? []).find(
      (execution) => execution.label?.trim().toLowerCase() === action.trim().toLowerCase()
    );

    if (matchingExecution) {
      await executeAssistantExecution(message.id, matchingExecution);
      return;
    }

    const normalizedAction = action.trim().toLowerCase();

    if (message.type === "weather") {
      const city = content?.city?.trim();

      if (normalizedAction === "tomorrow") {
        await handleSend(city ? `weather in ${city} tomorrow` : "weather tomorrow");
        return;
      }

      if (normalizedAction === "weekend outlook") {
        await handleSend(city ? `weather in ${city} this weekend` : "weather this weekend");
        return;
      }

      if (normalizedAction === "another city") {
        setDraft("weather in ");
        return;
      }
    }

    if (message.type === "news") {
      if (normalizedAction === "more headlines") {
        await handleSend("top headlines from today");
        return;
      }

      if (normalizedAction === "ai news") {
        await handleSend("latest AI news");
        return;
      }

      if (normalizedAction === "business news") {
        await handleSend("latest business news");
        return;
      }
    }

    if (message.type === "web_search") {
      const query = content?.query?.trim();

      if (normalizedAction === "summarize this") {
        await handleSend(query ? `Summarize the search results for ${query}` : "Summarize this");
        return;
      }

      if (normalizedAction === "show top result") {
        setDraft(query ? `Show the top result for ${query}` : "Show top result");
        return;
      }

      if (normalizedAction === "related search") {
        setDraft(query ? `Search the internet for topics related to ${query}` : "Related search");
        return;
      }
    }

    if (message.type === "youtube_search") {
      const query = content?.query?.trim();

      if (normalizedAction === "show more videos") {
        await handleSend(query ? `search YouTube for more ${query}` : "show more videos");
        return;
      }

      if (normalizedAction === "another topic") {
        setDraft("search YouTube for ");
        return;
      }

      if (normalizedAction === "open best match") {
        setDraft(query ? `Open the best YouTube match for ${query}` : "Open best match");
        return;
      }
    }

    if (message.type === "general" || message.type === "analysis") {
      if (normalizedAction === "tell me more") {
        await handleSend("Tell me more");
        return;
      }

      if (normalizedAction === "summarize") {
        await handleSend("Summarize that");
        return;
      }

      if (normalizedAction === "related") {
        await handleSend("Show me something related");
        return;
      }
    }

    if (
      normalizedAction === "turn my idea into an image prompt" ||
      normalizedAction === "generate image prompt" ||
      normalizedAction === "generate another image prompt"
    ) {
      await handleSend("Turn my idea into an image prompt");
      return;
    }

    if (normalizedAction === "generate midjourney prompt") {
      await handleSend("Turn my idea into a Midjourney image prompt");
      return;
    }

    if (normalizedAction === "generate flux prompt") {
      await handleSend("Turn my idea into a Flux image prompt");
      return;
    }

    if (
      normalizedAction === "turn my idea into a video prompt" ||
      normalizedAction === "generate video prompt" ||
      normalizedAction === "generate another video prompt"
    ) {
      await handleSend("Turn my idea into a video prompt");
      return;
    }

    if (normalizedAction === "generate runway prompt") {
      await handleSend("Turn my idea into a Runway video prompt");
      return;
    }

    if (normalizedAction === "generate kling prompt") {
      await handleSend("Turn my idea into a Kling video prompt");
      return;
    }

    if (normalizedAction === "generate sora prompt") {
      await handleSend("Turn my idea into a Sora video prompt");
      return;
    }

    if (normalizedAction === "use automatic provider") {
      setPreferredMediaPlatform("");
      return;
    }

    setDraft(action);
  };

  const startNewChat = () => {
    const nextSessionId = crypto.randomUUID();
    window.localStorage.setItem("omnicore-session-id", nextSessionId);
    setSessionId(nextSessionId);
    setDraft("");
    clearMessages();

    if (process.env.NODE_ENV === "development") {
      console.debug("[identity] new chat", {
        userId,
        sessionId: nextSessionId,
      });
    }
  };

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted) {
      return;
    }

    const persistedMediaPlatform = window.localStorage.getItem("omnicore-media-platform");

    if (persistedMediaPlatform !== null) {
      const matchesKnownPlatform = MEDIA_PLATFORM_OPTIONS.some((platform) => platform.id === persistedMediaPlatform);
      if (matchesKnownPlatform) {
        setPreferredMediaPlatform(persistedMediaPlatform);
      }
    }

  }, [isMounted]);

  useEffect(() => {
    if (!isMounted) {
      return;
    }

    window.localStorage.setItem("omnicore-media-platform", preferredMediaPlatform);
  }, [isMounted, preferredMediaPlatform]);


  useEffect(() => {
    if (!scrollRef.current) {
      return;
    }

    const scroller = scrollRef.current;
    window.requestAnimationFrame(() => {
      scroller.scrollTo({ top: scroller.scrollHeight, behavior: "smooth" });
    });
  }, [messages, isLoading]);

  useEffect(() => {
    if (!isMounted) {
      return;
    }

    const existingSessionId = window.localStorage.getItem("omnicore-session-id");
    if (existingSessionId) {
      setSessionId(existingSessionId);
      return;
    }

    const nextSessionId = crypto.randomUUID();
    window.localStorage.setItem("omnicore-session-id", nextSessionId);
    setSessionId(nextSessionId);
  }, [isMounted]);

  useEffect(() => {
    if (!isMounted) {
      return;
    }

    const existingUserId = window.localStorage.getItem("omnicore-user-id");
    if (existingUserId) {
      setUserId(existingUserId);
      return;
    }

    const nextUserId = crypto.randomUUID();
    window.localStorage.setItem("omnicore-user-id", nextUserId);
    setUserId(nextUserId);
  }, [isMounted]);

  const applyAssistantResponse = (messageId: string, response: AssistantResponse) => {
    const currentMessage = useMessageStore
      .getState()
      .messages.find((message) => message.id === messageId);
    const currentStatuses = currentMessage?.metadata?.statuses ?? [];
    const data = response.data ?? {};
    const resolvedTool = normalizeTool(data.tool);

    if (response.type === "web_search") {
      updateMessage(messageId, {
        type: "web_search",
        metadata: {
          tool: resolvedTool,
          statuses: currentStatuses,
        },
        content: {
          data: Array.isArray(data.results) ? (data.results as SearchResultsContent["data"]) : [],
          query: typeof data.query === "string" ? data.query : "",
          summary: polishAssistantCopy(response.summary ?? ""),
          insight: typeof data.insight === "string" ? data.insight : undefined,
          actions: Array.isArray(data.actions) ? data.actions : [],
        } satisfies SearchResultsContent,
      });
      return;
    }

    if (response.type === "youtube_search") {
      updateMessage(messageId, {
        type: "youtube_search",
        metadata: {
          tool: resolvedTool,
          statuses: currentStatuses,
        },
        content: {
          data: Array.isArray(data.results) ? (data.results as VideoResultsContent["data"]) : [],
          query: typeof data.query === "string" ? data.query : "",
          summary: polishAssistantCopy(response.summary ?? ""),
          insight: typeof data.insight === "string" ? data.insight : undefined,
          actions: Array.isArray(data.actions) ? data.actions : [],
        } satisfies VideoResultsContent,
      });
      return;
    }

    if (response.type === "weather") {
      updateMessage(messageId, {
        type: "weather",
        metadata: {
          tool: resolvedTool,
          statuses: currentStatuses,
        },
        content: {
          summary: polishAssistantCopy(response.summary ?? ""),
          insight: typeof data.insight === "string" ? data.insight : undefined,
          actions: Array.isArray(data.actions) ? data.actions : [],
          city: typeof data.city === "string" ? data.city : undefined,
          country: typeof data.country === "string" ? data.country : undefined,
          description: typeof data.description === "string" ? data.description : undefined,
          temperature:
            typeof data.temperature === "number"
              ? data.temperature
              : typeof data.temp === "number"
                ? data.temp
                : undefined,
          temp: typeof data.temp === "number" ? data.temp : undefined,
          feels_like: typeof data.feels_like === "number" ? data.feels_like : undefined,
          humidity: typeof data.humidity === "number" ? data.humidity : undefined,
          request_type: typeof data.request_type === "string" ? data.request_type : undefined,
          forecast_days: Array.isArray(data.forecast_days) ? data.forecast_days as WeatherContent["forecast_days"] : [],
        } satisfies WeatherContent,
      });
      return;
    }

    if (response.type === "news") {
      updateMessage(messageId, {
        type: "news",
        metadata: {
          tool: resolvedTool,
          statuses: currentStatuses,
        },
        content: {
          data: Array.isArray(data.results) ? (data.results as NewsContent["data"]) : [],
          query: typeof data.query === "string" ? data.query : "",
          summary: polishAssistantCopy(response.summary ?? ""),
          insight: typeof data.insight === "string" ? data.insight : undefined,
          actions: Array.isArray(data.actions) ? data.actions : [],
        } satisfies NewsContent,
      });
      return;
    }

    if (response.type === "error") {
      updateMessage(messageId, {
        type: "error",
        metadata: {
          tool: resolvedTool,
          statuses: currentStatuses,
        },
        content: {
          summary: response.summary ?? "Unexpected error",
          insight: typeof data.insight === "string" ? data.insight : "The request failed.",
          actions: Array.isArray(data.actions) ? data.actions : [],
          confidence: typeof data.confidence === "string" ? data.confidence : "low",
        },
      });
      return;
    }

    updateMessage(messageId, {
      type: response.type === "general" ? "general" : "analysis",
      metadata: {
        tool: resolvedTool,
        statuses: currentStatuses,
      },
      content: {
        summary: polishAssistantCopy(response.summary ?? ""),
        insight: typeof data.insight === "string" ? data.insight : "",
        actions: Array.isArray(data.actions) ? data.actions : [],
        tags: Array.isArray(data.tags) ? data.tags : [],
        executions: Array.isArray(data.executions) ? data.executions : [],
        confidence: typeof data.confidence === "string" ? data.confidence : "",
        sections: Array.isArray(data.sections) ? data.sections : [],
      } satisfies GeneralContent,
    });

    if (Array.isArray(data.executions)) {
      for (const execution of data.executions) {
        void executeAssistantExecution(messageId, execution);
      }
    }
  };

  const handleSend = async (prompt: string, options: SendOptions = {}) => {
    if (!sessionId || !userId) {
      return null;
    }

    const declaredName = extractDeclaredName(prompt);
    if (declaredName) {
      window.localStorage.setItem(USERNAME_STORAGE_KEY, declaredName);
    }

    const promptIntent = detectPromptIntent(prompt);
    const nextLoadingLabel = getLoadingLabel(promptIntent);

    const existingConversation = messages.filter((message) => message.role === "user" || message.role === "system");
    const isFollowUp = prompt.trim().split(/\s+/).filter(Boolean).length < 5 && existingConversation.length > 0;
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      type: "summary",
      content: prompt,
      metadata: {
        followUp: isFollowUp,
      },
      timestamp: Date.now(),
    };

    addMessage(userMessage);

    setDraft("");

    const systemMessageId = crypto.randomUUID();
    addMessage({
      id: systemMessageId,
      role: "system",
      type: "analysis",
      content: {
        summary: "",
        insight: "",
        actions: [],
        confidence: "",
        sections: [],
      },
      metadata: {
        tool:
          promptIntent === "news"
            ? "news"
            : promptIntent === "weather"
              ? "weather"
              : promptIntent === "web_search" || promptIntent === "youtube_search"
                ? "search"
                : "general",
        statuses: [nextLoadingLabel],
      },
      timestamp: Date.now(),
    });

    setAnimatedMessageId(systemMessageId);
    setLoadingLabel(nextLoadingLabel);
    setLoading(true);

    try {
      const response = await sendMessage(prompt, sessionId, userId, preferredMediaPlatform || null, {
        timeoutMs: options.timeoutMs,
      });
      applyAssistantResponse(systemMessageId, response);

      const latestSystemMessage = useMessageStore
        .getState()
        .messages.find((message) => message.id === systemMessageId);

      const latestExecutions =
        latestSystemMessage?.content &&
        typeof latestSystemMessage.content === "object" &&
        !Array.isArray(latestSystemMessage.content)
          ? (latestSystemMessage.content as AnalysisContent).executions ?? []
          : [];

      const assistantText = latestSystemMessage
        ? getSpeakableMessageText(latestSystemMessage)
        : polishAssistantCopy(response.summary ?? "");

      return {
        assistantText,
        messageId: systemMessageId,
      };
    } catch (error) {
      updateMessage(systemMessageId, {
        type: "error",
        content: {
          summary: error instanceof Error ? error.message : "Unexpected error",
          insight: "The request failed before a structured response was returned.",
          actions: ["Retry the request"],
          confidence: "low",
        },
        metadata: {
          tool: "general",
          statuses: ["Streaming failed"],
        },
      });

      if (options.rethrowOnError) {
        throw error;
      }

      return null;
    } finally {
      setLoading(false);
      setLoadingLabel("Thinking...");
    }
  };

  const handleTextSend = async (prompt: string) => {
    await handleSend(prompt);
  };

  if (!isMounted) {
    return null;
  }

  const latestAssistantMessageId = [...messages].reverse().find((message) => message.role === "system")?.id ?? null;

  return (
    <main className="h-screen bg-slate-100 p-4 text-slate-900">
      <div className="flex h-full gap-4 rounded-[28px] border border-slate-200 bg-white p-4 shadow-[0_24px_60px_rgba(15,23,42,0.08)]">
        <aside className="flex h-full w-[260px] flex-col rounded-[24px] bg-slate-950 px-5 py-6 text-slate-100">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-slate-400">OmniCore</p>
            <h1 className="mt-3 text-2xl font-semibold">Workspace</h1>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Minimal shell for chat, analysis, and recommendations.
            </p>
          </div>
          <div className="mt-10 space-y-3 text-sm text-slate-300">
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              <p className="font-medium text-white">Message types</p>
              <p className="mt-1 text-slate-400">Summary, analysis, recommendation, error</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              <p className="font-medium text-white">State</p>
              <p className="mt-1 text-slate-400">Powered by Zustand</p>
            </div>
          </div>
        </aside>

        <section className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-[24px] border border-slate-200 bg-slate-50">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Main panel</p>
              <h2 className="mt-1 text-lg font-semibold text-slate-900">Chat</h2>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={startNewChat}
                disabled={isLoading}
                className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 transition hover:border-slate-300 hover:bg-slate-100 disabled:cursor-not-allowed disabled:border-slate-100 disabled:bg-slate-100 disabled:text-slate-400"
              >
                New chat
              </button>
              <button
                type="button"
                onClick={() => setIsRightPanelOpen((value) => !value)}
                className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 transition hover:border-slate-300 hover:bg-slate-100"
              >
                {isRightPanelOpen ? "Hide panel" : "Show panel"}
              </button>
            </div>
          </div>

          <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
            {messages.length === 0 ? (
              <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-8 text-sm text-slate-500">
                Start a conversation to see streamed responses appear here.
              </div>
            ) : null}

            {messages.map((message) => (
              <article
                key={message.id}
                className={cn(
                  "max-w-3xl rounded-[26px] px-4 py-3 shadow-sm transition hover:shadow-md sm:px-5 sm:py-4",
                  message.role === "user"
                    ? "ml-auto bg-slate-900 text-white"
                    : "border border-slate-200 bg-white text-slate-900 shadow-[0_10px_24px_rgba(15,23,42,0.06)]"
                )}
              >
                <div className="mb-2 flex items-center justify-between gap-3 text-[11px] uppercase tracking-[0.18em] text-slate-400">
                  <span className={cn(message.role === "user" ? "text-slate-300" : "text-slate-400")}>{message.role === "user" ? "You" : "OmniCore"}</span>
                  <span className={cn(message.role === "user" ? "text-slate-300" : "text-slate-400")}>
                    {new Date(message.timestamp).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}
                  </span>
                </div>
                <ResponseRenderer
                  message={message}
                  onActionClick={(targetMessage, action) => {
                    void handleSuggestedAction(targetMessage, action);
                  }}
                  onExecutionClick={(targetMessage, execution) => {
                    void executeAssistantExecution(targetMessage.id, execution);
                  }}
                  onToggleAudio={() => {}}
                  isSpeaking={false}
                  animateSummary={message.role === "system" && message.id === animatedMessageId}
                  actions={message.role === "system" && message.id === latestAssistantMessageId ? getConversationalActions(message) : []}
                  showActionChips={message.role === "system" && message.id === latestAssistantMessageId}
                />
              </article>
            ))}

            {isLoading ? (
              <div className="max-w-xl rounded-[24px] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
                <div className="mb-2 flex items-center justify-between gap-3 text-[11px] uppercase tracking-[0.18em] text-slate-400">
                  <span>OmniCore</span>
                  <span>now</span>
                </div>
                <div className="inline-flex items-center gap-2.5">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
                  <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400 [animation-delay:120ms]" />
                  <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400 [animation-delay:240ms]" />
                  <span>{loadingLabel}</span>
                </div>
              </div>
            ) : null}
          </div>

          <ChatInput
            isLoading={isLoading}
            value={draft}
            onChange={setDraft}
            onSend={handleTextSend}
          />
        </section>

        {isRightPanelOpen ? (
          <aside className="hidden h-full w-[320px] flex-col rounded-[24px] border border-slate-200 bg-slate-50 p-5 lg:flex">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Right panel</p>
            <h3 className="mt-2 text-lg font-semibold text-slate-900">Settings</h3>
            <div className="mt-6 space-y-4 text-sm text-slate-600">
              <div className="rounded-2xl bg-white px-4 py-4 shadow-sm">
                <p className="font-medium text-slate-900">Streaming state</p>
                <p className="mt-1">Statuses, sections, and final synthesis arrive chunk by chunk.</p>
              </div>
              <div className="rounded-2xl bg-white px-4 py-4 shadow-sm">
                <p className="font-medium text-slate-900">Action buttons</p>
                <p className="mt-1">Suggested follow-ups populate the input so the next step is one click away.</p>
              </div>
              <div className="rounded-2xl bg-white px-4 py-4 shadow-sm">
                <label className="text-sm font-medium text-slate-900" htmlFor="media-platform-selector">
                  Preferred media provider
                </label>
                <p className="mt-1 text-sm text-slate-500">
                  Default image/video prompt provider for media-generation replies.
                </p>
                <select
                  id="media-platform-selector"
                  value={preferredMediaPlatform}
                  onChange={(event) => setPreferredMediaPlatform(event.target.value)}
                  className="mt-3 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400"
                >
                  {MEDIA_PLATFORM_OPTIONS.map((platform) => (
                    <option key={platform.id || "auto"} value={platform.id}>
                      {platform.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="rounded-2xl bg-white px-4 py-4 shadow-sm">
                <p className="text-sm font-medium text-slate-900">Workspace rendering</p>
                <p className="mt-1 text-sm text-slate-500">
                  Search and result actions render as structured content inside OmniCore instead of opening browser tabs.
                </p>
              </div>
            </div>
          </aside>
        ) : null}
      </div>

      <div className="sr-only" aria-live="polite">
        {isLoading ? "Streaming response" : "Ready"}
      </div>
    </main>
  );
}
