/** Minimal thread metadata returned for sidebar and thread list rendering. */
export interface ChatThreadSummaryApi {
  thread_id: string;
  title: string;
  updated_at: string;
  message_count: number;
}

/** Response wrapper for thread summary listing endpoint. */
export interface ChatThreadListApiResponse {
  threads: ChatThreadSummaryApi[];
}

/** Response shape for full message history of a single thread. */
export interface ChatThreadHistoryApiResponse {
  thread_id: string;
  messages: Array<{
    role: "user" | "assistant";
    content: string;
    created_at: string;
    sources?: string[] | null;
  }>;
}

/** Response shape for successful thread deletion. */
export interface DeleteThreadApiResponse {
  deleted: boolean;
}

/** Response shape for successful thread rename. */
export interface RenameThreadApiResponse {
  renamed: boolean;
}

/** First event in a stream, includes initial metadata and source citations. */
export interface StreamStartEvent {
  type: "start";
  thread_id: string;
  sources: string[];
}

/** Incremental token chunk from the assistant while streaming. */
export interface StreamTokenEvent {
  type: "token";
  content: string;
}

/** Terminal event indicating stream completion for a thread. */
export interface StreamEndEvent {
  type: "end";
  thread_id: string;
  sources: string[];
}

/** Error event emitted by backend stream channels. */
export interface StreamErrorEvent {
  type: "error";
  message?: string;
}

/** Union of all supported stream event payloads. */
export type StreamEvent =
  | StreamStartEvent
  | StreamTokenEvent
  | StreamEndEvent
  | StreamErrorEvent;

/** Optional callbacks used by UI to react to stream lifecycle updates. */
export interface StreamHandlers {
  onStart?: (event: StreamStartEvent) => void;
  onToken?: (token: string) => void;
  onEnd?: (event: StreamEndEvent) => void;
  onError?: (message: string) => void;
}
