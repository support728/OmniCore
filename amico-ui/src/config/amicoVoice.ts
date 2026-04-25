import type { AmicoDomainId } from "./amicoDomains";

export type AmicoVoiceStyle = {
  id: string;
  label: string;
  rate: number;
  pitch: number;
  lang: string;
};

export const AMICO_VOICE_STYLES = {
  guide: {
    id: "guide",
    label: "Guide",
    rate: 0.98,
    pitch: 1,
    lang: "en-US",
  },
  planner: {
    id: "planner",
    label: "Planner",
    rate: 0.96,
    pitch: 0.98,
    lang: "en-US",
  },
  tutor: {
    id: "tutor",
    label: "Tutor",
    rate: 1,
    pitch: 1.02,
    lang: "en-US",
  },
  analyst: {
    id: "analyst",
    label: "Analyst",
    rate: 0.94,
    pitch: 0.96,
    lang: "en-US",
  },
  creative: {
    id: "creative",
    label: "Creative",
    rate: 1,
    pitch: 1.04,
    lang: "en-US",
  },
} as const satisfies Record<string, AmicoVoiceStyle>;

export type AmicoVoiceStyleId = keyof typeof AMICO_VOICE_STYLES;

export const AMICO_VOICE_CONFIG = {
  defaultVoiceId: "system-default",
  defaultStyle: "guide" as AmicoVoiceStyleId,
  domainDefaults: {
    business: "planner",
    government: "guide",
    healthcare: "guide",
    education: "tutor",
    email: "guide",
    forms: "guide",
    blueprint: "planner",
    research: "analyst",
    images: "creative",
  } satisfies Record<AmicoDomainId, AmicoVoiceStyleId>,
};