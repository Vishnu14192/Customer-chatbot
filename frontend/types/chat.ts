export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  thread_id: string;
}

export interface ChatThread {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
  isLoaded?: boolean;
  persisted?: boolean;
}