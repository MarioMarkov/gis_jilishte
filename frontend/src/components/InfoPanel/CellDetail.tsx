import type { CellDetail as CellDetailType } from "../../types";

interface CellDetailProps {
  detail: CellDetailType | null;
  onClose: () => void;
}

const SCORE_LABELS: Record<string, string> = {
  transport: "Transport",
  parks: "Parks",
  education: "Education",
  playground: "Playgrounds",
  air_quality: "Air Quality",
};

const POI_LABELS: Record<string, string> = {
  transport: "Transport Stops",
  park: "Parks",
  kindergarten: "Kindergartens",
  school: "Schools",
  playground: "Playgrounds",
};

function ScoreBar({ label, value }: { label: string; value: number }) {
  const score10 = (value * 10).toFixed(1);
  const pct = Math.round(value * 100);
  const color =
    pct >= 70 ? "#1a9850" : pct >= 40 ? "#fee08b" : "#d73027";

  return (
    <div style={{ marginBottom: 6 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 12,
          marginBottom: 2,
        }}
      >
        <span>{label}</span>
        <span style={{ fontWeight: 600 }}>{score10} / 10</span>
      </div>
      <div
        style={{
          height: 6,
          background: "#eee",
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: color,
            borderRadius: 3,
          }}
        />
      </div>
    </div>
  );
}

export default function CellDetail({ detail, onClose }: CellDetailProps) {
  if (!detail) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: 10,
        right: 10,
        width: 280,
        maxHeight: "calc(100% - 20px)",
        overflowY: "auto",
        background: "#fff",
        borderRadius: 8,
        boxShadow: "0 2px 12px rgba(0,0,0,0.15)",
        padding: 16,
        zIndex: 20,
        fontSize: 13,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 12,
        }}
      >
        <h3 style={{ margin: 0, fontSize: 15 }}>Location Detail</h3>
        <button
          onClick={onClose}
          style={{
            background: "none",
            border: "none",
            fontSize: 18,
            cursor: "pointer",
            color: "#999",
          }}
        >
          x
        </button>
      </div>

      <div style={{ color: "#666", marginBottom: 12, fontSize: 12 }}>
        {detail.centroid[0].toFixed(4)}, {detail.centroid[1].toFixed(4)}
      </div>

      <h4 style={{ margin: "0 0 8px", fontSize: 13 }}>Score Breakdown</h4>
      {Object.entries(detail.scores).map(([key, value]) => (
        <ScoreBar key={key} label={SCORE_LABELS[key] || key} value={value} />
      ))}

      <h4 style={{ margin: "16px 0 8px", fontSize: 13 }}>Nearby Places</h4>
      {Object.entries(detail.nearby).map(([category, pois]) => (
        <div key={category} style={{ marginBottom: 10 }}>
          <div style={{ fontWeight: 600, fontSize: 12, marginBottom: 2 }}>
            {POI_LABELS[category] || category}
          </div>
          {pois.length === 0 && (
            <div style={{ color: "#999", fontSize: 11 }}>None nearby</div>
          )}
          {pois.map((poi, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: 11,
                color: "#555",
                padding: "1px 0",
              }}
            >
              <span>{poi.name}</span>
              <span>{poi.distance_m}m</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
