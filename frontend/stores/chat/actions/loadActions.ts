import { fetchThreadMessages, fetchThreads } from "@/services/chatApi/threads";
import { ChatStore, GetChatStore, SetChatStore } from "../types";
import { USER_ID } from "../constants";

export function createLoadActions(
  set: SetChatStore,
  get: GetChatStore
): Pick<ChatStore, "bootstrap" | "loadThreadIfNeeded"> {
  return {
    bootstrap: async () => {
      try {
        const backendThreads = await fetchThreads(USER_ID);

        if (backendThreads.length === 0) {
          return;
        }

        const restoredThreads = backendThreads.map((thread) => ({
          id: thread.thread_id,
          title: thread.title || "New Chat",
          messages: [],
          createdAt: Date.parse(thread.updated_at) || Date.now(),
          updatedAt: Date.parse(thread.updated_at) || Date.now(),
          isLoaded: false,
          persisted: true,
        }));

        set({
          threads: restoredThreads,
          activeThreadId: restoredThreads[0].id,
        });
      } catch {
        // Keep local default thread if bootstrap fails.
      } finally {
        set({ isBootstrapping: false });
      }
    },

    loadThreadIfNeeded: async (threadId) => {
      const targetThread = get().threads.find((thread) => thread.id === threadId);

      if (!targetThread || targetThread.isLoaded) {
        return;
      }

      try {
        const restoredMessages = await fetchThreadMessages(USER_ID, targetThread.id);

        set((state) => ({
          threads: state.threads.map((thread) =>
            thread.id === targetThread.id
              ? {
                  ...thread,
                  messages: restoredMessages,
                  isLoaded: true,
                  updatedAt: Date.now(),
                }
              : thread
          ),
        }));
      } catch {
        set((state) => ({
          threads: state.threads.map((thread) =>
            thread.id === targetThread.id
              ? {
                  ...thread,
                  isLoaded: true,
                }
              : thread
          ),
        }));
      }
    },
  };
}
