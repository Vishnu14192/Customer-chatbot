interface Props {
  role: string;
  content: string;
  sources?: string[] | null;
}

function mapSourceLabel(source: string): string {
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

  const safeSources = Array.isArray(sources)
    ? sources
    : [];

  return (
    <div
      className={`p-3 rounded-lg mb-2 ${
        role === "user"
          ? "bg-blue-500 text-white ml-auto"
          : "bg-gray-200 text-black"
      }`}
    >
      {content}

      {role === "assistant" && safeSources.length > 0 && (
        <div className="mt-2 pt-2 border-t border-zinc-300/80">
          <p className="text-xs font-semibold text-zinc-600 mb-1">Sources</p>
          <div className="flex flex-wrap gap-1.5">
            {safeSources.map((source) => (
              <span
                key={source}
                className="text-xs px-2 py-0.5 rounded-full bg-zinc-300 text-zinc-800"
              >
                {mapSourceLabel(source)}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}