/** Streaming transport helpers over WebSocket and HTTP NDJSON fallback. */
import { API_BASE_URL, WS_BASE_URL } from "./config";
import { StreamEvent, StreamHandlers } from "./types";

/**
 * Streams assistant response over WebSocket.
 * Resolves on `end`, rejects on socket or stream-level errors.
 */
export async function streamMessageWebSocket(
  question: string,
  userId: string,
  threadId: string,
  handlers: StreamHandlers = {}
): Promise<void> {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(`${WS_BASE_URL}/ws/chat`);

    let finished = false;

    socket.onopen = () => {
      socket.send(
        JSON.stringify({
          user_id: userId,
          question,
          thread_id: threadId,
        })
      );
    };

    socket.onmessage = (messageEvent) => {
      let event: StreamEvent;

      try {
        event = JSON.parse(messageEvent.data) as StreamEvent;
      } catch {
        return;
      }

      // Dispatch lifecycle events to caller-provided handlers.
      if (event.type === "start") {
        handlers.onStart?.(event);
        return;
      }

      if (event.type === "token") {
        handlers.onToken?.(event.content);
        return;
      }

      if (event.type === "end") {
        handlers.onEnd?.(event);
        finished = true;
        socket.close();
        resolve();
        return;
      }

      const message = event.message || "Streaming failed";
      handlers.onError?.(message);

      if (!finished) {
        finished = true;
        socket.close();
        reject(new Error(message));
      }
    };

    socket.onerror = () => {
      if (finished) {
        return;
      }

      finished = true;
      reject(new Error("WebSocket connection error"));
    };

    socket.onclose = () => {
      if (finished) {
        return;
      }

      finished = true;
      reject(new Error("WebSocket closed before stream completion"));
    };
  });
}

/**
 * Streams assistant response over HTTP as newline-delimited JSON events.
 * Useful as a fallback when WebSocket transport is unavailable.
 */
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

      // Forward each parsed event to the corresponding callback.
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
