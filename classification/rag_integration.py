"""
RAG Integration module for Evidence Sufficiency Classification.

Wraps the existing RAG pipeline (query.py) with an evidence
sufficiency gate that checks whether retrieved evidence is
sufficient before allowing the LLM to generate an answer.

Recovery mechanisms:
  1. Increase top-k retrieval.
  2. Query expansion with related terms.
  3. Abstention if evidence remains insufficient.

Usage:
    python rag_integration.py
"""

import sys
import os
import json
import argparse

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ==========================================
# Sufficiency-Gated RAG Pipeline
# ==========================================

class SufficiencyGatedRAG:
    """
    Enhanced RAG pipeline with evidence sufficiency checking.

    Workflow:
      1. User submits a question.
      2. Retrieve top-k passages from the knowledge base.
      3. Run the sufficiency classifier on (question, evidence).
      4. If sufficient -> generate LLM answer.
      5. If insufficient -> attempt recovery:
         a. Increase top-k and re-retrieve.
         b. If still insufficient, abstain.
      6. Do NOT re-classify unchanged evidence.
    """

    def __init__(
        self,
        model_key: str = "biomedbert",
        initial_top_k: int = 3,
        max_top_k: int = 10,
        sufficiency_threshold: float = 0.5,
    ):
        """
        Args:
            model_key:             Fine-tuned classifier to use.
            initial_top_k:         Initial number of passages to retrieve.
            max_top_k:             Maximum top-k for recovery retrieval.
            sufficiency_threshold: Minimum confidence to accept as sufficient.
        """
        self.model_key = model_key
        self.initial_top_k = initial_top_k
        self.max_top_k = max_top_k
        self.sufficiency_threshold = sufficiency_threshold

        # Lazy-load components to avoid loading everything at import time
        self._query_module = None
        self._classifier = None

    def _get_query_module(self):
        """Lazy-load the existing query module."""
        if self._query_module is None:
            # Import the existing query module
            import query as query_module
            self._query_module = query_module
        return self._query_module

    def _get_classifier(self):
        """Lazy-load the sufficiency classifier."""
        if self._classifier is None:
            from classification.inference import predict_sufficiency
            self._classifier = predict_sufficiency
        return self._classifier

    def _extract_evidence(self, results: dict) -> str:
        """
        Extract and combine retrieved passages from ChromaDB results.

        Args:
            results: ChromaDB query results dict.

        Returns:
            Combined evidence string from all retrieved documents.
        """
        docs = results.get("documents", [[]])[0]
        if not docs:
            return ""

        # Combine all retrieved passages with document markers
        evidence_parts = []
        for i, doc in enumerate(docs):
            evidence_parts.append(f"[Passage {i+1}]: {doc}")

        return " ".join(evidence_parts)

    def _check_sufficiency(self, question: str, evidence: str) -> dict:
        """
        Run the sufficiency classifier on question + evidence.

        Returns classifier result dict.
        """
        classifier = self._get_classifier()
        return classifier(
            question=question,
            retrieved_evidence=evidence,
            model_key=self.model_key,
        )

    def query(self, question: str) -> dict:
        """
        Run the full sufficiency-gated RAG pipeline.

        Args:
            question: The user's question.

        Returns:
            dict with:
              - question: The original question.
              - answer: The generated answer or abstention message.
              - evidence: The retrieved evidence text.
              - sufficiency: Classifier result dict.
              - retrieval_attempts: Number of retrieval rounds.
              - top_k_used: The final top-k value used.
              - sources: List of source documents.
              - abstained: Whether the system abstained.
        """
        qm = self._get_query_module()

        # Step 1: Initial retrieval
        current_top_k = self.initial_top_k
        results = qm.search(question, top_k=current_top_k)
        evidence = self._extract_evidence(results)
        retrieval_attempts = 1

        # Step 2: Check sufficiency
        sufficiency_result = self._check_sufficiency(question, evidence)

        # Step 3: Recovery loop if insufficient
        previous_evidence = None
        while (
            sufficiency_result["label"] == 0
            and current_top_k < self.max_top_k
        ):
            # Increase top-k
            current_top_k = min(current_top_k + 3, self.max_top_k)
            results = qm.search(question, top_k=current_top_k)
            new_evidence = self._extract_evidence(results)
            retrieval_attempts += 1

            # Do NOT re-classify unchanged evidence
            if new_evidence == evidence:
                break

            evidence = new_evidence
            sufficiency_result = self._check_sufficiency(question, evidence)

        # Step 4: Generate answer or abstain
        sources = []
        if results.get("metadatas") and results["metadatas"][0]:
            sources = [
                m.get("source", "Unknown")
                for m in results["metadatas"][0]
            ]

        if sufficiency_result["label"] == 1:
            # Evidence is sufficient -> generate LLM answer
            answer = qm.generate_rag_response(
                question, results, qm.GROQ_API_KEY
            )
            abstained = False
        else:
            # Evidence is insufficient -> abstain
            answer = (
                "I'm unable to provide a reliable answer to this question "
                "based on the available evidence in the knowledge base. "
                "The retrieved documents do not contain sufficient information "
                "to address your question accurately. Please consult a "
                "healthcare professional or refer to authoritative diabetes "
                "guidelines for children and adolescents."
            )
            abstained = True

        return {
            "question": question,
            "answer": answer,
            "evidence": evidence,
            "sufficiency": sufficiency_result,
            "retrieval_attempts": retrieval_attempts,
            "top_k_used": current_top_k,
            "sources": sources,
            "abstained": abstained,
        }

    def display_result(self, result: dict) -> None:
        """Pretty-print a query result."""
        print("=" * 60)
        print(f"QUESTION: {result['question']}")
        print("=" * 60)

        suff = result["sufficiency"]
        print(f"\n--- Evidence Sufficiency ---")
        print(f"  Prediction:  {suff['prediction']}")
        print(f"  Confidence:  {suff['confidence']:.4f}")
        print(f"  Scores:      {suff['scores']}")
        print(f"  Attempts:    {result['retrieval_attempts']}")
        print(f"  Top-K Used:  {result['top_k_used']}")
        print(f"  Abstained:   {result['abstained']}")

        print(f"\n--- Sources ---")
        for i, src in enumerate(result["sources"], 1):
            print(f"  {i}. {src}")

        print(f"\n--- Answer ---")
        print(result["answer"])
        print("=" * 60)


# ==========================================
# Interactive Loop
# ==========================================

def parse_args():
    parser = argparse.ArgumentParser(description="Sufficiency-Gated RAG Pipeline")
    parser.add_argument(
        "--question", "-q",
        type=str,
        default=None,
        help="Question to query (runs single query instead of interactive loop)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="biomedbert",
        help="Classifier model to use (default: biomedbert)",
    )
    parser.add_argument(
        "--initial_top_k",
        type=int,
        default=3,
        help="Initial top-k retrieval count (default: 3)",
    )
    parser.add_argument(
        "--max_top_k",
        type=int,
        default=10,
        help="Maximum top-k retrieval count for recovery (default: 10)",
    )
    return parser.parse_args()


def main():
    """Run the sufficiency-gated RAG pipeline interactively or via CLI."""
    args = parse_args()

    rag = SufficiencyGatedRAG(
        model_key=args.model,
        initial_top_k=args.initial_top_k,
        max_top_k=args.max_top_k,
    )

    if args.question:
        result = rag.query(args.question)
        rag.display_result(result)
        return

    print("=" * 60)
    print("Diabetes Knowledge Base — Sufficiency-Gated RAG")
    print("Type 'quit' or 'exit' to stop.")
    print("=" * 60)

    while True:
        print()
        question = input("Your question: ").strip()

        if not question:
            print("  (Please enter a question)")
            continue

        if question.lower() in ("quit", "exit", "q"):
            print("\nGoodbye!")
            break

        result = rag.query(question)
        rag.display_result(result)


if __name__ == "__main__":
    main()
