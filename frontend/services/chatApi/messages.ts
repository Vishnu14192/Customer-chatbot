/** One-shot (non-streaming) chat message transport helpers. */
import { ChatResponse } from "@/types/chat";
import { API_BASE_URL } from "./config";

/** Sends a single question and waits for the complete assistant response. */
export async function sendMessage(
  question: string,
  userId: string,
  threadId: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
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
    throw new Error(`Failed to send chat message: ${response.status}`);
  }

  return response.json();
}
