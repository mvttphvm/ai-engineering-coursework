"""Hybrid search ranking over the real sample KB (fake embedder, offline)."""


def test_password_query_ranks_password_article_first(searcher):
    results = searcher.search("How do I reset my forgotten password?", top_k=3)
    assert results, "expected results"
    assert results[0].chunk.source == "password-reset.md"


def test_refund_query_ranks_refund_article_first(searcher):
    results = searcher.search("How long does a refund take to appear?", top_k=3)
    assert results[0].chunk.source == "refunds.md"


def test_exact_terms_found_by_keyword_leg(searcher):
    # "429" and "Retry-After" are exact-term queries: the keyword leg's job.
    results = searcher.search("429 Too Many Requests Retry-After header", top_k=3)
    assert any(r.chunk.source == "api-keys.md" for r in results)
    top = results[0]
    assert top.keyword_rank is not None


def test_unrelated_query_returns_nothing_strong(searcher):
    results = searcher.search("zanzibar quantum banana helicopter recipe", top_k=5)
    # RRF only returns chunks with a positive leg score; anything returned
    # must have ~zero cosine so the /ask evidence gate can refuse.
    assert all(r.cosine < 0.2 for r in results)


def test_search_results_have_ranks_and_scores(searcher):
    results = searcher.search("delete my account permanently", top_k=3)
    assert results[0].chunk.source == "delete-account.md"
    for r in results:
        assert r.score > 0
        assert r.vector_rank is not None or r.keyword_rank is not None
