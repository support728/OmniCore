type ResultCardProps = {
  title: string;
  url: string;
  description: string;
  image?: string | null;
  loading?: boolean;
  source?: string;
  why?: string;
  rank?: number;
  onOpen: (url: string) => void;
  onSummarize?: (url: string) => void;
  onRelate?: (url: string) => void;
};

function getYouTubeEmbedUrl(url: string) {
  try {
    const parsed = new URL(url);

    if (parsed.hostname.includes("youtu.be")) {
      const videoId = parsed.pathname.replace(/^\//, "");
      return videoId ? `https://www.youtube.com/embed/${videoId}` : null;
    }

    if (parsed.hostname.includes("youtube.com")) {
      const videoId = parsed.searchParams.get("v");
      if (videoId) {
        return `https://www.youtube.com/embed/${videoId}`;
      }

      const parts = parsed.pathname.split("/").filter(Boolean);
      const markerIndex = parts.findIndex((part) => part === "embed" || part === "shorts");
      if (markerIndex >= 0 && parts[markerIndex + 1]) {
        return `https://www.youtube.com/embed/${parts[markerIndex + 1]}`;
      }
    }
  } catch {
    return null;
  }

  return null;
}

export default function ResultCard({
  title,
  url,
  description,
  image,
  loading = false,
  source,
  why,
  rank,
  onOpen,
  onSummarize,
  onRelate,
}: ResultCardProps) {
  const youtubeEmbedUrl = getYouTubeEmbedUrl(url);

  return (
    <div
      style={{
        border: "1px solid #eee",
        borderRadius: "12px",
        padding: "12px",
        marginTop: "10px",
        background: "#fff",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, marginBottom: 8 }}>
        {typeof rank === "number" ? (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              minWidth: 36,
              height: 28,
              padding: "0 10px",
              borderRadius: 999,
              background: "#172033",
              color: "#fff",
              fontSize: 12,
              fontWeight: 700,
            }}
          >
            #{rank}
          </span>
        ) : <span />}
        {source ? <span style={{ fontSize: 12, fontWeight: 700, color: "#60728e", textTransform: "uppercase" }}>{source}</span> : null}
      </div>

      {youtubeEmbedUrl ? (
        <iframe
          width="100%"
          height="200"
          src={youtubeEmbedUrl}
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          style={{ borderRadius: "8px", marginBottom: "8px" }}
          title={title}
        />
      ) : image ? (
        <img
          src={image}
          alt={title}
          style={{
            width: "100%",
            borderRadius: "8px",
            marginBottom: "8px",
          }}
        />
      ) : loading ? (
        <div
          style={{
            width: "100%",
            height: 120,
            borderRadius: "8px",
            marginBottom: "8px",
            background: "linear-gradient(90deg, #f2f4f7 0%, #e7edf5 50%, #f2f4f7 100%)",
          }}
        />
      ) : null}

      <h4 style={{ margin: "0 0 6px" }}>{title}</h4>
      <p style={{ fontSize: "14px", color: "#555", margin: 0 }}>{description}</p>
      {why ? <p style={{ fontSize: "13px", color: "#425874", margin: "8px 0 0" }}>{why}</p> : null}

    </div>
  );
}