import { create } from "zustand";
import { createNewThread } from "@/hooks/chatHelpers";
import { createLoadActions } from "@/stores/chat/actions/loadActions";
import { createSendAction } from "@/stores/chat/actions/sendAction";
import { createThreadActions } from "@/stores/chat/actions/threadActions";
import { ChatStore } from "@/stores/chat/types";

const initialThread = createNewThread();

export const useChatStore = create<ChatStore>((set, get) => ({
  threads: [initialThread],
  activeThreadId: initialThread.id,
  loadingThreadId: null,
  isBootstrapping: true,

  ...createThreadActions(set, get),
  ...createLoadActions(set, get),
  ...createSendAction(set, get),
}));
