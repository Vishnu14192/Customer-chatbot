/** Shared API endpoint roots used by all chat transport modules. */
export const API_BASE_URL = "http://localhost:8000";

/** WebSocket base URL derived from HTTP API base URL. */
export const WS_BASE_URL = API_BASE_URL
  .replace("http://", "ws://")
  .replace("https://", "wss://");
