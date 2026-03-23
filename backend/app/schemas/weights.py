from pydantic import BaseModel, Field


class WeightParams(BaseModel):
    w_transport: float = Field(5, ge=0, le=10)
    w_parks: float = Field(4, ge=0, le=10)
    w_education: float = Field(4, ge=0, le=10)
    w_air_quality: float = Field(3, ge=0, le=10)
    w_noise: float = Field(3, ge=0, le=10)
    w_shopping: float = Field(3, ge=0, le=10)
    w_healthcare: float = Field(3, ge=0, le=10)
    w_commute: float = Field(3, ge=0, le=10)

    def normalized(self) -> dict[str, float]:
        raw = {
            "transport": self.w_transport,
            "parks": self.w_parks,
            "education": self.w_education,
            "air_quality": self.w_air_quality,
            "noise": self.w_noise,
            "shopping": self.w_shopping,
            "healthcare": self.w_healthcare,
            "commute": self.w_commute,
        }
        total = sum(raw.values())
        if total == 0:
            return {k: 1.0 / len(raw) for k in raw}
        return {k: v / total for k, v in raw.items()}
