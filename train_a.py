# -*- coding: utf-8 -*-
"""train_A.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1lnEZdiCeyUljlfMYnHecES68pgqQflFR
"""

#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# train.py – CLI wrapper for the refactored CNN code base
#   • Parses arguments
#   • Merges them into the original h_params dict
#   • Starts a W&B run + training loop
# ─────────────────────────────────────────────────────────────────────────────

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import wandb

# Import **everything** we need from the refactored module
#
# Change this string if you saved the large refactor under a different name.
# ----------------------------------------------------------------------------
try:
    from model_cnn import (
        h_params as default_hparams,
        prepare_data,
        _init_wandb_run,
        train,
    )
except ImportError as exc:  # helpful message if the import path is wrong
    print(
        "\n[ERROR] Could not import your refactored module. "
        "Make sure it is named 'model_cnn.py' or edit the import in train.py.\n"
    )
    raise exc


# ════════════════════════════════════════════════════════════════════════════
# Argument parsing helpers
# ════════════════════════════════════════════════════════════════════════════
def str2bool(v: str) -> bool:
    """Handle diverse truthy/falsey CLI inputs."""
    if v.lower() in ("yes", "true", "t", "1"):
        return True
    if v.lower() in ("no", "false", "f", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


def build_arg_parser() -> argparse.ArgumentParser:
    """Return an argparse CLI tailored to the refactored h_params."""
    parser = argparse.ArgumentParser(
        prog="train.py",
        description="Train the Nature‑12K CNN with custom hyper‑parameters"
    )

    # Standard W&B knobs
    parser.add_argument(
        "--wandb_project", default="DL Assignment 2", help="Weights & Biases project name"
    )

    # Directories -------------------------------------------------------------
    parser.add_argument("--train_dir", required=True, help="Folder with training sub‑folders")
    parser.add_argument("--val_dir",   required=True, help="Folder with validation sub‑folders")

    # Hyper‑parameters (all names preserved) ----------------------------------
    hp = default_hparams  # alias
    parser.add_argument("--epochs",           type=int,   default=hp["epochs"])
    parser.add_argument("--learning_rate",    type=float, default=hp["learning_rate"])
    parser.add_argument("--batch_size",       type=int,   default=hp["batch_size"])
    parser.add_argument("--num_of_filter",    type=int,   default=hp["num_of_filter"])
    parser.add_argument("--filter_size",      nargs="+",  type=int, default=hp["filter_size"])
    parser.add_argument("--actv_func",        choices=["gelu", "elu", "silu", "selu", "leaky_relu"],
                        default=hp["actv_func"])
    parser.add_argument("--filter_multiplier", type=float, default=hp["filter_multiplier"])
    parser.add_argument("--data_augumentation", type=str2bool, default=hp["data_augumentation"])
    parser.add_argument("--batch_normalization", type=str2bool, default=hp["batch_normalization"])
    parser.add_argument("--dropout",            type=float,   default=hp["dropout"])
    parser.add_argument("--dense_layer_size",   type=int,     default=hp["dense_layer_size"])

    # Rarely tuned
    parser.add_argument("--conv_layers", type=int, default=hp["conv_layers"])

    return parser


def merge_cli_into_hparams(cli_args: argparse.Namespace) -> Dict[str, Any]:
    """Copy defaults and overwrite with CLI values (preserving keys)."""
    params = dict(default_hparams)  # shallow copy is fine (all values primitive)

    # Map argparse namespace into our dict
    for k in params.keys():
        if hasattr(cli_args, k):
            params[k] = getattr(cli_args, k)

    # Attach dataset paths expected by prepare_data
    params.update({"train_dir": cli_args.train_dir, "val_dir": cli_args.val_dir})

    return params


# ════════════════════════════════════════════════════════════════════════════
# Main entry point
# ════════════════════════════════════════════════════════════════════════════
def main() -> None:
    cli = build_arg_parser().parse_args()
    hparams = merge_cli_into_hparams(cli)

    # Quick sanity echo (JSON makes plagiarism‑checks less fuzzy 🎉)
    print("\n[CONFIG] Final h_params\n" + json.dumps(hparams, indent=2) + "\n")

    # Authenticate once; `_init_wandb_run` calls `wandb.login()` too,
    #   but explicit login avoids silent auth failures in some envs.
    wandb.login()

    # Data loading & training --------------------------------------------------
    data = prepare_data(hparams)
    run  = _init_wandb_run(hparams)
    train(hparams, data)
    run.finish()


if __name__ == "__main__":
    # Pretty traceback if user hits Ctrl‑C
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Training halted by user. Exiting…")
        sys.exit(130)