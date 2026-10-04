# Review-response reproduction package

This local supplement accompanies the revised paper. No public hosting URL is implied.

## Offline reproduction

The verified environment is Python 3.12.7, SciPy 1.13.1, NumPy 1.26.4, and Matplotlib 3.9.2. SciPy supports the original and new inferential calculations; NumPy and Matplotlib support figure generation. The existing-data audit in `audits` uses only the Python standard library. Other environments may work but have not been verified here. In an existing Python 3.12.7 environment, the numerical and plotting dependencies can be installed with `python -m pip install scipy==1.13.1 numpy==1.26.4 matplotlib==3.9.2`. Installation may require network access; the reproduction commands below do not make API calls or contact a model.

Run commands from each indicated directory:

1. `original`: `python reconstruct_requests.py --verify` then `python recompute_results.py` reconstruct all 44,800 original requests and 36 planned contrasts.
2. `audits`: `python reproduce_audits.py` reproduces first-attempt acquisition summaries, the stratified independent-choice baseline, and all 36 missing-response sensitivity bounds using the bundled science tables. See its README for details.
3. `new_experiment`: `python verify.py` verifies the fixed new design and scoring. `python export_results.py --run run_v2 --output reproduced_exports` replays recorded responses and reconstructs the complete 5,376-request independent study without contacting a model. `runtime.py --execute` and `io_recovery.py` are acquisition code and should NOT be invoked for offline reproduction.
4. `new_experiment`: `python audit_and_figures/independent_result_audit.py --experiment . --output reproduced_audit/independent_result_audit.json` independently rescores every final response, reconstructs the three planned aid contrasts and both interval methods, and checks acquisition counts. It imports neither the experiment's protocol nor analysis implementation. The command also regenerates both descriptive JOIN-payoff error CSVs beside its output JSON. These error frequencies are post hoc descriptions, not additional hypothesis tests or evidence of an internal mechanism.

The new study was planned after the original review, before its responses. Scientific settings and source hashes were frozen. A separately documented local-file recovery preserved all starts, accepted answers, budgets, and unknown-fee reserves. Independent diagnoses do not filter action responses or establish within-response mechanisms. Original supplementary-model collection differs by response limit and extraction history; first-attempt audits retain that limitation.

`original` includes all prompt variants, every request-to-block mapping and selected choice. `audits` includes all 1,012 selected extracted responses as well as failures and acquisition histories. `new_experiment/run_v2` includes every new scientific request and raw recorded response, including failures; its endpoint metadata contains no account preflight rows. Credentials are not included. A missing response is not imputed from a later answer.

The paper's LaTeX source archive is separate and contains only paper.tex and figure/ PDFs. Numerical reproduction does not establish universal model behavior, provider stationarity, or conference acceptance.

`REVIEW_RESPONSE.md` maps the revisions and their remaining limitations to reviewer concerns W1--W5. `PACKAGE_SHA256.json` records every bundled file except itself; the nested packages retain their own input manifests.
