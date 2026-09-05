"""
OceanEmbed — Tests for Training Loss Functions.
"""

import torch
import pytest

from src.training.losses import GaussianNLLLoss, MSELoss


def test_mse_loss():
    loss_fn = MSELoss()
    pred = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    target = torch.tensor([[1.0, 2.0], [3.0, 5.0]])
    loss = loss_fn(pred, target)
    assert torch.isclose(loss, torch.tensor(0.25))


def test_gaussian_nll_loss():
    loss_fn = GaussianNLLLoss()
    mean = torch.tensor([[20.0, 15.0]])
    target = torch.tensor([[20.0, 15.0]])  # zero error
    log_var = torch.tensor([[0.0, 0.0]])   # variance = 1.0

    loss = loss_fn(mean, log_var, target)
    assert torch.isfinite(loss)
    assert loss.item() == pytest.approx(0.0, abs=1e-5)

    # When error increases, loss increases
    bad_mean = torch.tensor([[25.0, 10.0]])
    loss_bad = loss_fn(bad_mean, log_var, target)
    assert loss_bad.item() > loss.item()
