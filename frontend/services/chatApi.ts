import { ChatMessage, ChatResponse } from "@/types/chat";

const API_BASE_URL = "http://localhost:8000";

export interface ChatThreadSummaryApi {
  thread_id: string;
  title: string;
  updated_at: string;
  message_count: number;
}

interface ChatThreadListApiResponse {
  threads: ChatThreadSummaryApi[];
}

interface ChatThreadHistoryApiResponse {
  thread_id: string;
  messages: Array<{
    role: "user" | "assistant";
    content: string;
    created_at: string;
    sources?: string[] | null;
  }>;
}

export async function sendMessage(
  question: string,
  userId: string,
  threadId: string
): Promise<ChatResponse> {

  const response = await fetch(
    `${API_BASE_URL}/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        user_id: userId,
        thread_id: threadId,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to send chat message: ${response.status}`);
  }

  return response.json();
}

interface StreamStartEvent {
  type: "start";
  thread_id: string;
  sources: string[];
}

interface StreamTokenEvent {
  type: "token";
  content: string;
}

interface StreamEndEvent {
  type: "end";
  thread_id: string;
  sources: string[];
}

interface StreamErrorEvent {
  type: "error";
  message?: string;
}

type StreamEvent =
  | StreamStartEvent
  | StreamTokenEvent
  | StreamEndEvent
  | StreamErrorEvent;

interface StreamHandlers {
  onStart?: (event: StreamStartEvent) => void;
  onToken?: (token: string) => void;
  onEnd?: (event: StreamEndEvent) => void;
  onError?: (message: string) => void;
}

export async function streamMessage(
  question: string,
  userId: string,
  threadId: string,
  handlers: StreamHandlers = {}
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      user_id: userId,
      thread_id: threadId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to stream chat message: ${response.status}`);
  }

  if (!response.body) {
    throw new Error("Streaming response body is not available");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) {
        continue;
      }

      let event: StreamEvent;

      try {
        event = JSON.parse(trimmed) as StreamEvent;
      } catch {
        continue;
      }

      if (event.type === "start") {
        handlers.onStart?.(event);
        continue;
      }

      if (event.type === "token") {
        handlers.onToken?.(event.content);
        continue;
      }

      if (event.type === "end") {
        handlers.onEnd?.(event);
        continue;
      }

      handlers.onError?.(event.message || "Streaming failed");
    }
  }
}

export async function fetchThreads(userId: string): Promise<ChatThreadSummaryApi[]> {
  const response = await fetch(`${API_BASE_URL}/chat/threads/${userId}`);

  if (!response.ok) {
    throw new Error(`Failed to load chat threads: ${response.status}`);
  }

  const payload: ChatThreadListApiResponse = await response.json();
  return payload.threads ?? [];
}

export async function fetchThreadMessages(
  userId: string,
  threadId: string
): Promise<ChatMessage[]> {
  const response = await fetch(
    `${API_BASE_URL}/chat/threads/${userId}/${threadId}`
  );

  if (!response.ok) {
    throw new Error(`Failed to load chat history: ${response.status}`);
  }

  const payload: ChatThreadHistoryApiResponse = await response.json();

  return (payload.messages ?? []).map((message, index) => ({
    id: `${threadId}-${index}-${message.created_at}`,
    role: message.role,
    content: message.content,
    sources: Array.isArray(message.sources)
      ? message.sources
      : undefined,
  }));
}

interface DeleteThreadApiResponse {
  deleted: boolean;
}

interface RenameThreadApiResponse {
  renamed: boolean;
}

export async function deleteThread(
  userId: string,
  threadId: string
): Promise<boolean> {
  const response = await fetch(
    `${API_BASE_URL}/chat/threads/${userId}/${threadId}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to delete chat thread: ${response.status}`);
  }

  const payload: DeleteThreadApiResponse = await response.json();
  return Boolean(payload.deleted);
}

export async function renameThread(
  userId: string,
  threadId: string,
  title: string
): Promise<boolean> {
  const response = await fetch(
    `${API_BASE_URL}/chat/threads/${userId}/${threadId}/title`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title }),
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to rename chat thread: ${response.status}`);
  }

  const payload: RenameThreadApiResponse = await response.json();
  return Boolean(payload.renamed);
}