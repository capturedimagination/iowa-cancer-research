"""Synthetic fixtures test scientific data joins and fail-closed analysis gates."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import h5py
import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("signature", ROOT / "scripts/run_gse292469_signature.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class SignatureTests(unittest.TestCase):
    def test_auc_orientation_and_ties(self):
        self.assertEqual(mod.auc(np.array([2., 2.]), np.array([1., 2.])), .75)
        self.assertEqual(mod.auc(np.array([1., 2.]), np.array([2., 2.])), .25)

    def test_exact_canonical_variant_tokens(self):
        self.assertTrue(mod.canonical_variant("E746_A750del; Amplification"))
        self.assertTrue(mod.canonical_variant("L858R, T790M"))
        self.assertFalse(mod.canonical_variant("E746_A750delinsAP"))

    def fixture(self, folder, bad_counts=False, missing_gene=False):
        n = 80
        arr = np.zeros((18, n), dtype=np.int32)
        arr[0, :40] = 1
        arr[:17, 40:] = 1
        arr[17, :] = 100
        mat = csc_matrix(arr)
        barcodes = [f"cell{i}" for i in range(n)]
        names = mod.GENES + ["BACKGROUND"]
        if missing_gene:
            names[0] = "MISSING_SFTPC"
        with h5py.File(folder / "counts.h5", "w") as f:
            m = f.create_group("matrix")
            for key, value in {"data":mat.data, "indices":mat.indices, "indptr":mat.indptr,
                               "shape":mat.shape, "barcodes":np.array(barcodes, dtype="S")}.items():
                m.create_dataset(key, data=value)
            features = m.create_group("features")
            features.create_dataset("name", data=np.array(names, dtype="S"))
            features.create_dataset("id", data=np.array([f"gene{i}" for i in range(18)], dtype="S"))
            features.create_dataset("feature_type", data=np.array(["Gene Expression"]*18, dtype="S"))
        cells = []
        samples = []
        for i in range(4):
            sid = f"sample{i}"
            state = "TN" if i < 2 else "MRD"
            samples.append(dict(sample_id=sid, state=state, histology="LUAD", tissue="Lung",
                                procedure="Biopsy", stage="IV", genotype="L858R",
                                kit_series_implied="v3.1", kit_conflict=False, malignant_nuclei=20))
            for j in range(i*20, (i+1)*20):
                cells.append(dict(cell_id=barcodes[j],sample_id=sid,core_id=sid,
                                  time_point=state,is_tumor_cell=True,
                                  **{"scDblFinder.class":"singlet"},
                                  nCount_RNA=int(arr[:,j].sum()) + int(bad_counts and j == 0),
                                  nFeature_RNA=int(np.count_nonzero(arr[:,j]))))
        # Deliberately reverse metadata row order to test the exact identifier join.
        pd.DataFrame(cells[::-1]).to_csv(folder / "cells.tsv.gz", sep="\t", index=False)
        (folder / "samples.json").write_text(json.dumps({"samples":samples}))
        files = [{"filename":name,"bytes":(folder/name).stat().st_size,"sha256":mod.digest(folder/name)}
                 for name in ("counts.h5", "cells.tsv.gz", "samples.json")]
        (folder / "manifest.json").write_text(json.dumps({"files":files}))
        cmd = [sys.executable, str(ROOT / "scripts/run_gse292469_signature.py"),
               "--h5", str(folder / "counts.h5"), "--cell-metadata", str(folder / "cells.tsv.gz"),
               "--sample-metadata", str(folder / "samples.json"), "--source-manifest", str(folder / "manifest.json"),
               "--out", str(folder / "out")]
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_end_to_end_reordered_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            result = self.fixture(p)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads((p / "out/results.json").read_text())
            scores = json.loads((p / "out/sample-scores.json").read_text())
            self.assertEqual(data["comparisons"]["primary"]["auc_MRD_above_TN"], 1.)
            self.assertEqual(data["comparisons"]["primary"]["n_TN"], 2)
            expected = np.log1p(10000 / 101) / 17
            self.assertAlmostEqual(scores[0]["score_mean"], expected, places=12)

    def test_bad_qc_does_not_release_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            result = self.fixture(p, bad_counts=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Deposited count QC mismatch", result.stderr)
            self.assertFalse((p / "out/results.json").exists())

    def test_missing_gene_does_not_release_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            result = self.fixture(p, missing_gene=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Absent or ambiguous target gene", result.stderr)
            self.assertFalse((p / "out/results.json").exists())


if __name__ == "__main__":
    unittest.main()
