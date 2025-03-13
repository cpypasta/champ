from typing import List, Dict, Optional, Any
import re, prompts
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from rich.markdown import Markdown
from llm_caller import LLMCaller

class TreeOfThought:
    """
    Implementation of Tree-of-Thought reasoning with an LLM.
    This approach generates multiple reasoning paths and evaluates them to find the best solution.
    """
    
    def __init__(self, llm_caller: LLMCaller, max_branches: int = 3, max_depth: int = 3, verbose: bool = True):
        """
        Initialize the Tree-of-Thought solver.
        
        Args:
            llm_caller: Instance of LLMCaller for generating responses
            max_branches: Maximum number of branches to explore at each node
            max_depth: Maximum depth of the reasoning tree
            verbose: Whether to display rich visualizations in the console
        """
        self.llm_caller = llm_caller
        self.max_branches = max_branches
        self.max_depth = max_depth
        self.verbose = verbose
        self.console = Console()
        
        # Create visualization tree for the reasoning process
        self.reasoning_tree = None
        self.path_count = 0
        self.solution_count = 0
           
    def solve_problem(self, problem: str) -> Dict[str, Any]:
        """
        Solve a problem using tree-of-thought approach.
        
        Args:
            problem: The problem statement
            
        Returns:
            Dictionary containing the best solution and its reasoning path
        """
        if self.verbose:
            self.console.print(Panel(f"[bold blue]Problem:[/bold blue] {problem}", 
                                    title="Tree-of-Thought Solver", 
                                    border_style="blue"))
            
            # Initialize the visualization tree
            self.reasoning_tree = Tree("[bold yellow]Reasoning Paths[/bold yellow]")
            
        # Initial thoughts
        if self.verbose:
            self.console.print("[bold blue]Generating initial approaches...[/bold blue]")
            
        initial_thoughts = self._generate_initial_thoughts(problem)
        
        if self.verbose:
            self.console.print(f"[green]Generated {len(initial_thoughts)} initial approaches[/green]")

        # Build reasoning tree
        solutions = []
        
        if self.verbose:
            self.console.print("[bold blue]Exploring reasoning paths...[/bold blue]")
            # Progress bar for tracking overall progress
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}[/bold blue]"),
                BarColumn(),
                TextColumn("{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console
            )
            progress.start()
            # Create a task for overall progress
            total_paths = len(initial_thoughts)
            main_task = progress.add_task("[blue]Overall progress", total=total_paths)
        
        for i, thought in enumerate(initial_thoughts):
            if self.verbose:
                branch_text = Text(f"Approach {i+1}: ", style="bold cyan")
                branch_text.append(thought, style="cyan")
                branch = self.reasoning_tree.add(branch_text)
                
                progress.update(main_task, description=f"[blue]Exploring path {i+1}/{total_paths}")
            else:
                branch = None
            
            solution = self._explore_path(problem, [thought], 1, parent_node=branch)
            
            if solution:
                solutions.append(solution)
                if self.verbose and branch:
                    solution_text = Text("✓ ", style="bold green")
                    solution_text.append(f"Solution (confidence: {solution['confidence']:.2f})", style="green")
                    branch.add(solution_text)
            
            if self.verbose:
                progress.update(main_task, advance=1)
        
        if self.verbose:
            progress.stop()
        
        # Evaluate and rank solutions
        if not solutions:
            if self.verbose:
                self.console.print("[bold red]No solutions found![/bold red]")
            return {"solution": "Could not find a solution", "reasoning_path": []}
        
        if self.verbose:
            self.console.print(f"[bold green]Found {len(solutions)} potential solutions[/bold green]")
            self.console.print("[bold blue]Evaluating solutions...[/bold blue]")
            
        best_solution = self._evaluate_solutions(problem, solutions)
        
        if self.verbose:
            self.console.print(self.reasoning_tree)
            
            # Display the best solution
            self.console.print(Panel(
                f"[bold green]Best Solution:[/bold green] {best_solution['solution']}\n\n" +
                f"[bold cyan]Confidence:[/bold cyan] {best_solution['confidence']:.2f}",
                title="Final Result",
                border_style="green"
            ))
            
            self.console.print(f"[yellow]Total paths explored:[/yellow] {self.path_count}")
            self.console.print(f"[yellow]Total solutions found:[/yellow] {self.solution_count}")
            
        return best_solution
    
    def _generate_title(self, text: str) -> str:
        """Generate a summary of the given text."""
        response = self.llm_caller.generate(prompts.generate_title(text))
        title = re.match(r"Title: (.*)", response, re.DOTALL)
        if title:
            return title.group(1).strip()
        return text 

    def _generate_initial_thoughts(self, problem: str) -> List[str]:
        """Generate multiple initial approaches to the problem."""            
        prompt = prompts.generate_approaches_for_question(problem, self.max_branches)       
        if self.verbose:
            self.console.print("  [dim]Querying LLM for initial approaches...[/dim]")
            self.console.print(Panel.fit(Markdown(prompt), title="Inital Approaches: [dim]Prompt[/dim]", border_style="blue", style="dim"))
        
        try:    
            response = self.llm_caller.generate(prompt)
            
            # Check if response is a string
            if not isinstance(response, str):
                if self.verbose:
                    self.console.print(f"  [bold red]Error: LLM response is not a string. Got {type(response)}[/bold red]")
                # Return a default approach to avoid crashing
                return [f"Answer the question '{problem}' step by step"]
                
            approaches = re.findall(r"APPROACH: (.*?)(?=APPROACH:|$)", response, re.DOTALL)
            
            # Clean and limit approaches
            approaches = [approach.strip() for approach in approaches if approach]
            
            if not approaches:
                if self.verbose:
                    self.console.print(Panel.fit(Markdown(response)))                    
                    self.console.print("  [yellow]Warning: No approaches found in LLM response. Using fallback approach.[/yellow]")
                approaches = [f"Answer the question '{problem}' step by step"]
            
            if self.verbose:
                for i, approach in enumerate(approaches):
                    approach_title = self._generate_title(approach)
                    self.console.print(f"  [dim]Approach {i+1} generated: {approach_title}[/dim]")
                    
            return approaches[:self.max_branches]
            
        except Exception as e:
            if self.verbose:
                self.console.print(f"  [bold red]Error generating initial thoughts: {str(e)}[/bold red]", no_wrap=True)
            # Return a default approach to avoid crashing
            return [f"Answer the question '{problem}' step by step"]
    
    def _explore_path(self, problem: str, current_path: List[str], depth: int, parent_node=None) -> Optional[Dict[str, Any]]:
        """
        Recursively explore a reasoning path up to max_depth.
        
        Args:
            problem: Original problem statement
            current_path: List of reasoning steps taken so far
            depth: Current depth in the tree
            parent_node: Parent node in the visualization tree (Rich)
            
        Returns:
            Solution dictionary if a valid solution is found, None otherwise
        """
        self.path_count += 1
        
        # Create a node for the current step in the tree visualization
        current_node = None
        if self.verbose and parent_node:
            current_text = Text(f"Step {depth}: ", style="bold blue")
            current_text.append(current_path[-1][:100] + "..." if len(current_path[-1]) > 100 else current_path[-1], 
                               style="blue")
            current_node = parent_node.add(current_text)
        
        if depth >= self.max_depth:
            # Try to get final solution at max depth
            solution = self._attempt_solution(problem, current_path)
            if solution:
                self.solution_count += 1
                confidence = self._evaluate_confidence(problem, current_path, solution)
                solution_dict = {
                    "solution": solution,
                    "reasoning_path": current_path,
                    "confidence": confidence
                }
                
                if self.verbose and current_node:
                    solution_text = Text("✓ ", style="bold green")
                    solution_text.append(f"Solution (confidence: {confidence:.2f})", style="green")
                    current_node.add(solution_text)
                
                return solution_dict
            
            if self.verbose and current_node:
                current_node.add(Text("✗ No solution at max depth", style="dim red"))
            return None
        
        # Generate next steps in reasoning
        next_steps = self._generate_next_steps(problem, current_path)
        
        # Explore each branch
        solutions = []
        for i, step in enumerate(next_steps):
            new_path = current_path + [step]
            
            if self.verbose and current_node:
                branch_text = Text(f"Branch {i+1}: ", style="dim")
                branch_text.append(step[:100] + "..." if len(step) > 100 else step, style="dim")
                branch_node = current_node.add(branch_text)
            
            # Check if we can solve at current step
            solution = self._attempt_solution(problem, new_path)
            if solution:
                self.solution_count += 1
                confidence = self._evaluate_confidence(problem, new_path, solution)
                solutions.append({
                    "solution": solution,
                    "reasoning_path": new_path,
                    "confidence": confidence
                })
                
                if self.verbose and branch_node:
                    solution_text = Text("✓ ", style="bold green")
                    solution_text.append(f"Early solution (confidence: {confidence:.2f})", style="green")
                    branch_node.add(solution_text)
            else:
                # Continue exploring
                result = self._explore_path(problem, new_path, depth + 1, parent_node=branch_node if self.verbose else None)
                if result:
                    solutions.append(result)
        
        # Return the highest confidence solution if any
        if not solutions:
            if self.verbose and current_node:
                current_node.add(Text("✗ No solutions in this branch", style="dim red"))
            return None
        
        best_solution = max(solutions, key=lambda x: x.get("confidence", 0))
        
        if self.verbose and current_node:
            best_text = Text("★ ", style="bold yellow")
            best_text.append(f"Best solution in branch (confidence: {best_solution['confidence']:.2f})", style="yellow")
            current_node.add(best_text)
            
        return best_solution
    
    def _generate_next_steps(self, problem: str, current_path: List[str]) -> List[str]:
        """Generate possible next reasoning steps given the current path."""        
        prompt = prompts.generate_appoaches_for_question_given_reasoning(problem, current_path, self.max_branches)
        
        if self.verbose:
            self.console.print(f"  [dim]Generating next steps for depth {len(current_path)}...[/dim]")
            self.console.print(Panel.fit(Markdown(prompt), title="Generate Next Steps: [dim]Prompt[/dim]", border_style="blue", style="dim"))            
        
        try:    
            response = self.llm_caller.generate(prompt)
            
            # Check if response is a string
            if not isinstance(response, str):
                if self.verbose:
                    self.console.print(f"  [bold red]Error: LLM response is not a string. Got {type(response)}[/bold red]")
                # Return default steps to avoid crashing
                return [f"Fallback step {i+1}: Continue reasoning from previous step" for i in range(self.max_branches)]
                
            steps = re.findall(r"STEP: (.*?)(?=STEP:|$)", response, re.DOTALL)
            
            # Clean and limit steps
            steps = [step.strip() for step in steps if step.strip()]
            
            if not steps:
                if self.verbose:
                    self.console.print("  [yellow]Warning: No steps found in LLM response. Using fallback steps.[/yellow]")
                steps = [f"Default step: Continue exploring the problem from the current state"]
            
            return steps[:self.max_branches]
            
        except Exception as e:
            if self.verbose:
                self.console.print(f"  [bold red]Error generating next steps: {str(e)}[/bold red]")
            # Return default steps to avoid crashing
            return [f"Fallback step: Continue with approach {current_path[-1][:30]}..."]
    
    def _attempt_solution(self, problem: str, reasoning_path: List[str]) -> Optional[str]:
        """Attempt to produce a final solution given the reasoning path."""        
        prompt = prompts.answer_question(problem, reasoning_path)     
        if self.verbose:
            self.console.print(f"  [dim]Attempting answer at depth {len(reasoning_path)}...[/dim]")
            self.console.print(Panel.fit(Markdown(prompt), title="Attempting Answer: [dim]Prompt[/dim]", border_style="blue", style="dim"))            
        
        try:    
            response = self.llm_caller.generate(prompt)
            
            # Check if response is a string
            if not isinstance(response, str):
                if self.verbose:
                    self.console.print(f"  [bold red]Error: LLM response is not a string. Got {type(response)}[/bold red]")
                return None
                
            solution_match = re.search(r"ANSWER: (.*)", response, re.DOTALL)
            
            if not solution_match:
                if self.verbose:
                    self.console.print("  [yellow]No answer format found in response.[/yellow]")
                return None
                
            solution = solution_match.group(1).strip()
            is_incomplete = "INCOMPLETE" in solution
            
            if self.verbose:
                if is_incomplete:
                    self.console.print("  [dim]Solution attempt was incomplete.[/dim]")
                else:
                    self.console.print(f"  [green]Found solution.[/green]")
                    
            return None if is_incomplete else solution
            
        except Exception as e:
            if self.verbose:
                self.console.print(f"  [bold red]Error attempting solution: {str(e)}[/bold red]")
            return None
    
    def _evaluate_confidence(self, problem: str, reasoning_path: List[str], solution: str) -> float:
        """Evaluate the confidence in a solution based on the reasoning path."""        
        prompt = prompts.answer_confidence(problem, reasoning_path, solution)
        
        if self.verbose:
            self.console.print(f"  [dim]Evaluating solution confidence...[/dim]")
            self.console.print(Panel(Markdown(prompt), title=f"Evaluate Confidence: [dim]Prompt[/dim]", border_style="blue", style="dim"))
        
        try:
            response = self.llm_caller.generate(prompt)
            
            # Check if response is a string
            if not isinstance(response, str):
                if self.verbose:
                    self.console.print(f"  [bold red]Error: LLM response is not a string. Got {type(response)}[/bold red]")
                return 0.5  # Return middle confidence as default
            
            # Extract categorical evaluations
            logic_match = re.search(r"LOGIC: (YES|NO|PARTIALLY)", response)
            completeness_match = re.search(r"COMPLETENESS: (YES|NO|PARTIALLY)", response)
            errors_match = re.search(r"ERRORS: (YES|NO|MAYBE)", response)
            
            # Convert categorical responses to numerical scores
            logic_score = 0.0
            if logic_match:
                if logic_match.group(1) == "YES":
                    logic_score = 1.0
                elif logic_match.group(1) == "PARTIALLY":
                    logic_score = 0.5
            
            completeness_score = 0.0
            if completeness_match:
                if completeness_match.group(1) == "YES":
                    completeness_score = 1.0
                elif completeness_match.group(1) == "PARTIALLY":
                    completeness_score = 0.5
            
            error_score = 0.0
            if errors_match:
                if errors_match.group(1) == "NO":
                    error_score = 1.0
                elif errors_match.group(1) == "MAYBE":
                    error_score = 0.5
            
            # Calculate weighted confidence score (prioritize error-free solutions)
            confidence = (logic_score * 0.35) + (completeness_score * 0.35) + (error_score * 0.3)
            
            # Log detailed evaluation if verbose
            if self.verbose:
                explanation_match = re.search(r"EXPLANATION: (.*?)(?=$)", response, re.DOTALL)
                explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided"
                
                self.console.print(f"  [dim]Confidence score: {confidence:.2f} " + 
                                  f"(Logic: {logic_score:.1f}, Completeness: {completeness_score:.1f}, Errors: {error_score:.1f})[/dim]")
                if confidence < 1.0:
                    self.console.print(f"  [dim]Explanation: {explanation}[/dim]")
                
            return confidence
            
        except Exception as e:
            if self.verbose:
                self.console.print(f"  [bold red]Error evaluating confidence: {str(e)}[/bold red]")
            return 0.5  # Return middle confidence as default
    
    def _evaluate_solutions(self, problem: str, solutions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate and compare multiple solutions to find the best one."""
        if len(solutions) == 1:
            return solutions[0]
            
        prompt = prompts.compare_answers(problem, solutions)
        
        if self.verbose:
            self.console.print(f"  [dim]Comparing {len(solutions)} solutions to find the best...[/dim]")
            self.console.print(Panel.fit(Markdown(prompt), title="Compare Solutions: [dim]Prompt[/dim]", border_style="blue", style="dim"))
        
        try:
            response = self.llm_caller.generate(prompt)
            
            # Check if response is a string
            if not isinstance(response, str):
                if self.verbose:
                    self.console.print(f"  [bold red]Error: LLM response is not a string. Got {type(response)}[/bold red]")
                # Fall back to confidence-based selection
                best_solution = max(solutions, key=lambda x: x.get("confidence", 0))
                if self.verbose:
                    self.console.print("  [yellow]Falling back to confidence-based selection[/yellow]")
                return best_solution
            
            best_match = re.search(r"BEST SOLUTION: (\d+)", response)
            
            if not best_match:
                # If can't determine best, return highest confidence
                best_solution = max(solutions, key=lambda x: x.get("confidence", 0))
                if self.verbose:
                    self.console.print("  [yellow]Couldn't determine best solution from LLM response, using highest confidence score.[/yellow]")
                return best_solution
                
            try:
                best_index = int(best_match.group(1)) - 1
                if 0 <= best_index < len(solutions):
                    best_solution = solutions[best_index]
                    if self.verbose:
                        explanation_match = re.search(r"EXPLANATION: (.*?)(?=$)", response, re.DOTALL)
                        explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided"
                        self.console.print(f"  [dim]Selected solution {best_index+1} as best: {explanation[:100]}...[/dim]")
                    return best_solution
                else:
                    best_solution = max(solutions, key=lambda x: x.get("confidence", 0))
                    if self.verbose:
                        self.console.print("  [yellow]Invalid solution index from LLM, using highest confidence score.[/yellow]")
                    return best_solution
            except ValueError:
                best_solution = max(solutions, key=lambda x: x.get("confidence", 0))
                if self.verbose:
                    self.console.print("  [yellow]Error parsing solution index, using highest confidence score.[/yellow]")
                return best_solution
                
        except Exception as e:
            if self.verbose:
                self.console.print(f"  [bold red]Error evaluating solutions: {str(e)}[/bold red]")
            # Fall back to confidence-based selection
            best_solution = max(solutions, key=lambda x: x.get("confidence", 0))
            if self.verbose:
                self.console.print("  [yellow]Exception occurred, falling back to confidence-based selection[/yellow]")
            return best_solution

# Example usage
if __name__ == "__main__":
    # Example problem: 24 Game (find operations to make 24 from four numbers)
    # problem = "I have a large 3 stall garage. I need help figuring out a plan on how to clean and organize it. Have any tips?"
    problem = "What is the best way to prompt a LLM so that it properly reasons through an answer?"
    
    # Import and instantiate your LLMCaller
    from llm_caller import LLMCaller
    llm_caller = LLMCaller()
    
    # Create the Tree-of-Thought solver with rich visualization and research tools
    tot_solver = TreeOfThought(
        llm_caller,
        max_branches=2,
        max_depth=3,
        verbose=True,  # Set to False to disable rich visualization
    )
    
    # Create a console for final rich output
    console = Console()
    
    # Display title
    console.print(Panel.fit(
        "[bold yellow]Tree-of-Thought Reasoning Demo[/bold yellow]",
        border_style="yellow"
    ))
    
    # Solve the problem with beautiful progress visualization
    result = tot_solver.solve_problem(problem)
    
    # Display the full reasoning path of the best solution
    console.print("\n[bold cyan]Complete Reasoning Path of Best Solution:[/bold cyan]")
    path_tree = Tree("[bold green]Final Solution Path[/bold green]")
    
    for i, step in enumerate(result['reasoning_path']):
        path_node = path_tree.add(Text(f"Step {i+1}", style="bold blue"))
        path_node.add(Text(step, style="blue"))
    
    console.print(path_tree)