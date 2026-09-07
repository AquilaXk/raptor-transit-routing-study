"""Protect learning resources and links while allowing the curriculum to grow."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = {
    '.github/workflows/ci.yml',
    '.gitignore',
    'LICENSE',
    'README.md',
    'assets/banner.jpg',
    'assets/easysubway_architecture.jpg',
    'assets/profile_breakpoints.png',
    'assets/round_labels.png',
    'assets/round_scan.jpg',
    'assets/service_day_time.jpg',
    'docs/00_why_transit_needs_raptor.md',
    'docs/01_rounds_labels_and_pareto.md',
    'docs/02_marked_route_scanning.md',
    'docs/03_service_days_and_timetables.md',
    'docs/04_easysubway_end_to_end.md',
    'docs/05_transfers_accessibility_and_identity.md',
    'docs/06_departure_profiles_and_reverse_search.md',
    'docs/07_multicriteria_frontiers_and_extensions.md',
    'docs/08_correctness_performance_and_study_plan.md',
    'example_journey_profiles.py',
    'example_routing.py',
    'example_walking_tradeoff.py',
    'notebooks/01_rounds_labels_and_journeys.ipynb',
    'notebooks/02_service_days_and_profiles.ipynb',
    'notebooks/03_frontiers_and_correctness.ipynb',
    'papers/raptor_reading_companion.pdf',
    'pytest.ini',
    'requirements-ci.txt',
    'requirements.txt',
    'src/__init__.py',
    'src/accessibility.py',
    'src/fixtures.py',
    'src/footpaths.py',
    'src/journey.py',
    'src/metrics.py',
    'src/oracle.py',
    'src/pareto.py',
    'src/profile.py',
    'src/raptor.py',
    'src/realtime.py',
    'src/reverse.py',
    'src/round_state.py',
    'src/route_index.py',
    'src/route_scan.py',
    'src/service_time.py',
    'src/timetable.py',
    'tests/test_components.py',
    'tests/test_invariants.py',
    'tests/test_metrics.py',
    'tests/test_oracle.py',
    'tests/test_profiles.py',
    'tests/test_raptor.py',
    'tests/test_structure.py',
    'tests/test_walking_tradeoff.py',
    'tests/test_witness.py',
    'tools/verify_notebooks.py',
}
IGNORED = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ipynb_checkpoints"}

def actual_files():
    return {str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file()
            and not any(part in IGNORED for part in p.relative_to(ROOT).parts)
            and p.name not in {".DS_Store"}}

def test_required_learning_resources_exist():
    assert REQUIRED_FILES <= actual_files()

def test_readme_has_distinct_learning_sections():
    text = (ROOT / "README.md").read_text()
    headings = re.findall(r"^## (.+)$", text, re.M)
    assert headings and len(headings) == len(set(headings))

def test_notebook_structure_has_no_stored_errors():
    # Structural check only. tools/verify_notebooks.py executes fresh kernels in CI.
    for path in (ROOT / "notebooks").glob("*.ipynb"):
        notebook = json.loads(path.read_text())
        code = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
        assert len(code) >= 4
        assert all(output.get("output_type") != "error" for cell in code for output in cell.get("outputs", []))

def test_learning_material_local_links_exist():
    for path in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")),
                 *sorted((ROOT / "notebooks").glob("*.ipynb"))]:
        text = path.read_text()
        if path.suffix == ".ipynb":
            text = "\n".join("".join(cell["source"]) for cell in json.loads(text)["cells"]
                             if cell["cell_type"] == "markdown")
        for link in re.findall(r"\]\(([^)]+)\)", text):
            if not link.startswith(("http://", "https://", "#")):
                assert (path.parent / link.split("#")[0]).exists(), (path, link)

def test_original_pdf_and_image_slots_exist():
    assert (ROOT / "papers/raptor_reading_companion.pdf").read_bytes().startswith(b"%PDF")
    assert list((ROOT / "assets").glob("*.jpg"))
    assert list((ROOT / "assets").glob("*.png"))
