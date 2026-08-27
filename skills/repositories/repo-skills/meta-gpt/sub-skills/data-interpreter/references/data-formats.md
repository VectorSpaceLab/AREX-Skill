# Data Formats and Task Inputs

DI benchmark workflows are prompt-driven. Most failures come from mismatched `task_name`, `data_dir`, or file paths in formatted requirements. Validate paths before letting DI generate code.

## `data_dir` Semantics

The benchmark runners accept `data_dir` as the directory that contains the `di_dataset` folder. The expected tree is:

```text
<data_dir>/
  di_dataset/
    ml_benchmark/
      04_titanic/
        split_train.csv
        split_eval.csv
      05_house-prices-advanced-regression-techniques/
        split_train.csv
        split_eval.csv
      06_santander-customer-transaction-prediction/
        split_train.csv
        split_eval.csv
      07_icr-identify-age-related-conditions/
        split_train.csv
        split_eval.csv
      08_santander-value-prediction-challenge/
        split_train.csv
        split_eval.csv
    open_ended_tasks/
      01_ocr.png
      02_ocr.jpg
      03_ocr.jpg
      14_image_background_removal.jpg
      16_image_2_code_generation.png
      17_image_2_code_generation.png
```

The README summary sometimes describes `ml_benchmark/...` directly under the dataset root, while the runnable requirements use `{data_dir}/di_dataset/...`. Prefer the runner behavior: `data_dir` points to the parent of `di_dataset`.

If a user gives a path ending in `di_dataset`, normalize it by either:

- Setting `data_dir` to the parent directory; or
- Rewriting the prompt paths manually so they do not duplicate `di_dataset/di_dataset`.

## ML Benchmark Task Names

`task_name` must be one of the keys used by the ML benchmark requirements:

| Task Name | Dataset | Expected Files or Source | Metric/Output |
| --- | --- | --- | --- |
| `01_iris` | sklearn Iris | Built-in sklearn dataset | Data analysis and plot |
| `02_wines_recognition` | sklearn Wine recognition | Built-in sklearn dataset | Plot, 20% test split, prediction accuracy |
| `03_breast_cancer` | sklearn Wisconsin Breast Cancer | Built-in sklearn dataset | Plot, 20% validation split, validation accuracy |
| `04_titanic` | Titanic survival | `di_dataset/ml_benchmark/04_titanic/split_train.csv`, `split_eval.csv` | Accuracy on eval data |
| `05_house_prices` | House Prices | `di_dataset/ml_benchmark/05_house-prices-advanced-regression-techniques/split_train.csv`, `split_eval.csv` | RMSE between log prediction and log observed price |
| `06_santander_customer` | Santander Customer Transaction | `di_dataset/ml_benchmark/06_santander-customer-transaction-prediction/split_train.csv`, `split_eval.csv` | AUC on eval data |
| `07_icr_identify` | ICR age-related conditions | `di_dataset/ml_benchmark/07_icr-identify-age-related-conditions/split_train.csv`, `split_eval.csv` | F1 score on eval data |
| `08_santander_value` | Santander Value Prediction | `di_dataset/ml_benchmark/08_santander-value-prediction-challenge/split_train.csv`, `split_eval.csv` | RMSLE on eval data |

Known path pitfall: one README table row refers to `ml_benchmark/4_titanic/split_train.csv` without the leading zero, while the runnable requirement uses `ml_benchmark/04_titanic/split_train.csv`. Prefer `04_titanic` and check for both names if troubleshooting a downloaded dataset.

## Open-Ended Task Names

`task_name` must be one of these keys for open-ended requirements:

| Task Name | Scenario | Main Prerequisites |
| --- | --- | --- |
| `01_ocr` | English invoice OCR | `di_dataset/open_ended_tasks/01_ocr.png`, PaddleOCR |
| `02_ocr` | Chinese invoice OCR | `di_dataset/open_ended_tasks/02_ocr.jpg`, PaddleOCR with Chinese support |
| `03_ocr` | Invoice OCR | `di_dataset/open_ended_tasks/03_ocr.jpg`, PaddleOCR with `lang='en'` |
| `04_web_search_and_crawling` | ICLR paper table crawl | Network access, HTML parsing |
| `05_web_search_and_crawling` | Chinese CPI page crawl/summarize | Network access, Chinese text handling |
| `06_web_search_and_crawling` | Shop product crawl | Network access, HTML parsing |
| `07_web_search_and_crawling` | Chinese financing flash crawl | Network access, Chinese site handling |
| `08_email_reply` | Outlook email read/reply | Secure email credentials and explicit send policy |
| `09_web_page_imitation` | Medium page imitation | Selenium/WebDriver, browser, network, vision/model support |
| `10_web_page_imitation` | PyTorch page imitation | Selenium/WebDriver, browser, network, vision/model support |
| `11_web_page_imitation` | Kaggle page imitation | Selenium/WebDriver, browser, network, vision/model support |
| `12_web_page_imitation` | ChatGPT login page imitation | Selenium/WebDriver, browser, network, login-site safety review |
| `13_web_page_imitation` | DeepMind page imitation | Selenium/WebDriver, browser, network, vision/model support |
| `14_image_background_removal` | Remove image background | `di_dataset/open_ended_tasks/14_image_background_removal.jpg`, `rembg` |
| `15_text2img` | Stable Diffusion text-to-image | Explicit `sd_url` service endpoint |
| `16_image_2_code_generation` | Image to web code | `di_dataset/open_ended_tasks/16_image_2_code_generation.png`, vision/model support |
| `17_image_2_code_generation` | Image to web code | `di_dataset/open_ended_tasks/17_image_2_code_generation.png`, vision/model support |
| `18_generate_games` | Snake game | `pyxel` environment if executing |
| `19_generate_games` | Jumping game | `pyxel` environment if executing |
| `20_generate_games` | Mouse click game | `pyxel` environment if executing |

Open-ended task prompts frequently assert that dependencies are already installed. Do not trust that assertion; verify dependencies or mark as skip/prerequisite.

## Common Prompt Placeholders

Use these placeholders consistently:

- `{data_dir}`: parent directory containing `di_dataset`, unless manually rewriting paths.
- `{task_name}`: exact key from the requirement dictionary, not the display ID alone.
- `{train_path}` and `{eval_path}`: concrete paths to train/eval CSVs for ML tasks.
- `{sd_url}`: Stable Diffusion service endpoint supplied by the user; do not invent or probe private services.
- `{email_account}` and `{email_password}`: should not be pasted into prompts; use secure secret handling and explicit dry-run policy.

## Dataset Validation Checklist

Before running a benchmark-style DI task:

1. Check whether the provided `data_dir` contains `di_dataset/`.
2. For ML file tasks, check both train and eval files exist.
3. For built-in sklearn tasks, confirm `scikit-learn`, `pandas`, and plotting dependencies are installed if execution is allowed.
4. For open-ended image tasks, check referenced image files exist and are readable.
5. For web/email/service tasks, record prerequisites and ask for explicit user approval rather than running automatically.
6. Include corrected file paths in the final prompt so DI does not infer stale or mismatched locations.

A minimal path validation snippet for user-side preparation:

```python
from pathlib import Path

def resolve_di_dataset(data_dir: str) -> Path:
    base = Path(data_dir).expanduser()
    if (base / "di_dataset").is_dir():
        return base
    if base.name == "di_dataset" and base.is_dir():
        return base.parent
    raise FileNotFoundError(f"Could not find di_dataset under {base}")
```

## DABench Layout

The InfiAgent-DABench example is optional and expensive. It expects a separate dataset cloned from an external repository and runners for single, all-serial, or all-parallel execution. Treat it as benchmark evidence only unless the user explicitly authorizes downloads and long LLM/code execution.

DABench requirement template shape:

```text
You are required to {question} from a CSV file named {file_name}.
Constraints: Ensure that {constraints}...
The output format should be {format}.
This task is categorized as {level}.
```

DABench notes:

- Requires external dataset acquisition.
- Original docs mention a notebook initialization workaround for benchmark execution; do not patch installed packages for routine usage without explicit user approval.
- Parallel DABench execution can multiply LLM cost and code-execution risk.

## Test Fixture Expectations

Repo tests mock or bound dangerous behavior:

- `DataInterpreter` tests patch `ExecuteNbCode.run` and assert responses plus finished task code.
- `DataInterpreter(react_mode="react")` is tested with mocked execution.
- `DataAnalyst.write_and_exec_code()` tests the no-current-task failure, success path, and failure status.
- `ExecuteNbCode` tests direct safe snippets, state across cells, plotting, timeout, markdown, terminate/reset, and parsed exception output.

For usability cases, prefer assertions over real benchmark runs: verify the agent identifies path mismatches, missing datasets, secret-bearing prompts, optional dependencies, and code-execution safety gates.
