import WeightSlider from "./WeightSlider";
import type { Category, Weights } from "../../types";

interface WeightPanelProps {
  categories: Category[];
  weights: Weights;
  onChange: (weights: Weights) => void;
  loading: boolean;
}

export default function WeightPanel({
  categories,
  weights,
  onChange,
  loading,
}: WeightPanelProps) {
  const handleChange = (key: string, value: number) => {
    onChange({ ...weights, [key]: value });
  };

  const resetDefaults = () => {
    const defaults: Weights = {};
    categories.forEach((c) => {
      defaults[c.key] = c.default_weight;
    });
    onChange(defaults);
  };

  return (
    <div
      style={{
        width: 300,
        padding: 16,
        background: "#fff",
        borderRight: "1px solid #e0e0e0",
        overflowY: "auto",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <h2 style={{ margin: "0 0 4px", fontSize: 18 }}>
        Жилище
      </h2>
      <p style={{ margin: "0 0 16px", fontSize: 13, color: "#666" }}>
        Adjust weights to find your ideal location in Sofia
      </p>

      {loading && (
        <div
          style={{
            padding: "6px 12px",
            background: "#e3f2fd",
            borderRadius: 4,
            fontSize: 12,
            marginBottom: 12,
            textAlign: "center",
          }}
        >
          Updating map...
        </div>
      )}

      {categories.map((cat) => (
        <WeightSlider
          key={cat.key}
          label={cat.label}
          label_bg={cat.label_bg}
          icon={cat.icon}
          value={weights[cat.key] ?? cat.default_weight}
          onChange={(v) => handleChange(cat.key, v)}
        />
      ))}

      <button
        onClick={resetDefaults}
        style={{
          marginTop: 8,
          padding: "8px 16px",
          background: "#f5f5f5",
          border: "1px solid #ddd",
          borderRadius: 4,
          cursor: "pointer",
          fontSize: 13,
        }}
      >
        Reset to Defaults
      </button>
    </div>
  );
}
