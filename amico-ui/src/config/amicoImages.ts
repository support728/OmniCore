const createAction = (label: string, prompt: string) => ({ label, prompt });
const createLink = (label: string, url: string, description: string) => ({
  label,
  url,
  description,
  openInApp: true,
});
const createWorkflow = (title: string, description: string, prompt: string) => ({
  title,
  description,
  prompt,
});

const IMAGE_INTENT_PREFIX_PATTERN = /^(create|design|build|make|generate|draft|plan|show|give me)\s+/i;
const IMAGE_KEYWORD_PATTERN = /\b(image|poster|design|visual|concept|postcard|layout|campaign|mockup|storyboard)\b/gi;
const IMAGE_STOPWORD_PATTERN = /\b(a|an|the|for|with|of|to|please|me|my)\b/gi;

function toTitleCase(value: string) {
  return value
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function extractImageSubject(userInput: string) {
  const cleaned = String(userInput || "")
    .replace(IMAGE_INTENT_PREFIX_PATTERN, "")
    .replace(IMAGE_KEYWORD_PATTERN, " ")
    .replace(IMAGE_STOPWORD_PATTERN, " ")
    .replace(/\s{2,}/g, " ")
    .trim();

  return cleaned || String(userInput || "").trim() || "the requested subject";
}

export function inferImageFormat(userInput: string) {
  if (/postcard/i.test(userInput)) {
    return "postcard";
  }

  if (/poster/i.test(userInput)) {
    return "poster";
  }

  if (/mockup/i.test(userInput)) {
    return "mockup";
  }

  if (/layout/i.test(userInput)) {
    return "layout";
  }

  return "concept";
}

export function inferImageStyle(userInput: string) {
  if (/cinematic/i.test(userInput)) {
    return "cinematic";
  }

  if (/luxury|premium/i.test(userInput)) {
    return "luxury";
  }

  if (/minimal|clean/i.test(userInput)) {
    return "minimal";
  }

  if (/travel/i.test(userInput)) {
    return "travel";
  }

  return "editorial";
}

export function buildImagePlanDetails(userInput: string) {
  const subject = extractImageSubject(userInput);
  const format = inferImageFormat(userInput);
  const styleTone = inferImageStyle(userInput);
  const subjectTitle = toTitleCase(subject);
  const aspectRatio =
    format === "postcard"
      ? "3:2"
      : format === "poster"
        ? "4:5"
        : format === "layout"
          ? "16:9"
          : "1:1";
  const style = `${toTitleCase(styleTone)} ${toTitleCase(format)}`;
  const composition =
    format === "postcard"
      ? `Keep ${subject} centered with clear mailing-safe margins, a foreground focal point, and reserved space for short message copy.`
      : format === "poster"
        ? `Use ${subject} as the hero element with bold hierarchy, a strong focal point, and dedicated headline space.`
        : format === "mockup"
          ? `Frame ${subject} in a realistic commercial setup with clean surfaces, product clarity, and depth.`
          : `Build a balanced visual around ${subject} with clear hierarchy, breathing room, and readable spacing.`;
  const lighting =
    styleTone === "cinematic"
      ? "Directional dramatic lighting with contrast, atmospheric highlights, and controlled shadows."
      : styleTone === "luxury"
        ? "Soft premium studio lighting with refined highlights and polished surface detail."
        : styleTone === "minimal"
          ? "Bright clean lighting with even exposure and low visual noise."
          : "Professional editorial lighting with crisp detail and balanced contrast.";
  const negativePrompt =
    format === "postcard"
      ? "blurry, distorted, cluttered layout, unreadable text, cropped borders, low detail"
      : "blurry, distorted, cluttered layout, unreadable text, bad anatomy, low detail";
  const prompt = [
    `Create a ${styleTone} ${format} centered on ${subject}`,
    composition,
    lighting,
    `Aspect ratio ${aspectRatio}`,
    `Avoid: ${negativePrompt}`,
  ].join(", ");
  const variations = [
    `${toTitleCase(format)} variation A: hero-focused ${subject} with ${styleTone} treatment, tighter crop, and bold focal contrast.`,
    `${toTitleCase(format)} variation B: wider environmental composition for ${subject} with supporting context and calmer pacing.`,
    `${toTitleCase(format)} variation C: typography-ready layout for ${subject} with negative space, alternate angle, and brand-safe framing.`,
  ];

  return {
    title: `${subjectTitle} ${toTitleCase(format)}`,
    subject: subjectTitle,
    format,
    aspectRatio,
    style,
    composition,
    lighting,
    negativePrompt,
    prompt,
    variations,
  };
}

const IMAGE_STARTER_ACTION_BIASES: Record<string, string> = {
  "Create image concept": "Focus on subject, mood, composition, palette, and a production-ready prompt.",
  "Poster design": "Bias toward poster hierarchy, headline space, bold focal composition, and print-ready layout guidance.",
  "Postcard design": "Bias toward postcard framing, concise message placement, readable margins, and tactile print mood.",
  "Product mockup": "Bias toward product visibility, clean surfaces, camera angle, lighting, and commercial polish.",
  "Storyboard concept": "Bias toward sequential visual beats, cinematic framing, and campaign-level continuity.",
};

export const AMICO_IMAGES_DOMAIN = {
  id: "images",
  title: "Images",
  description: "Create image concepts, poster designs, mockups, and production-ready AI visual prompts.",
  icon: "image",
  badge: "IMG",
  badgeLabel: "IMG",
  color: "#9b3b65",
  placeholder: "Ask Images anything...",
  systemPrompt:
    "You are Amico Images, an in-app visual concept and prompt design assistant. Convert ideas into image concepts, composition direction, lighting plans, production-ready prompts, and practical variations. Do not claim an image was created unless a generation result is actually returned.",
  starterActions: [
    createAction("Create image concept", "Create an image concept for my idea."),
    createAction("Poster design", "Design a poster concept for this message."),
    createAction("Postcard design", "Create a postcard visual concept."),
    createAction("Product mockup", "Create a product mockup prompt and concept."),
    createAction("Storyboard concept", "Create a storyboard concept for this idea."),
  ],
  quickLinks: [
    createLink("Adobe Color", "https://color.adobe.com/", "Color palette and visual harmony inspiration."),
    createLink("Google Fonts", "https://fonts.google.com/", "Typography ideas for posters, mockups, and visual systems."),
    createLink("Canva color wheel", "https://www.canva.com/colors/color-wheel/", "Color and contrast support for visual composition."),
  ],
  suggestedPrompts: [
    "Create a cinematic poster prompt.",
    "Write a clean product mockup prompt.",
    "Design a postcard with a travel mood.",
    "Turn this brand idea into a visual campaign concept.",
  ],
  categories: ["Image Concepts", "AI Prompts", "Posters", "Postcards", "Mockups", "Storyboards", "Brand Visuals", "Design Tips"],
  workflowTemplates: [
    createWorkflow("Concept to prompt", "Move from rough idea to polished AI image prompt.", "Turn my idea into an image concept and AI prompt."),
    createWorkflow("Campaign visual system", "Create concept, style, typography, and palette direction.", "Build a visual system for this campaign idea."),
    createWorkflow("Mockup planning", "Define camera angle, product placement, lighting, and detail.", "Create a product mockup plan and prompt."),
  ],
  workflows: [
    createWorkflow("Concept to prompt", "Move from rough idea to polished AI image prompt.", "Turn my idea into an image concept and AI prompt."),
    createWorkflow("Campaign visual system", "Create concept, style, typography, and palette direction.", "Build a visual system for this campaign idea."),
    createWorkflow("Mockup planning", "Define camera angle, product placement, lighting, and detail.", "Create a product mockup plan and prompt."),
  ],
  keywords: ["image concept", "prompt", "poster", "postcard", "mockup", "campaign visual", "scene concept", "brand visual"],
  responseStyle: "Creative, production-ready, visually specific, and honest about generation status.",
  toolHints: ["image_prompts", "variation_design", "format_adaptation", "visual_direction"],
  voiceStyle: "creative",
} as const;

export type ImagesPromptContext = {
  userInput: string;
  selectedStarterAction?: string | null;
  project?: string | null;
  sessionId?: string | null;
};

export function buildImagesPrompt(context: ImagesPromptContext) {
  const selectedStarterAction = context.selectedStarterAction?.trim() || null;
  const starterBias = selectedStarterAction ? IMAGE_STARTER_ACTION_BIASES[selectedStarterAction] : null;
  const projectLine = context.project ? `Current Project: ${context.project}` : null;
  const sessionLine = context.sessionId ? `Session Context: ${context.sessionId}` : null;
  const imagePlan = buildImagePlanDetails(context.userInput);

  return [
    AMICO_IMAGES_DOMAIN.systemPrompt,
    "Active Software Area: Images",
    projectLine,
    sessionLine,
    selectedStarterAction ? `Images Starter Action: ${selectedStarterAction}` : null,
    starterBias ? `Images Focus: ${starterBias}` : null,
    `Primary Subject: ${imagePlan.subject}`,
    `Requested Format: ${imagePlan.format}`,
    `Target Aspect Ratio: ${imagePlan.aspectRatio}`,
    `Style Direction: ${imagePlan.style}`,
    `Composition Direction: ${imagePlan.composition}`,
    `Lighting Direction: ${imagePlan.lighting}`,
    `Negative Prompt Guidance: ${imagePlan.negativePrompt}`,
    `Image Keywords: ${AMICO_IMAGES_DOMAIN.keywords.join(", ")}`,
    `Preferred Response Style: ${AMICO_IMAGES_DOMAIN.responseStyle}`,
    `Tool Hints: ${AMICO_IMAGES_DOMAIN.toolHints.join(", ")}`,
    "Always return domain: images.",
    "Return image-planning content only. Do not switch into business, research, or coaching guidance.",
    "Return a structured response with these fields when possible: type, title, summary, sections, links, actions, nextSteps, prompt, style, aspectRatio, subject, composition, lighting, negativePrompt, variations.",
    `Base prompt seed: ${imagePlan.prompt}`,
    `Required variation directions: ${imagePlan.variations.join(" | ")}`,
    "If direct image generation is unavailable, say exactly: Amico can currently produce a production-ready image prompt, layout plan, and variations, but direct image generation is not connected yet.",
    "Do not pretend an image was created unless a real image URL is present.",
    `User Request: ${context.userInput}`,
  ].filter(Boolean).join("\n\n");
}