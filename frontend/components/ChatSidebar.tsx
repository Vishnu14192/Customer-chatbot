"use client";

/** Sidebar listing chat threads with create/select/rename/delete controls. */

import { useState } from "react";
import { ChatThread } from "@/types/chat";

interface ChatSidebarProps {
  threads: ChatThread[];
  activeThreadId: string;
  onSelectChat: (threadId: string) => void;
  onNewChat: () => void;
  onDeleteChat: (threadId: string) => void;
  onRenameChat: (threadId: string, title: string) => Promise<void> | void;
}

export default function ChatSidebar({
  threads,
  activeThreadId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onRenameChat,
}: ChatSidebarProps) {
  /** Renders the left conversation navigator. */

  const [editingThreadId, setEditingThreadId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  function startRename(threadId: string, currentTitle: string) {
    /** Enters inline rename mode for one thread. */
    setEditingThreadId(threadId);
    setEditingTitle(currentTitle);
  }

  async function saveRename(threadId: string) {
    /** Persists edited thread title and exits rename mode. */
    const trimmedTitle = editingTitle.trim();
    if (!trimmedTitle) {
      return;
    }

    await onRenameChat(threadId, trimmedTitle);
    setEditingThreadId(null);
    setEditingTitle("");
  }

  function cancelRename() {
    /** Exits rename mode without applying changes. */
    setEditingThreadId(null);
    setEditingTitle("");
  }

  return (
    <aside className="w-full md:w-80 border-r border-zinc-200 bg-zinc-50 p-4 flex flex-col gap-4">
      <button
        onClick={onNewChat}
        className="w-full rounded-lg bg-blue-600 text-white px-4 py-2 font-medium hover:bg-blue-700"
      >
        + New Chat
      </button>

      <div className="flex-1 overflow-y-auto space-y-2">
        {threads.map((thread) => {
          const isActive = thread.id === activeThreadId;

          return (
            <div
              key={thread.id}
              className={`w-full rounded-lg px-3 py-2 border transition ${
                isActive
                  ? "bg-blue-100 border-blue-400"
                  : "bg-white border-zinc-200 hover:bg-zinc-100"
              }`}
            >
              <div className="flex items-start gap-2">
                <button
                  onClick={() => onSelectChat(thread.id)}
                  className="flex-1 text-left min-w-0"
                >
                  {editingThreadId === thread.id ? (
                    <input
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          saveRename(thread.id);
                        }

                        if (e.key === "Escape") {
                          e.preventDefault();
                          cancelRename();
                        }
                      }}
                      className="w-full text-sm border border-zinc-300 rounded px-2 py-1 text-black placeholder:text-black"
                      autoFocus
                    />
                  ) : (
                    <p className="font-medium truncate text-black">{thread.title}</p>
                  )}
                </button>

                <div className="flex flex-col gap-1">
                  {editingThreadId === thread.id ? (
                    <>
                      <button
                        onClick={() => saveRename(thread.id)}
                        className="text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-700 hover:bg-emerald-200"
                        aria-label="Save conversation name"
                        title="Save"
                      >
                        Save
                      </button>
                      <button
                        onClick={cancelRename}
                        className="text-xs px-2 py-1 rounded bg-zinc-200 text-zinc-700 hover:bg-zinc-300"
                        aria-label="Cancel renaming"
                        title="Cancel"
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => startRename(thread.id, thread.title)}
                        className="text-xs px-2 py-1 rounded bg-amber-100 text-amber-800 hover:bg-amber-200"
                        aria-label="Rename conversation"
                        title="Rename conversation"
                      >
                        Rename
                      </button>
                      <button
                        onClick={() => onDeleteChat(thread.id)}
                        className="text-xs px-2 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200"
                        aria-label="Delete conversation"
                        title="Delete conversation"
                      >
                        Delete
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
