"""CryptoGhost v3 - GPU Inference Engine."""

import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn as nn

from backend.shared.logging_config import get_logger
from backend.shared.metrics import AI_LATENCY

logger = get_logger("cryptoghost.gpu_inference")


@dataclass
class GPUStatus:
    available: bool
    device: str
    device_name: str
    vram_total_mb: float
    vram_used_mb: float
    cuda_version: str | None


@dataclass
class InferenceResult:
    predictions: Any
    latency_ms: float
    device: str
    batch_size: int


class GPUInferenceEngine:
    """Inferência acelerada com CUDA, batching e fallback CPU."""

    def __init__(self) -> None:
        self.device = self._select_device()
        self._models: dict[str, nn.Module] = {}
        logger.info("gpu_engine_init", device=str(self.device))

    @staticmethod
    def _select_device() -> torch.device:
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    def get_status(self) -> GPUStatus:
        available = self.device.type != "cpu"
        vram_total, vram_used = 0.0, 0.0
        device_name = "CPU"
        cuda_version = None

        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            vram_total = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
            vram_used = torch.cuda.memory_allocated(0) / 1024 / 1024
            cuda_version = torch.version.cuda

        return GPUStatus(
            available=available,
            device=str(self.device),
            device_name=device_name,
            vram_total_mb=round(vram_total, 1),
            vram_used_mb=round(vram_used, 1),
            cuda_version=cuda_version,
        )

    def register_model(self, name: str, model: nn.Module) -> None:
        model = model.to(self.device)
        if self.device.type == "cuda":
            model = model.half()
        model.eval()
        self._models[name] = model

    @torch.inference_mode()
    def predict_batch(self, model_name: str, inputs: np.ndarray, agent: str = "gpu") -> InferenceResult:
        if model_name not in self._models:
            raise KeyError(f"Model '{model_name}' not registered")

        model = self._models[model_name]
        start = time.perf_counter()

        tensor = torch.from_numpy(inputs.astype(np.float32)).to(self.device)
        if self.device.type == "cuda":
            tensor = tensor.half()

        output = model(tensor)
        if isinstance(output, torch.Tensor):
            predictions = output.cpu().numpy()
        else:
            predictions = output

        latency = (time.perf_counter() - start) * 1000
        AI_LATENCY.labels(agent=agent).observe(latency / 1000)

        return InferenceResult(
            predictions=predictions,
            latency_ms=round(latency, 2),
            device=str(self.device),
            batch_size=len(inputs),
        )

    def quantize_model(self, model: nn.Module) -> nn.Module:
        if self.device.type == "cpu":
            return torch.quantization.quantize_dynamic(model, {nn.Linear}, dtype=torch.qint8)
        return model

    def clear_cache(self) -> None:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


_gpu_engine: GPUInferenceEngine | None = None


def get_gpu_engine() -> GPUInferenceEngine:
    global _gpu_engine
    if _gpu_engine is None:
        _gpu_engine = GPUInferenceEngine()
    return _gpu_engine
