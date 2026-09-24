"""Tests for chronological walk-forward splitting."""

import pandas as pd
import pytest
from src.utils.walk_forward import walk_forward_splits

def test_splits_are_chronological_and_non_overlapping():
    index = pd.date_range("2020-01-01", periods=20, freq="D")
    splits = list(walk_forward_splits(index, train_size=8, test_size=4, step_size=4, embargo=1))
    assert len(splits) == 2
    assert splits[0].train[-1] < splits[0].test[0]
    assert set(splits[0].train).isdisjoint(set(splits[0].test))

def test_unsorted_index_rejected():
    index = pd.date_range("2020-01-01", periods=5, freq="D")[::-1]
    with pytest.raises(ValueError, match="sorted"):
        list(walk_forward_splits(index, train_size=2, test_size=1))
