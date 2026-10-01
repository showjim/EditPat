# Plan: Row-per-op config format for the Simplified interface

Branch: `feat/row-per-op-config` (off `master`)

## Problem

The simplified CSV format can configure one ATP file twice on one line — two
`(Process Type, Pin or Method, Cycle)` triples at column positions 3–5 and 6–8.
The requirement is 3 or 4 operations on the same file, and the format has no way
to express that.

## What we found before designing

**The processing engine already supports N operations per file. Only the parser
caps it at two.**

- [`_group_ops_by_atp`](../../src/main.py#L100) collects *all* rows for one ATP
  file, preserving order.
- [`_run_chained_ops`](../../src/main.py#L45) loops over *all* of them, feeding
  each op the previous op's output.
- [`analyse_merge_config`](../../src/atp_handler.py#L75) hard-codes `i == 3 or i == 6`,
  `i == 4 or i == 7`, `i == 5 or i == 8`, and has no branch for `i >= 9`. Extra
  columns are silently dropped, with no warning.

Verified by hand-building a config list with four chained ops on
`Sample_ATP.atp` (DSSC Capture TDO → DSSC Capture PORN → DSSC Source TDI →
WFLAG): all four effects landed in one output file, and
[`merge_instrument_declare`](../../src/pattern_processor.py#L132) merged the
three instrument declarations correctly.

**So this is a parser + UI change, not an engine change.**

### Other defects found during the review

Verified by running the code, not by reading:

1. **A failed op is reported as a successful output.** `edit_pattern` returns the
   *input path* on any error ([pattern_processor.py:463](../../src/pattern_processor.py#L463)),
   and [`process_atp_simple`](../../src/main.py#L156) appends anything truthy to
   `results`. A deliberately failing run returned
   `['Sample/Sample_ATP.atp']` — the source file — as its result. In the webapp
   that file is zipped and offered to the user as the deliverable.
2. **An op following a failed op crashes the pool worker.** `_run_chained_ops`
   assumes the previous op wrote `Output/<name>`; when it did not, `copy_and_rename`
   raises `FileNotFoundError` (verified). Since `apply_async` is called with no
   `error_callback` ([main.py:195](../../src/main.py#L195)), `my_callback` never
   fires, `counter` never reaches `total_tasks`, and the **Generate button stays
   disabled forever**. Longer chains make this more likely, not less.
3. **`Add Opcode` / `Remove Opcode` are silent no-ops from any CSV.**
   `_run_chained_ops` hardcodes `user_string=""` ([main.py:83](../../src/main.py#L83)),
   and `build_config_from_classical` does not accept a user string, so the
   Classical GUI's "Please Enter the User String" box is also dead. Verified:
   Remove Opcode through the config path produced a **byte-identical** output to
   its input.
4. `check_in_same_range` is passed a `set` and subscripts it
   ([utils.py:58](../../src/utils.py#L58)), raising `TypeError: 'set' object is
   not subscriptable` whenever a `repeat` line falls inside the cycle range.
   Reachable only via `IndexMode='Vector'`. **Not fixed — deferred**, see below.

## Decisions

| Area | Decision |
| --- | --- |
| Semantics | Ops **chain**: op N reads op N−1's output. One ATP in, one output out. One chain per file per run. |
| Row shape | One row = one operation. |
| Columns | `Instance`, `Pattern`, `Status`, `Process Type`, `Pin or Method`, `Cycle`, `User String`. `Instance` and `Status` are inert. |
| Grouping | `Pattern` repeated on every row. Implicit row order. Non-contiguous rows for one file warn but still group. |
| Parsing | Header-authoritative, single code path, no fallback. Names trimmed and case-insensitive. Missing or unknown column = hard error. Blank rows skipped, not treated as end-of-file. |
| Legacy | Unsupported. A 9-column file hard-errors with a message showing the migration. No converter, no sniffing, no second parsing path. |
| Validation | Up-front. All problems reported together; nothing dispatches until the config is clean. Unmatched `Pattern` is the single warning-and-skip. |
| Failure | Chain aborts at the failing op; the file is excluded from results; the partial output stays on disk for inspection; the log names the op that died. |
| TimeMode | No column. The simple format is Single-only; Dual-mode files use the Classical tab. Documented limitation. |
| IndexMode | No column. To be obsoleted; stays Classical-GUI-only. |
| Front-ends | Tk Simplified, Tk Classical and Streamlit all updated. The CSV remains the single source of truth. |

## The new format

```csv
Instance,Pattern,Status,Process Type,Pin or Method,Cycle,User String
,Sample_ATP.atp,Done,DSSC Capture,TDO,[7-7];[12-12],
,Sample_ATP.atp,Done,DSSC Capture,PORN,[13-14],
,Sample_ATP.atp,Done,DSSC Source,TDI,[9-9],
,Sample_ATP.atp,Done,WFLAG,,[8-8],
,Sample_ATP - 1.atp,Done,DSSC Source,TDI,[7-7];[9-9],
,Sample_ATP - 1.atp,Done,DSSC Capture,TDO,[7-7];[12-12],
,Sample_ATP - 2.atp,,Compress Pattern,,,
,Sample_ATP - 3.atp,,WFLAG,,[8-8],
```

Rows sharing a `Pattern` are one chain, applied in row order. Above:
`Sample_ATP.atp` gets four chained ops, `Sample_ATP - 1.atp` gets two,
`Sample_ATP - 2.atp` and `- 3.atp` get one each.

### Column contract

| Column | Required | Notes |
| --- | --- | --- |
| `Pattern` | yes | ATP filename, as listed in the file selection. `.atp` or `.atp.gz`. |
| `Process Type` | yes | One of the eight modes in `cmb_list`. |
| `Pin or Method` | yes (column present) | May be blank for modes that take no pin (`WFLAG`, `Expand Pattern`, `Compress Pattern`, `Add Opcode`, `Remove Opcode`). |
| `Cycle` | yes (column present) | `[a-b];[c-d]` form. May be blank for `Expand Pattern`, `Compress Pattern`, `Remove Opcode`. Required for the Capture/Source/WFLAG/Add Opcode modes. |
| `User String` | no | Only consumed by `Add Opcode` / `Remove Opcode`. Required *for those rows*, enforced at validation. |
| `Instance` | no | Inert. Not read. |
| `Status` | no | Inert. Not read, not written back. |

Names are matched after `strip().lower()`. Any column not in the table is a
warning; any required column that is absent is an error naming the column.

### Error cases

Hard errors, all reported together before anything runs:

- A 9-column legacy row — the message prints the offending row and the two
  row-per-op rows that replace it, so the migration is self-documenting.
- Unknown `Process Type`.
- `Add Opcode` / `Remove Opcode` with a blank `User String`.
- Capture/Source/`WFLAG`/`Add Opcode` with a blank `Cycle`.
- Capture/Source/`CMEM` with a blank `Pin or Method`.
- A missing required column, or a config with no operation rows.

Warning, then skip the row:

- `Pattern` naming a file that is not in the current ATP selection. This stays a
  warning because a config legitimately covers more files than are selected for
  a given run; hard-failing would make partial runs impossible. This is the one
  deliberate asymmetry in the validation rules.

## Code changes

### `src/atp_handler.py`

- **Rewrite `analyse_merge_config`** as a header-authoritative row-per-op parser.
  Read row 0 for the header, normalize names, map columns to fields, build one
  config dict per data row. Blank rows are skipped rather than terminating the
  loop. Detect the legacy shape (>= 9 columns) and raise a descriptive error.
- **Keep `build_config_from_classical`**, but add `user_string` to its signature
  and emit it in the config dicts, so the Classical tab's user-string box works.
- **Keep `read_csv`** unchanged — the Classical 2-column reader.

### `src/main.py`

- **`_resolve_atp_path`** — resolve by exact basename match first, then
  basename + `.gz`, instead of the current substring search in
  [`in_list`](../../src/utils.py#L26). The substring search is load-bearing for
  `.gz` support, so the `.gz` fallback is deliberate; what it removes is the
  accidental-prefix-match risk.
- **`validate_config(config_list, atp_files, logger) -> bool`** — new. Implements
  the error table above, collecting every problem before returning.
- **`_run_chained_ops`** — pass `op.get("UserString", "")` to `edit_pattern`
  instead of `""`; return `None` when an op fails and stop the chain at that op.
- **`process_atp_simple`** — call `validate_config` first and return `[]` if it
  fails. Only append to `results` when the returned path is a genuine output.
- **`dispatch_config_parallel`** — call `validate_config` first; attach an
  `error_callback` to each `apply_async` so an unexpected worker exception still
  increments the completion counter and unblocks the GUI.
- **`process_atp_classical`** — thread `user_string` through to the config list.

### `src/pattern_processor.py`

- **`edit_pattern`** — return `None` on failure instead of the input path. Every
  error path (including the broad `except Exception` handler) currently returns
  `something`; that single change is what fixes defect 1.

### `PAE.py`

- **`run_classical_multiprocess`** — pass the user string into
  `build_config_from_classical`.
- **`my_callback` / progress reporting** — distinguish succeeded from failed tasks
  so the final summary line reports how many files failed and why, rather than
  only "All tasks completed!!!".

### `PAE_webapp.py`

- **Default template** — two rows showing a chain on one file, with the new
  seven-column shape.
- **`column_config`** — one `Process Type` `SelectboxColumn` covering all **eight**
  modes (the current list omits `Add Opcode` / `Remove Opcode`), `User String` a
  plain text column, `num_rows="dynamic"` kept.
- **`df_on_change`** — unchanged.

### `Sample/Sample_ATP - simple.csv`

- Rewritten in place, in the new format, as shown above. The current file
  references `Sample_ATP - 4.atp`, which does not exist in `Sample/`; the
  rewritten sample references only files that are present.

### `README.md`

- Update the config-format description. The screenshot at
  [img/config_csv.png](../../img/config_csv.png) shows the old layout and needs
  re-taking.

## Verification

1. **Baseline first, on `master`, before any code changes.** Run the current
   `Sample_ATP - simple.csv` through the Simplified tab and archive `Output/`.
   This is the only way to prove the rewrite is behaviour-preserving.
2. **Regression.** Run the rewritten sample on the branch and diff against the
   baseline. `Sample_ATP.atp` and `Sample_ATP - 1.atp` must be byte-identical;
   `Sample_ATP.atp` in the new sample has two extra ops, so its baseline comes
   from the hand-built four-op run used during the review instead.
3. **New capability.** Confirm a four-op chain on one file produces one output
   with all four effects present and a single merged `instruments` block.
4. **Failure paths**, each asserting the run does *not* report success:
   unknown mode; missing pin for a Capture mode; missing `User String` for
   `Add Opcode`; a deliberately failing cycle range; a 9-column legacy file.
5. **GUI unblocking.** With a failing task in the batch, confirm the Generate
   button re-enables and the summary reports the failure. This is the regression
   test for defect 2 and it fails today.
6. **`User String` column.** `Remove Opcode` with a user string must produce an
   output that differs from its input. Byte-equality is the bug.
7. **Classical tab.** Run `Sample_ATP.csv` in DSSC Capture mode and confirm
   output is unchanged from the baseline.
8. **Cross-file grouping.** A file whose rows are non-contiguous must still group
   correctly and emit a warning.
9. **Blank row mid-file.** Must be skipped, not truncate the rest of the batch.
10. **Webapp smoke.** Upload the new sample, run, confirm the zip contains only
    genuine outputs.

## Out of scope / deferred

- **`check_in_same_range` / `IndexMode='Vector'`** (defect 4). Not fixed. Both the
  bug and the mode are expected to disappear when IndexMode is obsoleted, so
  fixing the function now means writing code that is deleted shortly after.
- **Legacy conversion tooling.** Deliberately none.
- **`TimeMode` in the simple format.** Deliberately absent; `Expand Pattern` and
  `Compress Pattern` are therefore Single-mode-only from a config file. Dual-mode
  files must use the Classical tab.

## Known limitations

- A pre-existing config file in the 9-column format will not run. It fails with
  an error showing the replacement rows.
- `Expand Pattern` and `Compress Pattern` are Single-mode-only from config
  (see above).
- `Expand Pattern` changes cycle numbering downstream in a chain, since it
  removes `repeat` statements. Chain order matters and is the user's
  responsibility.
