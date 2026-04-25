import { AMICO_CAPABILITIES, type AmicoCapabilities } from "./amicoCapabilities";
import { buildBusinessPrompt } from "./amicoBusiness";
import { buildImagesPrompt } from "./amicoImages";
import { AMICO_DOMAINS, type AmicoDomainId } from "./amicoDomains";

export type AmicoRequestType = "chat" | "image_generation";
export type AmicoClassifiedDomain = "business" | "images" | "links";

export type AssistantRequestContext = {
  activeDomain: AmicoDomainId;
  selectedStarterAction?: string | null;
  userInput: string;
  project?: string | null;
  sessionId?: string | null;
  capabilities?: Partial<AmicoCapabilities>;
  classifiedDomain?: AmicoClassifiedDomain | null;
};

export type AssistantRequestEnvelope = {
  requestType: AmicoRequestType;
  activeDomain: AmicoDomainId;
  uiDomain: AmicoDomainId;
  classifiedDomain: AmicoClassifiedDomain;
  message: string;
  selectedStarterAction: string | null;
  capabilities: AmicoCapabilities;
  responseStyle: string;
  toolHints: string[];
};

const BUSINESS_DOMAIN_PATTERN = /\b(business|llc|startup|pricing|compliance|roadmap|staffing|launch|legal|ein)\b/i;
const IMAGES_DOMAIN_PATTERN = /\b(image|poster|design|visual|concept|postcard|layout)\b/i;
const LINKS_DOMAIN_PATTERN = /\b(open|link|website|official page|source)\b/i;

export function resolveAmicoCapabilities(overrides?: Partial<AmicoCapabilities>): AmicoCapabilities {
  return {
    ...AMICO_CAPABILITIES,
    ...(overrides || {}),
  };
}

export function classifyDomain(message: string): AmicoClassifiedDomain {
  const normalized = String(message || "").trim().toLowerCase();

  if (LINKS_DOMAIN_PATTERN.test(normalized)) {
    return "links";
  }

  if (IMAGES_DOMAIN_PATTERN.test(normalized)) {
    return "images";
  }

  if (BUSINESS_DOMAIN_PATTERN.test(normalized)) {
    return "business";
  }

  return "business";
}

export function routingDomainFromClassification(classifiedDomain: AmicoClassifiedDomain): AmicoDomainId {
  return classifiedDomain === "images" ? "images" : "business";
}

export function resolveMessageRouting(activeDomain: AmicoDomainId, message: string, classifiedDomain?: AmicoClassifiedDomain | null) {
  const resolvedClassification = classifiedDomain || classifyDomain(message);
  const routingDomain = routingDomainFromClassification(resolvedClassification);
  const mismatchPrevented = resolvedClassification !== "links" && routingDomain !== activeDomain;

  if (mismatchPrevented) {
    console.warn("DOMAIN MISMATCH PREVENTED", {
      uiDomain: activeDomain,
      classifiedDomain: resolvedClassification,
      routingDomain,
      message,
    });
  }

  return {
    classifiedDomain: resolvedClassification,
    routingDomain,
    mismatchPrevented,
  };
}

export function determineRequestType(activeDomain: AmicoDomainId, userInput: string, selectedStarterAction?: string | null): AmicoRequestType {
  void userInput;
  void selectedStarterAction;

  if (activeDomain === "images") {
    return "image_generation";
  }

  return "chat";
}

export function buildAssistantRequest(context: AssistantRequestContext): AssistantRequestEnvelope {
  const routing = resolveMessageRouting(context.activeDomain, context.userInput, context.classifiedDomain);
  const domain = AMICO_DOMAINS[routing.routingDomain];
  const capabilities = resolveAmicoCapabilities(context.capabilities);
  const selectedStarterAction = context.selectedStarterAction?.trim() || null;
  const requestType = determineRequestType(routing.routingDomain, context.userInput, selectedStarterAction);
  const projectLine = context.project ? `Current Project: ${context.project}` : null;
  const sessionLine = context.sessionId ? `Session Context: ${context.sessionId}` : null;
  const starterLine = selectedStarterAction ? `Selected Starter Action: ${selectedStarterAction}` : null;
  const keywordLine = domain.keywords.length ? `Domain Keywords: ${domain.keywords.join(", ")}` : null;
  const toolHintLine = domain.toolHints.length ? `Tool Hints: ${domain.toolHints.join(", ")}` : null;

  if (routing.routingDomain === "business") {
    return {
      requestType: "chat",
      activeDomain: routing.routingDomain,
      uiDomain: context.activeDomain,
      classifiedDomain: routing.classifiedDomain,
      selectedStarterAction,
      capabilities,
      responseStyle: domain.responseStyle,
      toolHints: domain.toolHints,
      message: buildBusinessPrompt({
        userInput: context.userInput,
        selectedStarterAction,
        project: context.project,
        sessionId: context.sessionId,
      }),
    };
  }

  if (routing.routingDomain === "images") {
    return {
      requestType: "image_generation",
      activeDomain: routing.routingDomain,
      uiDomain: context.activeDomain,
      classifiedDomain: routing.classifiedDomain,
      selectedStarterAction,
      capabilities,
      responseStyle: domain.responseStyle,
      toolHints: domain.toolHints,
      message: buildImagesPrompt({
        userInput: context.userInput,
        selectedStarterAction,
        project: context.project,
        sessionId: context.sessionId,
      }),
    };
  }
  return {
    requestType,
    activeDomain: routing.routingDomain,
    uiDomain: context.activeDomain,
    classifiedDomain: routing.classifiedDomain,
    selectedStarterAction,
    capabilities,
    responseStyle: domain.responseStyle,
    toolHints: domain.toolHints,
    message: [
      domain.systemPrompt,
      projectLine,
      sessionLine,
      starterLine,
      keywordLine,
      toolHintLine,
      `Preferred Response Style: ${domain.responseStyle}`,
      "Behave like a practical in-app software workspace for this domain.",
      "Prioritize professional, actionable, domain-specific outputs over generic advice.",
      "When useful, return a title, summary, sections, next steps, relevant official resources, and follow-up actions.",
      `User Request: ${context.userInput}`,
    ].filter(Boolean).join("\n\n"),
  };
}