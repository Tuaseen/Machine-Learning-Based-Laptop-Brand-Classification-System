from __future__ import annotations

import os
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, computed_field, model_validator, ConfigDict
from pathlib import Path



model = joblib.load( "brand_prediction_model.joblib")
brand_le = joblib.load("brand_label_encoder.joblib")
FEATURES_PATH = [
    "price",
    "screen_size_in",
    "ram_gb",
    "storage_gb",
    "cpu_tier",
    "dedicated_gpu",
    "is_ssd",
    "performance_score"
]


class BrandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")  

    price: float = Field(..., gt=0)
    screen_size_in: float = Field(..., ge=8, le=25)
    ram_gb: int = Field(..., ge=1, le=256)
    storage_gb: int = Field(..., ge=16, le=8192)
    cpu_tier: int = Field(..., ge=1, le=10)
    is_ssd: int = Field(..., ge=0, le=1)
    dedicated_gpu: int = Field(..., ge=0, le=1)

    @model_validator(mode="after")
    def validate_inputs(self):
        # enforce strict binary
        if self.is_ssd not in (0, 1):
            raise ValueError("is_ssd must be 0 or 1")
        if self.dedicated_gpu not in (0, 1):
            raise ValueError("dedicated_gpu must be 0 or 1")

        # basic sanity (optional, keeps API clean)
        if self.ram_gb > 128 and self.price < 300:
            raise ValueError("price too low for extremely high RAM; check inputs")
        return self

    @computed_field
    @property
    def performance_score(self) -> float:
        # same formula as training
        return (
            2.0 * float(self.ram_gb) +
            1.5 * float(self.cpu_tier) +
            0.002 * float(self.storage_gb) +
            1.0 * float(self.is_ssd) +
            1.5 * float(self.dedicated_gpu)
        )


class BrandResponse(BaseModel):
    predicted_brand: str
    performance_score: float

app = FastAPI(title="Laptop Brand Predictor API", version="1.0.0")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=BrandResponse)
def predict(req: BrandRequest):
    # build exact feature row
    row = {
        "price": req.price,
        "screen_size_in": req.screen_size_in,
        "ram_gb": req.ram_gb,
        "storage_gb": req.storage_gb,
        "cpu_tier": req.cpu_tier,
        "dedicated_gpu": req.dedicated_gpu,
        "is_ssd": req.is_ssd,
        "performance_score": req.performance_score,
    }

    X_user = pd.DataFrame([row])

    # ensure correct order
    try:
        X_user = X_user[FEATURES_PATH]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature schema mismatch: {e}")

    # predict + decode
    try:
        pred_enc = model.predict(X_user)[0]
        pred_brand = brand_le.inverse_transform([pred_enc])[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    return BrandResponse(
        predicted_brand=str(pred_brand),
        performance_score=float(req.performance_score),
    )