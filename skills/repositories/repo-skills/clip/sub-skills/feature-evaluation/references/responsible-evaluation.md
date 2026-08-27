# Responsible Evaluation

CLIP is a research model for studying robustness, generalization, and zero-shot image classification. Treat feature extraction, similarity search, and linear probes as research and analysis tools unless the user has already completed task-specific safety, legal, and performance validation.

## Intended Use

- Primary intended users are AI researchers and practitioners investigating model capabilities, robustness, biases, and constraints.
- Good fits include offline experiments, constrained benchmark evaluation, feature analysis, prompt/taxonomy studies, and internal prototypes with fixed data and labels.
- Keep evaluation reproducible: record model name, checkpoint source, preprocessing, feature normalization, prompts/class names, data split, metric definitions, and known exclusions.

## Out-of-Scope Use

Avoid recommending CLIP feature workflows for:

- Unreviewed commercial or non-commercial deployment.
- Open-ended image search over uncontrolled user data.
- Safety-critical decisions, access control, hiring, credit, education, healthcare, law enforcement, or similar high-impact settings.
- Surveillance, face recognition, identity verification, or demographic classification.
- Any setting where mistakes, biased labels, or prompt/taxonomy choices can harm people.

The model card explicitly warns that deployed use is out of scope without careful in-domain testing, and that surveillance and facial recognition are out of scope regardless of apparent performance.

## Bias, Fairness, and Taxonomy Risk

CLIP behavior can change substantially with class design. Adding, removing, or rewording classes can change scores, rankings, and disparities. For evaluations involving people or sensitive attributes:

- Do not infer identity, race, gender, age, criminality, or other sensitive properties as an application goal.
- Audit per-class and per-demographic results when the dataset includes people.
- Inspect false positives and false negatives qualitatively, especially for classes that imply harmful labels.
- Document class taxonomy construction, excluded labels, prompt wording, and stakeholder review.
- Treat high aggregate accuracy as insufficient; subgroup behavior and label semantics matter.

The model card reports disparities in experiments involving race and gender and notes that disparities can shift based on class construction.

## English and Dataset Limits

CLIP was not purposefully trained in or evaluated on languages other than English. Limit text prompts, labels, and retrieval queries to English unless the user runs separate validation for the target language.

The training data was publicly available image-caption data with substantial internet crawling. That data is more representative of people and societies connected to the internet and may skew toward developed nations, younger users, and male users. Evaluation results may not transfer to underrepresented domains.

## Dataset Licensing and Download Caveats

Do not download large datasets by default. Treat these as opt-in, documented, and license-reviewed operations:

- Country211 is described as an 11 GB archive derived from YFCC100M, with 150 train, 50 validation, and 100 test images per country. Underlying media use is subject to Creative Commons licenses selected by the uploaders.
- Rendered SST2 is described as a 131 MB archive of rendered Stanford Sentiment Treebank v2 sentences for OCR-style evaluation.
- The YFCC100M subset lists 14,829,396 image identifiers filtered for English natural-language titles or descriptions; it is metadata, and underlying media remains subject to uploader-selected Creative Commons licenses.

For skill validation or examples, prefer tiny local fixtures, user-owned images, or pre-existing cached data. Do not make benchmark downloads a default step.

## When to Avoid Use

Avoid CLIP feature evaluation entirely when:

- The task depends on fine-grained counting, precise localization, or subtle visual distinctions without validation; the model card notes limitations in fine-grained classification and counting.
- The class taxonomy is fluid, adversarial, or socially sensitive.
- The user needs a legally cleared dataset but has not reviewed media licenses.
- The environment cannot record reproducible metadata for checkpoints, prompts, splits, and preprocessing.
- The user expects linear-probe accuracy alone to justify deployment.

When in doubt, keep the workflow offline, small, reproducible, and explicitly labeled as exploratory research.
