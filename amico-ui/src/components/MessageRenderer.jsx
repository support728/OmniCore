import { useEffect, useMemo, useState } from "react";

import "./message-renderer.css";
import ResultCard from "./ResultCard";
import WeatherCard from "./WeatherCard";
import YouTubeList from "./YouTubeList";
import { fetchPreview } from "../services/api";

const URL_PATTERN = /https?:\/\/[^\s]+/g;

const TOOL_LABELS = {
  business: "Business",
  general: "General",
  images: "Images",
  answer: "Answer",
  guide: "Guide",
  checklist: "Checklist",
  roadmap: "Roadmap",
  compliance: "Compliance",
  pricing: "Pricing",
  staffing: "Staffing",
  search_results: "Search Results",
  web_search: "Search Results",
  workflow: "Workflow",
  resource_list: "Resources",
  youtube: "▶️ YouTube Results",
  youtube_search: "▶️ YouTube Results",
  news: "📰 News",
  weather: "🌤 Weather",
};

function normalizeStructuredCollection(value, predicate) {
  return Array.isArray(value) ? value.filter((item) => item && typeof item === "object" && predicate(item)) : [];
}

function parseStructuredText(text) {
  const blocks = String(text || "")
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);

  const lead = [];
  const sections = [];

  blocks.forEach((block) => {
    const match = block.match(/^([A-Z][A-Za-z0-9 /&-]{2,48}):\s*([\s\S]*)$/);
    if (!match) {
      lead.push(block);
      return;
    }

    const heading = match[1].trim();
    const body = match[2].trim();
    if (!body || heading.toLowerCase().includes("http")) {
      lead.push(block);
      return;
    }

    sections.push({ heading, body });
  });

  return {
    leadSummary: lead.join("\n\n"),
    sections,
  };
}

function dedupeStructuredLinks(links) {
  const seen = new Set();
  return normalizeStructuredCollection(links, (item) => item.url && item.label).filter((item) => {
    const key = String(item.url || "").trim();
    if (!key || seen.has(key)) {
      return false;
    }

    seen.add(key);
    return true;
  });
}

function normalizeActionList(actions, summary) {
  if (!Array.isArray(actions)) {
    return [];
  }

  return actions
    .map((action) => {
      if (typeof action === "string" && action.trim()) {
        return {
          label: action.trim(),
          prompt: action.trim() === summary ? action.trim() : `${action.trim()}: ${summary}`,
        };
      }

      if (action && typeof action === "object" && action.label && action.prompt) {
        return action;
      }

      return null;
    })
    .filter(Boolean);
}

function normalizeFollowUpAction(value) {
  const normalized = String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");

  if (!normalized) {
    return null;
  }

  if (normalized === "explain_that_differently" || normalized === "explain") {
    return "explain";
  }
  if (normalized === "give_me_next_steps" || normalized === "next_steps") {
    return "next_steps";
  }
  if (normalized === "search_deeper") {
    return "search_deeper";
  }
  if (normalized === "open_top_result") {
    return "open_top_result";
  }

  return normalized;
}

function getFollowUpBadge(action) {
  switch (action) {
    case "explain":
      return "Explain";
    case "next_steps":
      return "Next Steps";
    case "search_deeper":
      return "Search Deeper";
    case "open_top_result":
      return "Top Result";
    default:
      return null;
  }
}

function splitParagraphBlocks(text) {
  return String(text || "")
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);
}

function buildOrderedSteps(text) {
  return String(text || "")
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.replace(/^[0-9]+[.)]\s*/, "").trim())
    .filter(Boolean);
}

function buildFollowUpSections(action, summary, sections) {
  if (sections.length) {
    return sections;
  }

  if (action !== "search_deeper" && action !== "open_top_result") {
    return [];
  }

  return splitParagraphBlocks(summary).map((block, index) => {
    const headingMatch = block.match(/^([^:\n]{3,48}):\s*([\s\S]*)$/);
    if (headingMatch) {
      return {
        heading: headingMatch[1].trim(),
        body: headingMatch[2].trim(),
      };
    }

    return {
      heading: action === "open_top_result" && index === 0 ? "Overview" : `Detail ${index + 1}`,
      body: block,
    };
  });
}

function inferDomainType(domain, response, summary) {
  const responseMeta = response?.meta && typeof response.meta === "object" ? response.meta : {};
  const explicitType = response?.type || responseMeta?.type || responseMeta?.source_type;
  if (explicitType) {
    return explicitType;
  }

  if (domain === "images") {
    return responseMeta?.prompt || responseMeta?.image_url || response?.image_url ? "images" : "answer";
  }

  if (domain === "business") {
    if (/checklist/i.test(summary)) {
      return "checklist";
    }
    if (/roadmap|launch phases/i.test(summary)) {
      return "roadmap";
    }
    if (/compliance/i.test(summary)) {
      return "compliance";
    }
    if (/pricing/i.test(summary)) {
      return "pricing";
    }
    if (/staffing|operations/i.test(summary)) {
      return "staffing";
    }
  }

  return responseMeta?.data?.results?.length ? "resource_list" : "answer";
}

function normalizeResponse(message, expectedDomain) {
  const response = message?.response && typeof message.response === "object" ? message.response : null;
  const responseMeta = response?.meta && typeof response.meta === "object" ? response.meta : null;
  const responseData = responseMeta?.data || message?.data || null;
  const contextMessagesUsed =
    typeof message?.contextMessagesUsed === "number"
      ? message.contextMessagesUsed
      : typeof responseMeta?.context_messages_used === "number"
        ? responseMeta.context_messages_used
        : null;
  const domain = message?.domain || responseMeta?.domain || (response?.type === "business" || response?.type === "images" ? response.type : null) || null;
  const sourceSummary = response?.content || message?.content || message?.summary || "";
  const parsedText = domain && domain !== "business" && domain !== "images" ? parseStructuredText(sourceSummary) : { leadSummary: "", sections: [] };
  const sections = normalizeStructuredCollection(responseMeta?.sections || responseData?.sections, (item) => item.heading && item.body);
  const links = dedupeStructuredLinks(responseMeta?.links || responseData?.links);
  const actions = normalizeActionList(response?.actions, sourceSummary);
  const followUpAction = normalizeFollowUpAction(
    message?.action || response?.followUpAction || response?.action || responseMeta?.follow_up_action || responseData?.follow_up_action,
  );
  const nextSteps = Array.isArray(responseMeta?.nextSteps || responseData?.nextSteps)
    ? (responseMeta?.nextSteps || responseData?.nextSteps).filter((item) => typeof item === "string" && item.trim())
    : [];
  const orderedSteps = followUpAction === "next_steps" ? buildOrderedSteps(sourceSummary) : [];
  const resolvedSections = buildFollowUpSections(
    followUpAction,
    sourceSummary,
    sections.length ? sections : parsedText.sections,
  );
  const imagePlan =
    (response?.type === "images" || responseMeta?.image_url || response?.image_url || responseMeta?.prompt)
      ? {
          prompt: responseMeta?.prompt || responseData?.prompt || "",
          variations: Array.isArray(responseMeta?.variations || responseData?.variations) ? (responseMeta?.variations || responseData?.variations) : [],
          aspectRatio: responseMeta?.aspect_ratio || responseData?.aspectRatio || "",
          style: responseMeta?.style || responseData?.style || "",
          subject: responseMeta?.subject || responseData?.subject || "",
          composition: responseMeta?.composition || responseData?.composition || "",
          lighting: responseMeta?.lighting || responseData?.lighting || "",
          negativePrompt: responseMeta?.negativePrompt || responseData?.negativePrompt || "",
          generationStatus: responseMeta?.generationStatus || responseData?.generationStatus || "generated",
          generatorEndpoint: responseMeta?.generatorEndpoint || responseData?.generatorEndpoint || "",
          previewImageUrl: response?.image_url || responseMeta?.image_url || responseMeta?.previewImageUrl || responseData?.previewImageUrl || null,
          canGenerate: Boolean(response?.image_url || responseMeta?.image_url || responseMeta?.canGenerate),
        }
      : null;

  return {
    domain,
    type: message?.type || inferDomainType(domain, response, sourceSummary) || (message?.role === "assistant" ? "general" : undefined),
    title: message?.title || responseMeta?.title || responseData?.title || "",
    summary: parsedText.leadSummary || sourceSummary,
    contextMessagesUsed,
    followUpAction,
    followUpBadge: getFollowUpBadge(followUpAction),
    data: responseData,
    sections: resolvedSections,
    links,
    actions,
    nextSteps: nextSteps.length ? nextSteps : orderedSteps,
    imagePlan,
  };
}

function extractLinks(text) {
  return String(text || "").match(URL_PATTERN) || [];
}

function stripLinks(text) {
  return String(text || "")
    .replace(URL_PATTERN, "")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function getDomainTitle(link) {
  try {
    return new URL(link).hostname.replace(/^www\./, "");
  } catch {
    return link;
  }
}

function getLinkDescription(link) {
  const normalized = String(link || "").toLowerCase();

  if (normalized.includes("youtube.com") || normalized.includes("youtu.be")) {
    return "Watch this video inside Amico or open it in the embedded browser.";
  }

  if (normalized.includes("news") || normalized.includes("article") || normalized.includes("blog")) {
    return "Open this article without leaving the chat.";
  }

  return "Click to view content.";
}

export default function MessageRenderer({ message, expectedDomain, onOpenLink, onSummarizeLink, onRelateLink, onActionPrompt, onCopyText, onGenerateImage }) {
  const { domain, type, title, summary, contextMessagesUsed, followUpAction, followUpBadge, data, sections, links: structuredLinks, actions, nextSteps, imagePlan } = normalizeResponse(message, expectedDomain);

  console.log("MessageRenderer action", message?.action || followUpAction || null, message?.id || null);

  if (expectedDomain && domain && expectedDomain !== domain) {
    return null;
  }

  const resultIntent = typeof data?.intent === "string" && data.intent ? data.intent : type;
  const structuredResults = useMemo(
    () => (Array.isArray(data?.results) ? data.results.filter((item) => item && typeof item === "object") : []),
    [data],
  );
  const usesRankedSourceCards = (resultIntent === "web_search" || resultIntent === "news" || type === "search_results") && structuredResults.length > 0;
  const links = useMemo(() => {
    if (usesRankedSourceCards || structuredLinks.length) {
      return [];
    }

    return extractLinks(summary);
  }, [structuredLinks.length, summary, usesRankedSourceCards]);
  const summaryWithoutLinks = stripLinks(summary);
  const [previews, setPreviews] = useState({});
  const cardUrls = useMemo(() => {
    const urls = structuredResults
      .map((item) => item?.url || item?.link || "")
      .filter((item) => typeof item === "string" && item);

    structuredLinks.forEach((link) => {
      if (link?.url && !urls.includes(link.url)) {
        urls.push(link.url);
      }
    });

    links.forEach((link) => {
      if (!urls.includes(link)) {
        urls.push(link);
      }
    });

    return urls;
  }, [links, structuredResults]);

  useEffect(() => {
    if (!cardUrls.length) {
      return;
    }

    let cancelled = false;

    cardUrls.forEach((link) => {
      if (previews[link]) {
        return;
      }

      void fetchPreview(link)
        .then((preview) => {
          if (cancelled) {
            return;
          }

          setPreviews((current) => ({
            ...current,
            [link]: preview,
          }));
        })
        .catch(() => {
          if (cancelled) {
            return;
          }

          setPreviews((current) => ({
            ...current,
            [link]: {
              title: getDomainTitle(link),
              description: "Preview unavailable",
              image: null,
              url: link,
            },
          }));
        });
    });

    return () => {
      cancelled = true;
    };
  }, [cardUrls, previews]);

  if (!summary && !data && !title && !sections.length && !structuredLinks.length && !actions.length && !nextSteps.length && !imagePlan) {
    return null;
  }

  const normalizedType = typeof resultIntent === "string" ? resultIntent : typeof type === "string" ? type : "text";
  const label = TOOL_LABELS[normalizedType] || (domain === "business" ? "Business" : domain === "images" ? "Images" : null);
  const followUpClassName = followUpAction ? ` message-renderer--${followUpAction}` : "";

  let content = null;

  if (normalizedType === "youtube" || normalizedType === "youtube_search") {
    content = <YouTubeList data={data} onOpenLink={onOpenLink} />;
  } else if (normalizedType === "weather") {
    content = <WeatherCard data={data} />;
  }

  return (
    <div className={`message-renderer${followUpClassName}`}>
      {typeof contextMessagesUsed === "number" ? (
        <div className="message-renderer__context-indicator">Context messages used: {contextMessagesUsed}</div>
      ) : null}
      {label || followUpBadge ? (
        <div className="message-renderer__header-row">
          {label ? <div className="message-renderer__label">{label}</div> : null}
          {followUpBadge ? <div className="message-renderer__action-badge">{followUpBadge}</div> : null}
        </div>
      ) : null}
      {title ? <h3 className="message-renderer__title">{title}</h3> : null}
      {summaryWithoutLinks && followUpAction !== "next_steps" && !sections.length ? (
        <p className={`message-renderer__summary${followUpAction ? ` message-renderer__summary--${followUpAction}` : ""}`} style={{ whiteSpace: "pre-wrap" }}>
          {summaryWithoutLinks}
        </p>
      ) : null}
      {sections.length ? (
        <div className="message-renderer__sections">
          {sections.map((section, index) => (
            <section
              key={`${section.heading}-${index}`}
              className={`message-renderer__section-card${followUpAction ? ` message-renderer__section-card--${followUpAction}` : ""}`}
            >
              <div className="message-renderer__section-heading">{section.heading}</div>
              <p className="message-renderer__section-body" style={{ whiteSpace: "pre-wrap" }}>
                {section.body}
              </p>
            </section>
          ))}
        </div>
      ) : null}
      {type === "images" && imagePlan ? (
        <div className="message-renderer__image-plan">
          <div className="message-renderer__image-plan-header">
            <div className="message-renderer__image-plan-kicker">Image Workflow</div>
            <div className={`message-renderer__image-status${imagePlan.canGenerate ? " is-ready" : " is-pending"}`}>
              {imagePlan.canGenerate ? "Generate Ready" : "Generate Soon"}
            </div>
          </div>
          {imagePlan.previewImageUrl ? (
            <img className="message-renderer__image-preview" src={imagePlan.previewImageUrl} alt={title || "Generated preview"} />
          ) : imagePlan.generationStatus !== "generated" ? (
            <div className="message-renderer__image-placeholder">
              <div className="message-renderer__image-placeholder-title">Direct image generation status</div>
              <div className="message-renderer__image-placeholder-body">
                Image generation did not return a preview for this request. Retry or use a variation prompt.
              </div>
            </div>
          ) : null}
          <div className="message-renderer__section-card">
            <div className="message-renderer__section-heading">Final Prompt</div>
            <p className="message-renderer__section-body" style={{ whiteSpace: "pre-wrap" }}>{imagePlan.prompt || summary}</p>
          </div>
          <div className="message-renderer__image-output-grid">
            {imagePlan.style ? (
              <div className="message-renderer__section-card">
                <div className="message-renderer__section-heading">Style</div>
                <p className="message-renderer__section-body">{imagePlan.style}</p>
              </div>
            ) : null}
            {imagePlan.aspectRatio ? (
              <div className="message-renderer__section-card">
                <div className="message-renderer__section-heading">Aspect Ratio</div>
                <p className="message-renderer__section-body">{imagePlan.aspectRatio}</p>
              </div>
            ) : null}
            {imagePlan.subject ? (
              <div className="message-renderer__section-card">
                <div className="message-renderer__section-heading">Subject</div>
                <p className="message-renderer__section-body">{imagePlan.subject}</p>
              </div>
            ) : null}
            {imagePlan.composition ? (
              <div className="message-renderer__section-card">
                <div className="message-renderer__section-heading">Composition</div>
                <p className="message-renderer__section-body">{imagePlan.composition}</p>
              </div>
            ) : null}
            {imagePlan.lighting ? (
              <div className="message-renderer__section-card">
                <div className="message-renderer__section-heading">Lighting</div>
                <p className="message-renderer__section-body">{imagePlan.lighting}</p>
              </div>
            ) : null}
            {imagePlan.negativePrompt ? (
              <div className="message-renderer__section-card">
                <div className="message-renderer__section-heading">Negative Prompt</div>
                <p className="message-renderer__section-body">{imagePlan.negativePrompt}</p>
              </div>
            ) : null}
          </div>
          {imagePlan.variations.length ? (
            <div className="message-renderer__variation-list">
              {imagePlan.variations.map((variation, index) => (
                <button
                  key={`${variation}-${index}`}
                  type="button"
                  className="message-renderer__variation"
                  onClick={() => onActionPrompt?.(variation)}
                >
                  Variation {index + 1}
                </button>
              ))}
            </div>
          ) : null}
          <div className="message-renderer__actions">
            <button type="button" className="message-renderer__action" onClick={() => onCopyText?.(imagePlan.prompt || summary)}>
              Copy Full Prompt
            </button>
            <button type="button" className="message-renderer__action" onClick={() => onCopyText?.(`${imagePlan.prompt || summary}\n\nVariant: postcard layout, concise typography, mailing-safe composition.`)}>
              Copy Postcard Variant
            </button>
            <button type="button" className="message-renderer__action" onClick={() => onCopyText?.(`${imagePlan.prompt || summary}\n\nVariant: poster layout, bold focal hierarchy, print-ready composition.`)}>
              Copy Poster Variant
            </button>
            <button type="button" className="message-renderer__action" onClick={() => onCopyText?.(`${imagePlan.prompt || summary}\n\nVariant: product-shot layout, studio lighting, commercial framing.`)}>
              Copy Product-Shot Variant
            </button>
            <button type="button" className="message-renderer__action" onClick={() => onActionPrompt?.(`Regenerate this image concept with stronger visual variation:\n\n${imagePlan.prompt || summary}`)}>
              Regenerate
            </button>
            <button type="button" className="message-renderer__action" onClick={() => onGenerateImage?.(imagePlan)}>
              Generate
            </button>
          </div>
        </div>
      ) : null}
      {structuredLinks.length ? (
        <div className="message-renderer__resources">
          <div className="message-renderer__resources-label">Resources</div>
          <div className="message-renderer__resource-list">
            {structuredLinks.map((link, index) => (
              <button
                key={`${link.url}-${index}`}
                type="button"
                className="message-renderer__resource"
                onClick={() => onOpenLink(link.url, { title: link.label, description: link.description, official: link.official })}
              >
                <span className="message-renderer__resource-title-row">
                  <span className="message-renderer__resource-title">{link.label}</span>
                  {link.official ? <span className="message-renderer__resource-badge">Official</span> : null}
                </span>
                <span className="message-renderer__resource-url">{getDomainTitle(link.url)}</span>
                {link.description ? <span className="message-renderer__resource-description">{link.description}</span> : null}
              </button>
            ))}
          </div>
        </div>
      ) : null}
      {nextSteps.length ? (
        <div className="message-renderer__next-steps">
          <div className="message-renderer__resources-label">Next Steps</div>
          <ol className="message-renderer__next-step-list">
            {nextSteps.map((step, index) => (
              <li key={`${step}-${index}`} className="message-renderer__next-step-item">
                <span className="message-renderer__next-step-number">{index + 1}</span>
                <span className="message-renderer__next-step-text">{step}</span>
              </li>
            ))}
          </ol>
        </div>
      ) : null}
      {actions.length ? (
        <div className="message-renderer__actions">
          {actions.map((action, index) => (
            <button
              key={`${action.label}-${index}`}
              type="button"
              className="message-renderer__action"
              onClick={() => onActionPrompt?.(action.prompt, action.label)}
            >
              {action.label}
            </button>
          ))}
        </div>
      ) : null}
      {usesRankedSourceCards ? (
        structuredResults.length ? (
          <div style={{ marginTop: 10 }}>
            {structuredResults.map((result, index) => {
              const url = result?.url || result?.link;
              if (!url) {
                return null;
              }

              const preview = previews[url];
              const source = result?.source || getDomainTitle(url);

              return (
                <ResultCard
                  key={`${url}-${index}`}
                  title={result?.title || preview?.title || getDomainTitle(url)}
                  url={url}
                  description={result?.snippet || preview?.description || "Loading preview..."}
                  image={preview?.image || result?.image || null}
                  loading={!preview && !result?.snippet}
                  source={source}
                  why={result?.why}
                  rank={result?.rank || index + 1}
                  onOpen={onOpenLink}
                  onSummarize={onSummarizeLink}
                  onRelate={onRelateLink}
                />
              );
            })}
          </div>
        ) : null
      ) : links.length ? (
        <div style={{ marginTop: 10 }}>
          {links.map((link, index) => {
            const preview = previews[link];

            return (
              <ResultCard
                key={`${link}-${index}`}
                title={preview?.title || getDomainTitle(link)}
                url={link}
                description={preview?.description || "Loading preview..."}
                image={preview?.image}
                loading={!preview}
                source={preview?.url ? getDomainTitle(preview.url) : getDomainTitle(link)}
                onOpen={onOpenLink}
                onSummarize={onSummarizeLink}
                onRelate={onRelateLink}
              />
            );
          })}
        </div>
      ) : null}
      {content}
    </div>
  );
}