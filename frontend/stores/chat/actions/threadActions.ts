import { createId, createNewThread } from "@/hooks/chatHelpers";
import { deleteThread, renameThread } from "@/services/chatApi/threads";
import { ChatStore, GetChatStore, SetChatStore } from "../types";
import { USER_ID } from "../constants";

export function createThreadActions(
  set: SetChatStore,
  get: GetChatStore
): Pick<
  ChatStore,
  "updateThread" | "selectChat" | "newChat" | "removeChat" | "renameChat"
> {
  return {
    updateThread: (threadId, updater) => {
      set((state) => ({
        threads: state.threads.map((thread) =>
          thread.id === threadId ? updater(thread) : thread
        ),
      }));
    },

    selectChat: (threadId) => {
      set({ activeThreadId: threadId });
    },

    newChat: () => {
      set((state) => {
        const newThread = {
          id: createId(),
          title: `New Chat ${state.threads.length + 1}`,
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
          isLoaded: true,
          persisted: false,
        };

        return {
          threads: [newThread, ...state.threads],
          activeThreadId: newThread.id,
        };
      });
    },

    removeChat: async (threadId) => {
      const state = get();
      const threadToDelete = state.threads.find((thread) => thread.id === threadId);

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

      set((current) => {
        const nextThreads = current.threads.filter((thread) => thread.id !== threadId);

        if (nextThreads.length === 0) {
          const fallbackThread = createNewThread();
          return {
            threads: [fallbackThread],
            activeThreadId: fallbackThread.id,
          };
        }

        const nextActiveThreadId =
          current.activeThreadId === threadId
            ? nextThreads[0].id
            : current.activeThreadId;

        return {
          threads: nextThreads,
          activeThreadId: nextActiveThreadId,
        };
      });
    },

    renameChat: async (threadId, title) => {
      const trimmedTitle = title.trim();

      if (!trimmedTitle) {
        return;
      }

      const targetThread = get().threads.find((thread) => thread.id === threadId);

      if (!targetThread) {
        return;
      }

      if (targetThread.persisted) {
        const renamed = await renameThread(USER_ID, threadId, trimmedTitle);
        if (!renamed) {
          return;
        }
      }

      get().updateThread(threadId, (thread) => ({
        ...thread,
        title: trimmedTitle,
        updatedAt: Date.now(),
      }));
    },
  };
}
