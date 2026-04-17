"""Domain tools for the Archimedes adaptive teaching agent."""

import json
import random

from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Embedded educational content (self-contained for demo)
# ---------------------------------------------------------------------------

TOPICS_DB: dict[str, dict] = {
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
    "neural network": "A neural network is like a team of decision-makers: each one (neuron) votes on a small question, and together they solve the big problem.",
    "gradient descent": "Gradient descent is like a blindfolded hiker trying to reach the valley bottom — they feel the slope under their feet and step downhill.",
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
        subject: Subject being studied (e.g., 'python', 'machine_learning', 'deep_learning', 'llm_agents').
        student_response: The student's answer or self-description of their knowledge.
    """
    subject_lower = subject.lower().strip().replace(" ", "_")
    if subject_lower not in TOPICS_DB:
        available = ", ".join(TOPICS_DB.keys())
        return f"Subject '{subject}' not available. Subjects: {available}"

    response_lower = student_response.lower()
    advanced_kw = ["transformer", "attention", "fine-tun", "rag", "langraph", "langgraph",
                   "diffusion", "shap", "decorator", "async", "metaclass", "multi-agent",
                   "architecture search", "xgboost"]
    intermediate_kw = ["cnn", "rnn", "transfer learning", "gradient", "cross-validation",
                       "function", "comprehension", "embedding", "vector", "langchain",
                       "random forest", "feature engineer"]

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
        subject: Subject (e.g., 'python', 'machine_learning', 'deep_learning').
        topic: Specific topic (e.g., 'Linear Regression', 'Decorators').
        level: Student level: 'beginner', 'intermediate', or 'advanced'.
    """
    exercises = {
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

    key = (subject.lower().replace(" ", "_"), level.lower())
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
        concept: The concept to explain (e.g., 'neural network', 'gradient descent', 'RAG').
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
        f"(The tutor Archimedes will elaborate the full explanation using this guidance.)"
    )


@tool
def find_resources(topic: str) -> str:
    """Find study materials and references for a topic.

    Args:
        topic: Study topic (e.g., 'transformers', 'Python decorators', 'RAG').
    """
    resources = {
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
        if key in topic_lower:
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


all_tools = [
    assess_level,
    generate_exercise,
    explain_concept,
    find_resources,
]
