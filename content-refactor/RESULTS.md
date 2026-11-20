# Bake-off results: content-to-skill on two sources

Date: 2026-11-19
Converter: gnipbao/content-to-skill pinned at `ce5776a5161065836ed4647f9b96629d062ffdee` (commit confirmed by `git cat-file -t` and `git rev-parse HEAD`; SKILL.md, references/*, and scripts/check_skill_package.py were read before anything ran)
Sources: A = cookbook `managed-agents-cma-use-skills-from-a-repo`; B = docs page `web-search-tool` (both fetched as rendered text; the notebook file and linked pages were not read)
Target: runtime-neutral, English. Output: `bakeoff/a/`, `bakeoff/b/`.

## Outcome

- **Independence: `uncertainty`.** No fresh-context agent was available in this session. The generating agent had already read the expectations and predictions in the plan. Every `found` below could be inflated by that. The two `missed` rows on A are the only results the contamination cannot have helped.
- **Generation: `completed`** for A and B. Validator `contract_label: passed` for both (structural check only; see Gaps).
- **Fidelity, reviewed:** A found 13, partial 1, missed 2 of 16. B found 2 of 2.
- **Executability:** A's generated script is valid and agreed with 9 of 9 fixtures taken from the source's rules. The cookbook's own runnable sample was not carried into either package: 0 of 16 A identifiers appear in the package; 7 of them are not recorded anywhere. B has no executable artifact. Live execution: `not_run` for both.
- **Stopped after scoring**, as the plan says. No Pass 1 content was written.

## A: expectations (reviewed status; auto status was the regex proxy)

| id | auto | reviewed | evidence (file:line) | note |
|---|---|---|---|---|
| A1.layout | found | found | `a/repo-skill-discovery/references/scanner-rules.md:5,10,11,12` | root-only plus bare, doubly nested, missing `.claude` |
| A1.frontmatter | found | found | `scanner-rules.md:17,19`; `SKILL.md:25` | no frontmatter, CRLF, empty description |
| A1.cap64 | found | found | `scanner-rules.md:23`; `SKILL.md:26` | silent drop stated |
| A1.truncation2000 | found | found | `scanner-rules.md:18`; `SKILL.md:25` | flatten to one line also stated |
| A1.scan_once | found | found | `scanner-rules.md:24`; `SKILL.md:28` | new session needed |
| A1.lazy_nested | found | found | `scanner-rules.md:28`; `SKILL.md:27` | read tool yes, shell no |
| A2.scanner_standin | partial | partial | `SKILL.md:57`; `scripts/audit_skill_layout.py:4-5` | the script is labeled an approximation of the hosted scanner. The package never classifies the scanner as provider-hosted or says another runtime needs a stand-in. |
| A2.injection_standin | missed | missed | no match for inject / stand-in / surrogate anywhere in the package; `scanner-rules.md:32` states catalog delivery as fact | |
| A2.github_mount_dropped | found | found | absent from package; `a/_workings/03-source-to-skill-brief.md:6`, `02-mechanism-cards.md:95-105` | recorded only outside the package; a future agent using the package cannot see that a mount existed |
| A2.cloud_env_dropped | found | found | same lines | same note |
| A2.beta_header_dropped | found | found | same lines | same note |
| A3.order_of_64 | found | found | `SKILL.md:26,55`; `references/source-boundary.md:10` | |
| A3.catalog_format | found | found | `source-boundary.md:11` | |
| A3.truncation_marker | found | found | `source-boundary.md:12` | |
| A3.missing_file_read | missed | missed | no match | not noticed during extraction |
| A3.model_dependent_matching | found | found | `source-boundary.md:13` | the regex also hit "deterministic" on unrelated lines (`SKILL.md:14`, brief:7); those do not count |

The A3 rows are not in the source page. The plan lists them as gaps a good conversion should surface, so they test inference rather than extraction. They are also the most exposed to the contamination above.

## B: expectations

| id | auto | reviewed | evidence | note |
|---|---|---|---|---|
| B1.provider_hosted_no_portable_core | found | found | `b/web-search-tool-config/SKILL.md:8,46` | stated as provider-hosted with no search implementation supplied |
| B1.no_invented_provider | found | found | no provider names in package or records | `SKILL.md:45` mentions "any other search provider" only to forbid it |

B's result came from the "Tool fantasy" anti-pattern in the converter plus the agent's prior knowledge of what the plan expected. The protocol has no step that asks for this (judgment call 1 in `b/_workings/04-judgment-calls.md`).

## Predictions from the plan (unverified before this run)

| id | reviewed | evidence |
|---|---|---|
| P1 numbers lost in mechanism cards | not supported here | 64 at `a/_workings/02-mechanism-cards.md:34,35,37`; 2,000 at `:21,22,25`. The card template has no field for limits (judgment call 5); the numbers survived because the agent put them under "Decision rule". Weak evidence, since the agent knew the numbers mattered. |
| P2 no portability classification | supported for A; not supported for B | A: wording appears only in run records (`01-source-inventory.md:8`, `02-mechanism-cards.md:105`), none in the package. B: the package states the dependency (`SKILL.md:8`), but see the B note above. |
| P3 A assumes a provider mount exists | partial | the package never mentions a mount except `scanner-rules.md:37` (Skills API case). It does assume a session-start scanner exists on the user's runtime (`SKILL.md:3,8`) without any check. |
| P4 B assumes a web_search tool exists | not supported as "silently" | the dependency is stated as a precondition (`SKILL.md:8,46`). The assumption exists, but it is not hidden. |

## Executability

| probe | A | B |
|---|---|---|
| E1 syntax (`check_executable.py compile`) | `valid`: 1 python unit (`scripts/audit_skill_layout.py`), stdlib imports only | `not_run`: 0 python units, nothing to compile |
| E2 behavior (`probe`, 9 fixtures from source rules) | `valid` 9 of 9 | `not_run`: no script, no fixtures |
| E3 source identifiers carried | 0 of 16 in package; 9 only in run records; 7 absent everywhere (`agent_toolset_20260401`, `client.beta.environments.create`, `client.beta.agents.create`, `client.beta.sessions.create`, `events.send`, `claude-sonnet-5-5`, `anthropic>=2.0.0`) | 15 of 16 in package as rules; absent: `claude-opus-5-5` (the page's sample model) |
| E4 live run of the source's sample | `not_run`: needs `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, managed-agents beta, `anthropic_cloud` | `not_run`: needs `ANTHROPIC_API_KEY` and web search enabled for the org |

What E2 does and does not show. The fixtures come from section 7 of the source and the script was written from the same reading by the same agent, so a shared misreading would pass. The script is itself a stand-in for the hosted scanner, so 9 of 9 means self-consistent with the written rules, not equal to the real scanner. The real scanner is unreachable offline.

A source limit that applies to any reconstruction: the cookbook imports `stream_until_end_turn` and `wait_for_idle_status` from a `utilities` module that the page does not show. The sample as published cannot run standalone. The package records this as not read (`a/repo-skill-discovery/references/source-boundary.md:5`).

## Gaps this run measured (evidence, not a Pass 1 proposal)

1. **No portable-versus-provider-hosted step.** Scanner and catalog injection are not classified; one row partial, one missed. Evidence: A2 rows, judgment call 2.
2. **Validator checks structure only.** Both packages passed while A missed 3 expected items and carried no runnable source sample. `scripts/check_skill_package.py` inspects frontmatter keys, section headings, link presence, and file presence (lines 38-106). Impact: a `passed` result says nothing about fidelity.
3. **Validator requires a Codex-specific file.** `agents/openai.yaml` is mandatory (`check_skill_package.py:93-95`), so a runtime-neutral target ships one anyway (both packages do).
4. **Discard accounting is coarse.** Mount and scaffolding were recorded as discarded at card level; 7 sample identifiers vanished with no record, and none of the discards are visible inside the package itself.
5. **Output depends on unstated choices.** Judgment-call logs hold 7 rows for A and 4 for B: places where the pinned protocol did not decide the result. A second agent could choose differently.
6. **No gate on claims about checks.** The package's own line `source-boundary.md:15` described a check before it ran (judgment call 7).

## Instrument defects found and fixed

Two defects in the measuring scripts, both fixed and logged in `content-refactor/references/instrument-selftest.md`: an absence check that passed on an empty scope, and a scorer whose "package" scope included its own saved output (this flipped three A rows until fixed; the fixed scorer reproduced the first unpolluted statuses exactly). The probe was shown to fail correctly against a deliberately wrong adapter (8 of 9 fixtures `not_valid`).

## Not run

- Independent fresh-context generation (the main open item).
- Independent review of the regex hits and of the reviewed statuses above; they are the generating agent's own.
- The converter's 100-point rubric (needs judgment; self-scoring is not independent).
- Live execution of either source's sample.
- A repeat run to measure variance between two generations of the same source.
- Reading the Multi_Skill layout: `git clone https://github.com/itz1508/Multi_Skill.git` returned `could not read Username` (private or missing; the unauthenticated API call was rate-limited and inconclusive).
