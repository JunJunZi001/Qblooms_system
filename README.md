# edugenie-academic
This is a tool that generates questions, answers, and explanations that address specific cognitive skills: **Remembering** - Recall facts and basic concepts; **Understanding** - Comprehend and explain the meaning of ideas or concepts; **Applying** - Use information in new situations and contexts; **Analyzing** - Draw connections and identify patterns among ideas; **Evaluating** - Make and justify judgments using criteria; **Creating** - Generate new ideas, plans, solutions, or products by synthesizing concepts. The Q&As are generated based on user specifications and an input educational text.

The project includes the following files:
* ```app.py```: the main Gradio application and question-generation workflow.
* ```edugenie.py```: prompt components and output data structures.
* ```QuestionsText/```: public few-shot examples used to build the local vector store.
* ```requirements.txt```: Python dependencies.
* ```.env.example```: environment-variable template.

## Installation

1. Create and activate a Python virtual environment.
2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy ```.env.example``` to ```.env``` and add your OpenAI API key.
4. Start the application:

   ```bash
   python app.py
   ```

The local Chroma vector store is generated automatically from the examples in
```QuestionsText/``` when the application starts.

