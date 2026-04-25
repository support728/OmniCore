"use client";

import { useEffect } from "react";

import { useMic } from "@/hooks/use-mic";

type ChatInputProps = {
  isLoading: boolean;
  value: string;
  onChange: (value: string) => void;
  onSend: (value: string) => Promise<void> | void;
};

export function ChatInput({ isLoading, value, onChange, onSend }: ChatInputProps) {
  const { listening, text, setText, start, stop } = useMic();

  useEffect(() => {
    if (value !== text) {
      setText(value);
    }
  }, [setText, text, value]);

  useEffect(() => {
    onChange(text);
  }, [onChange, text]);

  const submit = async () => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) {
      return;
    }

    await onSend(trimmed);
  };

  return (
    <div className="border-t border-slate-200 bg-white/80 px-5 py-4">
      <div className="space-y-2 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 shadow-sm">
        {listening ? <div className="text-xs font-medium text-rose-500">Listening...</div> : null}
        <div className="flex items-center gap-3">
        <input
          value={text}
          disabled={isLoading}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void submit();
            }
          }}
          placeholder="Ask OmniCore anything..."
          className="flex-1 bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed"
        />
        <button
          type="button"
          onClick={listening ? stop : start}
          className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-100"
        >
          {listening ? "Stop 🎤" : "Mic 🎤"}
        </button>
        <button
          type="button"
          onClick={() => void submit()}
          disabled={isLoading || !text.trim()}
          className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          Send
        </button>
        </div>
      </div>
    </div>
  );
}