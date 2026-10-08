# Models used, and their licences

Ten models were run: nine published tags and one local build. All are small open models, served on one machine by
[Ollama](https://ollama.com). No hosted model was called in any saved run: every saved request went to
`http://127.0.0.1:11434`. The first harness (`lab/gne/`) was written to call a hosted model, and `lab/.env.example`
names two API keys as placeholders; no saved run used either.

This repository holds what the models wrote (their replies), not the models themselves. Each model's licence is listed
here because those replies are part of the data.

## The models

| Model tag in Ollama | Digest (first 12 characters) | Studies | How far it got | Licence of the model |
| --- | --- | --- | --- | --- |
| `qwen2.5:7b` | `845dbda0ea48` | C2, C3, C5, C6, C5P | Scored in all five studies | Apache 2.0 |
| `qwen2.5:14b` | `7cdf5a0187d5` | C3 | Scored once | Apache 2.0 |
| `gpt-oss:20b` | `17052f91a42e` | C4, C4G | Scored stage ran twice: in C4, where 113 of 120 runs could not be scored, and in C4G | Apache 2.0, with OpenAI's gpt-oss usage policy |
| `qwen2.5:3b` | `357c53fb659c` | C1, C2 | Scored in C1 (no scripted history); stopped by the rating gate in C2 | Qwen Research License |
| `llama3.1:8b` | `46e0c10c039e` | C1, C2, C3 | Scored in C1; stopped by the rating gate in C2; rating questions only in C3 | Llama 3.1 Community License |
| `mistral:7b` | `6577803aa9a0` | C1, C1M | Controls only in C1; scored in C1M with calls read from text | Apache 2.0 |
| `granite3.3:8b` | `fd429f23b909` | C3 | Controls and rating check only | Apache 2.0 |
| `command-r7b` | `ff4e9696ef9f` | C4 | Controls and rating questions only | CC BY-NC 4.0, with Cohere Labs' acceptable use policy |
| `mistral-nemo:12b` | `e7e06d107c6c` | C4 | Controls and rating questions only | Apache 2.0 |
| `day1-qwen25-3b` (local build) | `7ad55ddc88cd` | V6, X1, V7 | Baseline runs in V6 and V7, and X1's test of the rule's wording. No test of the competence question | Recorded base model: `qwen2.5:3b` (Qwen Research License) |

- The full 64-character digest of each model is in every `batch.json` of the C studies (field `model_digest`) and in
  `docs/replicate.md`, section 2.1. Each tag had one digest throughout.
- The digest identifies the model file that Ollama served. The record does not state the quantisation of each tag.
- `day1-qwen25-3b` is a model installed under a name of the lab's own. One pilot settings file names `qwen2.5:3b` as
  its base. Its build file is not in the record, so it cannot be rebuilt and checked (`docs/replicate.md`,
  section 2.4). It is not the same install as the published tag `qwen2.5:3b` that C1 and C2 ran: the two have
  different digests and were run with different settings.
- A further model, `qwen3:4b`, appears in the lists of installed models. It was never run.

## Where each licence was read

Each licence was read on a public page of its publisher, or on the licence page that the Ollama library shows for the
tag, on 6 October 2026. Model pages change; check the licence shown for the exact tag you download.

| Model | Licence page |
| --- | --- |
| `qwen2.5:7b`, `qwen2.5:14b` | [Qwen2.5-7B-Instruct, LICENSE](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/main/LICENSE); [Qwen2.5-14B-Instruct, LICENSE](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct/blob/main/LICENSE) |
| `qwen2.5:3b` | [licence shown by Ollama for `qwen2.5:3b`](https://ollama.com/library/qwen2.5:3b/blobs/b5c0e5cf74cf) |
| `llama3.1:8b` | [licence shown by Ollama for `llama3.1:8b`](https://ollama.com/library/llama3.1:8b/blobs/0ba8f0e314b4); [the same text at Meta](https://github.com/meta-llama/llama-models/blob/main/models/llama3_1/LICENSE) |
| `mistral:7b` | [Mistral-7B-Instruct-v0.3](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3) |
| `mistral-nemo:12b` | [Mistral-Nemo-Instruct-2407](https://huggingface.co/mistralai/Mistral-Nemo-Instruct-2407) |
| `granite3.3:8b` | [granite-3.3-8b-instruct](https://huggingface.co/ibm-granite/granite-3.3-8b-instruct) |
| `gpt-oss:20b` | [gpt-oss model card](https://openai.com/index/gpt-oss-model-card/) |
| `command-r7b` | [c4ai-command-r7b-12-2024](https://huggingface.co/CohereLabs/c4ai-command-r7b-12-2024) |

## What this means for reuse

This is a plain statement of what the licences say. It is not legal advice.

- The code and the documents in this repository are under the MIT licence (`LICENSE`).
- The models' replies are published here as research data, with each model named.
- Three of the licences restrict use. The **Qwen Research License** (`qwen2.5:3b` and the local build) grants use
  "for non-commercial purposes only". **CC BY-NC 4.0** (`command-r7b`) is a non-commercial licence, and Cohere adds an
  acceptable use policy. The **Llama 3.1 Community License** (`llama3.1:8b`) is Meta's own licence, with an
  acceptable use policy of its own.
- `gpt-oss:20b` is under Apache 2.0; OpenAI also publishes a usage policy for it.
- If you plan to reuse the replies of one of those models, read that model's licence first. For the nine published
  tags, the replies sit in batch folders that carry the model's name, for example
  `lab/runs/gne_core_c1-qwen2.5-3b-main-real-20260927T165400229910Z`. The replies of the local build are in the batch
  folders of V6, X1 and V7 (their names begin `phase1_`) and in the early pilot folders (`docs/lab-map.md`).

## Settings

All ten models were sampled at temperature 0.7 on a CPU. The C studies used a context of 8,192 tokens and a reply
budget of 512 tokens (2,048 for `gpt-oss:20b`, which also ran with low reasoning effort); V6, X1 and V7 used a
context of 4,096 tokens. `docs/replicate.md`, section 2.2, has the full table, study by study.
