# Clean complete Monte Carlo reproduction

**All scientific results reproduced exactly.** A fresh isolated copy ran all 72 frozen cases: 720,000 prospective founders and 48,568,750 generated cells. It exited with code 0 and passed all 28 deterministic implementation fixtures. No original result or checkpoint was provided as simulation input.

The rerun used byte-identical simulator and protocol files, the original case seeds, 250-founder batches, Python 3.12.14, NumPy 2.3.5 and SciPy 1.16.3. Only those two source files were present when the isolated copy was prepared. All original code, results, checkpoints and the comparator remained unchanged. Actual local command/execution records and raw checkpoints remain in ignored temporary storage; their hashes and project-relative locations are recorded in [monte-carlo-reproduction.json](monte-carlo-reproduction.json).

## What was compared

The comparison checked the complete public result, all 72 per-case aggregates, the run manifest, fixture report, all 2,880 checkpoint metadata records, and **31,680 arrays containing 27,560,400 elements**. Array payloads total 149,503,200 bytes per run. Every stored founder-level quantity, query-time array, RNG state, founder type/stage, chronological weight, subtree count, eligibility flag, event-count summary and resource diagnostic was included. Checkpoints retain those observations and summaries; individual latent cell-event records are not retained.

Arrays matched in dtype, shape and C-order raw bytes, including signed zeros and NaN payload bytes. There was no floating-point tolerance or equal-NaN shortcut. JSON scientific values and numeric types matched exactly. Every recorded checkpoint checksum was checked against its corresponding actual file. There were **zero scientific differences**.

Only these exact metadata positions were excluded from scientific equality:

| File | Excluded JSON paths |
|---|---|
| Public result | `/created_utc`, `/cases/*/created_utc`, `/cases/*/runtime_seconds_this_invocation`, `/cases/*/batch_files/*/sha256` |
| Per-case aggregate | `/created_utc`, `/runtime_seconds_this_invocation`, `/batch_files/*/sha256` |
| Run manifest and fixture report | `/created_utc` |
| Decoded checkpoint metadata | `/created_utc` |

The audit examined all 8,931 excluded field occurrences: 3,027 creation timestamps, 144 runtimes and 5,760 checkpoint checksum references across the public and per-case aggregate copies. All changed as expected between runs. All 2,880 checkpoint container checksums differed; they were accepted only after every decoded array byte and every other metadata field matched. Checkpoint timestamps and container clock metadata are not scientific observations. The complete ignored-field ledger retains each file, JSON pointer and both values; nothing was assumed equal because it was inconvenient to compare.

## Pinned inputs and outputs

| Artifact | SHA-256 |
|---|---|
| Simulator | `cbbdb12707fb55641bd2701a3be0c862f4f47d0b758bec7b829239cb6f084c46` |
| Frozen protocol | `e7fe08e71d614f27f7d312a6afa7cf64d8022cba2af908cc92c7965d7d6caeb5` |
| Original public result | `3ab903e06c5a7ba80b0ca59b12cc6e9a56ad0fa62bbe6ca42f3492293ff21adb` |
| Rerun public result | `56f3b607cefbfeb01ece38e1ab037c3d435a8139b76bf9f8b8fa6f2b8b686b94` |
| Public result after the exact exclusions above, both runs | `f8196850896d4766f8e2993c98f13a1494616a02699a7377323342f236f8930b` |
| Scientific checkpoint ledger, both runs | `af65f6439267bf65b3714a72a551a4bc1b3fec4f385ad452079e34638296bf55` |

The companion JSON includes every per-case aggregate hash, normalized aggregate hash and scientific checkpoint digest. The ledger digest below can be recreated from a new run without publishing the original founder-level arrays.

## Portable rerun and digest check

From the project root, use a Python interpreter with the pinned versions above. The following prepares a fresh root without copying any outcomes:

```sh
repro_root="$(mktemp -d)"
repro_base="research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity"
mkdir -p "$repro_root/scripts" "$repro_root/$repro_base"
cp scripts/simulate_age_lineage_trees.py "$repro_root/scripts/"
cp "$repro_base/protocol.json" "$repro_root/$repro_base/"
cd "$repro_root"
python scripts/simulate_age_lineage_trees.py --run --fixture-report fixture-report.json
```

The actual clean run used that simulator invocation and exited 0. It required about 8.24 seconds on this run's host; runtime is not a performance guarantee. Preserve the fresh root for the following scientific digest calculation:

```python
from pathlib import Path
import hashlib, json, struct
import numpy as np

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

local = Path("tmp/age-lineage-2026-11-10/monte-carlo")
manifest = json.loads((local / "run-manifest.json").read_text())
cases = []
for case_id in manifest["case_ids"]:
    batches = []
    for path in sorted((local / case_id / "batches").glob("*.npz")):
        with np.load(path, allow_pickle=False) as data:
            payload = hashlib.sha256()
            for key in sorted(k for k in data.files if k != "metadata"):
                array = data[key]
                header = canonical({"key": key, "dtype": array.dtype.str,
                                    "shape": list(array.shape)})
                raw = array.tobytes(order="C")
                payload.update(struct.pack(">Q", len(header)))
                payload.update(header)
                payload.update(struct.pack(">Q", len(raw)))
                payload.update(raw)
            metadata = json.loads(str(data["metadata"]))
            del metadata["created_utc"]
            batches.append({"path": str(path),
                            "array_payload_sha256": payload.hexdigest(),
                            "metadata_without_created_utc_sha256": digest(metadata)})
    cases.append({"case_id": case_id,
                  "checkpoint_scientific_ledger_sha256": digest(batches)})
print(digest(cases))
```

Expected digest in the reproduced environment: `af65f6439267bf65b3714a72a551a4bc1b3fec4f385ad452079e34638296bf55`. The exact Python block above was executed against the clean rerun, exited 0 and produced that digest. This is a same-code, same-environment reproduction; it does not promise bit identity across dependency versions, numerical libraries or hardware.

Exact reproduction preserves the original comparison flags. It does not resolve the two flagged contrast MCSE diagnostics, establish a Gaussian approximation for sparse contributions, or convert synthetic model behavior into biological evidence. Those findings remain in their separate comparison and diagnostic reports.
