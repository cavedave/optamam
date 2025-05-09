from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_fair_division(items: List[Dict], people: List[str], valuations: Dict[str, Dict[str, float]]) -> Dict:
    """
    Calculate fair division for a list of items and people with their valuations.
    
    Args:
        items: List of items with their properties
        people: List of people's names
        valuations: Dictionary mapping item names to dictionaries of person valuations
    
    Returns:
        Dictionary containing the allocation and worst satisfaction value
    """
    try:
        # Separate divisible and indivisible items
        divisible_items = [item for item in items if item['is_divisible']]
        indivisible_items = [item for item in items if not item['is_divisible']]
        
        # Create matrices for the solver
        indivisible_matrix = []
        divisible_matrix = []
        
        for person in people:
            # Handle indivisible items
            if indivisible_items:
                indivisible_row = [valuations[item['name']][person] for item in indivisible_items]
                indivisible_matrix.append(indivisible_row)
            
            # Handle divisible items
            if divisible_items:
                divisible_row = [valuations[item['name']][person] for item in divisible_items]
                divisible_matrix.append(divisible_row)
        
        # Solve the fair division problem
        allocation, worst_satisfaction = solve_fair_division_mixed(indivisible_matrix, divisible_matrix)
        
        if allocation is None:
            raise ValueError("No solution found")
        
        # Convert allocation to the expected format
        result = {
            'allocations': {},
            'worst_satisfaction': worst_satisfaction / 100  # Convert to percentage
        }
        
        # Convert numeric indices to names
        for i, person in enumerate(people):
            person_allocation = allocation[i]
            result['allocations'][person] = {
                'indivisible': {},
                'divisible': {}
            }
            
            # Add indivisible allocations
            if 'indivisible' in person_allocation:
                for j, value in enumerate(person_allocation['indivisible']):
                    if value == 1:  # Only include items that were allocated
                        result['allocations'][person]['indivisible'][indivisible_items[j]['name']] = 1
            
            # Add divisible allocations
            if 'divisible' in person_allocation:
                for j, value in enumerate(person_allocation['divisible']):
                    if value > 0:  # Only include non-zero allocations
                        result['allocations'][person]['divisible'][divisible_items[j]['name']] = value
        
        return result
        
    except Exception as e:
        logger.error(f"Error in fair division calculation: {str(e)}", exc_info=True)
        raise

def solve_fair_division_mixed(indivisible_matrix: List[List[int]], 
                            divisible_matrix: List[List[int]], 
                            scale: int = 100) -> Tuple[Optional[Dict], Optional[float]]:
    """
    Solve the fair division problem for a mix of divisible and indivisible items.
    
    Args:
        indivisible_matrix: Matrix of valuations for indivisible items
        divisible_matrix: Matrix of valuations for divisible items
        scale: Scaling factor for numerical precision
    
    Returns:
        Tuple of (allocation dictionary, worst satisfaction value)
    """
    try:
        logger.info("=== Starting Fair Division Solver ===")
        
        # Validate input matrices
        if not indivisible_matrix and not divisible_matrix:
            logger.error("Both matrices are empty")
            return None, None

        # Get dimensions
        num_people = len(indivisible_matrix) if indivisible_matrix else len(divisible_matrix)
        num_indivisible = len(indivisible_matrix[0]) if indivisible_matrix else 0
        num_divisible = len(divisible_matrix[0]) if divisible_matrix else 0

        logger.info(f"Problem size: {num_people} people, {num_indivisible} indivisible items, {num_divisible} divisible items")

        model = cp_model.CpModel()
        logger.info("Created CP model")
        
        # Create variables for indivisible items
        indivisible_vars = {}
        if num_indivisible > 0:
            for i in range(num_people):
                for j in range(num_indivisible):
                    indivisible_vars[i, j] = model.NewBoolVar(f'indivisible_{i}_{j}')
            logger.info(f"Created {len(indivisible_vars)} indivisible variables")
        
        # Create variables for divisible items
        divisible_vars = {}
        if num_divisible > 0:
            for i in range(num_people):
                for j in range(num_divisible):
                    divisible_vars[i, j] = model.NewIntVar(0, scale, f'divisible_{i}_{j}')
            logger.info(f"Created {len(divisible_vars)} divisible variables")
        
        # Each indivisible item must be assigned to exactly one person
        if num_indivisible > 0:
            for j in range(num_indivisible):
                model.Add(sum(indivisible_vars[i, j] for i in range(num_people)) == 1)
            logger.info("Added constraints for indivisible items")
        
        # Each divisible item must be fully allocated
        if num_divisible > 0:
            for j in range(num_divisible):
                model.Add(sum(divisible_vars[i, j] for i in range(num_people)) == scale)
            logger.info("Added constraints for divisible items")
        
        # Calculate satisfaction for each person
        satisfactions = []
        for i in range(num_people):
            # Handle indivisible items
            indivisible_satisfaction = 0
            if num_indivisible > 0:
                indivisible_satisfaction = sum(
                    int(indivisible_matrix[i][j]) * indivisible_vars[i, j]
                    for j in range(num_indivisible)
                )
            
            # Handle divisible items
            divisible_satisfaction = 0
            if num_divisible > 0:
                divisible_satisfaction = sum(
                    int(divisible_matrix[i][j]) * divisible_vars[i, j]
                    for j in range(num_divisible)
                )
            
            total_satisfaction = indivisible_satisfaction + divisible_satisfaction
            satisfactions.append(total_satisfaction)
            logger.info(f"Person {i} satisfaction expression created")
        
        # Calculate maximum possible satisfaction for scaling
        max_possible = 0
        if indivisible_matrix:
            max_possible += sum(max(int(row[j]) for j in range(len(row))) for row in indivisible_matrix)
        if divisible_matrix:
            max_possible += sum(max(int(row[j]) for j in range(len(row))) for row in divisible_matrix) * scale
        
        logger.info(f"Maximum possible satisfaction: {max_possible}")
        
        # Maximize the minimum satisfaction
        min_satisfaction = model.NewIntVar(0, int(max_possible), 'min_satisfaction')
        for satisfaction in satisfactions:
            model.Add(min_satisfaction <= satisfaction)
        model.Maximize(min_satisfaction)
        logger.info("Added objective function")
        
        # Solve the model
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30.0  # Set a timeout
        logger.info("Starting solver...")
        status = solver.Solve(model)
        logger.info(f"Solver status: {status}")
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            # Extract the solution
            allocation = {}
            for i in range(num_people):
                person_allocation = {}
                
                # Get indivisible allocations
                if num_indivisible > 0:
                    indivisible_allocation = [
                        solver.Value(indivisible_vars[i, j])
                        for j in range(num_indivisible)
                    ]
                    person_allocation['indivisible'] = indivisible_allocation
                    logger.info(f"Person {i} indivisible allocation: {indivisible_allocation}")
                
                # Get divisible allocations
                if num_divisible > 0:
                    divisible_allocation = [
                        solver.Value(divisible_vars[i, j]) / scale
                        for j in range(num_divisible)
                    ]
                    person_allocation['divisible'] = divisible_allocation
                    logger.info(f"Person {i} divisible allocation: {divisible_allocation}")
                
                allocation[i] = person_allocation
            
            worst_satisfaction = solver.Value(min_satisfaction)
            logger.info(f"Solution found with worst satisfaction: {worst_satisfaction/100}")
            logger.info("=== Fair Division Solver Complete ===")
            return allocation, worst_satisfaction
        else:
            logger.error(f"No solution found. Solver status: {status}")
            return None, None
            
    except Exception as e:
        logger.error(f"Error in fair division calculation: {str(e)}", exc_info=True)
        return None, None 