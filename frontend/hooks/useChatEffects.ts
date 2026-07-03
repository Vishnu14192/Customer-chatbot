/**
 * Side effects for the chat hook.
 * Handles bootstrap restoration and lazy-loading of message history.
 */

import { useEffect } from "react";
import { fetchThreadMessages, fetchThreads } from "@/services/chatApi";
import { ChatThread } from "@/types/chat";

const USER_ID = "vishnu"; // Hardcoded user ID for API calls

/**
 * Effect 1: Bootstrap/restore thread list from backend on component mount.
 * Restores conversation history so users don't lose their threads on page refresh.
 * @param setThreads - State setter to update threads list
 * @param setActiveThreadId - State setter to update active thread
 * @param setIsBootstrapping - State setter to signal bootstrap complete
 */
export function useBootstrapEffect(
  setThreads: (threads: ChatThread[]) => void,
  setActiveThreadId: (id: string) => void,
  setIsBootstrapping: (value: boolean) => void
) {
  useEffect(() => {
    async function bootstrapFromBackend() {
      try {
        // Fetch all thread summaries for this user
        const backendThreads = await fetchThreads(USER_ID);

        if (backendThreads.length === 0) {
          setIsBootstrapping(false);
          return;
        }

        // Convert backend thread summaries to frontend thread objects
        const restoredThreads: ChatThread[] = backendThreads.map((thread) => ({
          id: thread.thread_id,
          title: thread.title || "New Chat",
          messages: [],  // Will be lazy-loaded when user selects
          createdAt: Date.parse(thread.updated_at) || Date.now(),
          updatedAt: Date.parse(thread.updated_at) || Date.now(),
          isLoaded: false,  // Mark as not yet loaded
          persisted: true,  // These came from backend
        }));

        // Replace initial local thread with backend threads
        setThreads(restoredThreads);
        // Activate the most recent thread
        setActiveThreadId(restoredThreads[0].id);
      } catch {
        // If backend is unavailable, keep the default local thread (fail gracefully)
      } finally {
        // Allow UI interaction (done bootstrapping)
        setIsBootstrapping(false);
      }
    }

    bootstrapFromBackend();
  }, [setThreads, setActiveThreadId, setIsBootstrapping]);  // Run once on mount
}

/**
 * Effect 2: Lazy-load messages when user switches to a thread.
 * Fetches full message history only when the user views a specific thread.
 * This avoids loading all message history at startup.
 * @param activeThread - Currently active thread
 * @param isBootstrapping - Whether still loading from backend
 * @param setThreads - State setter to update threads with loaded messages
 */
export function useLazyLoadEffect(
  activeThread: ChatThread | undefined,
  isBootstrapping: boolean,
  setThreads: (updater: (prev: ChatThread[]) => ChatThread[]) => void
) {
  useEffect(() => {
    async function loadActiveThreadMessages() {
      if (!activeThread) {
        return;
      }

      // Skip if already loaded
      if (activeThread.isLoaded) {
        return;
      }

      try {
        // Fetch the full message history for this thread from backend
        const restoredMessages = await fetchThreadMessages(
          USER_ID,
          activeThread.id
        );

        // Update the thread with loaded messages and mark as loaded
        setThreads((prev) =>
          prev.map((thread) =>
            thread.id === activeThread.id
              ? {
                  ...thread,
                  messages: restoredMessages,
                  isLoaded: true,  // Mark loaded to prevent retry
                  updatedAt: Date.now(),
                }
              : thread
          )
        );
      } catch {
        // If fetch fails, still mark as loaded to prevent infinite retry loop
        setThreads((prev) =>
          prev.map((thread) =>
            thread.id === activeThread.id
              ? {
                  ...thread,
                  isLoaded: true,  // Prevent retry even on error
                }
              : thread
          )
        );
      }
    }

    // Only load if bootstrap is complete (prevents race conditions)
    if (!isBootstrapping) {
      loadActiveThreadMessages();
    }
  }, [activeThread, isBootstrapping, setThreads]);  // Re-run when thread changes or bootstrap completes
}
