# LLM test dataset and MELLM

## Dataset versions
- Pass version strings: `'1.0'` or `'1.1'`.
- Float versions such as `1.0` and `1.1` are rejected.

## Dataset item shape
Typical fields include:
- `question_type`
- `score` in version 1.1
- `correct_answer`
- `question`

## How MELLM uses the dataset
1. Load the dataset with `llm_test_dataset_loader(version='1.1')`.
2. Prepare a list of LLM names and a same-length list of callable API wrappers.
3. Pass the questions into `MELLM(llm_names, llm_apis, exam_questions)`.
4. Use `answer_questions`, `build_grading_matrix`, `run_whole`, or `run_singular` when you have real answers and scores.

## Practical notes
- The full example requires external API access and may use large or private scoring JSON files.
- The bundled smoke script only checks that the loader and constructor work locally.
