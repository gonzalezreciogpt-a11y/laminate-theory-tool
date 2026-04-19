from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_DIR = REPO_ROOT / "examples" / "reference_cases"
MATLAB_RUNNER_DIR = REPO_ROOT / "matlab_reference"
DEFAULT_MANIFESTS = (
    "even_case_manifest.json",
    "odd_case_manifest.json",
    "nonsymmetric_case_manifest.json",
)


def build_batch_command(input_path: Path, output_path: Path) -> str:
    input_arg = input_path.as_posix().replace("'", "''")
    output_arg = output_path.as_posix().replace("'", "''")
    add_path = MATLAB_RUNNER_DIR.as_posix().replace("'", "''")
    return (
        f"addpath('{add_path}'); "
        f"run_case_from_json('{input_arg}', '{output_arg}');"
    )


def generate_case(matlab_executable: Path, manifest_name: str) -> Path:
    input_path = REFERENCE_DIR / manifest_name
    output_name = manifest_name.replace("_manifest.json", "_golden.json")
    output_path = REFERENCE_DIR / output_name
    batch_command = build_batch_command(input_path, output_path)
    subprocess.run(
        [str(matlab_executable), "-batch", batch_command],
        cwd=REPO_ROOT,
        check=True,
    )
    normalize_output_json(output_path)
    return output_path


def normalize_output_json(output_path: Path) -> None:
    raw = json.loads(output_path.read_text(encoding="utf-8"))
    normalized = {
        "fiber_assignment": raw["fiber_assignment"],
        "material_ids": raw["material_ids"],
        "theta": raw["theta"],
        "es_simetrico": raw["es_simetrico"],
        "espesor_total_mm": raw["espesor_total"],
        "z_mm": raw["z"],
        "a_matrix": raw["A"],
        "b_matrix": raw["B"],
        "d_matrix": raw["D"],
        "a1_matrix": raw["A1"],
        "d1_matrix": raw["D1"],
        "e11_pa": raw["E11"],
        "e22_pa": raw["E22"],
        "g122_pa": raw["G122"],
        "nu12": raw["nuu12"],
        "nu21": raw["nuu21"],
        "last_nu12_used_for_g12g": raw["last_nu12"],
        "g12g_pa": raw["G12G"],
        "e1_p_manual": raw["E1_P_Manual"],
        "th_fibra_mm": raw["th_Fibra"],
        "elastic_gradient_corrected": raw["Elastic_Gradient_Corregido"],
        "ei_ensayo": raw["EI_ensayo"],
        "e_fibra_ensayo": raw["E_fibra_ensayo"],
        "ei_theory": raw["EI_theory"],
        "elastic_gradient_theory": raw["Elastic_gradient_Theory"],
        "legacy_capa_central_value": raw["legacy_capa_central_value"],
    }
    output_path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate MATLAB goldens from JSON manifests.")
    parser.add_argument(
        "--matlab-executable",
        default=r"C:\Program Files\MATLAB\R2024b\bin\matlab.exe",
        help="Absolute path to matlab.exe",
    )
    parser.add_argument(
        "manifests",
        nargs="*",
        default=list(DEFAULT_MANIFESTS),
        help="Manifest filenames under examples/reference_cases/",
    )
    args = parser.parse_args()

    matlab_executable = Path(args.matlab_executable)
    outputs: list[Path] = []
    for manifest_name in args.manifests:
        outputs.append(generate_case(matlab_executable, manifest_name))

    print(json.dumps([str(path.relative_to(REPO_ROOT)) for path in outputs], indent=2))


if __name__ == "__main__":
    main()
