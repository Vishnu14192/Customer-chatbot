/** Chat bubble renderer with role styling and source attribution chips. */

interface Props {
  role: string;
  content: string;
  sources?: string[] | null;
}

function mapSourceLabel(source: string): string {
  /** Converts raw source ids into user-friendly labels. */
  const normalized = source.toLowerCase();

  if (normalized === "llm") {
    return "LLM Analysis";
  }

  if (normalized === "memory") {
    return "Saved User Memory";
  }

  if (normalized.endsWith(".md") || normalized.endsWith(".txt")) {
    return `Flipkart Docs: ${source}`;
  }

  return source;
}

export default function MessageBubble({
  role,
  content,
  sources,
}: Props) {
  /** Renders one message bubble in user/assistant style. */

  const safeSources = Array.isArray(sources)
    ? sources
    : [];

  const isUser = role === "user";
  const roleLabel = isUser ? "You" : "Assistant";

  return (
    <div className={`mb-1.5 flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`w-fit max-w-[80%] px-2.5 py-2 rounded-lg ${
          isUser
            ? "bg-blue-500 text-white"
            : "bg-gray-200 text-black"
        }`}
      >
        <div className={`mb-0.5 text-[10px] font-semibold flex items-center gap-1 ${isUser ? "text-blue-100" : "text-zinc-600"}`}>
          <span className={`inline-block h-1.5 w-1.5 rounded-full ${isUser ? "bg-blue-100" : "bg-zinc-500"}`} />
          <span>{roleLabel}</span>
        </div>

        {content}

        {role === "assistant" && safeSources.length > 0 && (
          <div className="mt-1.5 pt-1.5 border-t border-zinc-300/80">
            <p className="text-[11px] font-semibold text-zinc-600 mb-1">Sources</p>
            <div className="flex flex-wrap gap-1">
              {safeSources.map((source) => (
                <span
                  key={source}
                  className="text-[11px] px-1.5 py-0.5 rounded-full bg-zinc-300 text-zinc-800"
                >
                  {mapSourceLabel(source)}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}