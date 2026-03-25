import { useState, useEffect } from "react";
import WeightSlider from "./WeightSlider";
import type { Category, Weights } from "../../types";

interface WeightPanelProps {
  categories: Category[];
  weights: Weights;
  onChange: (weights: Weights) => void;
  loading: boolean;
}

type Answer = string | null;

interface Answers {
  hasKids: Answer;
  commute: Answer;
  parks: Answer;
  airQuality: Answer;
  nightlife: Answer;
  budget: Answer;
  affluent: Answer;
}

const DEFAULT_ANSWERS: Answers = {
  hasKids: null,
  commute: null,
  parks: null,
  airQuality: null,
  nightlife: null,
  budget: null,
  affluent: null,
};

// Only the 5 keys the backend actually uses; nightlife/budget are neighbourhood-only extras
function answersToWeights(answers: Answers): Weights {
  const w: Weights = {
    transport: 4,
    parks: 4,
    education: 4,
    playground: 2,
    air_quality: 3,
    nightlife: 0,
    budget: 0,
    affluent: 0,
  };

  if (answers.hasKids === "yes") {
    w.education = 9;
    w.playground = 8;
  } else if (answers.hasKids === "no") {
    w.education = 2;
    w.playground = 1;
  }

  if (answers.commute === "transit") {
    w.transport = 9;
  } else if (answers.commute === "walk") {
    w.transport = 5;
  } else if (answers.commute === "car") {
    w.transport = 2;
  }

  if (answers.parks === "lot") {
    w.parks = 9;
  } else if (answers.parks === "some") {
    w.parks = 5;
  } else if (answers.parks === "no") {
    w.parks = 1;
  }

  if (answers.airQuality === "very") {
    w.air_quality = 9;
  } else if (answers.airQuality === "somewhat") {
    w.air_quality = 5;
  } else if (answers.airQuality === "no") {
    w.air_quality = 1;
  }

  if (answers.nightlife === "yes") {
    w.nightlife = 8;
  } else if (answers.nightlife === "no") {
    w.nightlife = 0;
  }

  if (answers.budget === "yes") {
    w.budget = 8;
  } else if (answers.budget === "no") {
    w.budget = 0;
  }

  if (answers.affluent === "yes") {
    w.affluent = 8;
  } else if (answers.affluent === "no") {
    w.affluent = 0;
  }

  return w;
}

// Sofia neighbourhoods with rough scores (0–10) per category
interface Neighbourhood {
  name: string;
  name_en: string;
  description: string;
  scores: {
    transport: number;
    parks: number;
    education: number;
    playground: number;
    air_quality: number;
    nightlife: number;
    budget: number;
    affluent: number;
  };
}

const NEIGHBOURHOODS: Neighbourhood[] = [
  {
    name: "Младост",
    name_en: "Mladost",
    description: "Metro hub, many schools & playgrounds, family-friendly",
    scores: { transport: 9, parks: 5, education: 8, playground: 8, air_quality: 5, nightlife: 2, budget: 5, affluent: 5 },
  },
  {
    name: "Лозенец",
    name_en: "Lozenets",
    description: "Leafy streets, good transport, quiet and upscale",
    scores: { transport: 7, parks: 7, education: 7, playground: 6, air_quality: 7, nightlife: 3, budget: 2, affluent: 9 },
  },
  {
    name: "Изток",
    name_en: "Iztok",
    description: "Central, green boulevards, well-connected",
    scores: { transport: 8, parks: 7, education: 7, playground: 6, air_quality: 6, nightlife: 3, budget: 2, affluent: 8 },
  },
  {
    name: "Изгрев",
    name_en: "Izgrev",
    description: "Residential, calm, near South Park",
    scores: { transport: 7, parks: 7, education: 7, playground: 6, air_quality: 7, nightlife: 2, budget: 3, affluent: 7 },
  },
  {
    name: "Симеоново / Витоша",
    name_en: "Simeonovo / Vitosha",
    description: "Fresh mountain air, nature at the doorstep, less transit",
    scores: { transport: 4, parks: 9, education: 5, playground: 6, air_quality: 9, nightlife: 1, budget: 2, affluent: 8 },
  },
  {
    name: "Бояна",
    name_en: "Boyana",
    description: "Upmarket, quiet, near Vitosha, limited public transport",
    scores: { transport: 3, parks: 8, education: 5, playground: 5, air_quality: 9, nightlife: 1, budget: 1, affluent: 10 },
  },
  {
    name: "Княжево",
    name_en: "Knyazhevo",
    description: "Near Vitosha, clean air, hillside residential",
    scores: { transport: 5, parks: 7, education: 5, playground: 5, air_quality: 8, nightlife: 1, budget: 4, affluent: 7 },
  },
  {
    name: "Люлин",
    name_en: "Lyulin",
    description: "Metro access, affordable, large family district",
    scores: { transport: 8, parks: 4, education: 7, playground: 7, air_quality: 4, nightlife: 2, budget: 9, affluent: 2 },
  },
  {
    name: "Дружба",
    name_en: "Druzhba",
    description: "Affordable blocks, metro nearby, practical location",
    scores: { transport: 7, parks: 4, education: 6, playground: 6, air_quality: 4, nightlife: 2, budget: 9, affluent: 2 },
  },
  {
    name: "Студентски град",
    name_en: "Studentski grad",
    description: "Vibrant nightlife, bars & clubs, metro, young crowd",
    scores: { transport: 8, parks: 6, education: 6, playground: 4, air_quality: 5, nightlife: 10, budget: 8, affluent: 3 },
  },
  {
    name: "Слатина",
    name_en: "Slatina",
    description: "Central-ish, good bus links, residential",
    scores: { transport: 7, parks: 5, education: 7, playground: 6, air_quality: 5, nightlife: 3, budget: 6, affluent: 4 },
  },
  {
    name: "Надежда",
    name_en: "Nadezhda",
    description: "Affordable, improving transport, dense residential",
    scores: { transport: 6, parks: 4, education: 6, playground: 5, air_quality: 4, nightlife: 2, budget: 9, affluent: 2 },
  },
  {
    name: "Банишора / Сердика",
    name_en: "Banishora / Serdika",
    description: "Metro station, central, mixed area",
    scores: { transport: 8, parks: 4, education: 6, playground: 5, air_quality: 4, nightlife: 3, budget: 7, affluent: 3 },
  },
  {
    name: "Обеля",
    name_en: "Obelya",
    description: "Quiet outskirts, very affordable, limited amenities",
    scores: { transport: 5, parks: 4, education: 5, playground: 5, air_quality: 5, nightlife: 1, budget: 10, affluent: 1 },
  },
];

function scoreNeighbourhood(n: Neighbourhood, weights: Weights): number {
  const mapKeys = ["transport", "parks", "education", "playground", "air_quality"] as const;
  const extraKeys = ["nightlife", "budget", "affluent"] as const;
  const allKeys = [...mapKeys, ...extraKeys];
  const totalW = allKeys.reduce((s, k) => s + (weights[k] ?? 0), 0);
  if (totalW === 0) return 0;
  return allKeys.reduce((s, k) => s + (weights[k] ?? 0) * n.scores[k], 0) / totalW;
}

function getTopNeighbourhoods(weights: Weights, n = 3): Neighbourhood[] {
  return [...NEIGHBOURHOODS]
    .sort((a, b) => scoreNeighbourhood(b, weights) - scoreNeighbourhood(a, weights))
    .slice(0, n);
}

interface ChoiceOption {
  value: string;
  label: string;
}

function QuestionCard({
  question,
  options,
  value,
  onSelect,
}: {
  question: string;
  options: ChoiceOption[];
  value: Answer;
  onSelect: (v: string) => void;
}) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6, color: "#222" }}>
        {question}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {options.map((opt) => {
          const selected = value === opt.value;
          return (
            <button
              key={opt.value}
              onClick={() => onSelect(selected ? "" : opt.value)}
              style={{
                padding: "5px 12px",
                fontSize: 12,
                borderRadius: 20,
                border: selected ? "2px solid #1976d2" : "1.5px solid #ccc",
                background: selected ? "#e3f2fd" : "#fafafa",
                color: selected ? "#1565c0" : "#444",
                cursor: "pointer",
                fontWeight: selected ? 600 : 400,
                transition: "all 0.15s",
              }}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function NeighbourhoodCard({ n, rank, weights }: { n: Neighbourhood; rank: number; weights: Weights }) {
  const score = scoreNeighbourhood(n, weights);
  const pct = Math.round((score / 10) * 100);
  const medals = ["", "gold", "#aaa", "#cd7f32"];
  const medalColors = ["", "#f59e0b", "#9ca3af", "#b45309"];

  return (
    <div
      style={{
        border: rank === 1 ? "2px solid #f59e0b" : "1px solid #e0e0e0",
        borderRadius: 8,
        padding: "10px 12px",
        marginBottom: 8,
        background: rank === 1 ? "#fffbeb" : "#fff",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
        <span style={{ fontWeight: 700, fontSize: 13, color: "#111" }}>
          <span style={{ color: medalColors[rank], marginRight: 4 }}>
            {rank === 1 ? "★" : rank === 2 ? "▲" : "●"}
          </span>
          {n.name}
        </span>
        <span style={{ fontSize: 12, color: "#555", fontWeight: 600 }}>{pct}% match</span>
      </div>
      <div style={{ fontSize: 11, color: "#666", marginBottom: 6 }}>{n.description}</div>
      <div style={{ height: 4, background: "#e0e0e0", borderRadius: 2 }}>
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            background: rank === 1 ? "#f59e0b" : "#1976d2",
            borderRadius: 2,
            transition: "width 0.3s",
          }}
        />
      </div>
    </div>
  );
}

export default function WeightPanel({
  categories,
  weights,
  onChange,
  loading,
}: WeightPanelProps) {
  const [answers, setAnswers] = useState<Answers>(DEFAULT_ANSWERS);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const answeredCount = Object.values(answers).filter((v) => v !== null && v !== "").length;
  const hasAnyAnswer = answeredCount > 0;

  useEffect(() => {
    const computed = answersToWeights(answers);
    onChange(computed);
  }, [answers]);

  const setAnswer = (key: keyof Answers) => (value: string) => {
    setAnswers((prev) => ({ ...prev, [key]: value || null }));
  };

  const handleSliderChange = (key: string, value: number) => {
    onChange({ ...weights, [key]: value });
  };

  const topNeighbourhoods = getTopNeighbourhoods(weights);

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
      <h2 style={{ margin: "0 0 4px", fontSize: 18 }}>Жилище</h2>
      <p style={{ margin: "0 0 14px", fontSize: 13, color: "#666" }}>
        Answer a few questions to find your ideal Sofia neighbourhood.
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

      <QuestionCard
        question="Do you have young children?"
        options={[
          { value: "yes", label: "Yes" },
          { value: "no", label: "No" },
        ]}
        value={answers.hasKids}
        onSelect={setAnswer("hasKids")}
      />

      <QuestionCard
        question="How do you get around the city?"
        options={[
          { value: "transit", label: "Public transport" },
          { value: "walk", label: "On foot / bike" },
          { value: "car", label: "By car" },
        ]}
        value={answers.commute}
        onSelect={setAnswer("commute")}
      />

      <QuestionCard
        question="How important are parks and green spaces?"
        options={[
          { value: "lot", label: "Very important" },
          { value: "some", label: "Somewhat" },
          { value: "no", label: "Not really" },
        ]}
        value={answers.parks}
        onSelect={setAnswer("parks")}
      />

      <QuestionCard
        question="Do you care about air quality?"
        options={[
          { value: "very", label: "Very much" },
          { value: "somewhat", label: "Somewhat" },
          { value: "no", label: "Not really" },
        ]}
        value={answers.airQuality}
        onSelect={setAnswer("airQuality")}
      />

      <QuestionCard
        question="Do you enjoy going out — bars, clubs, nightlife?"
        options={[
          { value: "yes", label: "Yes, love it" },
          { value: "no", label: "Not really" },
        ]}
        value={answers.nightlife}
        onSelect={setAnswer("nightlife")}
      />

      <QuestionCard
        question="Do you prefer affluent, upscale neighbourhoods?"
        options={[
          { value: "yes", label: "Yes, prestige matters" },
          { value: "no", label: "Not a priority" },
        ]}
        value={answers.affluent}
        onSelect={setAnswer("affluent")}
      />

      <QuestionCard
        question="Are you looking for budget-friendly rent?"
        options={[
          { value: "yes", label: "Yes, price matters" },
          { value: "no", label: "Not a priority" },
        ]}
        value={answers.budget}
        onSelect={setAnswer("budget")}
      />

      <div style={{ marginTop: 4, marginBottom: 12 }}>
        <button
          onClick={() => setShowAdvanced((v) => !v)}
          style={{
            padding: "6px 12px",
            fontSize: 12,
            background: "none",
            border: "1px solid #ccc",
            borderRadius: 4,
            cursor: "pointer",
            color: "#555",
            width: "100%",
          }}
        >
          {showAdvanced ? "Hide" : "Show"} fine-tune sliders
        </button>
      </div>

      {showAdvanced && (
        <div style={{ marginBottom: 12 }}>
          {categories.map((cat) => (
            <WeightSlider
              key={cat.key}
              label={cat.label}
              label_bg={cat.label_bg}
              icon={cat.icon}
              value={weights[cat.key] ?? cat.default_weight}
              onChange={(v) => handleSliderChange(cat.key, v)}
            />
          ))}
        </div>
      )}

      <div
        style={{
          borderTop: "1px solid #e0e0e0",
          paddingTop: 14,
          marginTop: 4,
        }}
      >
        <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10, color: "#222" }}>
          Recommended neighbourhoods
        </div>
        {!hasAnyAnswer && (
          <div style={{ fontSize: 12, color: "#999", fontStyle: "italic", marginBottom: 8 }}>
            Answer questions above to get personalised recommendations.
          </div>
        )}
        {topNeighbourhoods.map((n, i) => (
          <NeighbourhoodCard key={n.name_en} n={n} rank={i + 1} weights={weights} />
        ))}
      </div>

      <button
        onClick={() => setAnswers(DEFAULT_ANSWERS)}
        style={{
          marginTop: 12,
          padding: "8px 16px",
          background: "#f5f5f5",
          border: "1px solid #ddd",
          borderRadius: 4,
          cursor: "pointer",
          fontSize: 13,
        }}
      >
        Reset answers
      </button>
    </div>
  );
}
