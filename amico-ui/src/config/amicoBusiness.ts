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

const BUSINESS_STARTER_ACTION_BIASES: Record<string, string> = {
  "Start LLC": "Prioritize entity formation order, state filing, EIN, operating agreement, banking, licenses, tax setup, and first-week actions.",
  "Write business plan": "Produce a concise, execution-ready business plan with offer, customer, market, operations, finances, and launch milestones.",
  "Pricing model": "Recommend practical pricing logic, margin thinking, positioning, competitor context, and a starting offer structure.",
  "Compliance checklist": "Call out licenses, permits, insurance, registrations, tax obligations, contracts, and recordkeeping needs without pretending to give legal advice.",
  "Launch roadmap": "Organize the answer as a phased launch sequence with what to do first, dependencies, and immediate next actions.",
  "Staffing and operations": "Focus on essential roles, responsibilities, workflows, handoffs, staffing order, and operating controls for an early-stage team.",
  "Construction startup": "Bias toward licensing, bonding, insurance, estimating, crews, equipment, job costing, safety, and bid readiness.",
  "Restaurant startup": "Bias toward concept definition, permits, food safety, menu economics, labor planning, vendors, and opening-readiness steps.",
  "Consulting startup": "Bias toward service packaging, pricing, niche positioning, client acquisition, proposals, contracts, and delivery workflow.",
  "Product business startup": "Bias toward product validation, sourcing, unit economics, branding, channels, inventory, and launch sequencing.",
};

export const AMICO_BUSINESS_DOMAIN = {
  id: "business",
  title: "Business",
  description: "Formation, planning, pricing, staffing, compliance, and launch operations for real businesses.",
  icon: "briefcase",
  badge: "BUS",
  badgeLabel: "BUS",
  color: "#1f4b99",
  placeholder: "Ask Amico Business anything...",
  systemPrompt:
    "You are Amico Business, a dedicated business operating assistant inside Amico. Help users move from idea to operating business with practical step-by-step execution, startup structure, pricing, staffing, launch planning, compliance awareness, and resource-oriented guidance. Be commercially realistic, avoid generic motivational filler, and keep the user inside Amico whenever possible.",
  starterActions: [
    createAction("Start LLC", "Help me start an LLC step by step, including filings, EIN, banking, and first setup tasks."),
    createAction("Write business plan", "Write a practical business plan for my business idea with sections I can use immediately."),
    createAction("Pricing model", "Create a pricing model for my offer with tiers, margin thinking, and positioning guidance."),
    createAction("Compliance checklist", "Create a compliance checklist for launching this business, including licenses, tax, insurance, and documents."),
    createAction("Launch roadmap", "Build a launch roadmap for this business from setup to first customers."),
    createAction("Staffing and operations", "Define staffing roles, responsibilities, and operations workflows for this business."),
    createAction("Construction startup", "Help me start a construction company with licensing, staffing, estimating, and launch steps."),
    createAction("Restaurant startup", "Help me launch a restaurant business with permits, staffing, menu planning, and opening steps."),
    createAction("Consulting startup", "Help me start a consulting business with positioning, services, pricing, and client acquisition steps."),
    createAction("Product business startup", "Help me start a product business with validation, sourcing, pricing, and launch planning."),
  ],
  quickLinks: [
    createLink("SBA startup guide", "https://www.sba.gov/business-guide", "Official startup, planning, and registration guidance for small businesses."),
    createLink("IRS EIN guide", "https://www.irs.gov/businesses/small-businesses-self-employed/employer-id-numbers", "Official EIN setup information for new businesses."),
    createLink("SBA learning center", "https://www.sba.gov/learning-center", "Business planning, operations, and growth training resources."),
    createLink("SCORE mentoring", "https://www.score.org/", "Mentoring, templates, and startup planning support for business owners."),
  ],
  suggestedPrompts: [
    "Create a first-90-days launch checklist for my business.",
    "Turn my idea into a lean business plan with revenue assumptions.",
    "What documents and accounts should I set up first?",
    "Create staffing roles for a five-person startup team.",
  ],
  categories: ["Startup Setup", "Planning", "Pricing", "Compliance", "Launch", "Staffing", "Operations", "Positioning"],
  workflowTemplates: [
    createWorkflow("LLC setup workflow", "Move from entity choice to filings, EIN, banking, and launch readiness.", "Create an LLC setup workflow with formation, EIN, banking, taxes, and immediate next steps."),
    createWorkflow("Business plan sprint", "Turn a business idea into a usable operating plan, offer, market, and financial outline.", "Build a business plan sprint with core sections, decisions, and next actions."),
    createWorkflow("Launch roadmap", "Organize setup, compliance, pricing, marketing, and first-customer milestones.", "Create a business launch roadmap with phases, dependencies, and first-customer milestones."),
    createWorkflow("Compliance checklist", "List the registrations, licenses, insurance, tax, and contract basics to launch safely.", "Create a business compliance checklist with licenses, registrations, tax, insurance, and recordkeeping steps."),
  ],
  workflows: [
    createWorkflow("LLC setup workflow", "Move from entity choice to filings, EIN, banking, and launch readiness.", "Create an LLC setup workflow with formation, EIN, banking, taxes, and immediate next steps."),
    createWorkflow("Business plan sprint", "Turn a business idea into a usable operating plan, offer, market, and financial outline.", "Build a business plan sprint with core sections, decisions, and next actions."),
    createWorkflow("Launch roadmap", "Organize setup, compliance, pricing, marketing, and first-customer milestones.", "Create a business launch roadmap with phases, dependencies, and first-customer milestones."),
    createWorkflow("Compliance checklist", "List the registrations, licenses, insurance, tax, and contract basics to launch safely.", "Create a business compliance checklist with licenses, registrations, tax, insurance, and recordkeeping steps."),
  ],
  keywords: ["llc", "business plan", "pricing", "compliance", "launch", "staffing", "construction", "restaurant", "consulting", "product business"],
  responseStyle: "Structured, execution-first, commercially realistic, and resource-oriented.",
  toolHints: ["official_resources", "launch_plans", "pricing_frameworks", "compliance_checklists", "operations_design"],
  voiceStyle: "planner",
} as const;

export const AMICO_BUSINESS_PANEL = {
  title: "Business",
  subtitle: "Operate Amico like a business workspace with startup setup, pricing, compliance, staffing, and launch planning.",
  badge: "BUS",
  primaryStarterActions: AMICO_BUSINESS_DOMAIN.starterActions.slice(0, 6),
  workflowPills: ["LLC setup", "Business plan", "Pricing", "Compliance", "Launch", "Staffing"],
  quickResources: AMICO_BUSINESS_DOMAIN.quickLinks,
} as const;

export type BusinessPromptContext = {
  userInput: string;
  selectedStarterAction?: string | null;
  project?: string | null;
  sessionId?: string | null;
};

type BusinessFallbackResponse = {
  title: string;
  summary: string;
  sections: Array<{ heading: string; body: string }>;
  links: Array<{ label: string; url: string; description: string; openInApp: boolean; official?: boolean }>;
  nextSteps: string[];
};

export function buildBusinessFallbackResponse(userInput: string): BusinessFallbackResponse {
  const normalized = String(userInput || "").toLowerCase();

  if (/llc|ein|minnesota/.test(normalized)) {
    return {
      title: "Basic LLC Setup Checklist",
      summary: "Here’s a basic LLC setup checklist you can start with right now.",
      sections: [
        {
          heading: "Formation Steps",
          body: "Choose your LLC name, confirm Minnesota availability, file the LLC with the Minnesota Secretary of State, and save the formation confirmation.",
        },
        {
          heading: "Tax and Banking",
          body: "Apply for an EIN with the IRS, open a business bank account, and separate personal and business spending from day one.",
        },
        {
          heading: "Operating Basics",
          body: "Create an operating agreement, list required licenses or permits, and decide who is responsible for taxes, records, and renewals.",
        },
      ],
      links: [
        {
          label: "Minnesota Secretary of State business filings",
          url: "https://www.sos.state.mn.us/business-liens/start-a-business/how-to-register-your-business/",
          description: "Official Minnesota LLC and business registration guidance.",
          openInApp: true,
          official: true,
        },
        {
          label: "IRS EIN guide",
          url: "https://www.irs.gov/businesses/small-businesses-self-employed/employer-id-numbers",
          description: "Official EIN application information from the IRS.",
          openInApp: true,
          official: true,
        },
      ],
      nextSteps: [
        "Confirm the LLC name is available in Minnesota.",
        "File the LLC paperwork and save your confirmation documents.",
        "Apply for the EIN after the filing is accepted.",
      ],
    };
  }

  if (/roadmap|launch/.test(normalized)) {
    return {
      title: "Basic Launch Roadmap",
      summary: "Here is a simple launch roadmap you can use while the backend is unavailable.",
      sections: [
        {
          heading: "Week 1",
          body: "Define the offer, target customer, price, and the one result you want early customers to get.",
        },
        {
          heading: "Week 2",
          body: "Set up the legal basics, payment flow, contact method, and a simple page or one-page sales explanation.",
        },
        {
          heading: "Week 3",
          body: "Talk to real prospects, test the offer, collect objections, and tighten the message based on what they say.",
        },
      ],
      links: AMICO_BUSINESS_DOMAIN.quickLinks.map((link) => ({ ...link, official: /sba|irs/i.test(link.url) })),
      nextSteps: [
        "Write the first offer in one plain sentence.",
        "Choose one channel to reach the first 5 prospects.",
        "Turn the roadmap into a dated checklist.",
      ],
    };
  }

  return {
    title: "Basic Business Guidance",
    summary: "Here is a simple business fallback plan while the backend is unavailable.",
    sections: [
      {
        heading: "Core Setup",
        body: "Define what you sell, who it is for, what problem it solves, and how someone pays you.",
      },
      {
        heading: "First Operating Steps",
        body: "Set up the legal, payment, contact, and recordkeeping basics before trying to scale anything.",
      },
    ],
    links: AMICO_BUSINESS_DOMAIN.quickLinks.map((link) => ({ ...link, official: /sba|irs/i.test(link.url) })),
    nextSteps: [
      "Clarify the offer and target customer.",
      "List the first legal or tax actions required.",
      "Ask Amico Business for a checklist, roadmap, or pricing model once the backend is available.",
    ],
  };
}

export function buildBusinessPrompt(context: BusinessPromptContext) {
  const selectedStarterAction = context.selectedStarterAction?.trim() || null;
  const projectLine = context.project ? `Current Project: ${context.project}` : null;
  const sessionLine = context.sessionId ? `Session Context: ${context.sessionId}` : null;
  const starterLine = selectedStarterAction ? `Business Starter Action: ${selectedStarterAction}` : null;
  const starterBias = selectedStarterAction ? BUSINESS_STARTER_ACTION_BIASES[selectedStarterAction] : null;

  return [
    AMICO_BUSINESS_DOMAIN.systemPrompt,
    "Active Software Area: Business",
    projectLine,
    sessionLine,
    starterLine,
    starterBias ? `Business Focus: ${starterBias}` : null,
    `Business Keywords: ${AMICO_BUSINESS_DOMAIN.keywords.join(", ")}`,
    `Preferred Response Style: ${AMICO_BUSINESS_DOMAIN.responseStyle}`,
    `Tool Hints: ${AMICO_BUSINESS_DOMAIN.toolHints.join(", ")}`,
    "Always return domain: business.",
    "Respond like a business operating assistant, not a generic chatbot.",
    "Bias toward step-by-step execution, required documents or inputs, pricing and operating decisions, compliance awareness, and immediate next actions.",
    "When useful, use one of these response shapes: guide, workflow, resource_list, or answer.",
    "At minimum include a title, a concise summary, practical sections, and next steps when the request involves planning or execution.",
    "When official resources are relevant, include direct links the user can open inside Amico.",
    "Avoid filler, repeated coaching, and cross-domain wording.",
    `User Request: ${context.userInput}`,
  ].filter(Boolean).join("\n\n");
}
