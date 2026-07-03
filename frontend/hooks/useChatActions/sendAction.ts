import { ChatThread } from "@/types/chat";
import { streamMessage, streamMessageWebSocket } from "@/services/chatApi";
import { createId, createMessage } from "../chatHelpers";
import { USER_ID } from "./constants";
import { SendActionContext } from "./types";

/** Creates the message send action with streaming and fallback handling. */
export function createSendAction({
  updateThread,
  setLoadingThreadId,
}: SendActionContext) {
  async function send(question: string, activeThread: ChatThread | undefined) {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || !activeThread) {
      return;
    }

    if (!activeThread.isLoaded) {
      return;
    }

    const threadId = activeThread.id;
    const userMessage = createMessage("user", trimmedQuestion);
    const assistantMessageId = createId();

    setLoadingThreadId(threadId);

    updateThread(threadId, (thread) => {
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

    updateThread(threadId, (thread) => ({
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
          updateThread(threadId, (thread) => ({
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
          updateThread(threadId, (thread) => ({
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
          updateThread(threadId, (thread) => ({
            ...thread,
            persisted: true,
            updatedAt: Date.now(),
          }));
        },
        onError: (message: string) => {
          updateThread(threadId, (thread) => ({
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
        await streamMessage(
          trimmedQuestion,
          USER_ID,
          threadId,
          streamHandlers
        );
      }
    } catch {
      updateThread(threadId, (thread) => ({
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
      // Keep current behavior and clear loading state when this thread finishes.
      setLoadingThreadId((current) =>
        current === threadId ? null : current
      );
    }
  }

  return { send };
}
