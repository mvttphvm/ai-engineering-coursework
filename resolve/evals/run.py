"""Eval harness runner — Layer 3.

    python -m evals.run                # offline: retrieval metrics for all
                                       # golden items + answer checks with
                                       # keyword faithfulness (fake provider)
    python -m evals.run --judge        # also run LLM-as-judge faithfulness
                                       # via whichever provider is configured
                                       # (Gemini/Groq free tiers, or Ollama)

The harness ingests the sample KB, runs every golden question through the
real search pipeline, and reports per-item and average recall@k, MRR, and
answer faithfulness. Wire the averages into CI as a regression gate: fail
the build if recall@5 or MRR drops below the thresholds in THRESHOLDS.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import rag  # noqa: E402
from app.config import Settings  # noqa: E402
from app.ingestion.pipeline import ingest_directory  # noqa: E402
from app.providers.factory import generate_with_fallback  # noqa: E402
from app.retrieval.embeddings import FakeEmbedder  # noqa: E402
from app.retrieval.search import HybridSearcher  # noqa: E402
from app.retrieval.store import InMemoryStore  # noqa: E402
from evals.metrics import keyword_faithfulness, recall_at_k, reciprocal_rank  # noqa: E402

THRESHOLDS = {"recall@5": 0.90, "mrr": 0.70}
TOP_K = 5

_JUDGE_PROMPT = """You are grading a support answer for faithfulness.
Answer ONLY "FAITHFUL" if every factual claim in the answer is supported by
the source excerpt, or "UNFAITHFUL" if it invents anything.

Source excerpt:
{source}

Answer:
{answer}"""


def load_golden(path: Path) -> list[dict]:
    items = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Resolve eval harness")
    parser.add_argument("--judge", action="store_true",
                        help="Also run LLM-as-judge faithfulness (needs a "
                             "configured provider; skipped gracefully without)")
    parser.add_argument("--golden", default=str(Path(__file__).parent / "golden.jsonl"))
    parser.add_argument("--kb", default=str(PROJECT_ROOT / "data" / "sample_kb"))
    args = parser.parse_args()

    settings = Settings.from_env()
    # Answers in the offline harness come from the deterministic fake
    # provider unless keys are configured; force fake for reproducibility
    # when no real provider is available.
    eval_settings = Settings.from_env()
    if not (eval_settings.gemini_api_key or eval_settings.groq_api_key):
        eval_settings.llm_provider = "fake"
        eval_settings.llm_fallbacks = ""

    store = InMemoryStore()
    embedder = FakeEmbedder()
    stats = ingest_directory(args.kb, store, embedder,
                             settings.chunk_size, settings.chunk_overlap)
    print(f"KB: {stats['documents']} documents, {stats['chunks']} chunks\n")
    searcher = HybridSearcher(store=store, embedder=embedder)

    golden = load_golden(Path(args.golden))
    rows = []
    totals = {"recall": 0.0, "rr": 0.0, "faith": 0.0, "judge": 0.0}
    judge_count = 0

    header = f"{'#':>2}  {'recall@5':>8}  {'RR':>5}  {'faith':>5}  {'judge':>5}  question"
    print(header)
    print("-" * len(header))
    for i, item in enumerate(golden, start=1):
        results = searcher.search(item["question"], top_k=TOP_K)
        retrieved_sources = [r.chunk.source for r in results]
        rec = recall_at_k(retrieved_sources, item["expected_sources"], TOP_K)
        rr = reciprocal_rank(retrieved_sources, item["expected_sources"])

        answer = rag.ask(item["question"], searcher, eval_settings, top_k=TOP_K)
        faith = 0.0 if answer.refused else keyword_faithfulness(
            answer.answer, item.get("expected_keywords", []))

        judge_score = None
        if args.judge and not answer.refused and results:
            try:
                verdict, _ = generate_with_fallback(
                    settings,
                    _JUDGE_PROMPT.format(source=results[0].chunk.text,
                                         answer=answer.answer),
                )
                judge_score = 1.0 if verdict.strip().upper().startswith("FAITHFUL") else 0.0
                totals["judge"] += judge_score
                judge_count += 1
            except Exception as exc:  # no provider configured — skip quietly
                print(f"    (judge skipped: {exc})")
                args.judge = False

        totals["recall"] += rec
        totals["rr"] += rr
        totals["faith"] += faith
        rows.append((rec, rr, faith))
        judge_cell = "-" if judge_score is None else f"{judge_score:.0f}"
        print(f"{i:>2}  {rec:>8.2f}  {rr:>5.2f}  {faith:>5.2f}  {judge_cell:>5}  "
              f"{item['question'][:64]}")

    n = len(golden)
    avg_recall = totals["recall"] / n
    avg_rr = totals["rr"] / n
    avg_faith = totals["faith"] / n
    print("-" * len(header))
    print(f"AVERAGES over {n} golden items:  recall@{TOP_K}={avg_recall:.3f}  "
          f"MRR={avg_rr:.3f}  faithfulness(keywords)={avg_faith:.3f}")
    if judge_count:
        print(f"LLM judge faithfulness: {totals['judge'] / judge_count:.3f} "
              f"over {judge_count} judged answers")

    ok = avg_recall >= THRESHOLDS["recall@5"] and avg_rr >= THRESHOLDS["mrr"]
    print(f"Regression gate (recall@5 >= {THRESHOLDS['recall@5']}, "
          f"MRR >= {THRESHOLDS['mrr']}): {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
