"""Tests for shared/semantic_store.py — Chroma-backed long-term memory."""

import os
import tempfile

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORY_CHROMA_PATH", str(tmp_path / "chroma"))
    from shared.semantic_store import SemanticStore
    return SemanticStore(persist_directory=str(tmp_path / "chroma"))


class TestSemanticStoreRoundtrip:
    def test_put_then_get(self, store):
        ns = ("student_profile", "alice")
        store.put(ns, "fact1", {"content": "Alice struggles with chain rule"})
        rec = store.get(ns, "fact1")
        assert rec is not None
        assert "chain rule" in rec.value["content"]

    def test_prefix_scan_search(self, store):
        ns = ("student_profile", "bob")
        store.put(ns, "a", {"content": "knows linear algebra"})
        store.put(ns, "b", {"content": "needs help with limits"})
        res = store.search(ns)
        contents = [r.value["content"] for r in res]
        assert "knows linear algebra" in contents
        assert "needs help with limits" in contents

    def test_semantic_search_prioritizes_relevant(self, store):
        ns = ("student_profile", "carol")
        store.put(ns, "math", {"content": "Carol struggles with chain rule of derivatives"})
        store.put(ns, "ml", {"content": "Carol is advanced in CNNs and computer vision"})
        store.put(ns, "py", {"content": "Carol knows Python decorators"})

        res = store.search(ns, query="calculus derivative", limit=3)
        assert len(res) > 0
        assert "chain rule" in res[0].value["content"]

    def test_delete_removes_fact(self, store):
        ns = ("student_profile", "dan")
        store.put(ns, "x", {"content": "temporary fact"})
        assert store.get(ns, "x") is not None
        store.delete(ns, "x")
        assert store.get(ns, "x") is None

    def test_namespace_isolation(self, store):
        a = ("student_profile", "alice")
        b = ("student_profile", "bob")
        store.put(a, "f", {"content": "alice-only fact"})
        store.put(b, "f", {"content": "bob-only fact"})
        a_res = store.search(a)
        b_res = store.search(b)
        assert all("alice-only" in r.value["content"] for r in a_res)
        assert all("bob-only" in r.value["content"] for r in b_res)
