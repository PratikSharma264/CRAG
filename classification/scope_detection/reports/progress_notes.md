# Progress Notes - Scope Detection Dataset Build

## STEP 0: INVENTORY (2026-11-16)

### Git Status
- Branch: django-branch (clean, up to date with origin/django-branch)
- No modified or untracked files under classification/scope_detection/

### .jsonl Files in generation/ (row counts)

**Active (generation/):**
| File | Rows | Notes |
|------|------|-------|
| blocklist_relabel_candidates.jsonl | 15 | Blocklist - never restore to OUT, never relabel to IN |
| in_scope_01.jsonl | 82 | |
| in_scope_02.jsonl | 82 | |
| in_scope_03.jsonl | 82 | |
| in_scope_04.jsonl | 82 | |
| in_scope_05.jsonl | 82 | |
| in_scope_06.jsonl | 82 | |
| in_scope_07.jsonl | 82 | |
| in_scope_08.jsonl | 82 | |
| in_scope_09.jsonl | 82 | |
| in_scope_10.jsonl | 82 | |
| in_scope_11.jsonl | 65 | |
| **in_scope subtotal (non-nl)** | **905** | |
| in_scope_nl_01.jsonl | 70 | UNTRUSTED - regex rewrites |
| in_scope_nl_02.jsonl | 70 | UNTRUSTED |
| in_scope_nl_03.jsonl | 70 | UNTRUSTED |
| in_scope_nl_04.jsonl | 70 | UNTRUSTED |
| in_scope_nl_05.jsonl | 70 | UNTRUSTED |
| in_scope_nl_06.jsonl | 70 | UNTRUSTED |
| in_scope_nl_07.jsonl | 70 | UNTRUSTED |
| in_scope_nl_08.jsonl | 70 | UNTRUSTED |
| in_scope_nl_09.jsonl | 70 | UNTRUSTED |
| in_scope_nl_10.jsonl | 70 | UNTRUSTED |
| in_scope_nl_11.jsonl | 70 | UNTRUSTED |
| in_scope_nl_12.jsonl | 70 | UNTRUSTED |
| in_scope_nl_13.jsonl | 70 | UNTRUSTED |
| in_scope_nl_14.jsonl | 70 | UNTRUSTED |
| in_scope_nl_15.jsonl | 70 | UNTRUSTED |
| in_scope_nl_16.jsonl | 70 | UNTRUSTED |
| in_scope_nl_17.jsonl | 70 | UNTRUSTED |
| in_scope_nl_18.jsonl | 70 | UNTRUSTED |
| in_scope_nl_19.jsonl | 70 | UNTRUSTED |
| in_scope_nl_20.jsonl | 70 | UNTRUSTED |
| in_scope_nl_21.jsonl | 70 | UNTRUSTED |
| in_scope_nl_22.jsonl | 70 | UNTRUSTED |
| in_scope_nl_23.jsonl | 51 | UNTRUSTED |
| **in_scope_nl subtotal** | **1,621** | UNTRUSTED - 133 rows flagged for label-determining fact changes |
| out_of_scope_01.jsonl | 80 | |
| out_of_scope_02.jsonl | 80 | |
| out_of_scope_03.jsonl | 80 | |
| out_of_scope_04.jsonl | 80 | |
| out_of_scope_05.jsonl | 80 | |
| out_of_scope_06.jsonl | 80 | |
| out_of_scope_07.jsonl | 80 | |
| out_of_scope_08.jsonl | 80 | |
| out_of_scope_09.jsonl | 80 | |
| out_of_scope_10.jsonl | 80 | |
| out_of_scope_11.jsonl | 80 | |
| out_of_scope_12.jsonl | 35 | |
| **out_of_scope subtotal (non-nl)** | **895** | |
| out_of_scope_nl_01.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_02.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_03.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_04.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_05.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_06.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_07.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_08.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_09.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_10.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_11.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_12.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_13.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_14.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_15.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_16.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_17.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_18.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_19.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_20.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_21.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_22.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_23.jsonl | 70 | UNTRUSTED |
| out_of_scope_nl_24.jsonl | 46 | UNTRUSTED |
| **out_of_scope_nl subtotal** | **1,686** | UNTRUSTED |
| needs_clarification_candidates.jsonl | 0 | EMPTY |

**Reserve (generation/reserve/):**
| File | Rows | Notes |
|------|------|-------|
| reserve/fragments/in_scope_fragments.jsonl | 60 | |
| reserve/fragments/out_scope_fragments.jsonl | 55 | |
| reserve/in_scope_no_context.jsonl | 59 | |
| reserve/in_scope_reserve_01.jsonl | 99 | |
| reserve/in_scope_reserve_02.jsonl | 99 | |
| reserve/in_scope_reserve_03.jsonl | 76 | |
| **reserve in_scope subtotal** | **448** | |
| reserve/original_fragments/in_scope_original.jsonl | 885 | SOURCE OF TRUTH #1 |
| reserve/original_fragments/out_of_scope_original.jsonl | 915 | SOURCE OF TRUTH #1 |
| reserve/out_of_scope_reserve_01.jsonl | 196 | |
| reserve/out_of_scope_reserve_02.jsonl | 111 | |
| **reserve out_of_scope subtotal** | **307** | |
| reserve/rewrite_flagged/flagged_rows.jsonl | 133 | Flagged for label-determining fact changes |
| reserve/rewrite_flagged/in_scope_flagged.jsonl | 48 | |
| reserve/rewrite_flagged/in_scope_no_context.jsonl | 3 | |
| reserve/rewrite_flagged/out_of_scope_flagged.jsonl | 85 | |

### Stray Scripts (already in scripts/ and scripts_archive_do_not_run/)
No stray scripts at project root - already moved.

---

## Next: STEP 1 - Build build_pools.py