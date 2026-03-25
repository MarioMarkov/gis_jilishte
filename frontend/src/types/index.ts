export interface Category {
  key: string;
  label: string;
  label_bg: string;
  default_weight: number;
  icon: string;
}

export interface CellScores {
  transport: number;
  parks: number;
  education: number;
  playground: number;
  air_quality: number;
}

export interface GridFeature {
  type: "Feature";
  geometry: GeoJSON.Polygon;
  properties: {
    row: number;
    col: number;
    score: number;
    lat: number;
    lon: number;
    scores: CellScores;
  };
}

export interface GridGeoJSON {
  type: "FeatureCollection";
  features: GridFeature[];
}

export interface NearbyPoi {
  name: string;
  distance_m: number;
  type?: string;
}

export interface CellDetail {
  row: number;
  col: number;
  centroid: [number, number];
  scores: CellScores;
  nearby: Record<string, NearbyPoi[]>;
}

export type Weights = Record<string, number>;
