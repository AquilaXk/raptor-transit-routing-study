"""Execute learning notebooks from clean kernels; never rewrite stored outputs."""
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    paths = sorted((root / "notebooks").glob("*.ipynb"))
    if not paths:
        raise RuntimeError("No learning notebooks found")
    total = 0
    for path in paths:
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        code = [cell for cell in notebook.cells if cell.cell_type == "code"]
        if not code:
            raise RuntimeError(f"No executable cells: {path.name}")
        for cell in code:
            cell.outputs = []
            cell.execution_count = None
        # A temporary cell proves the kernel uses this verification environment.
        # It is never written into the source notebook.
        notebook.cells.insert(0, nbformat.v4.new_code_cell(
            f"import sys\nassert sys.prefix == {sys.prefix!r}, 'Wrong notebook environment'"))
        NotebookClient(notebook, timeout=30, kernel_name="python3",
                       resources={"metadata": {"path": str(root)}}).execute()
        if any(cell.execution_count is None or any(out.output_type == "error" for out in cell.outputs)
               for cell in code):
            raise RuntimeError(f"Incomplete or failed execution: {path.name}")
        total += len(code)
        print(f"PASS {path.name}: {len(code)} code cells", flush=True)
    print(f"Executed {len(paths)} notebooks / {total} learning code cells")


if __name__ == "__main__":
    main()
