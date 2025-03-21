import networkx as nx, prompts, re
from typing import List, Dict
from rich.markdown import Markdown
from rich.panel import Panel
from rich import print as rprint
from rich.console import Console
from rich.tree import Tree
from llm_caller import LLMCaller
import matplotlib.pyplot as plt

def print_graph(G):
    console = Console()
    tree = Tree(f"DiGraph with {len(G.nodes())} nodes and {len(G.edges())} edges")
    
    for node in G.nodes():
        node_branch = tree.add(f"Node: [bold cyan]{node}[/bold cyan]")
        successors = list(G.successors(node))
        if successors:
            succ_branch = node_branch.add("Successors:")
            for successor in successors:
                edge_data = G.get_edge_data(node, successor)
                edge_info = f"to {successor}"
                if edge_data:
                    edge_info += f" ({edge_data})"
                succ_branch.add(edge_info)
    
    console.print(tree)

def print_graph_compact(G):
    console = Console()
    edges = [f"[cyan]{src}[/] → [magenta]{dst}[/]" for src, dst in G.edges()]
    console.print("Graph edges:")
    console.print("\n".join(edges))
    console.print(f"\nTotal nodes: {len(G.nodes())}")
    console.print(f"Total edges: {len(G.edges())}")

class AtomOfThought:
    def __init__(self, llm_caller: LLMCaller, debug: bool = True):
        self.llm = llm_caller
        self.debug = debug

    def decompose_question(self, question: str) -> nx.DiGraph:
        prompt = prompts.decompose_question(question)
        subquestions = self.llm.generate(prompt)
        if self.debug:
            rprint(Panel(Markdown(subquestions), title="Decompose Question"))

        subquestion_pairs = []
        subquestion_matches = re.finditer(r"\*\sSubquestion\s\d+(?:\n|\s).*?(?=\n*\*\sSubquestion\s\d+|$)", subquestions, flags=re.DOTALL)
        for match in subquestion_matches:
            match = match.group(0).strip()
            subquestion = re.search(r"Subquestion:\s(.*)", match)
            if subquestion:
                subquestion = subquestion.group(1).strip()
                dependencies = re.search(r"Dependencies:\s(.*)", match)
                if dependencies:
                    dependencies = dependencies.group(1).strip().lower()
                    if dependencies == "none":
                        dependencies = []
                    else:
                        dependencies_match = re.findall(r"subquestion\s(\d+)", dependencies)
                        dependencies_indices = []
                        for match in dependencies_match:
                            dependencies_indices.append(int(match) - 1)
                        dependencies = dependencies_indices
                    subquestion_pairs.append((subquestion, dependencies))
                else:
                    subquestion_pairs.append((subquestion, None))
        
        G = nx.DiGraph()
        for subquestion, dependencies in subquestion_pairs:
            G.add_node(subquestion)
            for dependency in dependencies:
                G.add_edge(subquestion_pairs[dependency][0], subquestion)

        return G

    def answer_subquestions(self, question: str, subquestions: List[str]) -> List[str]:
        answers = [
            self.llm.generate(prompts.answer_subquestion(question, subquestion))
            for subquestion in subquestions
        ]        
        question_answers = zip(subquestions, answers)
        answers = [
            f"* **Subquestion**: {question}\n* **Answer**: {answer}"
            for question, answer in question_answers
        ]
        if self.debug:
            rprint(Panel(Markdown("\n\n".join(answers)), title="Answers"))
        return answers

    def answer_question(self, question: str) -> str:
        answer_prompt = prompts.answer_question(question)
        if self.debug:
            rprint(Panel(Markdown(answer_prompt), title="Answer"))
        return self.llm.generate(answer_prompt)

    def valid_answer(self, question: str, answer: str) -> bool:
        decision = self.llm.generate(prompts.evaluate_solution(question, answer))
        if decision:
            return decision.lower().strip() == "yes"
        return False

    def solve_problem(self, problem: str, terminate_on_answer: bool = True) -> Dict[str, str]:
        """A way of decomposing a question into subquestions. These subquestions get `compacted` into a single question. Therefore, this can be used to simply reword a question considering it's atomic subquestions. If `terminate_on_answer` is `True`, then this will stop the DAG traversal on a valid answer.

        Args:
            problem (str): The problem to solve.
            terminate_on_answer (bool, optional): Try to answer question each iteration and stop when one found. If `False`, then traverse the whole DAG and compact until you get all independent (atomic) subquestions. Defaults to `True`.

        Returns:
            Dict: A dictionary with `question` and `answer` keys.
        """
        Q0 = problem
        i = 0
        D = None
        Qi = Q0
        Ai = None

        while D is None or i < D:
            # decompose question into subquestions
            Gi = self.decompose_question(Qi)

            if D is None:
                # on initial decomposition, determine largest dag depth
                D = nx.dag_longest_path_length(Gi)
                D = max(D, 0)

            # answer subquestions that are independent
            Q_ind = [node for node in Gi if Gi.in_degree(node) == 0]            
            answers = self.answer_subquestions(Qi, Q_ind)

            Q_dep = [node for node in Gi if Gi.in_degree(node) > 0]
            if Q_dep:
                # if we have dependencies compact question considering remaining, dependent subquestions
                compact_prompt = prompts.restate_question_given_answers(Qi, answers, Q_dep)
                if self.debug:
                    rprint(Panel(Markdown(compact_prompt), title="Compact Question"))
                Qi_next = self.llm.generate(compact_prompt)
            else:
                # should be able to answer given no dependency
                # however, if evaluation fails it will decompose the same question
                Qi_next = Qi
        
            if terminate_on_answer:
                # try to answer question
                Ai = self.answer_question(Qi_next)
                if self.valid_answer(Qi_next, Ai):
                    # if we have a valid answer no need to do further decomposition
                    return {
                        "question": Qi_next,
                        "answer": Ai
                    }

            Qi = Qi_next    
            i += 1

        Ai = self.answer_question(Qi)

        return {
            "question": Qi,
            "answer": Ai
        }
            


if __name__ == "__main__":
    # question = "Find operations to make 24 from the number: 4, 9, 10, and 13."
    # question = "What are the best use-cases for microservices?"
    # question = "Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?"
    # question = "What are the societal impacts of automation?"
    question = "How can traffic congestion be reduced in large cities?"

    llm = LLMCaller()
    atom = AtomOfThought(llm)
    response = atom.solve_problem(question)
    rprint(Panel(Markdown(response["question"]), title="Final Question"))
    rprint(Panel(Markdown(response["answer"]), title="Final Answer"))