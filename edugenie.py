### Prompt Elements ###

Q_TYPE = {}
LEARNING_OBJECTIVE = {}

SYSTEM_TEMPLATE = """You are an educational expert specializing in developing assessment questions tailored to specific requirements. You should always first review carefully the intended learning objectives and other characteristics for a question, and then compose it so that it best meets those requirements. Especially, pay attention to the cognitive skill that the question is expected to target, keeping in mind Bloom's Taxonomy of learning objectives:
	
Here are the strategies:
    - Remembering: Focuses on learners' ability to memorize, recognize, and recall information, facts, details, and terms. 
	- Understanding: Focuses on learners' ability to comprehend the meaning of concepts and principles and explain it in their own words. Related questions should assess learners' ability to interpret, demonstrate, classify, summarize, infer, compare and/or explain.
	- Applying: Focuses on learners' ability to apply knowledge (concepts, approaches, principles, techniques, skills) and use it to solve problems or perform tasks in new situations and contexts.
	- Analyzing: Focuses on learners' ability to break down information into its constituent parts and identify patterns, relationships, or connections among them.
	- Evaluating: Focuses on learners' ability to make judgments about the value or quality of ideas, solutions, or arguments. They can critique, assess, and defend their positions.
	- Creating: Focuses on learners' ability to generate new ideas, concepts, or products. They can synthesize information from different sources to create something new.
"""
HUMAN_TEMPLATE = """Develop {N} question/s based on the requirements below and the textbook section delimited by triple backticks. Note: learners may not have access to the textbook section, so avoid making references to it. 
{educational_context}
{examples}

{q_type}

{learning_objective}

{format_instructions}

Textbook Section:
```
{textbook_section}
```
"""

Q_TYPE["Multiple"] = """You should create multiple choice question/s. To write effective multiple-choice questions that target high cognitive skills, you should consider the following guidelines:
```
1. Create a focused stem: The stem of the question should be concise and clearly state the problem or situation being addressed. It should provide enough context for learners to understand what is being asked. If learners are being asked to assess an unseen scenario, describe the scenario using concrete details rather than in terms of the learned concepts. Remember – the learners should be able to draw their own connections between learned concepts and concrete scenario. 
2. Avoid extra information: Ensure that the stem does not include irrelevant or excessive information. This can distract learners the key concepts being assessed and may lead to confusion.
3. Use plausible distractors: options, including the correct answer and the distractors, should be plausible and similar in length to avoid giving away the answer. Distractors should represent common misconceptions or errors that learners might make and be attractive to learners who lack a complete understanding of the topic. Effective distractors can often use learned concepts from the text in incorrect ways that could be believable to someone with incomplete understanding of the topic.  
4. Avoid grammatical clues: Ensure that there are no grammatical clues or inconsistencies that give away the correct answer. Learners should rely solely on their understanding and application of the topic to select the correct response.
5. Avoid giving away clues with the tone of words: when formulating a distractor, avoid using words with a negative connotation or tone that could make the distractor unattractive to learners. For example, in a question about the way to address an employee how has performed a task with very little apparent care or effort, compare the following distractors:
	- ‘Micromanage the employee's every move to ensure they put in more effort’ – the connotation of the phrase ‘micromanage… every move’ is negative, which could make it too obvious that this answer is incorrect.
	- ‘"Provide detailed guidance and close monitoring to ensure the employee is putting in their best effort" – this rephrased version carries a similar meaning but uses a positive tone and is therefore much more plausible as a distractor.
6. Include clear instructions: Provide clear instructions regarding how many options learners should select, whether they should choose the best answer or all that apply. Ambiguous instructions can confuse learners and affect their performance.
7. Keep the options homogeneous but differentiated: Make sure that the options are similar in terms of style and grammar. This prevents learners from easily identifying the correct answer based on differences in language or formatting. At the same time, options should be well-differentiated in their meaning. 
8. Use a variety of question formats: Incorporate different question formats, such as multiple correct options, matching items, or scenarios, to keep the assessment diverse and engaging.
9. Write each option in a separate line.```
"""
Q_TYPE["Open"] = """You should create open questions"""

LEARNING_OBJECTIVE["Applying"] = """The questions should assess the learning objective of Application - learners' ability to apply knowledge (concepts, approaches, principles, techniques, skills) and use it to solve problems or perform tasks in a new scenario.

For each question you develop, do the following:
```
1.  Assign a number to the question (starting from 1)
2.  Identify one or more key elements (concepts/principles/approaches/techniques/skills) taught in the textbook, which could be effectively applied by learners to a new scenario in ways that allows assessing and promoting their understanding and ability to apply these elements to unseen contexts. If what is taught in the textbook cannot be effectively applied to a new scenario, say "The knowledge taught in the textbook cannot be effectively applied to a new scenario."  
3.  Construct a fairly detailed scenario, using 30 to 50 words, that invites learners to effectively apply to the scenario the taught elements you identified in step 1. The scenario should be new, offering learners an opportunity to apply their learning in a fresh way that goes beyond the examples given in the textbook. At the same time, the learned concepts from the textbook should be sufficient for allowing learners to engage with the scenario in a meaningful way.
4.  Using the scenario you constructed in step 2, develop a question that assesses the learner’s ability to apply the learned concepts you identified in step 1. 
5.  Answer the question you developed in step 3. 
6.  Explain the answer to the learner in a way that deepens their understanding of their learned concepts and promotes their ability to successfully answer similar questions in the future. 
```"""
LEARNING_OBJECTIVE["Remembering"] = """The questions should assess the learning objective of Remembering - to memorize, recognize, and recall information, facts, details, and terms. """
LEARNING_OBJECTIVE["Creating"] = """The questions should assess the learning objective of Creating - learners' ability to generate new ideas, concepts, or products by synthesizing information from the textbook section.

For each question assessing Creating, follow one of the strategies below. Pick strategies that fit the textbook section and vary the strategies as much as possible. The question should require learners to construct something new, not merely recall, explain, or evaluate existing information. Strategies:
```
    - Design: Ask learners to design a concrete solution, plan, model, or artifact that uses key concepts from the text. The task should include realistic constraints.
    - Compose: Ask learners to compose an explanation, argument, message, or product for a new purpose or audience by combining multiple ideas from the text.
    - Improve: Present an existing approach, product, or explanation and ask learners to redesign it into a stronger version using principles from the text.
    - Plan: Ask learners to create a step-by-step plan or procedure for addressing a new situation using ideas from the text.
    - Synthesize: Ask learners to combine two or more concepts from the text into a new framework, proposal, or example.
```

For each question you develop, do the following:
```
1. Assign a number to the question (starting from 1).
2. Identify the chosen creating strategy.
3. Identify the key concepts from the text that learners must synthesize.
4. State the constraints or requirements that make the task concrete and assessable.
5. Develop a question that asks learners to create a new product, plan, solution, or idea.
6. Provide an example of a strong answer or the correct answer.
7. Explain why the answer shows successful synthesis and creation.
```"""
LEARNING_OBJECTIVE["Evaluating"] = """The questions should assess the learning objective of Evaluating - learners' ability to make judgments about the value or quality of ideas, solutions, explanations, or arguments using criteria grounded in the textbook section.

For each question assessing Evaluating, follow one of the strategies below. Pick strategies that fit the textbook section and vary the strategies as much as possible. The question should require learners to judge, justify, critique, or defend a position rather than merely identify or explain information. Strategies:
```
    - Critique: Ask learners to identify strengths and weaknesses in an argument, solution, or explanation using concepts from the text.
    - Judge: Ask learners to decide which option, claim, or approach is best based on explicit criteria from the text.
    - Defend: Ask learners to defend a judgment or recommendation using evidence and reasoning from the text.
    - Prioritize: Ask learners to rank alternatives or considerations and justify the ranking using criteria from the text.
    - Test: Ask learners to evaluate whether a claim, solution, or explanation satisfies relevant principles from the text.
```

For each question you develop, do the following:
```
1. Assign a number to the question (starting from 1).
2. Identify the chosen evaluating strategy.
3. Identify the evaluation target: the claim, argument, solution, explanation, or choice learners must judge.
4. Identify the criteria learners should use for the judgment.
5. Develop a question that asks learners to make and justify an evaluation.
6. Provide the correct answer or an example of a strong answer.
7. Explain why the answer is well justified according to the criteria.
```"""
LEARNING_OBJECTIVE["Understanding"] = """The questions should assess the learning objective of Understanding - learners' ability to comprehend the meaning of concepts. Learners should interpret, demonstrate, classify, summarize, infer, compare and/or explain key ideas from the text. 

For each question, pick one of the strategies below for writing questions assessing understanding. Pick strategies based on their fit with the textbook section and vary your choices if appropriate. Strategies:
```
    - Exemplify: Ask learners to identify or create an example that does not appear in the textbook and instantiates a concept that does appear in it.
    - Restate: Ask learners to identify or create a definition of a concept that is defined or explained in the textbook, but stated in a way that is very different from that in the textbook. 
    - Classify: Ask learners classify an example that does not appear in the textbook according to classification(s) that do(es) appear in it. It can be especially effective to combine two orthogonal classifications from the textbook in one question; for example, combining the classifications of gas/liquid/solid and toxic/nontoxic, and ask learners to classify Carbon Monoxide (gas, toxic).
    - Infer: Construct an example or a scenario that do not appear in the textbook and ask learners to make an inference about the example/scenario based on what is taught in the textbook.
    - Summarize: Outline an idea that is articulated in a longer form over a section of the textbook.  
```"""
LEARNING_OBJECTIVE["Analyzing"] = """The questions should assess the learning objective of Analyzing - learners' ability to break down information into its constituent parts and identify patterns, relationships, or connections among them. 

For each question assessing Understanding, follow one of the strategies below. Pick strategies that would make the most effective questions for the textbook section and vary the strategies as much as possible. Creating questions using these strategies requires a preliminary analysis step, which is specified for each strategy. Strategies:
```
    - Assumptions: Ask learners to identify the assumptions they need to make for a certain proposition, theory, or claim from the text to be valid. Preliminary analysis: What is a proposition/claim/theory in the text that requires certain assumptions? What are these assumptions?
    - Commonality: Ask learners to identify a common theme in the text or common characteristics among the taught elements, which are not stated explicitly in the text. Preliminary analysis: What is the common theme or what are the common characteristics?  
    - Comparison: Ask learners to compare and contrast entities or entity parts from the text in new ways that are not stated explicitly in it. The comparison should be insightful and deepen learners’ understanding. Preliminary analysis: What are the entities for comparison? What are the dimensions for comparison?    
	- Classification: Ask learners to classify entities or entity parts from the text in new ways that are not explicit in it. The classification should be insightful and deepen learners’ understanding. Preliminary analysis: What are the entities to classify? What is the classification system?
    - Solution: Ask learners to find a solution that does not appear in the text to a problem/puzzle/tension that does appear in the text. Preliminary analysis: What is the problem/puzzle/tension? 
	- Prediction: Describe a scenario that does not appear in the text but relates to it and ask learners to determine plausible and/or implausible causes or outcomes of that situation. Preliminary analysis: What is the situation? What is the cause or outcome?
```
"""

REFINE_TEMPLATE= """Create a question and answer based on the feedback and requirements below. Note: learners may not have access to the textbook section, so avoid making references to it.

{q_type}

The question should follow the selected learning objective instructions:
{learning_objective}

This question should assess the following learning goal:
{learning_goal}

Textbook Section:
```
{textbook_section}
```

Following is feedback on the generated question and answer. The overall rating is {rating} out of 5, which means they are {rating_meaning}.
Things I liked about the generated Q&A: '{liked}'
Things that should be improved: '{to_improve}'
{next_step}

{format_instructions}
"""


REFINE_TEMPLATE_EXISTING= """
You have previously generated a question based on a textbook passage. You must revise
this question based on the feedback given and requirements listed below and the textbook section delimited by triple backticks. Note: learners may not have access to the textbook section, so avoid making references to it. 



{q_type}
The question was generated based on the following textbook section:
Textbook Section:
```
{textbook_section}
```

The question was developed based on the following learning objective instructions: {learning_objective}.

This question was generated to assess the following learning goal:
{learning_goal}
The following is the question that you had previously created.
Question: {question}
Options: {options}
Correct Answer: {correct_answer}
Explanation: {explanation}

The following is feedback on the generated question and answer. The overall rating is {rating} out of 5, which means they are {rating_meaning}.
Things I liked about the generated Q&A: '{liked}'
The question should be improved by following these instructions: '{to_improve}'

Revise this question based on the feedback given and the requirements listed below. The revised question
must follow the selected question type requirements above and the output format instructions below.


{next_step} 


{format_instructions}





"""
RATING_MEANING = {1: "way off the mark",
                  2: "not very good", 
                  3: "just so so",
                  4: "quite good, but needs minor improvement",
                  5: "right on!"
                 }
REFINE_NEXT_STEP = {"Revise the Q&A": "Revise the question and answer based on the user's feedback.",
					"Create new Q&A": "Create a new question and answer based on the user's feedback."
					}

INITIAL_OBJECTIVE = "Understanding"

### Classes ###
from langchain.pydantic_v1 import BaseModel, Field, validator
from typing import List

class ApplicationQA(BaseModel):
	q_num: int = Field(description="question number")
	key_elements: List[str] = Field(description="key elements to assess")
	scenario: str = Field(description="the scenario to base the question on")
	question: str = Field(description="question based on the scenario")
	options: str = Field(description="the options for the answer; inthe question is open and no options are provided, return an empty string")
	correct_answer: str = Field(description="if the question is multiple choice, the letter representing the correct answer; if the question is open, an example of a good answer")
	explanation: str = Field(description="an explanation of the correct answer")

	def get_question(self): 
		std_q = self.scenario + " " + self.question + "\n\n" + self.options
		return std_q
		
class AnalyzingQA(BaseModel): 	
	q_num: int = Field(description="question number")
	strategy: str = Field(description="the chosen strategy (Assumptions/Commonality/Comparison/Classification/Solution/Prediction)")
	analysis: str = Field(description="the output of the preliminary analysis step for the chosen strategy")
	question: str = Field(description="question based on the chosen strategy and the analysis; please note that learners will not have access to the analysis, so the question should be understandable by itself")
	options: str = Field(description="if the question is multiple choice, the options for the answer; if the question is open, return an empty string")
	correct_answer: str = Field(description="if the question is multiple choice, the letter representing the correct answer; if the question is open, an example of a good answer")
	explanation: str = Field(description="an explanation of the correct answer")

	def get_question(self): 
		std_q = self.question + "\n\n" + self.options
		return std_q
		
class UnderstandingQA(BaseModel):
	q_num: int = Field(description="question number")
	strategy: str = Field(description="the chosen strategy (Exemplify/Restate/Classify/Infer/Summarize)")
	question: str = Field(description="question based on the strategy")
	options: str = Field(description="if the question is multiple choice, the options for the answer; if the question is open, return an empty string")
	correct_answer: str = Field(description="if the question is multiple choice, the letter representing the correct answer; if the question is open, an example of a good answer")
	explanation: str = Field(description="an explanation of the correct answer")

	def get_question(self): 
		print(self.question)
		print(self.options)
		print(self.correct_answer)
		std_q = self.question + "\n\n" + self.options
		return std_q

class RememberingQA(BaseModel):
	q_num: int = Field(description="question number")
	question: str = Field(description="question")
	options: str = Field(description="if the question is multiple choice, the options for the answer; if the question is open, return an empty string")
	correct_answer: str = Field(description="if the question is multiple choice, the letter representing the correct answer; if the question is open, an example of a good answer")
	explanation: str = Field(description="an explanation of the correct answer")

	def get_question(self): 
		std_q = self.question + "\n\n" + self.options
		return std_q

class EvaluatingQA(BaseModel):
	q_num: int = Field(description="question number")
	strategy: str = Field(description="the chosen strategy (Critique/Judge/Defend/Prioritize/Test)")
	evaluation_target: str = Field(description="the claim, argument, solution, explanation, or choice that learners must evaluate")
	criteria: List[str] = Field(description="the criteria learners should use to make the evaluation")
	question: str = Field(description="question that asks learners to make and justify an evaluation")
	options: str = Field(description="if the question is multiple choice, the options for the answer; if the question is open, return an empty string")
	correct_answer: str = Field(description="if the question is multiple choice, the letter representing the correct answer; if the question is open, an example of a strong answer")
	explanation: str = Field(description="an explanation of why the answer is well justified according to the criteria")

	def get_question(self):
		std_q = self.question + "\n\n" + self.options
		return std_q

class CreatingQA(BaseModel):
	q_num: int = Field(description="question number")
	strategy: str = Field(description="the chosen strategy (Design/Compose/Improve/Plan/Synthesize)")
	key_concepts: List[str] = Field(description="key concepts from the text that learners must synthesize")
	constraints: str = Field(description="the constraints or requirements that make the creation task concrete and assessable")
	question: str = Field(description="question that asks learners to create a new product, plan, solution, or idea")
	options: str = Field(description="if the question is multiple choice, the options for the answer; if the question is open, return an empty string")
	correct_answer: str = Field(description="if the question is multiple choice, the letter representing the correct answer; if the question is open, an example of a strong answer")
	explanation: str = Field(description="an explanation of why the answer shows successful synthesis and creation")

	def get_question(self):
		std_q = self.question + "\n\n" + self.options
		return std_q

class OpenQA(BaseModel):
	q_num: int = Field(description="question number")
	question: str = Field(description="question based on the strategy")
	correct_answer: str = Field(description="if the question is multiple choice, the letter representing the correct answer; if the question is open, an example of a good answer to the question")
	explanation: str = Field(description="an explanation of the correct answer")

	def get_question(self): 
		std_q = self.question
		return std_q

class AppQAList(BaseModel):
	QAs: List[ApplicationQA]

	def get_response(self):
		response = ""
		for q in self.QAs:
			response += "\n" + str(q.q_num) + ". " + q.get_question() + "\n\nCorrect Answer: " + q.correct_answer + "\n\nExplanation: " + q.explanation + "\n"
		return response
    
class UndQAList(BaseModel):
	QAs: List[UnderstandingQA]

	def get_response(self):
		response = ""
		for q in self.QAs:
			response += "\n" + str(q.q_num) + ". " + q.get_question() + "\n\nCorrect Answer: " + q.correct_answer + "\n\nExplanation: " + q.explanation + "\n"
		return response
    
class AnaQAList(BaseModel):
	QAs: List[AnalyzingQA]

	def get_response(self):
		response = ""
		for q in self.QAs:
			response += "\n" + str(q.q_num) + ". " + q.get_question() + "\n\nCorrect Answer: " + q.correct_answer + "\n\nExplanation: " + q.explanation + "\n"
		return response
        
class RemQAList(BaseModel):
	QAs: List[RememberingQA]

	def get_response(self):
		response = ""
		for q in self.QAs:
			response += "\n" + str(q.q_num) + ". " + q.get_question() + "\n\nCorrect Answer: " + q.correct_answer + "\n\nExplanation: " + q.explanation + "\n"
		return response

class EvalQAList(BaseModel):
	QAs: List[EvaluatingQA]

	def get_response(self):
		response = ""
		for q in self.QAs:
			response += "\n" + str(q.q_num) + ". " + q.get_question() + "\n\nCorrect Answer: " + q.correct_answer + "\n\nExplanation: " + q.explanation + "\n"
		return response

class CreateQAList(BaseModel):
	QAs: List[CreatingQA]

	def get_response(self):
		response = ""
		for q in self.QAs:
			response += "\n" + str(q.q_num) + ". " + q.get_question() + "\n\nCorrect Answer: " + q.correct_answer + "\n\nExplanation: " + q.explanation + "\n"
		return response
    
class OpenList(BaseModel):
	QAs: List[OpenQA]
    
	def get_response(self):
		response = ""
		for q in self.QAs:
			response += "\n" + str(q.q_num) + ". " + q.get_question() + "\n\nCorrect Answer: " + q.correct_answer + "\n\nExplanation: " + q.explanation + "\n"
		return response
QA_STRUCT = {"Remembering": RemQAList,
			   "Understanding": UndQAList,
               "Applying": AppQAList,
			   "Analyzing": AnaQAList,
			   "Creating": CreateQAList,
			   "Evaluating": EvalQAList}