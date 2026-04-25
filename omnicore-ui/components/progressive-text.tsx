"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

type ProgressiveTextProps = {
  text: string;
  animate?: boolean;
  className?: string;
  renderText?: (value: string) => ReactNode;
};

function splitIntoChunks(text: string) {
  const normalized = text.replace(/\r\n/g, "\n");
  const lines = normalized.split("\n");
  const chunks: string[] = [];

  lines.forEach((line, index) => {
    const suffix = index < lines.length - 1 ? "\n" : "";
    const isStructuredLine = /^\s*(#{1,3}\s+|[-*+]\s+|\d+\.\s+|<h[1-3]>)/.test(line);

    if (!line.length) {
      chunks.push(suffix || "\n");
      return;
    }

    if (isStructuredLine) {
      chunks.push(`${line}${suffix}`);
      return;
    }

    const words = line.match(/\S+\s*/g) ?? [line];
    words.forEach((word, wordIndex) => {
      const wordSuffix = wordIndex === words.length - 1 ? suffix : "";
      chunks.push(`${word}${wordSuffix}`);
    });
  });

  return chunks.length ? chunks : [text];
}

export function ProgressiveText({ text, animate = false, className, renderText }: ProgressiveTextProps) {
  const chunks = useMemo(() => splitIntoChunks(text), [text]);
  const [visibleText, setVisibleText] = useState(animate ? "" : text);

  useEffect(() => {
    if (!animate || !text.trim()) {
      setVisibleText(text);
      return;
    }

    setVisibleText("");
    let index = 0;
    const timer = window.setInterval(() => {
      index += 1;
      setVisibleText(chunks.slice(0, index).join(""));

      if (index >= chunks.length) {
        window.clearInterval(timer);
      }
    }, 32);

    return () => window.clearInterval(timer);
  }, [animate, chunks, text]);

  const rendered = renderText ? renderText(visibleText) : visibleText;
  const isStreaming = animate && visibleText !== text;

  return (
    <div className={className}>
      {rendered}
      {isStreaming ? <span className="ml-1 inline-block h-[1.05em] w-2 animate-pulse rounded-full bg-current align-text-bottom opacity-70" aria-hidden="true" /> : null}
    </div>
  );
}