"""
basketslr.colab_app
===================
Google Colab entry point mirroring the EmbedSLR pattern:

    !pip install git+https://github.com/s-matysik/BasketSLR.git
    from basketslr.colab_app import run
    run()

Uploads a Scopus CSV, asks for the ARM parameters, runs the full
pipeline and downloads a ZIP with all results. Falls back to a plain
console flow outside Colab.
"""
from __future__ import annotations

import io as _io
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd

from .pipeline import run_analysis

IN_COLAB = "google.colab" in sys.modules


def _params_from_prompts() -> dict:
    ms_raw = input("min_support sigma (float / 'auto') [0.005]: ").strip() \
        or "0.005"
    min_support = ms_raw if ms_raw == "auto" else float(ms_raw)
    gamma = input("min_confidence gamma [0.3]: ").strip() or "0.3"
    max_len = input("max itemset size (0 = unlimited) [4]: ").strip() or "4"
    return {
        "min_support": min_support,
        "min_confidence": float(gamma),
        "max_len": None if max_len == "0" else int(max_len),
    }


# interactive Colab
def _colab_ui(out_dir: Path):
    from google.colab import files  # type: ignore
    from IPython.display import HTML, display

    display(HTML(
        "<h3>BasketSLR - association rules of author keywords</h3>"
        "<ol><li><b>Browse</b> -> Scopus CSV</li><li>Wait for the upload"
        "</li><li>Answer prompts in the console</li></ol>"
    ))
    up = files.upload()
    if not up:
        display(HTML("<b style='color:red'>abort - no file</b>"))
        return
    name, data = next(iter(up.items()))
    df = pd.read_csv(_io.BytesIO(data), low_memory=False)
    display(HTML(f"[ok] Loaded <code>{name}</code> ({len(df)} rows)<br>"))

    params = _params_from_prompts()

    print("[..] Computing ...")
    zip_tmp = run_analysis(df, out=out_dir, **params)

    dst = Path.cwd() / zip_tmp.name
    shutil.copy(zip_tmp, dst)
    print("[ok] Finished - downloading ZIP")
    files.download(str(dst))


# CLI fallback
def _cli(out_dir: Path):
    print("== BasketSLR console ==")
    csv_p = Path(input("CSV path: ").strip())
    df = pd.read_csv(csv_p, low_memory=False)
    params = _params_from_prompts()
    z = run_analysis(df, out=out_dir, **params)
    print("ZIP saved:", z)


# public
def run(save_dir: str | os.PathLike | None = None):
    save_dir = Path(save_dir or tempfile.mkdtemp(prefix="basketslr_"))
    if IN_COLAB:
        from IPython.display import clear_output
        clear_output()
        _colab_ui(save_dir)
    else:
        _cli(save_dir)
