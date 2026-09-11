# Kaggle release runbook

Verified against Kaggle CLI 2.2.4 on Windows on 2026-09-11 and the current official `datasets_metadata.md` documentation.

## Preflight

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
kaggle --version
kaggle datasets create -h
kaggle datasets version -h
kaggle datasets metadata -h
kaggle datasets status -h
kaggle kernels push -h
```

`dataset-metadata.json` is written by Python as UTF-8 without BOM. The release directory contains only `data.csv`, `dataset-metadata.json`, and `dataset-cover-image.png`; Kaggle treats the conventional cover image as metadata rather than a data file.

## Dataset create/update

First release:

```powershell
kaggle datasets create -p release -u
```

Real content updates only:

```powershell
kaggle datasets version -p release -m "Refresh from latest NHTSA current SGO files"
```

After every write, authoritative readback is required:

```powershell
kaggle datasets status taeyangg4/nhtsa-autonomous-driving-crashes
kaggle datasets files taeyangg4/nhtsa-autonomous-driving-crashes
kaggle datasets metadata taeyangg4/nhtsa-autonomous-driving-crashes -p state\kaggle_readback
```

If a metadata-only change is necessary, make one `kaggle datasets metadata --update` attempt and immediately download live metadata. If the CLI returns a client/parsing error but live state already matches, do not retry or create a new dataset version.

## Column descriptions

The current Kaggle metadata spec requires *all* fields in exact file order for schema matching. `src/build_product.py` generates 123 field descriptors in exact `data.csv` order from `qa/column_mapping.json`. After upload, compare the live resource schema/order and description coverage before changing anything.

## Notebook

```powershell
kaggle kernels push -p notebooks
kaggle kernels status taeyangg4/what-do-reported-autonomous-driving-crashes-look-like
```

Only declare the notebook complete after Kaggle reports a successful run. If it fails, inspect `kaggle kernels logs` and fix the notebook rather than recreating unrelated dataset metadata.

## Final live gate

Confirm current version ready, only intended live data file, title/subtitle/overview, one file description, 123/123 column descriptions, usability target, notebook complete, live cover/card crop, clean Git state, and manifest Git SHA/hash reconciliation.
