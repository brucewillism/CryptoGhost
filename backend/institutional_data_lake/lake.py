"""CryptoGhost v5 - Institutional Data Lake."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.institutional_data_lake")

LAKE_ROOT = Path("data/lake")


class InstitutionalDataLake:
    """Data lake com Parquet particionado por categoria/symbol/date."""

    CATEGORIES = ("ticks", "orderflow", "macro", "embeddings", "sentiment", "whale", "ai_decisions", "outcomes")

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or LAKE_ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    def _partition_path(self, category: str, symbol: str | None = None) -> Path:
        date = datetime.now(UTC).strftime("%Y-%m-%d")
        sym = (symbol or "global").replace("/", "_")
        path = self.root / category / f"symbol={sym}" / f"date={date}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def ingest_async(self, category: str, data: dict[str, Any], symbol: str | None = None) -> str:
        return self.ingest(category, data, symbol)

    def ingest(self, category: str, data: dict[str, Any], symbol: str | None = None) -> str:
        if category not in self.CATEGORIES:
            logger.warning("unknown_category", category=category)

        path = self._partition_path(category, symbol)
        ts = datetime.now(UTC).strftime("%H%M%S_%f")
        record = {**data, "_ingested_at": datetime.now(UTC).isoformat(), "_symbol": symbol, "_category": category}

        parquet_path = path / f"{ts}.parquet"
        json_path = path / f"{ts}.json"

        try:
            df = pd.DataFrame([record])
            df.to_parquet(parquet_path, compression="snappy", index=False)
            return str(parquet_path)
        except Exception as exc:
            logger.debug("parquet_fallback_json", error=str(exc))
            json_path.write_text(json.dumps(record, default=str), encoding="utf-8")
            return str(json_path)

    def query_recent(self, category: str, symbol: str | None = None, limit: int = 50) -> list[dict]:
        sym = (symbol or "global").replace("/", "_")
        base = self.root / category
        if not base.exists():
            return []

        records: list[dict] = []
        for sym_dir in sorted(base.glob(f"symbol={sym}"), reverse=True):
            for date_dir in sorted(sym_dir.glob("date=*"), reverse=True):
                for f in sorted(date_dir.glob("*.parquet"), reverse=True):
                    try:
                        df = pd.read_parquet(f)
                        records.extend(df.to_dict(orient="records"))
                    except Exception:
                        pass
                    if len(records) >= limit:
                        return records[:limit]
                for f in sorted(date_dir.glob("*.json"), reverse=True):
                    try:
                        records.append(json.loads(f.read_text(encoding="utf-8")))
                    except Exception:
                        pass
                    if len(records) >= limit:
                        return records[:limit]
        return records[:limit]

    def ingest_analysis_bundle(self, symbol: str, v2: dict, quant: dict | None, investment: dict | None) -> None:
        self.ingest("ai_decisions", {"v2": v2, "quant_v3": quant, "investment_v4": investment}, symbol)
        if investment:
            self.ingest("outcomes", {
                "expected_return": investment.get("priority", {}).get("expected_return"),
                "confidence": investment.get("priority", {}).get("confidence"),
            }, symbol)
