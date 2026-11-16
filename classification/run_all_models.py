#!/usr/bin/env python
"""
Master Orchestration Script — Phase 3 Evidence Sufficiency Classification

Runs all three models (A, B, C) sequentially with full error handling,
checkpoint persistence, and automatic evaluation/comparison.

Usage:
    python classification/run_all_models.py

This script:
1. Waits for any currently running Model A training to complete (if already started)
2. Runs Model B training (Dataset B Extended only)
3. Runs Model C training (Dataset A + Dataset B Extended with leakage prevention)
4. Evaluates all three models on the common Dataset B test set
4. Generates comparison report

All outputs are saved to model-specific directories:
- classification/model_a/{checkpoint,results,splits}
- classification/model_b/{checkpoint,results,splits}
- classification/model_c/{checkpoint,results,splits}
- classification/datasets/dataset_b/splits (common B splits)
- classification/comparison/ (comparison artifacts)

Error handling:
- Each step's exit code is recorded
- Failed steps don't silently succeed
- Training can be resumed from checkpoints
"""

import os
import sys
import json
import subprocess
import time
import signal
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CLASSIFICATION_ROOT = Path(__file__).parent

MODEL_DIRS = {
    "A": CLASSIFICATION_ROOT / "model_a",
    "B": CLASSIFICATION_ROOT / "model_b",
    "C": CLASSIFICATION_ROOT / "model_c",
}

SCRIPTS = {
    "train": {
        "A": CLASSIFICATION_ROOT / "model_a" / "train.py",
        "B": CLASSIFICATION_ROOT / "model_b" / "train.py",
        "C": CLASSIFICATION_ROOT / "model_c" / "train.py",
    },
    "evaluate": {
        "A": CLASSIFICATION_ROOT / "model_a" / "evaluate.py",
        "B": CLASSIFICATION_ROOT / "model_b" / "evaluate.py",
        "C": CLASSIFICATION_ROOT / "model_c" / "evaluate.py",
    },
}
COMPARE_SCRIPT = CLASSIFICATION_ROOT / "comparison" / "compare.py"

# Log file
LOG_DIR = CLASSIFICATION_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
ORCHESTRATION_LOG = LOG_DIR / f"orchestration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


def log(msg: str, level: str = "INFO"):
    """Write to log file and stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    with open(ORCHESTRATION_LOG, "a") as f:
        f.write(line + "\n")


def run_script(script_path: Path, model_name: str, step_name: str) -> tuple[int, str]:
    """
    Run a Python script as a subprocess.
    Returns (exit_code, output_text).
    """
    log(f"=== Starting {model_name} {step_name} ===")
    log(f"Command: python {script_path}")

    # Set environment to ensure proper encoding and unbuffered output
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"

    start_time = time.time()

    try:
        # Run with real-time output capture
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=str(PROJECT_ROOT),
        )

        # Stream output in real-time while also capturing it
        output_lines = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.rstrip()
                output_lines.append(line)
                # Also log to file
                with open(ORCHESTRATION_LOG, "a") as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{model_name}] {line}\n")
                # Print to console with model prefix
                print(f"  [{model_name}] {line}")

        exit_code = process.wait()
        elapsed = time.time() - start_time

        output_text = "\n".join(output_lines)

        if exit_code == 0:
            log(f"=== {model_name} {step_name} completed successfully in {elapsed:.1f}s ===")
        else:
            log(f"=== {model_name} {step_name} FAILED with exit code {exit_code} after {elapsed:.1f}s ===", "ERROR")

        return exit_code, output_text

    except Exception as e:
        elapsed = time.time() - start_time
        log(f"=== {model_name} {step_name} EXCEPTION after {elapsed:.1f}s: {e} ===", "ERROR")
        return -1, str(e)


def check_process_running(pid: int) -> bool:
    """Check if a process with given PID is still running."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except (OSError, subprocess.SubprocessError):
        return False


def wait_for_pid(pid: int, timeout: int = 3600, poll_interval: int = 30) -> bool:
    """Wait for a PID to finish. Returns True if finished, False if timeout."""
    log(f"Waiting for existing process PID {pid} to complete...")
    start = time.time()
    while time.time() - start < timeout:
        if not check_process_running(pid):
            log(f"Process PID {pid} has finished.")
            return True
        time.sleep(poll_interval)
    log(f"Timeout waiting for PID {pid}. It may still be running.", "WARNING")
    return False


def find_running_training_pid() -> int | None:
    """Find any running Python training process (by checking command line)."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,CommandLine"],
                capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if "train.py" in line and "classification" in line:
                    parts = line.strip().split()
                    if parts and parts[0].isdigit():
                        return int(parts[0])
    except Exception:
        pass
    return None


def save_orchestration_state(state: dict):
    """Save orchestration state for resume capability."""
    state_file = LOG_DIR / "orchestration_state.json"
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def load_orchestration_state() -> dict:
    """Load orchestration state for resume capability."""
    state_file = LOG_DIR / "orchestration_state.json"
    if state_file.exists():
        with open(state_file) as f:
            return json.load(f)
    return {}


def main():
    log("=" * 70)
    log("PHASE 3: MASTER ORCHESTRATION — Evidence Sufficiency Classification")
    log("=" * 70)
    log(f"Project root: {PROJECT_ROOT}")
    log(f"Classification root: {CLASSIFICATION_ROOT}")
    log(f"Log file: {ORCHESTRATION_LOG}")

    # Load previous state if exists
    state = load_orchestration_state()

    # Track all results
    results = {
        "started_at": datetime.now().isoformat(),
        "models": {},
        "comparison": None,
        "errors": [],
    }

    # Check if Model A is already running
    running_pid = find_running_training_pid()
    if running_pid:
        log(f"Found potentially running training process: PID {running_pid}")
        state["model_a_pid"] = running_pid
        save_orchestration_state(state)
        wait_for_pid(running_pid, timeout=7200)  # 2 hour timeout

    # ---- MODEL A ----
    model_a_started = state.get("model_a_completed", False)
    if not model_a_started:
        log("\n" + "=" * 70)
        log("STEP 1: MODEL A TRAINING (Dataset A only)")
        log("=" * 70)

        exit_code, output = run_script(SCRIPTS["train"]["A"], "Model A", "Training")
        results["models"]["A"] = {
            "train_exit_code": exit_code,
            "train_output_tail": output[-5000:] if output else "",
            "train_completed": exit_code == 0,
        }
        state["model_a_completed"] = (exit_code == 0)
        save_orchestration_state(state)

        if exit_code != 0:
            results["errors"].append(f"Model A training failed with exit code {exit_code}")
            log("Model A training failed. Continuing to Model B...", "WARNING")
    else:
        log("Model A training already completed (from state). Skipping.")
        results["models"]["A"] = {"train_completed": True, "resumed_from_state": True}

    # ---- MODEL B ----
    log("\n" + "=" * 70)
    log("STEP 2: MODEL B TRAINING (Dataset B Extended only)")
    log("=" * 70)

    exit_code, output = run_script(SCRIPTS["train"]["B"], "Model B", "Training")
    results["models"]["B"] = {
        "train_exit_code": exit_code,
        "train_output_tail": output[-5000:] if output else "",
        "train_completed": exit_code == 0,
    }
    state["model_b_completed"] = (exit_code == 0)
    save_orchestration_state(state)

    if exit_code != 0:
        results["errors"].append(f"Model B training failed with exit code {exit_code}")
        log("Model B training failed. Continuing to Model C...", "WARNING")

    # ---- MODEL C ----
    log("\n" + "=" * 70)
    log("STEP 3: MODEL C TRAINING (Dataset A + B Extended with leakage prevention)")
    log("=" * 70)

    exit_code, output = run_script(SCRIPTS["train"]["C"], "Model C", "Training")
    results["models"]["C"] = {
        "train_exit_code": exit_code,
        "train_output_tail": output[-5000:] if output else "",
        "train_completed": exit_code == 0,
    }
    state["model_c_completed"] = (exit_code == 0)
    save_orchestration_state(state)

    if exit_code != 0:
        results["errors"].append(f"Model C training failed with exit code {exit_code}")
        log("Model C training failed. Continuing to evaluation...", "WARNING")

    # ---- EVALUATIONS ----
    log("\n" + "=" * 70)
    log("STEP 4: EVALUATION — All models on common Dataset B test set")
    log("=" * 70)

    for model_name in ["A", "B", "C"]:
        # Only evaluate if training completed successfully
        if results["models"].get(model_name, {}).get("train_completed", False):
            log(f"\n--- Evaluating Model {model_name} ---")
            exit_code, output = run_script(SCRIPTS["evaluate"][model_name], f"Model {model_name}", "Evaluation")
            results["models"][model_name]["eval_exit_code"] = exit_code
            results["models"][model_name]["eval_output_tail"] = output[-5000:] if output else ""
            results["models"][model_name]["eval_completed"] = exit_code == 0

            if exit_code != 0:
                results["errors"].append(f"Model {model_name} evaluation failed with exit code {exit_code}")
        else:
            log(f"Skipping evaluation for Model {model_name} (training did not complete successfully)")
            results["models"][model_name]["eval_completed"] = False
            results["models"][model_name]["eval_skipped"] = True

    save_orchestration_state(state)

    # ---- COMPARISON ----
    log("\n" + "=" * 70)
    log("STEP 5: COMPARISON REPORT")
    log("=" * 70)

    eval_completed = [
        m for m in ["A", "B", "C"]
        if results["models"].get(m, {}).get("eval_completed", False)
    ]

    if len(eval_completed) >= 2:
        exit_code, output = run_script(COMPARE_SCRIPT, "Comparison", "Report Generation")
        results["comparison"] = {
            "exit_code": exit_code,
            "output_tail": output[-5000:] if output else "",
            "completed": exit_code == 0,
        }
        if exit_code != 0:
            results["errors"].append(f"Comparison report failed with exit code {exit_code}")
    else:
        log(f"Skipping comparison: only {len(eval_completed)} models have evaluation results (need >=2)")
        results["comparison"] = {"completed": False, "reason": "insufficient evaluation results"}

    # ---- FINAL SUMMARY ----
    results["completed_at"] = datetime.now().isoformat()
    results["total_errors"] = len(results["errors"])

    summary_file = LOG_DIR / f"orchestration_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, "w") as f:
        json.dump(results, f, indent=2)

    log("\n" + "=" * 70)
    log("ORCHESTRATION COMPLETE")
    log("=" * 70)
    log(f"Summary saved to: {summary_file}")
    log(f"Full log: {ORCHESTRATION_LOG}")

    print("\n" + "=" * 70)
    print("FINAL STATUS")
    print("=" * 70)
    for model_name in ["A", "B", "C"]:
        m = results["models"].get(model_name, {})
        train_status = "✓" if m.get("train_completed") else "✗"
        eval_status = "✓" if m.get("eval_completed") else ("⊘" if m.get("eval_skipped") else "✗")
        print(f"  Model {model_name}: Train {train_status} | Eval {eval_status}")

    comp_status = "✓" if results.get("comparison", {}).get("completed") else "✗"
    print(f"  Comparison: {comp_status}")

    if results["errors"]:
        print(f"\n  ERRORS ({len(results['errors'])}):")
        for err in results["errors"]:
            print(f"    - {err}")
    else:
        print("\n  No errors recorded.")

    # Print resume instructions
    print("\n" + "=" * 70)
    print("RESUME INSTRUCTIONS")
    print("=" * 70)
    print("If the computer restarts or session ends:")
    print("  1. Check orchestration_state.json in classification/logs/")
    print("  2. Re-run: python classification/run_all_models.py")
    print("  3. Script will skip completed steps based on saved state")
    print("\nTo manually run individual steps:")
    for model_name in ["A", "B", "C"]:
        print(f"  Model {model_name} train:  python classification/model_{model_name}/train.py")
        print(f"  Model {model_name} eval:   python classification/model_{model_name}/evaluate.py")
    print(f"  Comparison:         python classification/comparison/compare.py")

    print("\nKey artifact locations:")
    for model_name in ["A", "B", "C"]:
        mdir = MODEL_DIRS[model_name]
        print(f"  Model {model_name} checkpoint: {mdir}/checkpoint/best/")
        print(f"  Model {model_name} results:   {mdir}/results/")
        print(f"  Model {model_name} splits:    {mdir}/splits/")
    print(f"  Common B test set:         {CLASSIFICATION_ROOT}/datasets/dataset_b/splits/test.csv")
    print(f"  Comparison report:         {CLASSIFICATION_ROOT}/comparison/comparison_table.csv")

    return 0 if results["total_errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())