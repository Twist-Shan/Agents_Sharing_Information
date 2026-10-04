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

## Targeted follow-up revision

The extended root workflow passed in a clean output copy with network connections blocked. All original 106 scientific hashes were preserved; the expanded manifest verifies 128 files. The checks reconstruct the original 44,800 choices and 36 contrasts, the 5,376-response diagnostic study, and all 5,632 targeted responses. A separate implementation checks the targeted study's eight estimates, approximate and conservative intervals, and all 88 cell summaries. Descriptive expected regret is reconstructed from 24,576 original programmed-partner choices. No new API request is made by reproduction.

The targeted run has two transport retries and no final missing scientific IDs. Both first-attempt and final-answer exports remain archived. The new known API charge is $0.2627016, with $0.001609 reserved for unknown charges; cumulative occupied accounting is $43.94696833418 under the authorized $50 cap. These are historical ledger values, not a fresh collection budget.
