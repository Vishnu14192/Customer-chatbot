/**
 * Chat action functions that modify state and call APIs.
 * These functions handle user interactions (thread management and messaging).
 */

import { ChatThread } from "@/types/chat";
import { createSendAction } from "./useChatActions/sendAction";
import { createThreadActions } from "./useChatActions/threadActions";
import { SetLoadingThreadId } from "./useChatActions/types";

/**
 * Factory function to create action functions that depend on state setters.
 * @param threads - Current threads array
 * @param setThreads - State setter for threads
 * @param activeThreadId - Current active thread ID
 * @param setActiveThreadId - State setter for active thread ID
 * @param setLoadingThreadId - State setter for loading thread ID
 * @returns Object containing all action functions
 */
export function createChatActions(
  threads: ChatThread[],
  setThreads: (
    threads: ChatThread[] | ((prev: ChatThread[]) => ChatThread[])
  ) => void,
  activeThreadId: string,
  setActiveThreadId: (id: string) => void,
  setLoadingThreadId: SetLoadingThreadId
) {
  /** Immutably updates one thread in the thread list. */
  function updateThread(
    threadId: string,
    updater: (thread: ChatThread) => ChatThread
  ) {
    setThreads((prev) =>
      prev.map((thread) =>
        thread.id === threadId ? updater(thread) : thread
      )
    );
  }

  const { selectChat, newChat, removeChat, renameChat } = createThreadActions({
    threads,
    setThreads,
    activeThreadId,
    setActiveThreadId,
    setLoadingThreadId,
    updateThread,
  });

  const { send } = createSendAction({
    updateThread,
    setLoadingThreadId,
  });

  return {
    updateThread,
    selectChat,
    newChat,
    removeChat,
    renameChat,
    send,
  };
}

export type ChatActions = ReturnType<typeof createChatActions>;
