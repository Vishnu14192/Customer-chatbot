import type { StoreApi } from "zustand";
import { ChatThread } from "@/types/chat";

export interface ChatStore {
  threads: ChatThread[];
  activeThreadId: string;
  loadingThreadId: string | null;
  isBootstrapping: boolean;
  updateThread: (
    threadId: string,
    updater: (thread: ChatThread) => ChatThread
  ) => void;
  bootstrap: () => Promise<void>;
  loadThreadIfNeeded: (threadId: string) => Promise<void>;
  selectChat: (threadId: string) => void;
  newChat: () => void;
  removeChat: (threadId: string) => Promise<void>;
  renameChat: (threadId: string, title: string) => Promise<void>;
  send: (question: string) => Promise<void>;
}

export type SetChatStore = StoreApi<ChatStore>["setState"];
export type GetChatStore = StoreApi<ChatStore>["getState"];
