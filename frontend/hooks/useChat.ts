"use client";

import { useEffect, useState } from "react";
import {
  deleteThread,
  fetchThreadMessages,
  fetchThreads,
  renameThread,
  streamMessage,
} from "@/services/chatApi";
import { ChatMessage, ChatThread } from "@/types/chat";

const USER_ID = "vishnu";

function createId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}

function createNewThread(title: string = "New Chat"): ChatThread {
  const now = Date.now();

  return {
    id: createId(),
    title,
    messages: [],
    createdAt: now,
    updatedAt: now,
    isLoaded: true,
    persisted: false,
  };
}

function createMessage(role: "user" | "assistant", content: string, sources?: string[]): ChatMessage {
  return {
    id: createId(),
    role,
    content,
    sources,
  };
}

export function useChat() {

  const initialThread = createNewThread();

  const [threads, setThreads] = useState<ChatThread[]>([initialThread]);
  const [activeThreadId, setActiveThreadId] = useState(initialThread.id);
  const [loadingThreadId, setLoadingThreadId] = useState<string | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  const activeThread = threads.find((thread) => thread.id === activeThreadId) || threads[0];
  const messages = activeThread?.messages || [];
  const loading = loadingThreadId === activeThread?.id;
  const loadingHistory = isBootstrapping || !activeThread?.isLoaded;

  function updateThread(threadId: string, updater: (thread: ChatThread) => ChatThread) {
    setThreads((prev) =>
      prev.map((thread) => (thread.id === threadId ? updater(thread) : thread))
    );
  }

  function selectChat(threadId: string) {
    setActiveThreadId(threadId);
  }

  function newChat() {
    const thread = createNewThread(`New Chat ${threads.length + 1}`);
    setThreads((prev) => [thread, ...prev]);
    setActiveThreadId(thread.id);
  }

  async function removeChat(threadId: string) {
    const threadToDelete = threads.find((thread) => thread.id === threadId);

    if (!threadToDelete) {
      return;
    }

    const isLocalOnly = !threadToDelete.persisted;

    if (!isLocalOnly) {
      const deleted = await deleteThread(USER_ID, threadId);
      if (!deleted) {
        return;
      }
    }

    const nextThreads = threads.filter((thread) => thread.id !== threadId);

    if (nextThreads.length === 0) {
      const fallbackThread = createNewThread();
      setThreads([fallbackThread]);
      setActiveThreadId(fallbackThread.id);
      return;
    }

    setThreads(nextThreads);

    if (activeThreadId === threadId) {
      setActiveThreadId(nextThreads[0].id);
    }
  }

  async function renameChat(threadId: string, title: string) {
    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      return;
    }

    const targetThread = threads.find((thread) => thread.id === threadId);
    if (!targetThread) {
      return;
    }

    if (targetThread.persisted) {
      const renamed = await renameThread(USER_ID, threadId, trimmedTitle);
      if (!renamed) {
        return;
      }
    }

    updateThread(threadId, (thread) => ({
      ...thread,
      title: trimmedTitle,
      updatedAt: Date.now(),
    }));
  }

  async function send(question: string) {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || !activeThread) {
      return;
    }

    if (!activeThread.isLoaded) {
      return;
    }

    const threadId = activeThread.id;
    const userMessage = createMessage("user", trimmedQuestion);
    const assistantMessageId = createId();

    setLoadingThreadId(threadId);

    updateThread(threadId, (thread) => {
      const nextMessages = [...thread.messages, userMessage];
      const nextTitle =
        thread.messages.length === 0
          ? trimmedQuestion.slice(0, 40)
          : thread.title;

      return {
        ...thread,
        title: nextTitle,
        messages: nextMessages,
        updatedAt: Date.now(),
      };
    });

    updateThread(threadId, (thread) => ({
      ...thread,
      messages: [
        ...thread.messages,
        {
          id: assistantMessageId,
          role: "assistant",
          content: "",
          sources: [],
        },
      ],
      updatedAt: Date.now(),
    }));

    try {
      await streamMessage(trimmedQuestion, USER_ID, threadId, {
        onStart: (event) => {
          updateThread(threadId, (thread) => ({
            ...thread,
            messages: thread.messages.map((message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    sources: event.sources,
                  }
                : message
            ),
            updatedAt: Date.now(),
          }));
        },
        onToken: (token) => {
          updateThread(threadId, (thread) => ({
            ...thread,
            messages: thread.messages.map((message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    content: message.content + token,
                  }
                : message
            ),
            updatedAt: Date.now(),
          }));
        },
        onEnd: () => {
          updateThread(threadId, (thread) => ({
            ...thread,
            persisted: true,
            updatedAt: Date.now(),
          }));
        },
        onError: (message) => {
          updateThread(threadId, (thread) => ({
            ...thread,
            messages: thread.messages.map((item) =>
              item.id === assistantMessageId
                ? {
                    ...item,
                    content: message || "Streaming failed. Please try again.",
                  }
                : item
            ),
            updatedAt: Date.now(),
          }));
        },
      });
    } catch {
      updateThread(threadId, (thread) => ({
        ...thread,
        messages: thread.messages.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                content: "I could not reach the server. Please try again.",
              }
            : message
        ),
        updatedAt: Date.now(),
      }));
    } finally {
      setLoadingThreadId((current) => (current === threadId ? null : current));
    }
  }

  useEffect(() => {
    async function bootstrapFromBackend() {
      try {
        const backendThreads = await fetchThreads(USER_ID);

        if (backendThreads.length === 0) {
          setIsBootstrapping(false);
          return;
        }

        const restoredThreads: ChatThread[] = backendThreads.map((thread) => ({
          id: thread.thread_id,
          title: thread.title || "New Chat",
          messages: [],
          createdAt: Date.parse(thread.updated_at) || Date.now(),
          updatedAt: Date.parse(thread.updated_at) || Date.now(),
          isLoaded: false,
          persisted: true,
        }));

        setThreads(restoredThreads);
        setActiveThreadId(restoredThreads[0].id);
      } catch {
        // Keep local default thread if backend history is unavailable.
      } finally {
        setIsBootstrapping(false);
      }
    }

    bootstrapFromBackend();
  }, []);

  useEffect(() => {
    async function loadActiveThreadMessages() {
      if (!activeThread) {
        return;
      }

      if (activeThread.isLoaded) {
        return;
      }

      try {
        const restoredMessages = await fetchThreadMessages(USER_ID, activeThread.id);

        setThreads((prev) =>
          prev.map((thread) =>
            thread.id === activeThread.id
              ? {
                  ...thread,
                  messages: restoredMessages,
                  isLoaded: true,
                  updatedAt: Date.now(),
                }
              : thread
          )
        );
      } catch {
        setThreads((prev) =>
          prev.map((thread) =>
            thread.id === activeThread.id
              ? {
                  ...thread,
                  isLoaded: true,
                }
              : thread
          )
        );
      }
    }

    if (!isBootstrapping) {
      loadActiveThreadMessages();
    }
  }, [activeThread, isBootstrapping]);

  return {
    threads,
    activeThreadId: activeThread?.id || "",
    messages,
    send,
    loading,
    loadingHistory,
    newChat,
    renameChat,
    removeChat,
    selectChat,
  };
}