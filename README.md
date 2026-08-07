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

## Notes
* The application reads ```OPENAI_API_KEY``` from a local ```.env``` file. Never commit that file.
* Most previously missing UI secondary functions are now implemented (see update section).

## Update
The following previously incomplete UI and workflow issues have now been implemented and fixed:

* Connected both "Generate Q&A based on the textbook section" buttons to the generation pipeline.
* Fixed the Refine Q&A input wiring by passing `liked` correctly into `refine_qa(...)`.
* Aligned backend return values with Gradio output bindings to avoid runtime output mismatch errors.
* Implemented the "Export Q&As" action so users can export the saved question bank file.
* Added a status message field in the UI to show clear feedback for save, clear, and export actions.
* Connected `qa_purpose` to prompt construction so this UI field now affects generation behavior.
* Added a safe logging utility to prevent Windows GBK console crashes (`UnicodeEncodeError`) when prompts/responses include special characters.
* Added friendly API failure handling for generation/refinement: when quota is exceeded (HTTP 429), the web UI now shows a clear status message instead of crashing with a long traceback.
* Fully integrated `Evaluating` and `Creating` with dedicated prompt strategies, parser schemas, UI options, and export fields.
