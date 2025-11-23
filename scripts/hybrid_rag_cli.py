#!/usr/bin/env python3
"""Convenience CLI wrapper for Hybrid RAG.

Usage:
  python scripts/hybrid_rag_cli.py "Your question" --entities 5 --docs 5 --hops 1
"""

from rag.hybrid_rag import main


if __name__ == "__main__":
    main()
