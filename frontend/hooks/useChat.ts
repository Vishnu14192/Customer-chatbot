"use client";

/**
 * Main chat hook that manages thread lifecycle, streaming, and history restore.
 * 
 * This hook composes multiple sub-modules:
 * - chatHelpers.ts: Utility functions for creating entities
 * - useChatState.ts: State initialization and derived values
 * - useChatActions.ts: All action functions
 * - useChatEffects.ts: Side effects (bootstrap & lazy-load)
 * 
 * It provides the single interface that components use for chat functionality.
 */

import {
  initializeChatState,
  computeDerivedValues,
} from "./useChatState";
import {
  createChatActions,
} from "./useChatActions";
import {
  useBootstrapEffect,
  useLazyLoadEffect,
} from "./useChatEffects";

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
  // Initialize all state
  const {
    threads,
    setThreads,
    activeThreadId,
    setActiveThreadId,
    loadingThreadId,
    setLoadingThreadId,
    isBootstrapping,
    setIsBootstrapping,
  } = initializeChatState();

  // Compute derived values from state
  const {
    activeThread,
    messages,
    loading,
    loadingHistory,
  } = computeDerivedValues(
    threads,
    activeThreadId,
    loadingThreadId,
    isBootstrapping
  );

  // Create action functions with access to state setters
  const {
    selectChat,
    newChat,
    removeChat,
    renameChat,
    send: sendMessage,
  } = createChatActions(
    threads,
    setThreads,
    activeThreadId,
    setActiveThreadId,
    setLoadingThreadId
  );

  // Set up side effects
  useBootstrapEffect(
    setThreads,
    setActiveThreadId,
    setIsBootstrapping
  );

  useLazyLoadEffect(
    activeThread,
    isBootstrapping,
    setThreads
  );

  // Export all state and actions for use in components
  return {
    // State
    threads,
    activeThreadId: activeThread?.id || "",
    messages,
    loading,
    loadingHistory,

    // Actions
    send: (question: string) => sendMessage(question, activeThread),
    newChat,
    selectChat,
    removeChat,
    renameChat,
  };
}