import { ChatThread } from "@/types/chat";

export type LoadingThreadState = string | null;
export type SetThreads = (
  threads: ChatThread[] | ((prev: ChatThread[]) => ChatThread[])
) => void;
export type SetLoadingThreadId = (
  id: LoadingThreadState | ((current: LoadingThreadState) => LoadingThreadState)
) => void;

export interface CreateChatActionsArgs {
  threads: ChatThread[];
  setThreads: SetThreads;
  activeThreadId: string;
  setActiveThreadId: (id: string) => void;
  setLoadingThreadId: SetLoadingThreadId;
}

export type UpdateThread = (
  threadId: string,
  updater: (thread: ChatThread) => ChatThread
) => void;

export interface ThreadActionsContext extends CreateChatActionsArgs {
  updateThread: UpdateThread;
}

export interface SendActionContext {
  updateThread: UpdateThread;
  setLoadingThreadId: SetLoadingThreadId;
}
