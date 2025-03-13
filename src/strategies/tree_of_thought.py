import prompts
from dataclasses import dataclass
from typing import Optional, List, Dict
from llm_caller import LLMCaller
from rich.tree import Tree
from rich.markdown import Markdown
from rich import print as rprint

@dataclass
class TreeStep:
    thought: str
    answer: Optional[str] = None
    confidence: Optional[float] = 0.0
    best: Optional[bool] = False
    final: Optional[bool] = False

class TreeNode:
    def __init__(self, question: str, step: Optional[TreeStep] = None, parent: Optional["TreeNode"] = None):
        self.question = question
        self.step = step if step else TreeStep(question, best=True)
        self.parent: TreeNode = parent
        self.children: List[TreeNode] = []
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
        self.step.answer = answer

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

    def get_original_question(self) -> str:
        if self.parent is None:
            return self.question
        return self.parent.get_original_question()

    def get_steps(self) -> List[TreeStep]:
        if self.parent is None:
            return []
        steps = self.parent.get_steps()
        if self.step and self.step.answer:
            steps.append(self.step)
        return steps

    def get_steps_markdown(self) -> str:
        result = []
        for i, step in enumerate(self.get_steps()):
            thought_answer = f"### Step {i+1}:\n* Thought: {step.thought}\n* Answer: {step.answer}"
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
            max_branches: int = 2
        ):
        self.llm = llm
        self.initial_branches = initial_branches
        self.max_branches = max_branches
        self.problem = problem
        self.root = TreeNode(problem)

    def _calculate_confidence(self, confidence: Dict[str, str]) -> float:
        logic = confidence["logic"].lower().strip()
        completeness = confidence["completeness"].lower().strip()
        errors = confidence["errors"].lower().strip()
        
        logic_score = 0.0
        if logic == "yes":
            logic_score = 1.0
        elif logic == "no":
            logic_score = 0.0
        elif logic == "partially":
            logic_score = 0.5

        completeness_score = 0.0
        if completeness == "yes":
            completeness_score = 1.0
        elif completeness == "no":
            completeness_score = 0.0
        elif completeness == "partially":
            completeness_score = 0.5

        errors_score = 0.0
        if errors == "yes":
            errors_score = 1.0
        elif errors == "no":
            errors_score = 0.0
        elif errors == "maybe":
            errors_score = 0.5

        return round((logic_score + completeness_score + errors_score) / 3.0, 2)
        

    def explore_thoughts(self, node: TreeNode, current_depth: int = 1) -> Optional[TreeNode]:
        if current_depth >= self.max_branches:
            return None

        # from this node find branch thoughts
        next_steps = prompts.next_steps(node, self.max_branches)
        thoughts = self.llm.generate(next_steps, json_format=True)["next_steps"]
        
        correct_thoughts: List[TreeNode] = []
        for thought in thoughts:
            new_node = TreeNode(node.get_original_question(), TreeStep(thought), node)

            # using this thought, previous reasoning, answer the question
            thought_answer = self.llm.generate(prompts.answer_step(new_node), json_format=True)["answer"]
            if thought_answer:
                new_node.add_step_answer(thought_answer)

                # evaluate if this answer is any good
                confidence = self.llm.generate(prompts.evaluate_step(new_node), json_format=True)
                confidence_score = self._calculate_confidence(confidence)
                new_node.add_step_confidence(confidence_score)
                correct_thoughts.append(new_node)
            else:
                # if no answer, then there is no need to evaluate; explore more thoughts   
                result = self.explore_thoughts(new_node, current_depth + 1) 
                if result:
                    correct_thoughts.append(result)

         
        # of the correct results, decide which one is the best
        best_thought: TreeNode = max(correct_thoughts, key=lambda x: x.step.confidence)
        best_thought.step.best = True

        return best_thought
                

    def solve_problem(self) -> str:
        initial_prompt = prompts.next_steps(self.root, self.initial_branches)
        initial_thoughts = self.llm.generate(initial_prompt, json_format=True)["next_steps"]
        initial_nodes = [TreeNode(self.root.get_original_question(), TreeStep(thought), self.root) for thought in initial_thoughts]

        best_answers = [
            self.explore_thoughts(node)
            for node in initial_nodes   
        ]        
        best_answer: TreeNode = max(best_answers, key=lambda x: x.step.confidence)  
        best_answer.step.final = True  

        return best_answer.step.answer    
            
            
if __name__ == "__main__":
    # question = "Find operations to make 24 from the number: 4, 9, 10, and 13."
    question = "What are micro-services?"
    tot = TreeOfThought(LLMCaller(), question)
    answer = tot.solve_problem()
    tot.root.display_tree()
    print()
    rprint(Markdown(answer))

    # root = TreeNode(question)
    # second = TreeNode(question, TreeStep("second step", best=True), root)
    # third = TreeNode(question, TreeStep("third step"), root)
    # second_first = TreeNode(question, TreeStep("second first step"), second)
    # second_second = TreeNode(question, TreeStep("second second step", best=True, final=True), second)    
    # root.display_tree()
    