"""Model B evaluate script."""
import sys
from pathlib import Path
CLS_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CLS_ROOT.parent))
from classification.common.evaluation import evaluate

if __name__ == "__main__":
    evaluate(
        model_dir=Path(__file__).parent / "checkpoint",
        results_dir=Path(__file__).parent / "results",
        model_name="Model B (Dataset B only)",
        max_length=512,
    )
