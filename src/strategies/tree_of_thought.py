import config.prompts as prompts, re
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from tools.llm_caller import LLMCaller
from rich.tree import Tree
from rich.markdown import Markdown
from rich.panel import Panel
from rich import print as rprint
from enum import Enum

class EvaluationStrategy(Enum):
    CALCULATE = "calculate"
    COMPARE = "compare"

@dataclass
class TreeStep:
    thought: str
    answer: Optional[str] = None
    confidence: Optional[float] = 0.0
    best: Optional[bool] = False
    final: Optional[bool] = False
    prompts: Optional[Dict[str, Optional[str]]] = field(default_factory=lambda: {
        "next_steps": None,
        "answer": None
    })

class TreeNode:
    def __init__(
            self, 
            question: str, 
            step: Optional[TreeStep] = None, 
            parent: Optional["TreeNode"] = None,
            depth: int = 0,
            id: int = 0
        ):
        self.question = question
        self.step = step if step else TreeStep(question, best=True)
        self.parent: TreeNode = parent
        self.children: List[TreeNode] = []
        self.depth = depth
        self.id = id
        if self.parent:
            self.parent.add_child(self)

    def get_parents(self) -> List["TreeNode"]:
        if self.parent is None:
            return []
        parents = self.parent.get_parents()
        parents.append(self.parent)
        return parents

    def get_root(self) -> "TreeNode":
        if self.parent is None:
            return self
        return self.get_parents()[0]

    def add_child(self, child: "TreeNode"):
        self.children.append(child)

    def add_step_answer(self, answer: str) -> None:
        self.step.answer = str(answer)

    def add_step_confidence(self, confidence: float) -> None:
        self.step.confidence = confidence

    def get_reasoning(self) -> List[str]:
        if self.parent is None:
            return []
        reasoning = self.parent.get_reasoning()
        reasoning.append(self.step.thought)
        return reasoning

    def get_answers(self) -> List[str]:
        answers = self.parent.get_answers()
        if self.step and self.step.answer:
            answers.append(self.step.answer)
        return answers

    def get_steps(self) -> List[TreeStep]:
        if self.parent is None:
            return []
        steps = self.parent.get_steps()
        if self.step:
            steps.append(self.step)
        return steps

    def get_steps_markdown(self) -> str:
        steps = self.get_steps()
        if len(steps) == 0:
            return "None"
        result = []
        for i, step in enumerate(steps):
            thought_answer = f"### Step {i+1}:\n{step.thought}"
            result.append(thought_answer)        
        return "\n".join(result)   

    def display(self) -> None:
        parents = self.get_parents() + [self]
        root = Tree(parents[0].step.thought)
        tree = [root]
        for i in range(len(parents) - 1):
            next_parent = parents[i+1]
            child = tree[i].add(next_parent.step.thought)
            tree.append(child)                
        return rprint(root)

    def get_tree_branches(self, node: "TreeNode") -> Tree:
        if node.step.best:
            if node.step.final:
                value = f"[yellow bold]{node.step.thought} ({node.step.confidence}) (BEST)"
            else:
                value = f"[blue bold]{node.step.thought} ({node.step.confidence})"
        else:
            value = node.step.thought
        root = Tree(value)
        for child in node.children:
            child_tree = self.get_tree_branches(child)
            root.add(child_tree)
        return root

    def display_tree(self) -> None:
        tree = self.get_tree_branches(self)
        return rprint(tree)

    def __str__(self):
        if self.step is None:
            return "\nNo step"
        return f"""
Thought: {self.step.thought}
Answer: {self.step.answer}
Confidence: {self.step.confidence}
"""      


class TreeOfThought:
    def __init__(
            self, 
            llm: LLMCaller, 
            problem: str, 
            initial_branches: int = 2, 
            max_branches: int = 2,
            max_depth: int = 2,
            evaluate: EvaluationStrategy = EvaluationStrategy.CALCULATE,
            be_conservative: bool = False,
            confidence_threadhold: float = 0.5
        ):
        self.llm = llm
        self.initial_branches = initial_branches
        self.max_branches = max_branches
        self.max_depth = max_depth
        self.problem = problem
        self.root = TreeNode(problem)
        self.evaluate = evaluate
        self.be_conservative = be_conservative
        self.confidence_threshold = confidence_threadhold

    def _calculate_confidence(self, confidence: Dict[str, str]) -> float:
        logic = confidence["logic"].lower().strip()
        completeness = confidence["completeness"].lower().strip()
        clarity = confidence["clarity"].lower().strip()
        
        logic_score = 0.0
        if logic == "yes":
            logic_score = 1.0
        elif logic == "no":
            logic_score = 0.0

        completeness_score = 0.0
        if completeness == "yes":
            completeness_score = 1.0
        elif completeness == "no":
            completeness_score = 0.0

        clarity_score = 0.0
        if clarity == "yes":
            clarity_score = 1.0
        elif clarity == "no":
            clarity_score = 0.0

        return round((.5 * logic_score) + (.3 * completeness_score) + (.2 * clarity_score), 2)
        
    def _pick_best_answer(self, answers: List[TreeNode]) -> TreeNode:
        prompt = prompts.compare_answers(answers)
        best_answer_number = self.llm.generate(prompt, json_format=True)["best_answer"]
        return answers[best_answer_number - 1]

    def explore_thoughts(self, node: TreeNode, current_depth: int = 1) -> Optional[TreeNode]:
        """
        Explores a tree of thoughts that may answer the question at the root node in the tree. This appraoch
        uses depth-first-search strategy.

        There are two reasons that cause this algorithm to go deeper in the tree:
        1. No answer can be found given the reasoning steps at the current depth.
        2. An answer was provided at this depth but fails to meet confidence threshold (only for calculate strategy)
        """
        if current_depth > self.max_depth:
            return None

        # from this node find branch thoughts
        next_steps = prompts.next_steps(node, self.max_branches)
        node.step.prompts["next_steps"] = next_steps
        thoughts = self.llm.generate(next_steps, json_format=True)["next_steps"]   
        thoughts = thoughts[:self.max_branches]     
        
        correct_thoughts: List[TreeNode] = []
        for i, thought in enumerate(thoughts):
            thought = thought.strip()
            new_node = TreeNode(node.question, TreeStep(thought), node, depth=current_depth, id=i)
            rprint(f"[dim]{current_depth + 2}.{new_node.id + 1} {new_node.step.thought}")

            # using thoughts answer the question
            answer_prompt = prompts.answer_step(new_node)
            new_node.step.prompts["answer"] = answer_prompt
            thought_answer = self.llm.chat(answer_prompt, format="json")
            if thought_answer and "answer" in thought_answer and thought_answer["answer"]:
                thought_answer = thought_answer["answer"]
                new_node.add_step_answer(thought_answer)

                # evaluate if this answer is any good
                if self.evaluate == EvaluationStrategy.CALCULATE:
                    confidence = self.llm.generate(prompts.evaluate_step(new_node), json_format=True)
                    confidence_score = self._calculate_confidence(confidence)
                    new_node.add_step_confidence(confidence_score)
                    if confidence_score < self.confidence_threshold:                        
                        result = self.explore_thoughts(new_node, current_depth + 1) # continue looking or better
                        if result:
                            correct_thoughts.append(result)
                    else:
                        correct_thoughts.append(new_node)
            elif not self.be_conservative:
                # if no answer, then there is no need to evaluate; explore more thoughts   
                result = self.explore_thoughts(new_node, current_depth + 1) 
                if result:
                    correct_thoughts.append(result)
         
        # of the correct results, decide which one is the best
        if len(correct_thoughts) == 0:
            return None
        
        if self.evaluate == EvaluationStrategy.COMPARE:
            best_thought: TreeNode = self._pick_best_answer(correct_thoughts)
        else:
            best_thought: TreeNode = max(correct_thoughts, key=lambda x: x.step.confidence)
        best_thought.step.best = True

        return best_thought                

    def solve_problem(self) -> str:
        initial_prompt = prompts.next_steps(self.root, self.initial_branches)
        initial_thoughts = self.llm.generate(initial_prompt, json_format=True)["next_steps"]
        initial_nodes = [TreeNode(self.root.question, TreeStep(thought, best=True), self.root) for thought in initial_thoughts]
        
        rprint(f"[dim]1.1 {self.problem}")
        for i, node in enumerate(initial_nodes):
            rprint(f"[dim]2.{i+1} {node.step.thought}")

        best_answers = [
            self.explore_thoughts(node)
            for node in initial_nodes   
        ]   
        best_answers = [answer for answer in best_answers if answer]

        if len(best_answers) == 0:
            rprint("[bold red]No answer found")
            return None

        if self.evaluate == EvaluationStrategy.COMPARE:
            best_answer: TreeNode = self._pick_best_answer(best_answers)
        else:
            best_answer: TreeNode = max(best_answers, key=lambda x: x.step.confidence)  
            
        best_answer.step.final = True  

        rprint(Panel(Markdown(best_answer.parent.step.prompts["next_steps"]), title="Next Steps", border_style="blue", title_align="left"))    
        rprint(Panel(Markdown(best_answer.step.prompts["answer"]), title="Answer Prompt", border_style="blue", title_align="left"))

        return best_answer.step.answer    
            
    def solve_with_experts(self) -> str:
        """Attempts to solve the problem using 3 experts with a single prompt.

        This approach is a simplification of the full tree-of-thought where each expert is like branch and the number of rounds is like the depth of the tree. The instructions ask that an expert drop out if thy are wrong, which is trying to mimic the pruning part of the process (though they never seem to drop out in my experience).

        Returns:
            str: The answer provided by the experts.
        """
        prompt = prompts.three_experts(self.problem)
        expert_answer = self.llm.generate(prompt)
        rprint(Panel(Markdown(expert_answer), title="Experts", border_style="blue", title_align="left"))
        match = re.search(r"ANSWER:\s(.*)", expert_answer)
        if match:
            return match.group(1).strip()
        return None

if __name__ == "__main__":
    from tools.wiki import get_wikipedia_article
    from tools.perplexity import search_internet
    from tools.math import multiply_numbers

    tools = [
        get_wikipedia_article,
        search_internet,
        multiply_numbers,
    ]

    # question = "Find operations to make 24 from the number: 4, 9, 10, and 13."
    # question = "What are the best use-cases for microservices?"
    # question = "What is the latest new regarding the current president of the United States Donald Trump?"
    # question = "Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?"
    question = "What is 2 * 3 * 112?"
    tot = TreeOfThought(
        LLMCaller(tools=tools), 
        question, 
        max_branches = 2, 
        max_depth=3,
        evaluate=EvaluationStrategy.CALCULATE,
        be_conservative=False
    )
    # answer = tot.solve_problem()
    # print()
    # tot.root.display_tree()
    # print()
    # rprint(Panel(Markdown(answer), title="Final Answer", border_style="blue", title_align="left"))

    print()
    expert_answer = tot.solve_with_experts()
    if expert_answer:
        rprint(Panel(Markdown(expert_answer), title="Expert Answer", border_style="blue", title_align="left"))
    else:
        rprint("[red bold]No expert answer found.")
    

    