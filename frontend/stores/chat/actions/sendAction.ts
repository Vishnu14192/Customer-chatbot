import { createId, createMessage } from "@/hooks/chatHelpers";
import { streamMessage, streamMessageWebSocket } from "@/services/chatApi";
import { ChatStore, GetChatStore, SetChatStore } from "../types";
import { USER_ID } from "../constants";

export function createSendAction(
  set: SetChatStore,
  get: GetChatStore
): Pick<ChatStore, "send"> {
  return {
    send: async (question) => {
      const trimmedQuestion = question.trim();
      const { activeThreadId, threads } = get();
      const activeThread = threads.find((thread) => thread.id === activeThreadId);

      if (!trimmedQuestion || !activeThread || !activeThread.isLoaded) {
        return;
      }

      const threadId = activeThread.id;
      const userMessage = createMessage("user", trimmedQuestion);
      const assistantMessageId = createId();

      set({ loadingThreadId: threadId });

      get().updateThread(threadId, (thread) => {
        const nextMessages = [...thread.messages, userMessage];
        const nextTitle =
          thread.messages.length === 0
            ? trimmedQuestion.slice(0, 40)
            : thread.title;

        return {
          ...thread,
          title: nextTitle,
          messages: nextMessages,
          updatedAt: Date.now(),
        };
      });

      get().updateThread(threadId, (thread) => ({
        ...thread,
        messages: [
          ...thread.messages,
          {
            id: assistantMessageId,
            role: "assistant",
            content: "",
            sources: [],
          },
        ],
        updatedAt: Date.now(),
      }));

      try {
        const streamHandlers = {
          onStart: (event: { sources: string[] }) => {
            get().updateThread(threadId, (thread) => ({
              ...thread,
              messages: thread.messages.map((message) =>
                message.id === assistantMessageId
                  ? {
                      ...message,
                      sources: event.sources,
                    }
                  : message
              ),
              updatedAt: Date.now(),
            }));
          },
          onToken: (token: string) => {
            get().updateThread(threadId, (thread) => ({
              ...thread,
              messages: thread.messages.map((message) =>
                message.id === assistantMessageId
                  ? {
                      ...message,
                      content: message.content + token,
                    }
                  : message
              ),
              updatedAt: Date.now(),
            }));
          },
          onEnd: () => {
            get().updateThread(threadId, (thread) => ({
              ...thread,
              persisted: true,
              updatedAt: Date.now(),
            }));
          },
          onError: (message: string) => {
            get().updateThread(threadId, (thread) => ({
              ...thread,
              messages: thread.messages.map((item) =>
                item.id === assistantMessageId
                  ? {
                      ...item,
                      content: message || "Streaming failed. Please try again.",
                    }
                  : item
              ),
              updatedAt: Date.now(),
            }));
          },
        };

        try {
          await streamMessageWebSocket(
            trimmedQuestion,
            USER_ID,
            threadId,
            streamHandlers
          );
        } catch {
          await streamMessage(trimmedQuestion, USER_ID, threadId, streamHandlers);
        }
      } catch {
        get().updateThread(threadId, (thread) => ({
          ...thread,
          messages: thread.messages.map((message) =>
            message.id === assistantMessageId
              ? {
                  ...message,
                  content: "I could not reach the server. Please try again.",
                }
              : message
          ),
          updatedAt: Date.now(),
        }));
      } finally {
        set((state) => ({
          loadingThreadId:
            state.loadingThreadId === threadId ? null : state.loadingThreadId,
        }));
      }
    },
  };
}
