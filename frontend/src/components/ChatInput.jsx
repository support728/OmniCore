import React, { useEffect, useRef } from "react";
import useMic from "../hooks/useMic";

export function ChatInput({
  value,
  isLoading,
  inputRef,
  editingDraftLabel,
  onCancelDraft,
  onChange,
  onSend,
}) {
  const { listening, text, setText, start, stop } = useMic();
  const syncingFromParentRef = useRef(false);
  const previousValueRef = useRef(value);

  useEffect(() => {
    if (previousValueRef.current !== value) {
      previousValueRef.current = value;
      syncingFromParentRef.current = true;
      if (value !== text) {
        setText(value);
      }
    }
  }, [setText, text, value]);

  useEffect(() => {
    if (syncingFromParentRef.current) {
      syncingFromParentRef.current = false;
      return;
    }

    onChange(text);
  }, [onChange, text]);

  const handleSend = async () => {
    const messageToSend = text.trim();
    if (!messageToSend || isLoading) {
      return;
    }

    await onSend(messageToSend);
  };

  return (
    <div className="input-area">
      <div className="composer-wrap">
        {editingDraftLabel || listening ? (
          <div className="draft-editing-row">
            <div className="composer-status-group">
              {editingDraftLabel ? <div className="draft-editing-indicator">{editingDraftLabel}...</div> : null}
              {listening && <div>Listening...</div>}
            </div>
            <div>
              {editingDraftLabel ? (
                <button className="draft-cancel-button" type="button" onClick={onCancelDraft}>
                  Cancel draft
                </button>
              ) : null}
            </div>
          </div>
        ) : null}
        <textarea
          ref={inputRef}
          placeholder="Type your message..."
          value={text}
          disabled={isLoading}
          rows={editingDraftLabel ? 8 : 2}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void handleSend();
            }
          }}
        />
      </div>
      <button disabled={isLoading || !text.trim()} onClick={() => void handleSend()}>
        Send
      </button>
      <button onClick={listening ? stop : start}>
        {listening ? "Stop 🎤" : "Mic 🎤"}
      </button>
    </div>
  );
}