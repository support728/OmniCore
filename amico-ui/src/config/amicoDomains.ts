import { AMICO_BUSINESS_DOMAIN, buildBusinessPrompt } from "./amicoBusiness";
import { AMICO_IMAGES_DOMAIN, buildImagesPrompt } from "./amicoImages";

export type DomainStarterAction = {
  label: string;
  prompt: string;
};

export type DomainQuickLink = {
  label: string;
  url: string;
  description: string;
  openInApp: boolean;
};

export type DomainWorkflow = {
  title: string;
  description: string;
  prompt: string;
};

export type AmicoDomainConfig = {
  id: string;
  title: string;
  description: string;
  icon: string;
  badge: string;
  badgeLabel: string;
  color: string;
  placeholder: string;
  systemPrompt: string;
  starterActions: DomainStarterAction[];
  quickLinks: DomainQuickLink[];
  suggestedPrompts: string[];
  categories: string[];
  workflowTemplates: DomainWorkflow[];
  workflows: DomainWorkflow[];
  keywords: string[];
  responseStyle: string;
  toolHints: string[];
  voiceStyle: string;
};

const createAction = (label: string, prompt: string): DomainStarterAction => ({ label, prompt });

const createLink = (label: string, url: string, description: string): DomainQuickLink => ({
  label,
  url,
  description,
  openInApp: true,
});

const createWorkflow = (title: string, description: string, prompt: string): DomainWorkflow => ({
  title,
  description,
  prompt,
});

export const AMICO_DOMAINS = {
  business: AMICO_BUSINESS_DOMAIN,
  government: {
    id: "government",
    title: "Government",
    description: "Public programs, permits, grants, agencies, and official process navigation.",
    icon: "landmark",
    badge: "GOV",
    badgeLabel: "GOV",
    color: "#215c48",
    placeholder: "Ask Government anything...",
    systemPrompt:
      "You are Amico Government, an in-app public resource navigator. Help users work through grants, permits, licenses, benefits, city-state-federal programs, and agency processes. Prefer official resources, explain steps plainly, identify likely documents, and give realistic next actions.",
    starterActions: [
      createAction("Find grants", "Find grants that may fit my situation."),
      createAction("Permit checklist", "Create a permit and license checklist."),
      createAction("Agency lookup", "Which government agency should I contact?"),
      createAction("Program application", "Walk me through applying for a government program."),
      createAction("Official forms help", "Explain this government form in simple steps."),
    ],
    quickLinks: [
      createLink("USA.gov", "https://www.usa.gov/", "Official federal services and information portal."),
      createLink("Grants.gov", "https://www.grants.gov/", "Official grant search and application portal."),
      createLink("Benefits.gov", "https://www.benefits.gov/", "Find public assistance and benefits programs."),
    ],
    suggestedPrompts: [
      "What documents do I need for this license?",
      "Compare city, state, and federal requirements.",
      "Find public programs for a small business owner.",
      "Explain this agency application in plain language.",
    ],
    categories: ["Grants", "Permits", "Licenses", "Benefits", "Agencies", "Applications", "Forms", "Official Links"],
    workflowTemplates: [
      createWorkflow("Grant search workflow", "Find, qualify, and prepare for a grant application.", "Build a grant search workflow with eligibility, deadlines, and document prep."),
      createWorkflow("Permit path", "Map the sequence for approvals and agency contact points.", "Map the permit process for my project with agency touchpoints."),
      createWorkflow("Program readiness", "Checklist for documents, deadlines, and follow-up.", "Create a readiness checklist for a public program application."),
    ],
    workflows: [
      createWorkflow("Grant search workflow", "Find, qualify, and prepare for a grant application.", "Build a grant search workflow with eligibility, deadlines, and document prep."),
      createWorkflow("Permit path", "Map the sequence for approvals and agency contact points.", "Map the permit process for my project with agency touchpoints."),
      createWorkflow("Program readiness", "Checklist for documents, deadlines, and follow-up.", "Create a readiness checklist for a public program application."),
    ],
    keywords: ["grants", "permits", "licenses", "agencies", "assistance", "filing", "eligibility", "official links"],
    responseStyle: "Official-resource-first, procedural, and document-aware.",
    toolHints: ["official_resources", "agency_lookup", "filing_checklists", "eligibility_guidance"],
    voiceStyle: "guide",
  },
  healthcare: {
    id: "healthcare",
    title: "Healthcare",
    description: "Provider setup, 245D, compliance, documentation, and operational guidance.",
    icon: "shield",
    badge: "HLT",
    badgeLabel: "HLT",
    color: "#8d2f54",
    placeholder: "Ask Healthcare anything...",
    systemPrompt:
      "You are Amico Healthcare, an in-app healthcare operations assistant. Help users with provider startup, 245D services, clinic setup, policy guidance, documentation practices, compliance, quality, staffing, and safety considerations. Keep responses structured, operational, and practical.",
    starterActions: [
      createAction("Start a 245D company", "Help me start a 245D company step by step."),
      createAction("Compliance steps", "Create a healthcare compliance setup checklist."),
      createAction("Policy guidance", "What policies should a new provider have first?"),
      createAction("Clinic workflow", "Design a basic clinic workflow for intake and follow-up."),
      createAction("Documentation support", "Help me build documentation standards for staff."),
    ],
    quickLinks: [
      createLink("CMS", "https://www.cms.gov/", "Federal healthcare programs, compliance, and provider resources."),
      createLink("Minnesota 245D", "https://mn.gov/dhs/people-we-serve/people-with-disabilities/services/home-community/programs-and-services/245d/", "Official Minnesota 245D licensing and policy guidance."),
      createLink("Medicaid.gov", "https://www.medicaid.gov/", "Federal Medicaid policy and program resources."),
    ],
    suggestedPrompts: [
      "What documentation should staff complete daily?",
      "Build an intake to service delivery workflow.",
      "What training should new healthcare staff receive?",
      "Explain compliance priorities for a new provider.",
    ],
    categories: ["245D", "Compliance", "Policies", "Documentation", "Staff Training", "Clinic Setup", "Safety", "Quality"],
    workflowTemplates: [
      createWorkflow("Provider startup sequence", "Plan legal setup, policies, staffing, and audits.", "Create a provider startup sequence with compliance milestones."),
      createWorkflow("Documentation framework", "Outline documentation standards, reviews, and audits.", "Build a documentation framework for a healthcare provider."),
      createWorkflow("Quality and safety review", "Map incident handling, supervision, and quality checks.", "Create a quality and safety review workflow for my team."),
    ],
    workflows: [
      createWorkflow("Provider startup sequence", "Plan legal setup, policies, staffing, and audits.", "Create a provider startup sequence with compliance milestones."),
      createWorkflow("Documentation framework", "Outline documentation standards, reviews, and audits.", "Build a documentation framework for a healthcare provider."),
      createWorkflow("Quality and safety review", "Map incident handling, supervision, and quality checks.", "Create a quality and safety review workflow for my team."),
    ],
    keywords: ["245d", "compliance", "provider startup", "policies", "clinic", "documentation", "quality", "safety"],
    responseStyle: "Operational, compliant, and policy-conscious.",
    toolHints: ["compliance_checklists", "policy_guidance", "documentation_support", "workflow_design"],
    voiceStyle: "guide",
  },
  education: {
    id: "education",
    title: "Education",
    description: "Homework support, subject tutoring, concept explanation, and study planning.",
    icon: "book",
    badge: "EDU",
    badgeLabel: "EDU",
    color: "#785a12",
    placeholder: "Ask Education anything...",
    systemPrompt:
      "You are Amico Education, an in-app learning assistant. Help with homework, math, science, reading, writing, history, study plans, and concept explanations. Break problems into steps, teach clearly, and adapt explanations to the user's level.",
    starterActions: [
      createAction("Explain homework", "Explain this homework step by step."),
      createAction("Math help", "Help me solve a math problem and explain why."),
      createAction("Science help", "Explain this science concept in simple terms."),
      createAction("History help", "Help me understand this history topic."),
      createAction("Study plan", "Create a study plan for my subject."),
    ],
    quickLinks: [
      createLink("U.S. Department of Education", "https://www.ed.gov/", "Federal education information and student resources."),
      createLink("Khan Academy", "https://www.khanacademy.org/", "Structured learning support across subjects."),
      createLink("Library of Congress", "https://www.loc.gov/", "Historical and research materials for learning."),
    ],
    suggestedPrompts: [
      "Turn this lesson into a study guide.",
      "Quiz me on this topic.",
      "Explain this in kid-friendly language.",
      "Break this assignment into small steps.",
    ],
    categories: ["Math", "Science", "Reading", "Writing", "History", "Study Skills", "Homework", "Explanations"],
    workflowTemplates: [
      createWorkflow("Homework breakdown", "Turn a large assignment into manageable steps.", "Break my homework into a step-by-step plan."),
      createWorkflow("Study sprint plan", "Organize review sessions, practice, and self-testing.", "Create a one-week study sprint plan for my class."),
      createWorkflow("Concept mastery", "Learn, practice, review, and test understanding.", "Build a concept mastery plan for this subject."),
    ],
    workflows: [
      createWorkflow("Homework breakdown", "Turn a large assignment into manageable steps.", "Break my homework into a step-by-step plan."),
      createWorkflow("Study sprint plan", "Organize review sessions, practice, and self-testing.", "Create a one-week study sprint plan for my class."),
      createWorkflow("Concept mastery", "Learn, practice, review, and test understanding.", "Build a concept mastery plan for this subject."),
    ],
    keywords: ["homework", "math", "science", "history", "reading", "writing", "study plan", "explain"],
    responseStyle: "Clear, explanatory, and learner-adaptive.",
    toolHints: ["step_breakdown", "study_plans", "concept_explanations", "practice_support"],
    voiceStyle: "tutor",
  },
  email: {
    id: "email",
    title: "Email Help",
    description: "Explain emails, extract tasks, identify deadlines, and draft replies.",
    icon: "mail",
    badge: "EML",
    badgeLabel: "EML",
    color: "#3c4c97",
    placeholder: "Ask Email Help anything...",
    systemPrompt:
      "You are Amico Email Help, an in-app email assistant. Explain email meaning, summarize instructions, identify deadlines, extract action items, and draft replies. Keep responses calm, practical, and organized into what the email means, what to do next, and what to send back.",
    starterActions: [
      createAction("Explain this email", "Explain this email in plain language."),
      createAction("Draft reply", "Draft a professional reply to this email."),
      createAction("Action items", "Pull out all action items from this email."),
      createAction("Deadlines", "Identify deadlines and urgency in this email."),
      createAction("What do I do next?", "Tell me exactly what I should do next based on this email."),
    ],
    quickLinks: [
      createLink("Gmail Help", "https://support.google.com/mail/", "Official Gmail support and email workflow guidance."),
      createLink("Outlook Help", "https://support.microsoft.com/outlook", "Official Outlook help resources."),
      createLink("Google Workspace writing tips", "https://support.google.com/a/users/answer/9308722", "Professional email writing and organization help."),
    ],
    suggestedPrompts: [
      "Summarize this email in one paragraph.",
      "Draft a firm but polite response.",
      "Tell me what documents I need to send back.",
      "Turn this email into a checklist.",
    ],
    categories: ["Summaries", "Replies", "Deadlines", "Tasks", "Tone", "Clarification", "Follow-up", "Attachments"],
    workflowTemplates: [
      createWorkflow("Inbox triage", "Sort meaning, urgency, deadlines, and reply plan.", "Create an inbox triage workflow for this email."),
      createWorkflow("Reply drafting", "Build a clear, professional response with tone options.", "Draft a reply with a professional and concise tone."),
      createWorkflow("Action extraction", "Convert the email into tasks, owners, and due dates.", "Convert this email into action items and deadlines."),
    ],
    workflows: [
      createWorkflow("Inbox triage", "Sort meaning, urgency, deadlines, and reply plan.", "Create an inbox triage workflow for this email."),
      createWorkflow("Reply drafting", "Build a clear, professional response with tone options.", "Draft a reply with a professional and concise tone."),
      createWorkflow("Action extraction", "Convert the email into tasks, owners, and due dates.", "Convert this email into action items and deadlines."),
    ],
    keywords: ["email", "reply", "deadline", "summary", "checklist", "action items", "instructions"],
    responseStyle: "Concise, professional, and action-oriented.",
    toolHints: ["task_extraction", "reply_drafting", "deadline_detection", "instruction_summaries"],
    voiceStyle: "guide",
  },
  forms: {
    id: "forms",
    title: "Forms Help",
    description: "Field-by-field form guidance, missing information checks, and completion support.",
    icon: "form",
    badge: "FRM",
    badgeLabel: "FRM",
    color: "#5f3f91",
    placeholder: "Ask Forms Help anything...",
    systemPrompt:
      "You are Amico Forms Help, an in-app form walkthrough assistant. Explain form sections, break down each field, identify missing information, and guide users step by step through completion. Simplify legal or administrative language and keep instructions practical.",
    starterActions: [
      createAction("Explain this form", "Explain this form in simple language."),
      createAction("Field-by-field help", "Guide me through this form field by field."),
      createAction("Missing info", "What information is missing from this form?"),
      createAction("Document checklist", "What documents do I need for this form?"),
      createAction("Completion steps", "Create step-by-step completion instructions for this form."),
    ],
    quickLinks: [
      createLink("IRS forms", "https://www.irs.gov/forms-instructions", "Official tax forms and instructions."),
      createLink("SSA forms", "https://www.ssa.gov/forms/", "Official Social Security forms index."),
      createLink("USA.gov forms", "https://www.usa.gov/forms", "Federal forms and application portals."),
    ],
    suggestedPrompts: [
      "Explain section 1 in plain English.",
      "What should I prepare before starting this form?",
      "Check this form for missing answers.",
      "Summarize the key instructions from this application.",
    ],
    categories: ["Field Help", "Instructions", "Documents", "Missing Info", "Step-by-Step", "Applications", "Government Forms", "Compliance Forms"],
    workflowTemplates: [
      createWorkflow("Form prep", "Gather identity, supporting docs, and deadlines before filling.", "Create a preparation checklist for this form."),
      createWorkflow("Field walkthrough", "Explain the form field by field in order.", "Walk me through this form field by field."),
      createWorkflow("Final review", "Check completeness, consistency, and attachments.", "Review this form for missing or unclear information."),
    ],
    workflows: [
      createWorkflow("Form prep", "Gather identity, supporting docs, and deadlines before filling.", "Create a preparation checklist for this form."),
      createWorkflow("Field walkthrough", "Explain the form field by field in order.", "Walk me through this form field by field."),
      createWorkflow("Final review", "Check completeness, consistency, and attachments.", "Review this form for missing or unclear information."),
    ],
    keywords: ["form", "field", "missing information", "documents", "section", "legal form", "government form"],
    responseStyle: "Sequential, simplified, and detail-oriented.",
    toolHints: ["field_guidance", "document_checklists", "missing_info_detection", "plain_language_support"],
    voiceStyle: "guide",
  },
  blueprint: {
    id: "blueprint",
    title: "Blueprint",
    description: "Turn ideas into structured plans, milestones, deliverables, and implementation roadmaps.",
    icon: "blueprint",
    badge: "BLP",
    badgeLabel: "BLP",
    color: "#0b6a77",
    placeholder: "Ask Blueprint anything...",
    systemPrompt:
      "You are Amico Blueprint, an in-app planning and systems design assistant. Turn ideas into detailed blueprints with phases, milestones, deliverables, workflows, dependencies, risks, and compliance considerations. Organize responses like a software planning system.",
    starterActions: [
      createAction("Create a blueprint", "Create a full blueprint for my idea."),
      createAction("Idea to roadmap", "Turn this idea into a roadmap with phases and milestones."),
      createAction("System plan", "Design the system components and workflow for this concept."),
      createAction("Risk review", "Identify risks and blockers in this blueprint."),
      createAction("Deliverables", "List milestones and deliverables for this plan."),
    ],
    quickLinks: [
      createLink("NIST project resources", "https://www.nist.gov/itl/applied-cybersecurity/nice/resources", "Structured planning and capability-building resources."),
      createLink("NASA systems engineering", "https://www.nasa.gov/reference/systems-engineering-handbook/", "Reference material for system planning and structured design."),
      createLink("CISA planning resources", "https://www.cisa.gov/resources-tools", "Operational planning and readiness resources."),
    ],
    suggestedPrompts: [
      "Turn this concept into a three-phase roadmap.",
      "Write a milestone and dependency map.",
      "Convert this business idea into a working plan.",
      "Create a blueprint with compliance and risk sections.",
    ],
    categories: ["Roadmaps", "Milestones", "Deliverables", "Dependencies", "Risk", "Compliance", "Systems", "Implementation"],
    workflowTemplates: [
      createWorkflow("Concept to plan", "Move from rough idea to structured roadmap.", "Turn my idea into a structured implementation blueprint."),
      createWorkflow("Milestone planning", "Build phases, owners, and deliverables.", "Create milestones and deliverables for this project."),
      createWorkflow("Risk and compliance map", "Identify blockers, safeguards, and required reviews.", "Create a risk and compliance map for this plan."),
    ],
    workflows: [
      createWorkflow("Concept to plan", "Move from rough idea to structured roadmap.", "Turn my idea into a structured implementation blueprint."),
      createWorkflow("Milestone planning", "Build phases, owners, and deliverables.", "Create milestones and deliverables for this project."),
      createWorkflow("Risk and compliance map", "Identify blockers, safeguards, and required reviews.", "Create a risk and compliance map for this plan."),
    ],
    keywords: ["blueprint", "roadmap", "milestones", "risk", "deliverables", "phases", "implementation"],
    responseStyle: "Architectural, milestone-driven, and system-oriented.",
    toolHints: ["roadmap_templates", "risk_mapping", "deliverable_planning", "dependency_design"],
    voiceStyle: "planner",
  },
  research: {
    id: "research",
    title: "Research",
    description: "Compare options, summarize findings, rank results, and organize sources.",
    icon: "search",
    badge: "RSH",
    badgeLabel: "RSH",
    color: "#6b5d18",
    placeholder: "Ask Research anything...",
    systemPrompt:
      "You are Amico Research, an in-app research assistant. Compare options, gather sources, summarize findings, rank results, surface tradeoffs, and organize information into decision-ready outputs. Be structured, evidence-aware, and practical.",
    starterActions: [
      createAction("Compare options", "Compare these options with pros and cons."),
      createAction("Gather sources", "Research this topic and organize sources."),
      createAction("Summarize findings", "Summarize the findings clearly."),
      createAction("Rank results", "Rank the best options and explain why."),
      createAction("Research brief", "Create a concise research brief on this topic."),
    ],
    quickLinks: [
      createLink("Google Scholar", "https://scholar.google.com/", "Academic and research source discovery."),
      createLink("Data.gov", "https://www.data.gov/", "Official U.S. government datasets."),
      createLink("U.S. Census", "https://www.census.gov/", "Population, business, and location data for research."),
    ],
    suggestedPrompts: [
      "Find the top three options and rank them.",
      "Turn this topic into a pros and cons matrix.",
      "Summarize key trends from these results.",
      "Organize the sources by reliability and relevance.",
    ],
    categories: ["Comparisons", "Rankings", "Summaries", "Sources", "Data", "Tradeoffs", "Decision Support", "Briefs"],
    workflowTemplates: [
      createWorkflow("Research intake", "Clarify scope, questions, and success criteria.", "Create a research intake checklist for this topic."),
      createWorkflow("Comparison matrix", "Build categories, criteria, and rankings.", "Create a comparison matrix for these options."),
      createWorkflow("Decision brief", "Turn findings into a short recommendation memo.", "Write a decision brief based on the research findings."),
    ],
    workflows: [
      createWorkflow("Research intake", "Clarify scope, questions, and success criteria.", "Create a research intake checklist for this topic."),
      createWorkflow("Comparison matrix", "Build categories, criteria, and rankings.", "Create a comparison matrix for these options."),
      createWorkflow("Decision brief", "Turn findings into a short recommendation memo.", "Write a decision brief based on the research findings."),
    ],
    keywords: ["compare", "sources", "rank", "pros and cons", "decision", "research brief", "findings"],
    responseStyle: "Evidence-aware, comparative, and decision-ready.",
    toolHints: ["source_ranking", "comparison_matrices", "research_briefs", "decision_support"],
    voiceStyle: "analyst",
  },
  images: AMICO_IMAGES_DOMAIN,
} satisfies Record<string, AmicoDomainConfig>;

export type AmicoDomainId = keyof typeof AMICO_DOMAINS;
export type DomainQuickLinkEntry = DomainQuickLink & {
  domainId: AmicoDomainId;
  domainTitle: string;
};

export const AMICO_DOMAIN_ORDER = Object.keys(AMICO_DOMAINS) as AmicoDomainId[];

export function getDomainQuickLinks(): DomainQuickLinkEntry[] {
  return AMICO_DOMAIN_ORDER.flatMap((domainId) =>
    AMICO_DOMAINS[domainId].quickLinks.map((link) => ({
      ...link,
      domainId,
      domainTitle: AMICO_DOMAINS[domainId].title,
    })),
  );
}

export function buildDomainPrompt(domainId: AmicoDomainId, userMessage: string) {
  const domain = AMICO_DOMAINS[domainId];

  if (domainId === "business") {
    return buildBusinessPrompt({ userInput: userMessage });
  }

  if (domainId === "images") {
    return buildImagesPrompt({ userInput: userMessage });
  }

  return [
    domain.systemPrompt,
    `Active Domain: ${domain.title}`,
    `Response Style: ${domain.responseStyle}`,
    `Domain Keywords: ${domain.keywords.join(", ")}`,
    `Tool Hints: ${domain.toolHints.join(", ")}`,
    "Behave like a dedicated in-app software workspace for this domain.",
    "Respond with a practical structure that includes a short title, concise summary, step-by-step guidance, and next actions when useful.",
    "When official resources are relevant, include direct links that the user can open inside Amico.",
    `User Request: ${userMessage}`,
  ].join("\n\n");
}