# Local status-file recovery

An operational amendment was recorded after 1,152 accepted scientific responses, before any behavioral analysis. The process raised Windows PermissionError (WinError 5) at runtime.py line 445 while replacing status.json. Its attempt to save a fatal status failed for the same reason. The process exited with code 1; the last successfully saved status still said running.

At interruption there were 1,169 reserved starts and 1,153 settlements including one compatibility response. The 16 newly reserved starts preceded the failing snapshot and the ThreadPool submission. They had not been dispatched by that code path. Recovery nevertheless conservatively retains their full unknown-cost reserves and counts their started attempts, following the frozen interrupted-attempt policy; no attempt or row is erased. No provider-policy or contract failure was recorded.

io_recovery.py wraps only the save function, retrying atomic os.replace for up to 30 attempts separated by 0.2 seconds on PermissionError. It does not alter the frozen runtime.py, protocol, schedule, payloads, response limits, classification, first-valid selection, three-attempt cap, scientific sample, or budget. It resumes through the original OS lock and ledger reconstruction. All accepted responses remain locked. This amendment repairs local file output and does not tune scientific stimuli or model behavior.

First-attempt analyses count the 16 interrupted pre-dispatch reservations as missing started attempts. They should not be described as model failures or received model answers. Final accepted-response analyses retain their original planned IDs.
