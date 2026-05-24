"""Testes do GPU Inference Engine v3."""

import numpy as np
import torch
import torch.nn as nn

from backend.gpu_inference.engine import GPUInferenceEngine


class TinyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(4, 2)

    def forward(self, x):
        return self.fc(x)


def test_gpu_status():
    engine = GPUInferenceEngine()
    status = engine.get_status()
    assert status.device in ("cpu", "cuda", "mps")
    assert status.vram_total_mb >= 0


def test_predict_batch():
    engine = GPUInferenceEngine()
    model = TinyModel()
    engine.register_model("test", model)
    inputs = np.random.randn(8, 4).astype(np.float32)
    result = engine.predict_batch("test", inputs, agent="test_gpu")
    assert result.batch_size == 8
    assert result.latency_ms >= 0
    assert result.predictions.shape[0] == 8
