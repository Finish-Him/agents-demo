"""Adaptive teaching tools — math-for-ML primary, ML/Python/DL secondary."""

from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Topics database — math-for-ML is primary; ML/Python/DL/LLM kept for breadth.
# ---------------------------------------------------------------------------

TOPICS_DB: dict[str, dict] = {
    # ── Math-for-ML (primary) ───────────────────────────────────────────────
    "linear_algebra": {
        "beginner": ["Vectors & Scalars", "Matrix Addition & Multiplication", "Dot Product", "Identity & Inverse Matrices"],
        "intermediate": ["Determinants", "Linear Independence", "Rank & Null Space", "Orthogonality & Projections"],
        "advanced": ["Eigenvalues & Eigenvectors", "Singular Value Decomposition (SVD)", "Positive Definite Matrices", "Spectral Theorem"],
    },
    "calculus": {
        "beginner": ["Limits & Continuity", "Derivatives of Polynomials", "Product & Chain Rule", "Basic Integrals"],
        "intermediate": ["Partial Derivatives", "Gradient & Directional Derivative", "Taylor Series", "Multiple Integrals"],
        "advanced": ["Jacobian & Hessian", "Lagrange Multipliers", "Vector Calculus (div, curl)", "Calculus of Variations"],
    },
    "probability": {
        "beginner": ["Sample Spaces & Events", "Conditional Probability", "Independence", "Discrete Distributions"],
        "intermediate": ["Bayes' Theorem", "Expectation & Variance", "Continuous Distributions (Normal, Exponential)", "Covariance & Correlation"],
        "advanced": ["Law of Large Numbers & CLT", "Moment Generating Functions", "Markov Chains", "Measure-Theoretic Probability"],
    },
    "statistics": {
        "beginner": ["Descriptive Statistics", "Sampling & Population", "Histograms & Distributions", "Standard Error"],
        "intermediate": ["Hypothesis Testing (t-test, chi-square)", "Confidence Intervals", "Linear Regression (OLS)", "p-values & Type I/II errors"],
        "advanced": ["MLE & MAP Estimation", "Bayesian Inference", "Bootstrap & Resampling", "Generalized Linear Models"],
    },
    # ── ML/DL/Python/LLM (secondary breadth) ───────────────────────────────
    "machine_learning": {
        "beginner": ["Supervised vs. Unsupervised Learning", "Linear Regression", "Classification basics", "Train/Test Split"],
        "intermediate": ["Decision Trees & Random Forests", "Cross-Validation", "Feature Engineering", "Gradient Descent"],
        "advanced": ["Ensemble Methods (XGBoost, LightGBM)", "Hyperparameter Optimization", "Model Interpretability (SHAP)", "AutoML"],
    },
    "deep_learning": {
        "beginner": ["What is a Neural Network", "Activation Functions", "Forward & Back Propagation", "Loss Functions"],
        "intermediate": ["CNNs for Computer Vision", "RNNs & LSTMs", "Transfer Learning", "Regularization (Dropout, BatchNorm)"],
        "advanced": ["Transformers & Attention Mechanism", "Vision Transformers (ViT)", "Diffusion Models", "Neural Architecture Search"],
    },
    "python": {
        "beginner": ["Variables & Types", "Conditionals (if/else)", "Loops (for/while)", "Lists & Dicts"],
        "intermediate": ["Functions & Closures", "List Comprehensions", "Error Handling", "File I/O"],
        "advanced": ["Decorators & Generators", "Async/Await", "Metaclasses", "Type Hints & Protocols"],
    },
    "llm_agents": {
        "beginner": ["What are LLMs", "Prompt Engineering Basics", "Chat vs. Completion APIs", "Temperature & Sampling"],
        "intermediate": ["RAG (Retrieval-Augmented Generation)", "Function/Tool Calling", "LangChain Basics", "Embeddings & Vector DBs"],
        "advanced": ["LangGraph Agent Architectures", "Multi-Agent Systems", "Fine-Tuning LLMs", "Evaluation & Benchmarking"],
    },
}

ANALOGIES: dict[str, str] = {
    # Longer/compound keys MUST come before shorter keys so the lookup
    # ("gradient descent" before "gradient") matches specifically.
    "gradient descent": "Gradient descent is like a blindfolded hiker trying to reach the valley bottom — they feel the slope under their feet and step downhill.",
    # Math-for-ML
    "eigenvector": "An eigenvector is like a direction that a transformation respects — it stretches or shrinks along that line but never rotates off it.",
    "eigenvalue": "An eigenvalue is the stretch factor — how much its eigenvector direction grows or shrinks under the transformation.",
    "gradient": "A gradient is like a compass pointing to the steepest climb on a hill — each component tells you the slope along one axis.",
    "derivative": "A derivative is the instantaneous slope — the tilt of the curve if you zoomed in until it looked like a straight line.",
    "integral": "An integral is like adding up infinitely many tiny rectangles under a curve to measure its total area.",
    "chain rule": "The chain rule is like currency exchange: convert from x to u to y and multiply the exchange rates to get the overall rate.",
    "bayes": "Bayes' theorem is like updating your belief after new evidence — combine prior belief with how likely the evidence is under each hypothesis.",
    "variance": "Variance is the average squared distance from the mean — a measure of how spread out the data is around its center.",
    "expectation": "Expectation is the long-run average if you repeated the random experiment forever.",
    "mle": "Maximum Likelihood Estimation is picking the model parameters that make the observed data look least surprising.",
    "svd": "SVD is like finding the cleanest rotation-stretch-rotation decomposition of any matrix — the Swiss-army knife of linear algebra.",
    # ML/DL/LLM (kept)
    "neural network": "A neural network is like a team of decision-makers: each one (neuron) votes on a small question, and together they solve the big problem.",
    "overfitting": "Overfitting is like memorizing exam answers without understanding the subject — you ace the practice test but fail on new questions.",
    "transformer": "A transformer is like a reader who can highlight important words in a sentence all at once (attention), rather than reading left-to-right.",
    "embedding": "An embedding is like converting words into GPS coordinates — similar meanings end up near each other on the map.",
    "rag": "RAG is like an open-book exam: instead of memorizing everything, the model looks up relevant passages before answering.",
    "backpropagation": "Backpropagation is like tracing back through a recipe to figure out which ingredient ruined the dish — adjusting each step.",
    "regularization": "Regularization is like a coach telling players 'keep it simple' — it prevents the model from creating overly complex strategies.",
    "fine-tuning": "Fine-tuning is like a general chef learning to specialize in sushi — they already know cooking, now they adapt to a specific cuisine.",
    "agent": "An AI agent is like a smart assistant with a toolbox — it decides which tool to use, acts, observes results, and tries again if needed.",
}


@tool
def assess_level(subject: str, student_response: str) -> str:
    """Assess the student's knowledge level based on their response.

    Args:
        subject: Subject name (e.g., 'linear_algebra', 'calculus', 'probability',
            'statistics', 'machine_learning', 'deep_learning', 'python', 'llm_agents').
        student_response: The student's answer or self-description of their knowledge.
    """
    subject_lower = subject.lower().strip().replace(" ", "_").replace("-", "_")
    if subject_lower not in TOPICS_DB:
        available = ", ".join(TOPICS_DB.keys())
        return f"Subject '{subject}' not available. Subjects: {available}"

    response_lower = student_response.lower()
    advanced_kw = [
        # ML/DL
        "transformer", "attention", "fine-tun", "rag", "langraph", "langgraph",
        "diffusion", "shap", "decorator", "async", "metaclass", "multi-agent",
        "architecture search", "xgboost",
        # Math
        "svd", "eigendecompos", "jacobian", "hessian", "lagrange",
        "measure theor", "mle", "map estimat", "bayesian infer",
        "moment generating", "markov chain", "generalized linear",
        "spectral theorem",
    ]
    intermediate_kw = [
        # ML/DL
        "cnn", "rnn", "transfer learning", "gradient", "cross-validation",
        "function", "comprehension", "embedding", "vector", "langchain",
        "random forest", "feature engineer",
        # Math
        "determinant", "rank", "null space", "taylor", "partial derivative",
        "directional", "bayes", "variance", "expectation", "hypothesis test",
        "confidence interval", "regression", "orthogonal",
    ]

    if any(kw in response_lower for kw in advanced_kw):
        level = "advanced"
    elif any(kw in response_lower for kw in intermediate_kw):
        level = "intermediate"
    else:
        level = "beginner"

    topics = TOPICS_DB[subject_lower][level]
    return (
        f"Assessed level: {level.upper()}\n"
        f"Subject: {subject}\n"
        f"Recommended topics for your level:\n"
        + "\n".join(f"  - {t}" for t in topics)
    )


@tool
def generate_exercise(subject: str, topic: str, level: str) -> str:
    """Generate a practice exercise adapted to the student's level.

    Args:
        subject: Subject (e.g., 'linear_algebra', 'calculus', 'probability',
            'statistics', 'machine_learning', 'deep_learning', 'python').
        topic: Specific topic (e.g., 'Eigenvectors', 'Chain Rule', 'Bayes').
        level: Student level: 'beginner', 'intermediate', or 'advanced'.
    """
    exercises = {
        # ── Linear Algebra ───────────────────────────────────────────────
        ("linear_algebra", "beginner"): {
            "prompt": "Compute the dot product of vectors a = [1, 2, 3] and b = [4, 5, 6].",
            "hint": "a·b = a1*b1 + a2*b2 + a3*b3.",
            "solution": "a·b = 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32.",
        },
        ("linear_algebra", "intermediate"): {
            "prompt": "Given A = [[2, 0], [0, 3]], find its determinant and describe geometrically what A does to the unit square.",
            "hint": "det of a 2x2 diagonal matrix is the product of its diagonals; det = scaling factor of area.",
            "solution": "det(A) = 2*3 = 6. A stretches the unit square horizontally by 2 and vertically by 3, producing a 2x3 rectangle with area 6.",
        },
        ("linear_algebra", "advanced"): {
            "prompt": "Explain why the covariance matrix is always positive semi-definite and why PCA uses its eigenvectors.",
            "hint": "Write Cov(X) = E[(X-μ)(X-μ)^T]. For any vector v, consider v^T Cov(X) v.",
            "solution": "v^T Cov(X) v = Var(v^T X) ≥ 0, so Cov is PSD. Its eigenvectors point in directions of maximal variance; PCA projects onto the top-k eigenvectors to keep as much variance as possible in fewer dimensions.",
        },
        # ── Calculus ─────────────────────────────────────────────────────
        ("calculus", "beginner"): {
            "prompt": "Compute the derivative of f(x) = 3x^2 + 5x - 7.",
            "hint": "Use the power rule: d/dx x^n = n*x^(n-1).",
            "solution": "f'(x) = 6x + 5.",
        },
        ("calculus", "intermediate"): {
            "prompt": "Compute the partial derivatives ∂f/∂x and ∂f/∂y of f(x, y) = x^2 * y + sin(y).",
            "hint": "Treat the other variable as a constant.",
            "solution": "∂f/∂x = 2xy. ∂f/∂y = x^2 + cos(y).",
        },
        ("calculus", "advanced"): {
            "prompt": "Derive the gradient of the MSE loss L(w) = (1/n) * Σ(y_i - w^T x_i)^2 with respect to w.",
            "hint": "Use the chain rule. Let r_i = y_i - w^T x_i.",
            "solution": "∇L(w) = -(2/n) * Σ (y_i - w^T x_i) x_i = -(2/n) X^T (y - Xw). Setting to zero gives the normal equations X^T X w = X^T y.",
        },
        # ── Probability ──────────────────────────────────────────────────
        ("probability", "beginner"): {
            "prompt": "A fair six-sided die is rolled. What's the probability of rolling an even number greater than 2?",
            "hint": "List the favorable outcomes from {1,...,6}.",
            "solution": "Favorable: {4, 6}. P = 2/6 = 1/3.",
        },
        ("probability", "intermediate"): {
            "prompt": "A disease affects 1% of a population. A test is 99% accurate (both sensitivity and specificity). A person tests positive. What's the probability they have the disease?",
            "hint": "Use Bayes: P(D|+) = P(+|D)*P(D) / P(+).",
            "solution": "P(+) = 0.99*0.01 + 0.01*0.99 = 0.0198. P(D|+) = (0.99*0.01)/0.0198 ≈ 0.50. Only 50% — illustrates base-rate fallacy.",
        },
        ("probability", "advanced"): {
            "prompt": "Show that for independent X, Y with finite variance, Var(X + Y) = Var(X) + Var(Y).",
            "hint": "Expand Var(X+Y) = E[(X+Y)^2] - E[X+Y]^2 and use linearity + independence.",
            "solution": "Var(X+Y) = E[X^2] + 2E[XY] + E[Y^2] - (E[X]+E[Y])^2. Under independence E[XY] = E[X]E[Y], so cross terms cancel: Var(X+Y) = Var(X) + Var(Y).",
        },
        # ── Statistics ───────────────────────────────────────────────────
        ("statistics", "beginner"): {
            "prompt": "Data: 2, 4, 4, 4, 5, 5, 7, 9. Compute the mean and the sample standard deviation.",
            "hint": "Mean = Σx/n. Sample std uses division by (n-1).",
            "solution": "Mean = 40/8 = 5. Variance = Σ(x-5)^2 / 7 = 32/7 ≈ 4.57. Std ≈ 2.14.",
        },
        ("statistics", "intermediate"): {
            "prompt": "Why does the OLS estimator β̂ = (X^T X)^{-1} X^T y minimize the sum of squared residuals?",
            "hint": "Set ∇||y - Xβ||^2 = 0 and solve for β.",
            "solution": "d/dβ ||y-Xβ||^2 = -2 X^T (y - Xβ). Setting to zero gives X^T X β = X^T y, so β̂ = (X^T X)^{-1} X^T y (assuming full rank). This is a strict minimum because X^T X is positive semi-definite.",
        },
        ("statistics", "advanced"): {
            "prompt": "Derive the MLE for the mean μ of a Normal(μ, σ^2) given i.i.d. samples x_1, ..., x_n.",
            "hint": "Write the log-likelihood, differentiate w.r.t. μ, set to zero.",
            "solution": "L(μ) = Π (1/√(2πσ^2)) exp(-(x_i-μ)^2 / 2σ^2). log L = -(n/2)log(2πσ^2) - Σ(x_i-μ)^2/(2σ^2). d/dμ log L = Σ(x_i-μ)/σ^2 = 0 ⇒ μ̂ = x̄ (the sample mean).",
        },
        # ── Legacy ML/Python/DL (preserved) ──────────────────────────────
        ("python", "beginner"): {
            "prompt": "Create a variable called `name` with your name and `age` with your age. Print: 'My name is [name] and I am [age] years old.'",
            "hint": "Use f-strings: f'text {variable}'",
            "solution": "name = 'Alice'\nage = 25\nprint(f'My name is {name} and I am {age} years old.')",
        },
        ("python", "intermediate"): {
            "prompt": "Write a function that takes a list of numbers and returns only the even ones using a list comprehension.",
            "hint": "Use: [x for x in lst if condition]",
            "solution": "def evens(nums): return [x for x in nums if x % 2 == 0]",
        },
        ("python", "advanced"): {
            "prompt": "Create a `@timer` decorator that measures and prints the execution time of any function.",
            "hint": "Use time.time() before and after the call, and functools.wraps to preserve metadata.",
            "solution": "import time, functools\ndef timer(func):\n    @functools.wraps(func)\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        print(f'{func.__name__}: {time.time()-start:.4f}s')\n        return result\n    return wrapper",
        },
        ("machine_learning", "beginner"): {
            "prompt": "You have a dataset of house prices. The features are: area (sq ft), bedrooms, age. Which type of ML task is this (classification or regression)? Why?",
            "hint": "Think about what type of output you're predicting — a category or a number?",
            "solution": "Regression — because we're predicting a continuous value (price), not a category.",
        },
        ("machine_learning", "intermediate"): {
            "prompt": "Explain why you should NOT use accuracy as the metric for a dataset where 95% of samples are class A and 5% are class B. What metric would you use instead?",
            "hint": "Think about what happens if the model always predicts class A.",
            "solution": "A model predicting always 'A' gets 95% accuracy but is useless. Use F1-score, precision-recall, or AUC-ROC for imbalanced datasets.",
        },
        ("machine_learning", "advanced"): {
            "prompt": "Describe how SHAP values work for model interpretability. What is the connection to game theory?",
            "hint": "Think about Shapley values: fair allocation of a 'payout' (prediction) among 'players' (features).",
            "solution": "SHAP uses Shapley values from cooperative game theory. Each feature is a 'player' and the prediction is the 'payout'. SHAP computes each feature's marginal contribution across all possible coalitions of features.",
        },
        ("deep_learning", "beginner"): {
            "prompt": "What is an activation function? Why can't we just use a linear function at every layer?",
            "hint": "Think about what happens when you compose multiple linear functions.",
            "solution": "Activation functions introduce non-linearity. Without them, stacking linear layers is equivalent to a single linear layer (composition of linear functions is linear), so the network couldn't learn complex patterns.",
        },
        ("deep_learning", "intermediate"): {
            "prompt": "Explain the vanishing gradient problem. Which architectures were designed to solve it?",
            "hint": "Think about what happens to gradients during backprop through many layers with sigmoid activations.",
            "solution": "With sigmoid/tanh, gradients shrink exponentially through layers (derivatives < 1 multiply). LSTMs (gates), ResNets (skip connections), and ReLU activations were designed to mitigate this.",
        },
        ("deep_learning", "advanced"): {
            "prompt": "Explain the self-attention mechanism in transformers. Write the formula for scaled dot-product attention and explain each component.",
            "hint": "Q, K, V matrices. Why do we scale by sqrt(d_k)?",
            "solution": "Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) V. Q=queries, K=keys, V=values. Scaling by sqrt(d_k) prevents dot products from growing large, which would push softmax into saturated regions with tiny gradients.",
        },
    }

    key = (subject.lower().replace(" ", "_").replace("-", "_"), level.lower())
    ex = exercises.get(key)

    if ex:
        return (
            f"EXERCISE — {subject.title()} ({level})\n"
            f"Topic: {topic}\n\n"
            f"Problem:\n{ex['prompt']}\n\n"
            f"Hint: {ex['hint']}\n\n"
            f"(Try to solve it, then ask me to check your answer!)\n\n"
            f"[EXPECTED ANSWER — for tutor reference]:\n{ex['solution']}"
        )

    return (
        f"EXERCISE — {subject.title()} ({level})\n"
        f"Topic: {topic}\n\n"
        f"Create a practical exercise about {topic} at {level} level. "
        f"The student should solve and explain their reasoning."
    )


@tool
def explain_concept(concept: str, level: str, use_analogy: bool = True) -> str:
    """Explain a concept with language adapted to the student's level, optionally with an analogy.

    Args:
        concept: The concept to explain (e.g., 'eigenvector', 'chain rule', 'Bayes', 'RAG').
        level: Student level: 'beginner', 'intermediate', or 'advanced'.
        use_analogy: If True, include a real-world analogy.
    """
    concept_lower = concept.lower()

    analogy = ""
    if use_analogy:
        for key, val in ANALOGIES.items():
            if key in concept_lower:
                analogy = f"\n\nAnalogy: {val}"
                break
        if not analogy:
            analogy = "\n\nAnalogy: (no specific analogy for this concept — the tutor will craft one)"

    if level == "beginner":
        style = "Explain very simply, as if to someone with no technical background. Use everyday examples."
    elif level == "intermediate":
        style = "Explain with technical clarity but remain accessible. Include a practical example."
    else:
        style = "Explain with full technical depth, including edge cases, trade-offs, and advanced applications."

    return (
        f"EXPLANATION: {concept.title()}\n"
        f"Level: {level}\n"
        f"Approach: {style}"
        f"{analogy}\n\n"
        f"(O tutor Arquimedes desenvolverá a explicação completa seguindo essa orientação.)"
    )


@tool
def find_resources(topic: str) -> str:
    """Find study materials and references for a topic.

    Args:
        topic: Study topic (e.g., 'linear algebra', 'calculus', 'probability', 'transformers').
    """
    resources = {
        # Math-for-ML
        "linear_algebra": [
            {"title": "Gilbert Strang — Linear Algebra (MIT OCW 18.06)", "url": "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/", "type": "Course"},
            {"title": "3Blue1Brown — Essence of Linear Algebra", "url": "https://www.3blue1brown.com/topics/linear-algebra", "type": "YouTube"},
            {"title": "Mathematics for Machine Learning (Deisenroth et al.)", "url": "https://mml-book.github.io/", "type": "Free book"},
        ],
        "calculus": [
            {"title": "MIT OCW 18.01 Single Variable Calculus", "url": "https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/", "type": "Course"},
            {"title": "3Blue1Brown — Essence of Calculus", "url": "https://www.3blue1brown.com/topics/calculus", "type": "YouTube"},
            {"title": "OpenStax Calculus (Volumes 1-3)", "url": "https://openstax.org/subjects/math", "type": "Free book"},
        ],
        "probability": [
            {"title": "Harvard Stat 110 — Probability (Joe Blitzstein)", "url": "https://projects.iq.harvard.edu/stat110", "type": "Course"},
            {"title": "Introduction to Probability (Blitzstein & Hwang)", "url": "https://projects.iq.harvard.edu/stat110/book", "type": "Free book"},
            {"title": "Seeing Theory (Brown University)", "url": "https://seeing-theory.brown.edu/", "type": "Interactive"},
        ],
        "statistics": [
            {"title": "StatQuest with Josh Starmer (YouTube)", "url": "https://www.youtube.com/@statquest", "type": "YouTube"},
            {"title": "Introduction to Statistical Learning (James et al.)", "url": "https://www.statlearning.com/", "type": "Free book"},
            {"title": "Think Stats (Allen Downey)", "url": "https://greenteapress.com/thinkstats2/", "type": "Free book"},
        ],
        # Legacy topics (preserved)
        "python": [
            {"title": "Python Official Tutorial", "url": "https://docs.python.org/3/tutorial/", "type": "Documentation"},
            {"title": "Real Python", "url": "https://realpython.com/", "type": "Tutorials"},
            {"title": "Automate the Boring Stuff with Python", "url": "https://automatetheboringstuff.com/", "type": "Free book"},
        ],
        "machine_learning": [
            {"title": "Andrew Ng — Machine Learning Specialization (Coursera)", "url": "https://www.coursera.org/specializations/machine-learning-introduction", "type": "Course"},
            {"title": "Hands-On ML with Scikit-Learn (Aurélien Géron)", "url": "https://www.oreilly.com/library/view/hands-on-machine-learning/9781098125967/", "type": "Book"},
            {"title": "StatQuest with Josh Starmer (YouTube)", "url": "https://www.youtube.com/@statquest", "type": "YouTube"},
        ],
        "deep_learning": [
            {"title": "fast.ai — Practical Deep Learning for Coders", "url": "https://course.fast.ai/", "type": "Course"},
            {"title": "3Blue1Brown — Neural Networks (YouTube)", "url": "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi", "type": "YouTube"},
            {"title": "Deep Learning Book (Goodfellow, Bengio, Courville)", "url": "https://www.deeplearningbook.org/", "type": "Free book"},
        ],
        "llm": [
            {"title": "LangChain Documentation", "url": "https://python.langchain.com/docs/", "type": "Documentation"},
            {"title": "LangGraph Academy", "url": "https://academy.langchain.com/", "type": "Course"},
            {"title": "Andrej Karpathy — Let's build GPT (YouTube)", "url": "https://www.youtube.com/watch?v=kCc8FmEb1nY", "type": "YouTube"},
            {"title": "LLM Visualization", "url": "https://bbycroft.net/llm", "type": "Interactive"},
        ],
        "transformer": [
            {"title": "Attention Is All You Need (original paper)", "url": "https://arxiv.org/abs/1706.03762", "type": "Paper"},
            {"title": "The Illustrated Transformer (Jay Alammar)", "url": "https://jalammar.github.io/illustrated-transformer/", "type": "Blog"},
            {"title": "HuggingFace NLP Course", "url": "https://huggingface.co/learn/nlp-course", "type": "Course"},
        ],
    }

    topic_lower = topic.lower()
    matched = []
    for key, refs in resources.items():
        if key in topic_lower or key.replace("_", " ") in topic_lower:
            matched = refs
            break

    if not matched:
        return (
            f"Topic: {topic}\n"
            f"General suggestions:\n"
            f"  - Coursera or fast.ai for structured courses\n"
            f"  - YouTube — search '{topic} tutorial'\n"
            f"  - Google Scholar — search '{topic}'\n"
            f"  - Awesome lists on GitHub — search 'awesome-{topic.lower().replace(' ', '-')}'"
        )

    result = f"Resources for: {topic}\n\n"
    for ref in matched:
        result += f"  {ref['title']}\n     Type: {ref['type']}\n     Link: {ref['url']}\n\n"
    return result


teaching_tools = [
    assess_level,
    generate_exercise,
    explain_concept,
    find_resources,
]
