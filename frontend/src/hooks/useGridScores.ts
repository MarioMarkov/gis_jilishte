import { useState, useEffect, useRef } from "react";
import { fetchGridScores } from "../api/client";
import type { GridGeoJSON, Weights } from "../types";

export function useGridScores(weights: Weights) {
  const [data, setData] = useState<GridGeoJSON | null>(null);
  const [loading, setLoading] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    // Debounce 300ms
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const result = await fetchGridScores(weights);
        setData(result);
      } catch (err) {
        console.error("Failed to fetch grid scores:", err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [JSON.stringify(weights)]);

  return { data, loading };
}
