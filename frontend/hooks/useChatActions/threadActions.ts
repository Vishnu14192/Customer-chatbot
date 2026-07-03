import { deleteThread, renameThread } from "@/services/chatApi";
import { createId } from "../chatHelpers";
import { USER_ID } from "./constants";
import { ThreadActionsContext } from "./types";

/** Creates thread selection, creation, rename, and deletion actions. */
export function createThreadActions({
  threads,
  setThreads,
  activeThreadId,
  setActiveThreadId,
  updateThread,
}: ThreadActionsContext) {
  function selectChat(threadId: string) {
    setActiveThreadId(threadId);
  }

  function newChat() {
    const newThread = {
      id: createId(),
      title: `New Chat ${threads.length + 1}`,
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      isLoaded: true,
      persisted: false,
    };

    setThreads([newThread, ...threads]);
    setActiveThreadId(newThread.id);
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
      const fallbackThread = {
        id: createId(),
        title: "New Chat",
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
        isLoaded: true,
        persisted: false,
      };

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

  return {
    selectChat,
    newChat,
    removeChat,
    renameChat,
  };
}
