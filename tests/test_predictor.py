"""Unit tests for the signal predictor."""

import pandas as pd
import numpy as np
import pytest
from src.features.engineer import FeatureEngineer
from src.models.predictor import SignalPredictor


@pytest.fixture
def featured_data():
    dates = pd.date_range("2019-01-01", periods=300, freq="B")
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(300) * 0.8)
    df = pd.DataFrame(
        {
            "Open": close + np.random.randn(300) * 0.2,
            "High": close + np.random.rand(300) * 1.5,
            "Low": close - np.random.rand(300) * 1.5,
            "Close": close,
            "Volume": np.random.randint(1e6, 5e6, 300),
            "Adj Close": close,
        },
        index=dates,
    )
    eng = FeatureEngineer()
    return eng.transform(df)


def test_predictor_fit_and_predict(featured_data):
    eng = FeatureEngineer()
    feature_cols = eng.get_feature_columns(featured_data)

    model = SignalPredictor(model_type="random_forest", target_horizon=5, random_state=42)
    metrics = model.fit(featured_data, feature_cols, test_size=0.25)

    assert "accuracy" in metrics
    assert "roc_auc" in metrics
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert model.is_fitted

    proba = model.predict_proba(featured_data.dropna(subset=feature_cols))
    assert len(proba) > 0
    assert proba.between(0, 1).all()


def test_predictor_save_load(tmp_path, featured_data):
    eng = FeatureEngineer()
    feature_cols = eng.get_feature_columns(featured_data)

    model = SignalPredictor(model_type="logistic", target_horizon=3)
    model.fit(featured_data, feature_cols)

    path = tmp_path / "test_model.joblib"
    model.save(path)

    model2 = SignalPredictor()
    model2.load(path)
    assert model2.is_fitted
    assert model2.feature_names == model.feature_names
