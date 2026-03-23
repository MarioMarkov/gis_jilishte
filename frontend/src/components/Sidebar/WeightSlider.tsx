interface WeightSliderProps {
  label: string;
  label_bg: string;
  value: number;
  onChange: (value: number) => void;
}

const ICONS: Record<string, string> = {
  bus: "\u{1F68D}",
  tree: "\u{1F333}",
  school: "\u{1F3EB}",
  wind: "\u{1F32C}\u{FE0F}",
  volume: "\u{1F509}",
  cart: "\u{1F6D2}",
  hospital: "\u{1F3E5}",
  compass: "\u{1F9ED}",
};

export default function WeightSlider({
  label,
  label_bg,
  value,
  onChange,
}: WeightSliderProps & { icon?: string }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 13,
          marginBottom: 2,
        }}
      >
        <span title={label}>{label_bg}</span>
        <span style={{ fontWeight: 600, color: "#333" }}>{value} / 10</span>
      </div>
      <input
        type="range"
        min={1}
        max={10}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ width: "100%" }}
      />
    </div>
  );
}

export { ICONS };
