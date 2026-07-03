/**
 * State management utilities for the chat hook.
 * Handles state initialization and computation of derived values.
 */

import { useState } from "react";
import { ChatThread } from "@/types/chat";
import { createNewThread } from "./chatHelpers";

/**
 * Initializes all state for the chat hook.
 * @returns Object containing all state setters and values
 */
export function initializeChatState() {
  const initialThread = createNewThread();

  // List of all conversation threads for the user
  const [threads, setThreads] = useState<ChatThread[]>([initialThread]);
  
  // ID of the currently active/selected thread
  const [activeThreadId, setActiveThreadId] = useState(initialThread.id);
  
  // ID of the thread currently streaming a response
  const [loadingThreadId, setLoadingThreadId] = useState<string | null>(null);
  
  // Flag that prevents UI interaction until backend thread history is restored
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  return {
    threads,
    setThreads,
    activeThreadId,
    setActiveThreadId,
    loadingThreadId,
    setLoadingThreadId,
    isBootstrapping,
    setIsBootstrapping,
  };
}

/**
 * Computes derived values from state.
 * These are computed on every render based on current state values.
 * @param threads - Array of all threads
 * @param activeThreadId - ID of the active thread
 * @param loadingThreadId - ID of the thread being loaded
 * @param isBootstrapping - Whether still loading from backend
 * @returns Object containing all derived values
 */
export function computeDerivedValues(
  threads: ChatThread[],
  activeThreadId: string,
  loadingThreadId: string | null,
  isBootstrapping: boolean
) {
  // Get the thread object that is currently being viewed/edited
  const activeThread = threads.find((thread) => thread.id === activeThreadId) || threads[0];
  
  // Extract messages from the active thread for rendering in the chat window
  const messages = activeThread?.messages || [];
  
  // True if the active thread is currently streaming a response
  const loading = loadingThreadId === activeThread?.id;
  
  // True if we're still loading initial history OR the active thread's messages haven't been fetched yet
  const loadingHistory = isBootstrapping || !activeThread?.isLoaded;

  return {
    activeThread,
    messages,
    loading,
    loadingHistory,
  };
}
