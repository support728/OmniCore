import { buildAssistantRequest } from "../config/amicoOrchestration";
import api from "../api/client";

/**
 * CORE REQUEST
 */
async function postChat(data) {
  try {
    console.log("OUTGOING PAYLOAD:", data);

    const res = await api.post("/chat", data);

    console.log("API RAW RESPONSE:", res);

    if (!res || !res.data) {
      throw new Error("NO_RESPONSE_FROM_SERVER");
    }

    return res.data;
  } catch (error) {
    console.error("postChat ERROR:", error);

    if (error.response) {
      // Server responded but with error
      throw new Error(
        error.response.data?.message ||
        error.response.data?.error ||
        "SERVER_ERROR"
      );
    }

    if (error.request) {
      // Request made but no response
      throw new Error("BACKEND_NOT_REACHABLE");
    }

    throw new Error(error.message || "UNKNOWN_ERROR");
  }
}

/**
 * SIMPLE CHAT
 */
export async function sendChat(data) {
  return await postChat(data);
}

/**
 * BUSINESS REQUEST
 */
async function doBusinessRequest(payload) {
  const data = await postChat(payload);

  if (!data || !String(data.content || "").trim()) {
    throw new Error("EMPTY_RESPONSE");
  }

  return data;
}

export async function sendBusinessMessage({
  userMessage,
  sessionId,
  userId,
  project,
  selectedStarterAction,
  uiDomain = "business",
  capabilities,
  onRetry,
}) {
  const request = buildAssistantRequest({
    activeDomain: "business",
    classifiedDomain: "business",
    userInput: userMessage,
    project,
    sessionId,
    selectedStarterAction,
    capabilities,
  });

  const payload = {
    message: userMessage,
    mode: "business",
    prompt: request.message,
    session_id: sessionId,
    user_id: userId,
    project,
    activeDomain: request.activeDomain,
    ui_domain: uiDomain,
    selected_starter_action: request.selectedStarterAction,
    response_style: request.responseStyle,
    tool_hints: request.toolHints,
    capabilities: request.capabilities,
  };

  if (typeof onRetry === "function") {
    onRetry("Sending request to backend...");
  }

  return doBusinessRequest(payload);
}

/**
 * MESSAGE ACTIONS
 */
async function postMessageAction(prompt, message, session_id, user_id, activeDomain) {
  const request = buildAssistantRequest({
    activeDomain,
    userInput: `${prompt}${message}`,
    sessionId: session_id,
  });

  return await postChat({
    message: request.message,
    mode: activeDomain || "general",
    session_id,
    user_id,
    activeDomain,
    request_type: request.requestType,
    selected_starter_action: request.selectedStarterAction,
    response_style: request.responseStyle,
    tool_hints: request.toolHints,
    capabilities: request.capabilities,
  });
}

/**
 * BASIC HELPERS
 */
export async function sendQuery(query) {
  return sendChat({ message: query, mode: "general" });
}

export async function sendMessage(message) {
  try {
    return await sendQuery(message);
  } catch (error) {
    console.error("sendMessage ERROR:", error.message);
    return error.message;
  }
}

export async function fetchPreview(url) {
  try {
    const res = await api.get(`/preview?url=${encodeURIComponent(url)}`);
    return res.data;
  } catch (error) {
    console.error("fetchPreview ERROR:", error);
    throw new Error("PREVIEW_FAILED");
  }
}

export async function summarizeMessage(message, session_id, user_id, activeDomain) {
  return postMessageAction("Summarize this: ", message, session_id, user_id, activeDomain);
}

export async function relateMessage(message, session_id, user_id, activeDomain) {
  return postMessageAction("Relate this to something useful: ", message, session_id, user_id, activeDomain);
}