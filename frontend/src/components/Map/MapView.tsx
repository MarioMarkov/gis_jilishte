import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { GridGeoJSON } from "../../types";

interface MapViewProps {
  gridData: GridGeoJSON | null;
  onCellClick: (row: number, col: number) => void;
}

const SOFIA_CENTER: [number, number] = [23.3219, 42.6977];
const STYLE_URL = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";

export default function MapView({ gridData, onCellClick }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const gridDataRef = useRef(gridData);
  gridDataRef.current = gridData;
  const [styleJson, setStyleJson] = useState<any>(null);

  // Fetch and patch the style JSON before creating the map
  useEffect(() => {
    fetch(STYLE_URL)
      .then((res) => res.json())
      .then((style) => {
        if (!style.projection) {
          style.projection = { type: "mercator" };
        }
        setStyleJson(style);
      });
  }, []);

  useEffect(() => {
    if (!containerRef.current || mapRef.current || !styleJson) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleJson,
      center: SOFIA_CENTER,
      zoom: 12,
      minZoom: 10,
      maxZoom: 16,
      maxBounds: [
        [23.1, 42.55],
        [23.6, 42.85],
      ],
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");

    map.on("load", () => {
      map.addSource("grid-scores", {
        type: "geojson",
        data: gridDataRef.current ?? { type: "FeatureCollection", features: [] },
      });

      map.addLayer({
        id: "grid-heatmap",
        type: "fill",
        source: "grid-scores",
        paint: {
          "fill-color": [
            "interpolate",
            ["linear"],
            ["get", "score"],
            0.0, "#d73027",
            0.2, "#fc8d59",
            0.4, "#fee08b",
            0.6, "#d9ef8b",
            0.8, "#91cf60",
            1.0, "#1a9850",
          ],
          "fill-opacity": 0.65,
        },
      });

      map.addLayer({
        id: "grid-outline",
        type: "line",
        source: "grid-scores",
        paint: {
          "line-color": "#ffffff",
          "line-width": 0.3,
          "line-opacity": 0.3,
        },
        minzoom: 14,
      });

      // Hover effect
      map.on("mousemove", "grid-heatmap", (e) => {
        map.getCanvas().style.cursor = "pointer";
        if (e.features && e.features.length > 0) {
          const props = e.features[0].properties;
          const score = typeof props.score === "number" ? props.score : parseFloat(props.score);
          const popup = document.getElementById("hover-tooltip");
          if (popup) {
            popup.style.display = "block";
            popup.style.left = e.point.x + 15 + "px";
            popup.style.top = e.point.y - 10 + "px";
            popup.textContent = `Score: ${(score * 10).toFixed(1)} / 10`;
          }
        }
      });

      map.on("mouseleave", "grid-heatmap", () => {
        map.getCanvas().style.cursor = "";
        const popup = document.getElementById("hover-tooltip");
        if (popup) popup.style.display = "none";
      });

      // Click handler
      map.on("click", "grid-heatmap", (e) => {
        if (e.features && e.features.length > 0) {
          const props = e.features[0].properties;
          onCellClick(props.row, props.col);
        }
      });
    });

    mapRef.current = map;

    return () => map.remove();
  }, [styleJson]);

  // Update data when gridData changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !gridData) return;

    const update = () => {
      const source = map.getSource("grid-scores") as maplibregl.GeoJSONSource;
      if (source) {
        source.setData(gridData as any);
      }
    };

    if (map.isStyleLoaded()) {
      update();
    } else {
      map.once("load", update);
    }
  }, [gridData]);

  return (
    <div style={{ position: "relative", flex: 1, minHeight: 0 }}>
      <div ref={containerRef} style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, zIndex: 0 }} />
      <div
        id="hover-tooltip"
        style={{
          display: "none",
          position: "absolute",
          background: "rgba(0,0,0,0.8)",
          color: "#fff",
          padding: "4px 8px",
          borderRadius: 4,
          fontSize: 13,
          pointerEvents: "none",
          zIndex: 10,
        }}
      />
      {/* Color legend */}
      <div
        style={{
          position: "absolute",
          bottom: 30,
          left: 10,
          background: "rgba(255,255,255,0.92)",
          padding: "8px 12px",
          borderRadius: 6,
          fontSize: 12,
          boxShadow: "0 1px 4px rgba(0,0,0,0.2)",
          zIndex: 5,
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: 4 }}>Location Score</div>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span>Low</span>
          <div
            style={{
              width: 120,
              height: 12,
              borderRadius: 3,
              background:
                "linear-gradient(to right, #d73027, #fc8d59, #fee08b, #d9ef8b, #91cf60, #1a9850)",
            }}
          />
          <span>High</span>
        </div>
      </div>
    </div>
  );
}
