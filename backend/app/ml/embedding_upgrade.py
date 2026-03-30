"""Optional upgrade path: semantic embeddings for higher-quality symptom classification.

Usage (after installing sentence-transformers + torch):
    python -m app.ml.embedding_upgrade

This script is intentionally lightweight to keep default setup dependency-free.
"""

from __future__ import annotations


def main() -> None:
    print(
        'Embedding upgrade placeholder: install sentence-transformers and implement classifier '\
        'using sentence embeddings + linear head for production improvements.'
    )


if __name__ == '__main__':
    main()
