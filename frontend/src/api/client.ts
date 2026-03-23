import type { GridGeoJSON, CellDetail, Category } from "../types";

const API_BASE = "http://localhost:8000/api";

export async function fetchGridScores(
  weights: Record<string, number>
): Promise<GridGeoJSON> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(weights)) {
    params.set(`w_${key}`, value.toString());
  }
  const resp = await fetch(`${API_BASE}/grid/scores?${params}`);
  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
  return resp.json();
}

export async function fetchCellDetail(
  row: number,
  col: number
): Promise<CellDetail> {
  const resp = await fetch(`${API_BASE}/grid/cell/${row}/${col}`);
  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
  return resp.json();
}

export async function fetchCategories(): Promise<Category[]> {
  const resp = await fetch(`${API_BASE}/meta/categories`);
  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
  const data = await resp.json();
  return data.categories;
}
