/**
 * Pure utility functions for creating chat entities.
 * These functions have no side effects and are used throughout the chat hook.
 */

import { ChatMessage, ChatThread } from "@/types/chat";

/**
 * Generates a unique ID for messages and threads.
 * Uses browser crypto API with fallback to timestamp + random number.
 * @returns A stable unique identifier string
 */
export function createId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
}

/**
 * Creates an empty thread object with default values.
 * @param title - Optional thread title (defaults to "New Chat")
 * @returns A new ChatThread object with zero messages and persisted=false
 */
export function createNewThread(title: string = "New Chat"): ChatThread {
  const now = Date.now();
  return {
    id: createId(),
    title,
    messages: [],
    createdAt: now,
    updatedAt: now,
    isLoaded: true,
    persisted: false,
  };
}

/**
 * Creates a message object with metadata.
 * @param role - "user" or "assistant" to indicate message origin
 * @param content - The text content of the message
 * @param sources - Optional array of source references (for RAG retrieval)
 * @returns A new ChatMessage object
 */
export function createMessage(
  role: "user" | "assistant",
  content: string,
  sources?: string[]
): ChatMessage {
  return {
    id: createId(),
    role,
    content,
    sources,
  };
}
