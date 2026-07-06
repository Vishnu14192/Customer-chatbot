"use client";

/**
 * Main chat hook that exposes chat state/actions from the central Zustand store.
 */

import { useEffect, useMemo } from "react";
import { useChatStore } from "@/stores/useChatStore";

/**
 * Main chat hook that manages:
 * - Thread list and active thread selection
 * - Message history for each thread
 * - Streaming state and loading indicators
 * - Bootstrap/restore from backend on mount
 * - Lazy-load message history when switching threads
 * 
 * @returns Object containing all chat state, actions, and derived values
 */
export function useChat() {
  const threads = useChatStore((state) => state.threads);
  const activeThreadId = useChatStore((state) => state.activeThreadId);
  const loadingThreadId = useChatStore((state) => state.loadingThreadId);
  const isBootstrapping = useChatStore((state) => state.isBootstrapping);

  const bootstrap = useChatStore((state) => state.bootstrap);
  const loadThreadIfNeeded = useChatStore((state) => state.loadThreadIfNeeded);
  const selectChat = useChatStore((state) => state.selectChat);
  const newChat = useChatStore((state) => state.newChat);
  const removeChat = useChatStore((state) => state.removeChat);
  const renameChat = useChatStore((state) => state.renameChat);
  const sendMessage = useChatStore((state) => state.send);

  const activeThread = useMemo(
    () => threads.find((thread) => thread.id === activeThreadId) || threads[0],
    [threads, activeThreadId]
  );

  const messages = activeThread?.messages || [];
  const loading = loadingThreadId === activeThread?.id;
  const loadingHistory = isBootstrapping || !activeThread?.isLoaded;

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    if (!isBootstrapping && activeThread?.id) {
      void loadThreadIfNeeded(activeThread.id);
    }
  }, [activeThread?.id, isBootstrapping, loadThreadIfNeeded]);

  return {
    threads,
    activeThreadId: activeThread?.id || "",
    messages,
    loading,
    loadingHistory,

    send: (question: string) => sendMessage(question),
    newChat,
    selectChat,
    removeChat,
    renameChat,
  };
}