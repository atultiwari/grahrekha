"""Export every contract as JSON Schema.

Usage: `python -m grahrekha_engine.contracts.export OUT_DIR`
"""

import json
import sys
from pathlib import Path

from grahrekha_engine.contracts import CONTRACTS


def export_schemas(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, model in CONTRACTS:
        path = out_dir / f"{name}.json"
        # Serialization mode: fields with defaults are always present in responses, so
        # they are required in the generated TypeScript types.
        schema = model.model_json_schema(mode="serialization")
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
        written.append(path)
    return written


if __name__ == "__main__":  # pragma: no cover
    for path in export_schemas(Path(sys.argv[1])):
        print(path)
