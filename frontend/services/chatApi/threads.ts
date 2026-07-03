/** Thread management and history transport helpers. */
import { ChatMessage } from "@/types/chat";
import { API_BASE_URL } from "./config";
import {
  ChatThreadHistoryApiResponse,
  ChatThreadListApiResponse,
  ChatThreadSummaryApi,
  DeleteThreadApiResponse,
  RenameThreadApiResponse,
} from "./types";

export async function fetchThreads(userId: string): Promise<ChatThreadSummaryApi[]> {
  /** Loads thread summaries used to render the chat sidebar list. */
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
  /** Loads full message history for one selected thread. */
  const response = await fetch(`${API_BASE_URL}/chat/threads/${userId}/${threadId}`);

  if (!response.ok) {
    throw new Error(`Failed to load chat history: ${response.status}`);
  }

  const payload: ChatThreadHistoryApiResponse = await response.json();

  return (payload.messages ?? []).map((message, index) => ({
    id: `${threadId}-${index}-${message.created_at}`,
    role: message.role,
    content: message.content,
    sources: Array.isArray(message.sources) ? message.sources : undefined,
  }));
}

export async function deleteThread(
  userId: string,
  threadId: string
): Promise<boolean> {
  /** Deletes a thread and its persisted messages on the backend. */
  const response = await fetch(`${API_BASE_URL}/chat/threads/${userId}/${threadId}`, {
    method: "DELETE",
  });

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
  /** Renames an existing thread title on the backend. */
  const response = await fetch(`${API_BASE_URL}/chat/threads/${userId}/${threadId}/title`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    throw new Error(`Failed to rename chat thread: ${response.status}`);
  }

  const payload: RenameThreadApiResponse = await response.json();
  return Boolean(payload.renamed);
}
