"use client";

/** Main chat page composing sidebar, thread view, and input controls. */

import ChatWindow from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";
import ChatSidebar from "@/components/ChatSidebar";
import { useChat } from "@/hooks/useChat";

export default function Home() {
  /** Entry UI for the customer support chatbot experience. */

  const {
    threads,
    activeThreadId,
    messages,
    send,
    loading,
    loadingHistory,
    newChat,
    renameChat,
    removeChat,
    selectChat,
  } = useChat();

  return (
    <main className="min-h-screen bg-zinc-100 md:p-4">
      <div className="mx-auto max-w-7xl bg-white rounded-none md:rounded-xl shadow-sm border border-zinc-200 overflow-hidden">
        <div className="flex flex-col md:flex-row min-h-screen md:min-h-[92vh]">
          <ChatSidebar
            threads={threads}
            activeThreadId={activeThreadId}
            onSelectChat={selectChat}
            onNewChat={newChat}
            onRenameChat={renameChat}
            onDeleteChat={removeChat}
          />

          <section className="flex-1 p-4 md:p-6">
            <h1 className="text-2xl md:text-3xl font-bold mb-4 text-black">
              Flipkart Customer Care Chatbot
            </h1>

            <ChatWindow messages={messages} />

            {(loading || loadingHistory) && (
              <p className="text-sm text-zinc-500 mt-2">Thinking...</p>
            )}

            <ChatInput onSend={send} disabled={loading || loadingHistory} />
          </section>
        </div>
      </div>
    </main>
  );
}