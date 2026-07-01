"use client";

import { useState } from "react";

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function ChatInput({
  onSend,
  disabled = false,
}: ChatInputProps) {

  const [text, setText] = useState("");

  function submit() {
    const trimmed = text.trim();
    if (!trimmed || disabled) {
      return;
    }

    onSend(trimmed);
    setText("");
  }

  return (
    <div className="flex gap-2 pt-3">

      <input
        value={text}
        onChange={(e) =>
          setText(e.target.value)
        }
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            submit();
          }
        }}
        placeholder="Ask anything about your order, refund, shipping..."
        className="border border-zinc-300 rounded-lg px-3 py-2 flex-1"
        disabled={disabled}
      />

      <button
        onClick={submit}
        disabled={disabled || !text.trim()}
        className="bg-blue-600 text-white px-4 rounded-lg disabled:bg-zinc-400"
      >
        Send
      </button>

    </div>
  );
}