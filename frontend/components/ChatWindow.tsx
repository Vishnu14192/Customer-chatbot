"use client";

/** Scrollable message container that renders chat bubbles in order. */

import MessageBubble from "./MessageBubble";
import { ChatMessage } from "@/types/chat";

interface ChatWindowProps {
  messages: ChatMessage[];
}

export default function ChatWindow({
  messages,
}: ChatWindowProps) {
  /** Displays all messages for the active thread. */

  return (
    <div className="h-150 overflow-y-auto rounded-lg border border-zinc-200 bg-white p-3">

      {messages.map(
        (message: ChatMessage) => (

          <MessageBubble
            key={message.id}
            role={message.role}
            content={message.content}
            sources={message.sources}
          />

        )
      )}

    </div>
  );
}