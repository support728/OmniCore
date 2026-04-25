export type AmicoCapabilities = {
  canGenerateImage: boolean;
  canOpenInApp: boolean;
  canUseStructuredLinks: boolean;
  canSpeak: boolean;
  canDraftBlueprint: boolean;
  canGuideEmail: boolean;
  canGuideForms: boolean;
  canResearch: boolean;
  canUseWorkflowTemplates: boolean;
};

export const AMICO_CAPABILITIES: AmicoCapabilities = {
  canGenerateImage: false,
  canOpenInApp: true,
  canUseStructuredLinks: true,
  canSpeak: true,
  canDraftBlueprint: true,
  canGuideEmail: true,
  canGuideForms: true,
  canResearch: true,
  canUseWorkflowTemplates: true,
};

export type AmicoCapabilityKey = keyof AmicoCapabilities;