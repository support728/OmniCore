import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { Message } from "@/types/message";

function isMergeableObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

type MessageStore = {
  messages: Message[];
  isLoading: boolean;
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  deleteMessage: (id: string) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  mergeMessage: (id: string, updates: Partial<Message>) => void;
  setLoading: (value: boolean) => void;
};

export const useMessageStore = create<MessageStore>()(
  persist(
    (set) => ({
      messages: [],
      isLoading: false,
      addMessage: (message) =>
        set((state) => ({ messages: [...state.messages, message] })),
      clearMessages: () => set({ messages: [] }),
      deleteMessage: (id) =>
        set((state) => ({ messages: state.messages.filter((message) => message.id !== id) })),
      updateMessage: (id, updates) =>
        set((state) => ({
          messages: state.messages.map((message) =>
            message.id === id ? { ...message, ...updates } : message
          ),
        })),
      mergeMessage: (id, updates) =>
        set((state) => ({
          messages: state.messages.map((message) => {
            if (message.id !== id) {
              return message;
            }

            const baseContent = isMergeableObject(message.content) ? message.content : {};

            return {
              ...message,
              ...updates,
              content:
                isMergeableObject(updates.content)
                  ? { ...baseContent, ...updates.content }
                  : updates.content ?? message.content,
              metadata:
                typeof updates.metadata === "object" && updates.metadata !== null
                  ? { ...(message.metadata ?? {}), ...updates.metadata }
                  : updates.metadata ?? message.metadata,
            };
          }),
        })),
      setLoading: (value) => set({ isLoading: value }),
    }),
    {
      name: "omnicore-messages",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ messages: state.messages }),
    }
  )
);