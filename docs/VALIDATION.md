# Repository validation

The standalone repository was checked before its initial upload:

- The offline entry point completed under Python 3.12.7, NumPy 1.26.4, SciPy 1.13.1, and Matplotlib 3.9.2.
- All 106 files in the immutable scientific package matched their SHA-256 manifest before and after reproduction.
- All 44,800 original request payloads were reconstructed and hashed; all 36 planned contrasts, standard errors, degrees of freedom, and uncertainty intervals matched.
- First-attempt sensitivity and acquisition audits reconstructed 14,720 block bounds and replayed 1,012 extracted answers without disagreement.
- The 5,376-request independent diagnostic experiment replayed from the scientific journal and passed a separate scoring and interval implementation.
- All six figure scripts completed. The overview and discovery/validation plot were visually inspected after extraction to the standalone repository. Plot adapters preserve the archived values and introduce no new statistical estimates.
- Python source files passed syntax parsing. No API-token or private-key patterns were found in the upload set. Credentials and account preflights were excluded by construction.
- Reproduction made no API requests. A Python audit hook blocked network connections in analysis subprocesses.

The default command copies data into a new output directory, so replay lock files and generated exports do not alter the immutable inputs. It refuses an existing output directory; use `--output outputs/another_run` for a second verification. User-site packages are disabled in child analyses to prevent accidental mixing of incompatible NumPy/SciPy installations.

Historical collection entry points are included for provenance and inspection; they have not been advertised or tested as fresh end-to-end API runs. Live endpoints, costs, and provider behavior require separate verification before new collection.
