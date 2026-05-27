#!/usr/bin/env python3
"""
Exporte un fichier .vaudtax vers un fichier JSON propre (sans les états UI/navigation).

Usage :
    python export_json.py <fichier.vaudtax> [sortie.json]
    # Si le chemin de sortie est omis, écrit dans <nom>.json
"""

import sys
import json
from pathlib import Path
from parse_vaudtax import open_vaudtax, summarize

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : export_json.py <fichier.vaudtax> [sortie.json]")
        sys.exit(1)

    vaudtax_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else vaudtax_path.with_suffix(".json")

    root, _ = open_vaudtax(vaudtax_path)
    data = summarize(root)

    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Exporté dans {output_path}")
