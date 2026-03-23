import { useState, useEffect, useCallback } from "react";
import MapView from "./components/Map/MapView";
import WeightPanel from "./components/Sidebar/WeightPanel";
import CellDetail from "./components/InfoPanel/CellDetail";
import { useGridScores } from "./hooks/useGridScores";
import { fetchCategories, fetchCellDetail } from "./api/client";
import type { Category, CellDetail as CellDetailType, Weights } from "./types";

const DEFAULT_WEIGHTS: Weights = {
  transport: 5,
  parks: 4,
  education: 4,
  air_quality: 3,
  noise: 3,
  shopping: 3,
  healthcare: 3,
  commute: 3,
};

const FALLBACK_CATEGORIES: Category[] = [
  { key: "transport", label: "Metro & Public Transport", label_bg: "Метро и транспорт", default_weight: 5, icon: "bus" },
  { key: "parks", label: "Parks & Green Spaces", label_bg: "Паркове и зеленина", default_weight: 4, icon: "tree" },
  { key: "education", label: "Kindergartens & Schools", label_bg: "Детски градини и училища", default_weight: 4, icon: "school" },
  { key: "air_quality", label: "Air Quality", label_bg: "Качество на въздуха", default_weight: 3, icon: "wind" },
  { key: "noise", label: "Noise Level", label_bg: "Ниво на шум", default_weight: 3, icon: "volume" },
  { key: "shopping", label: "Supermarkets & Shopping", label_bg: "Магазини и пазаруване", default_weight: 3, icon: "cart" },
  { key: "healthcare", label: "Healthcare", label_bg: "Здравеопазване", default_weight: 3, icon: "hospital" },
  { key: "commute", label: "Commute to Center", label_bg: "Близост до центъра", default_weight: 3, icon: "compass" },
];

export default function App() {
  const [categories, setCategories] = useState<Category[]>(FALLBACK_CATEGORIES);
  const [weights, setWeights] = useState<Weights>(DEFAULT_WEIGHTS);
  const [cellDetail, setCellDetail] = useState<CellDetailType | null>(null);
  const { data: gridData, loading } = useGridScores(weights);

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => {});
  }, []);

  const handleCellClick = useCallback(async (row: number, col: number) => {
    try {
      const detail = await fetchCellDetail(row, col);
      setCellDetail(detail);
    } catch (err) {
      console.error("Failed to fetch cell detail:", err);
    }
  }, []);

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "system-ui, sans-serif" }}>
      <WeightPanel
        categories={categories}
        weights={weights}
        onChange={setWeights}
        loading={loading}
      />
      <div style={{ flex: 1, position: "relative", display: "flex", flexDirection: "column" }}>
        <MapView gridData={gridData} onCellClick={handleCellClick} />
        <CellDetail detail={cellDetail} onClose={() => setCellDetail(null)} />
      </div>
    </div>
  );
}
