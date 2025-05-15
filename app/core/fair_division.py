from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# TODO: Potential improvements to the fair division solver:
# 1. Better variable creation using dictionary comprehensions
#    - Replace nested loops with dictionary comprehensions for variable creation
#    - Makes code more concise and readable
#
# 2. More precise satisfaction calculation with proper scaling
#    - Improve how divisible items (like cash) are handled
#    - Ensure proper scaling of values
#
# 3. Improved constraints for divisible items using AddDivisionEquality
#    - Use AddDivisionEquality for better handling of divisible items
#    - Ensures fair splitting of divisible resources
#
# 4. Better satisfaction constraints with bounded variables
#    - Create bounded variables for total satisfaction
#    - Make solver's job easier by providing exact ranges
#    - Improve efficiency in finding solutions

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
        # Validate that valuations sum to 100 for each person
        for person in people:
            total_value = sum(valuations[item['name']][person] for item in items)
            if abs(total_value - 100) > 0.01:  # Allow for small floating point differences
                raise ValueError(f"Valuations for {person} must sum to 100, but sum to {total_value:.2f}")
        
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
            'worst_satisfaction': worst_satisfaction  # Already a percentage
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

        # Convert float values to integers
        indivisible_matrix = [[int(val) for val in row] for row in indivisible_matrix]
        divisible_matrix = [[int(val) for val in row] for row in divisible_matrix]

        # Get dimensions
        num_people = len(indivisible_matrix) if indivisible_matrix else len(divisible_matrix)
        num_indivisible = len(indivisible_matrix[0]) if indivisible_matrix else 0
        num_divisible = len(divisible_matrix[0]) if divisible_matrix else 0

        logger.info(f"Problem size: {num_people} people, {num_indivisible} indivisible items, {num_divisible} divisible items")
        
        # Log the input matrices
        if indivisible_matrix:
            logger.info("Indivisible matrix:")
            for i, row in enumerate(indivisible_matrix):
                logger.info(f"Person {i}: {row}")
        
        if divisible_matrix:
            logger.info("Divisible matrix:")
            for i, row in enumerate(divisible_matrix):
                logger.info(f"Person {i}: {row}")

        model = cp_model.CpModel()
        logger.info("Created CP model")
        
        # Create variables for indivisible items using dictionary comprehension
        indivisible_vars = {(i, j): model.NewBoolVar(f'indivisible_{i}_{j}')
                           for i in range(num_people)
                           for j in range(num_indivisible)}
        logger.info(f"Created {len(indivisible_vars)} indivisible variables")
        
        # Create variables for divisible items using dictionary comprehension
        divisible_vars = {(i, j): model.NewIntVar(0, scale, f'divisible_{i}_{j}')
                         for i in range(num_people)
                         for j in range(num_divisible)}
        logger.info(f"Created {len(divisible_vars)} divisible variables")
        
        # Each indivisible item must be assigned to exactly one person
        for j in range(num_indivisible):
            model.Add(sum(indivisible_vars[i, j] for i in range(num_people)) == 1)
        logger.info("Added constraints for indivisible items")
        
        # Each divisible item must be fully allocated
        for j in range(num_divisible):
            model.Add(sum(divisible_vars[i, j] for i in range(num_people)) == scale)
        logger.info("Added constraints for divisible items")

        # Determine max possible satisfaction to bound worst
        max_possible = max(
            sum(indivisible_matrix[i]) + sum(divisible_matrix[i]) if divisible_matrix else sum(indivisible_matrix[i])
            for i in range(num_people)
        )
        worst_satisfaction = model.NewIntVar(0, int(max_possible), 'worst_satisfaction')
        logger.info(f"Created worst satisfaction variable with max possible value: {max_possible}")

        # Build per-person satisfaction constraints
        for i in range(num_people):
            # Create bounded variable for total satisfaction
            tot = model.NewIntVar(
                0,
                int(sum(indivisible_matrix[i]) + (max(max(row) for row in divisible_matrix) if divisible_matrix else 0)),
                f'tot_{i}'
            )
            
            # Calculate indivisible satisfaction
            indiv_sum = sum(indivisible_matrix[i][j] * indivisible_vars[i, j]
                          for j in range(num_indivisible))
            
            # Calculate divisible satisfaction with proper scaling
            if num_divisible:
                div_contrib = sum(divisible_matrix[i][j] * divisible_vars[i, j]
                                for j in range(num_divisible))
                scaled_div = model.NewIntVar(0, int(max(max(row) for row in divisible_matrix)),
                                           f'scaled_div_{i}')
                model.AddDivisionEquality(scaled_div, div_contrib, scale)
            else:
                scaled_div = 0

            # Add constraints for total satisfaction
            model.Add(tot == indiv_sum + scaled_div)
            model.Add(tot >= worst_satisfaction)
            logger.info(f"Added satisfaction constraints for person {i}")

        # Maximize the worst satisfaction
        model.Maximize(worst_satisfaction)
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
            actual_satisfactions = []
            
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
                
                # Calculate actual satisfaction
                received_value = 0
                # Indivisible items
                if num_indivisible > 0:
                    for j in range(num_indivisible):
                        if solver.Value(indivisible_vars[i, j]) == 1:
                            received_value += int(indivisible_matrix[i][j])
                            logger.info(f"Person {i} received indivisible item {j} with value {int(indivisible_matrix[i][j])}")
                # Divisible items
                if num_divisible > 0:
                    for j in range(num_divisible):
                        fraction = solver.Value(divisible_vars[i, j]) / scale
                        received_value += int(divisible_matrix[i][j]) * fraction
                        logger.info(f"Person {i} received divisible item {j} with fraction {fraction} and value {int(divisible_matrix[i][j])}")
                actual_satisfactions.append(received_value)
                logger.info(f"Person {i} actual satisfaction: {received_value:.2f}% (received {received_value} out of 100)")
            
            worst_satisfaction = min(actual_satisfactions)
            logger.info(f"Worst satisfaction: {worst_satisfaction:.2f}%")
            logger.info("=== Fair Division Solver Complete ===")
            return allocation, worst_satisfaction
        else:
            logger.error(f"No solution found. Solver status: {status}")
            return None, None
            
    except Exception as e:
        logger.error(f"Error in fair division calculation: {str(e)}", exc_info=True)
        return None, None 