# Resources Catalog

## Purpose

Read this when a user asks for ML Glossary resource recommendations, dataset categories, library families, papers, courses, blogs, or application areas. The original repository contained very large curated lists; this runtime distills their structure and high-signal examples so ordinary routing does not require the original `docs/` tree.

## How to answer resource requests

1. Determine the user's intent: dataset, software library, paper, book/course/blog, or application area.
2. Ask for constraints only if they materially change the recommendation: domain, modality, programming language, beginner vs advanced level, academic vs production, or offline/network limitations.
3. Give a small focused list first. Mention that the original repo's resource lists were broad and somewhat historical; for modern choices, label updates as modern additions if they are outside the repo-grounded catalog.
4. Do not imply that every listed external URL is still alive. Treat URLs as leads, not guaranteed dependencies.

## Dataset categories from the repository

The dataset page was forked from a public awesome-datasets style catalog. It organized public datasets by domain. Use these categories to narrow a search:

- Agriculture: plant, nutrient, crop, and agriculture databases.
- Art: sketch and art datasets such as Google's Quick Draw.
- Biology and healthcare: genomics, microbiome, cell image, cancer, protein, medical, and public-health data.
- Chemistry/materials science: computational chemistry and materials databases.
- Climate/weather/earth science: meteorology, climate archives, satellite/earth data, weather history.
- Complex networks and computer networks: citation graphs, road networks, web/click datasets, internet scans, wireless traces.
- Data challenges: Kaggle, DrivenData, KDD Cup, CrowdANALYTIX, Yelp/Netflix-style challenge data.
- Economics, finance, energy, government, social sciences: public agency, finance, labor, economic, and civic datasets.
- GIS/transportation: geographic boundaries, OSM-derived data, taxi, flight, bike-share, traffic, airline, and route datasets.
- Image processing/computer vision: Quick Draw, Caltech, faces, ImageNet-style resources, MNIST, Oxford-IIIT Pets, Visual Genome, shape and action datasets.
- Machine learning general: UCI ML Repository, MovieLens, Yahoo ratings/classification, KEEL, Delve, Lending Club, context-aware datasets.
- Museums, music, neuroscience, physics, psychology/cognition, sports, time series, software, public domains, search engines, social networks, NLP.

## Dataset recommendation patterns

| User need | Repo-grounded category | Representative leads |
| --- | --- | --- |
| Beginner tabular classification/regression | Machine Learning / Data Challenges | UCI ML Repository, KEEL, Kaggle competition data, Lending Club, Titanic-style challenge data. |
| Recommender demo | Machine Learning / Public Domains | MovieLens, Yelp challenge, Netflix Prize historical data. |
| Image classification | Image Processing | MNIST, Oxford-IIIT Pet, Stanford Dogs, SUN, Visual Genome, ImageNet-style references. |
| NLP text classification or language modeling | Natural Language | SMS Spam, Blogger corpus, ClueWeb, DBpedia, Wikipedia/Wikidata, Google Ngrams, WordNet. |
| Social/citation/network analysis | Complex Networks / Social Networks | AMiner, DBLP, Stanford Large Network Dataset Collection, Enron email, Twitter/social network traces. |
| Time series | Time Series / Transportation / Finance | UCR time series, Backblaze hard-drive failure rates, bike-share/taxi/flight data, Quandl-style finance leads. |
| Biomedical/omics | Biology / Healthcare | 1000 Genomes, GEO, TCGA, Broad datasets, Cell Image Library, Protein Data Bank. |

## Library catalog structure

The library page was forked from an awesome-machine-learning list and grouped libraries by programming language and subdomain. It included APL, C, C++, Common Lisp, Clojure, Elixir, Erlang, Go, Haskell, Java, JavaScript, Julia, Lua, MATLAB, .NET, Objective-C, OCaml, PHP, Python, Ruby, Rust, R, SAS, Scala, Swift, and others.

### Python high-signal entries preserved

- Scientific stack: NumPy, SciPy, Pandas, matplotlib, Seaborn, statsmodels, SymPy, NetworkX, PyMC, astropy.
- General ML: scikit-learn, XGBoost, mlxtend, metric-learn, TPOT, Orange, SKLL, Shogun, Milk, Fuku-ML.
- Deep learning / neural networks: TensorFlow, Theano, Keras-era libraries, Lasagne, Chainer, MXNet, Caffe, TFLearn, PyBrain, Brainstorm, Neon, Neural Networks and Deep Learning code.
- NLP: NLTK, Pattern, TextBlob, spaCy, gensim, jieba, SnowNLP, KoNLPy, fuzzywuzzy, jellyfish, editdistance, textacy, Stanford CoreNLP wrappers.
- Computer vision: scikit-image, SimpleCV, VIGRA bindings, OpenFace, PCV.
- Recommenders and graph/probabilistic tools: python-recsys, Crab, pgmpy, Bayesian Methods for Hackers, Think Bayes.
- Reinforcement learning: OpenAI Gym.

### Library-routing advice

- For a beginner Python ML task, start with NumPy/Pandas/scikit-learn and add matplotlib/Seaborn for visualization.
- For neural-network education, the repo's historical list names TensorFlow/Keras/Theano-era tools; label modern alternatives separately if you mention PyTorch, JAX, or current TensorFlow/Keras.
- For NLP, choose NLTK/TextBlob for teaching basics, spaCy for industrial pipelines, and gensim for topic modeling/embeddings.
- For computer vision, choose scikit-image/OpenCV-style libraries for image processing; use modern deep-learning frameworks only if the user asks for model training.

## Papers catalog structure

The papers page centered on deep learning and included these groups:

- Understanding deep nets: knowledge distillation, fooling images, transferability of features, CNN feature baselines, visualization/understanding convnets.
- Optimization/training: batch normalization, rectifiers, dropout, Adam, co-adaptation prevention, random hyperparameter search.
- Unsupervised/generative models: PixelRNN, improved GAN training, DCGAN, DRAW, original GAN, variational autoencoders, large-scale feature learning.
- Image segmentation/object detection: YOLO, FCN, Faster R-CNN, Fast R-CNN, rich feature hierarchies, segmentation with CRFs.
- Image/video: super-resolution CNNs, neural style, image captioning, video recognition, DeepFace, pose estimation.
- NLP: neural NER, language modeling, machine reading, attention-based translation, CRF-RNN, memory networks, neural Turing machines, seq2seq, word2vec, GloVe, sentence/document embeddings.
- Speech/other: attention-based speech recognition, Deep Speech 2, deep recurrent speech recognition, DNN acoustic modeling.
- Reinforcement learning: asynchronous deep RL, Double Q-learning, AlphaGo-style work, DDPG, DQN, robotic grasping.
- Classic papers: sparse rectifiers, unsupervised feature learning, neural language models, stacked denoising autoencoders, document recognition, LSTM, deep belief nets, deep architectures.

## Books, courses, blogs, podcasts

The `Other Content` page grouped learning resources:

- Blogs: Distill, OpenAI, Andrej Karpathy, Colah, WildML, FastML, The Morning Paper, Jeremy Kun, Jake VanderPlas, Count Bayesie, Simply Statistics, Data School, and others.
- Machine-learning books: Introduction to Statistical Learning, Elements of Statistical Learning, Probabilistic Programming & Bayesian Methods for Hackers, Think Bayes, Gaussian Processes for ML, Mining Massive Datasets, Pattern Recognition and ML, A Course in ML, Reinforcement Learning resources.
- Deep-learning and NLP books: Deep Learning Book, Neural Networks and Deep Learning, NLTK Book, Foundations of Statistical NLP, Introduction to Information Retrieval.
- Probability/statistics and linear-algebra books: Think Stats, Basic Probability Theory, Introduction to Probability, Probability & Statistics Cookbook, Linear Algebra Done Wrong, Convex Optimization, Applied Numerical Linear Algebra.
- Courses: Stanford CS231n, CS224d/Oxford Deep NLP, Columbia AI/ML edX, Stanford Coursera ML, University of Toronto Neural Networks, University of Washington ML specialization, Oxford Nando de Freitas ML, Caltech Learning from Data.
- Podcasts: The O'Reilly Data Show, Talking Machines, Data Skeptic, Linear Digressions, Data Stories, Learning Machines 101, TWIMLAI.

## Applications page status

The applications page named target areas but was mostly placeholder content:

- Anomaly detection
- Computer vision: classification, object detection, segmentation
- Natural language: dialog systems, machine translation, speech recognition, text summarization, question answering
- Recommender systems
- Time series

If a user asks for an application explanation, provide a concise starter definition and route to relevant sub-skills: classical algorithms for simpler models, neural networks for CNN/RNN/deep-learning applications, and resources here for datasets/papers/courses.

## Reliability caveats

- The resource lists are broad, historical, and link-heavy. Verify live URLs only when the user explicitly needs current access.
- The catalog is useful for brainstorming and teaching, not for endorsing one library or benchmark as current state of the art.
- When suggesting resources for production work, add a modern verification step: check maintenance status, license, install instructions, and compatibility.
