# Ask Toskar

Ask [Toskar](https://toskar.ai), your own local AI, as a step in a GitHub Actions workflow: summarize a bug report, suggest an issue's labels, read a failing log. It runs on your runners and your models, so issue text, code, and logs never go to a hosted AI, and there's no bill per token.

```yaml
- uses: yeixio/toskar-action@v1
  id: toskar
  with:
    prompt: Summarize this bug in two sentences
    input: ${{ github.event.issue.body }}
- run: echo "$ANSWER"
  env:
    ANSWER: ${{ steps.toskar.outputs.answer }}
```

> **Preview.** It needs Toskar Core 1.11.0 or later, for `toskarctl ask` and the Linux archives.

## Two ways to run

**Ask a Toskar the runner can reach.** On a self-hosted runner beside a computer running Toskar, or with Toskar reachable over the network, give its address and a key. Make the key with **For a CI job** on Toskar's API Access page: it can only ask, with no memories, knowledge, or tools, whatever a job sends.

```yaml
- uses: yeixio/toskar-action@v1
  with:
    url: ${{ secrets.TOSKAR_URL }}
    api-key: ${{ secrets.TOSKAR_API_KEY }}
    prompt: What's the first real error in this log, and its likely cause?
    input-file: build.log
```

**Start Toskar on the runner.** Without `url`, the action installs Toskar in the job's temporary folder and starts it, with no root or service, then installs `start-model` and asks it. The model is cached between runs (about 0.8 GB for the default, `llama-3.2-1b-q4`). GitHub's hosted runners run small models, about 1 to 4 billion parameters, on the CPU, much slower than a computer with a graphics card does: time a run with your own prompts, and set `timeout` to match.

```yaml
- uses: yeixio/toskar-action@v1
  with:
    prompt: Suggest a title for this pull request
    input: ${{ github.event.pull_request.body }}
    timeout: 20m
```

Later steps of the same job reuse the Toskar the first one started.

## Inputs

| Input | |
| --- | --- |
| `prompt` | What to ask. Required. |
| `input` | Text to work on, such as an issue's body. It's sent as data apart from the prompt, and the model is told to follow only the prompt. |
| `input-file` | A file to work on, instead of `input`. |
| `json-schema` | A JSON Schema file. The answer is JSON that fits it; one that doesn't fails the step. |
| `model` | A model, `auto` (the default), or a specialized AI, `sai:<slug>`. |
| `profile` | Answer as this profile instead. |
| `system` | A system prompt. |
| `max-tokens`, `temperature` | The longest answer, and the sampling temperature. |
| `timeout` | How long to wait for the answer: `10m` unless set. |
| `url`, `api-key` | A Toskar the runner can reach, and its key. Without `url`, the action starts one on the runner. |
| `start-model` | The model to install when starting Toskar on the runner. |
| `cache` | Cache the started Toskar's models and llama.cpp. `true` unless set. |
| `version` | The Toskar release to install, such as `1.11.0`. The latest unless set. |

**Output:** `answer`, the answer, or with `json-schema`, compact JSON that fits it.

## Labels from an issue, safely

An issue's text is written by someone else. Keep it in `input`, ask for structured output, check the answer against the labels you allow, and apply them in a separate step that has the permission to write:

```yaml
on:
  issues:
    types: [opened]
jobs:
  triage:
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - uses: actions/checkout@v5
      - uses: yeixio/toskar-action@v1
        id: toskar
        with:
          prompt: Suggest labels for this issue, from bug, feature, docs, and question.
          input: |
            ${{ github.event.issue.title }}

            ${{ github.event.issue.body }}
          json-schema: .github/triage.schema.json
      - env:
          GH_TOKEN: ${{ github.token }}
          ISSUE: ${{ github.event.issue.number }}
          LABELS: ${{ steps.toskar.outputs.answer }}
        run: |
          for label in $(jq -r '.labels[]' <<<"$LABELS"); do
            case "$label" in bug | feature | docs | question) gh issue edit "$ISSUE" --repo "$GITHUB_REPOSITORY" --add-label "$label" ;; esac
          done
```

with `.github/triage.schema.json`:

```json
{"type": "object", "properties": {"labels": {"type": "array", "items": {"enum": ["bug", "feature", "docs", "question"]}}}, "required": ["labels"]}
```

The action passes what it's given to its scripts as environment variables, never as text inside a script, so an issue's title can't run commands. Do the same in your own steps: `env:` and `"$LABELS"`, as above, not `${{ }}` inside `run:`.

## Elsewhere

GitLab, Forgejo, and other CI systems use the same pieces from a shell: `install.sh ci` and `toskarctl ask` ([Toskar in CI](https://github.com/yeixio/toskar-core/blob/main/docs/ci.md)).

## License

Apache 2.0.
