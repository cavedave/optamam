import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model

# ---------------------------
# CP-SAT Optimization Model (Mixed Items)
# ---------------------------
def solve_fair_division_mixed(indivisible_matrix, divisible_matrix, scale=100):
    """
    Solve the fair division problem using max-min fairness.
    
    For each agent i:
      satisfaction[i] = scale * sum_j (indivisible_matrix[i][j] * y[i,j])
                      + sum_k (divisible_matrix[i][k] * x[i,k])
    
    where:
      - y[i,j] are binary variables for indivisible items (each must be assigned to exactly one agent).
      - x[i,k] are integer variables in [0, scale] for divisible items (and for each item, sum_i x[i,k] == scale).
    
    Returns a tuple (allocation, worst_value), where allocation is a dict with, for each agent,
    separate lists for the indivisible and divisible allocations.
    """
    model = cp_model.CpModel()
    
    # Determine dimensions. We assume the two matrices have the same number of rows (agents).
    nPeople = 0
    if indivisible_matrix and len(indivisible_matrix) > 0:
        nPeople = len(indivisible_matrix)
    elif divisible_matrix and len(divisible_matrix) > 0:
        nPeople = len(divisible_matrix)
    else:
        raise ValueError("No valuation data provided.")
    
    nIndivisible = len(indivisible_matrix[0]) if indivisible_matrix and len(indivisible_matrix) > 0 else 0
    nDivisible   = len(divisible_matrix[0])   if divisible_matrix and len(divisible_matrix) > 0 else 0
    
    # Binary variables for indivisible items.
    y = {}
    if nIndivisible > 0:
        for i in range(nPeople):
            for j in range(nIndivisible):
                y[i, j] = model.NewBoolVar(f'y_{i}_{j}')
        # Each indivisible item is given to exactly one agent.
        for j in range(nIndivisible):
            model.Add(sum(y[i, j] for i in range(nPeople)) == 1)
    
    # Integer variables for divisible items (simulate fractional allocation).
    x = {}
    if nDivisible > 0:
        for i in range(nPeople):
            for k in range(nDivisible):
                x[i, k] = model.NewIntVar(0, scale, f'x_{i}_{k}')
        # For each divisible item, the total allocation is exactly "scale" (i.e. 100%).
        for k in range(nDivisible):
            model.Add(sum(x[i, k] for i in range(nPeople)) == scale)
    
    # Compute satisfaction for each agent.
    satisfaction = []
    for i in range(nPeople):
        s = 0
        if nIndivisible > 0:
            # Multiply by scale so the units match.
            s += sum(indivisible_matrix[i][j] * scale * y[i, j] for j in range(nIndivisible))
        if nDivisible > 0:
            s += sum(divisible_matrix[i][k] * x[i, k] for k in range(nDivisible))
        satisfaction.append(s)
    
    # Compute an upper bound on satisfaction.
    max_possible = 0
    for i in range(nPeople):
        max_indivisible = sum(indivisible_matrix[i][j] for j in range(nIndivisible)) if nIndivisible > 0 else 0
        max_divisible   = sum(divisible_matrix[i][k] for k in range(nDivisible))     if nDivisible > 0 else 0
        candidate = scale * (max_indivisible + max_divisible)
        if candidate > max_possible:
            max_possible = candidate
    
    worst = model.NewIntVar(0, max_possible, 'worst')
    for i in range(nPeople):
        model.Add(satisfaction[i] >= worst)
    
    # Maximize the worst-off agent's satisfaction.
    model.Maximize(worst)
    
    # Solve the model.
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        allocation = {}
        for i in range(nPeople):
            allocation[i] = {}
            if nIndivisible > 0:
                allocation[i]['indivisible'] = [solver.Value(y[i, j]) for j in range(nIndivisible)]
            if nDivisible > 0:
                # Convert allocation to a fraction (e.g., 45 means 45% if scale==100)
                allocation[i]['divisible'] = [solver.Value(x[i, k]) / scale for k in range(nDivisible)]
        worst_val = solver.Value(worst)
        return allocation, worst_val
    else:
        return None, None

# ---------------------------
# Streamlit Web Form with Numeric Input Spinners
# ---------------------------
st.title("Fair Division Calculator - Mixed Items (Numeric Inputs)")

st.write("""
Enter the names of the people (comma-separated) and the number of items.
Then click **Generate Input Form** to enter data for each item:
- **Item Name**  
- **Divisible Flag** (enter 1 if the item is divisible, 0 if not)  
- For each person, their valuation (numeric spinner)
""")

# Header inputs
people_input = st.text_input("Enter names of People (comma-separated)", "Alice, Bob, Clare")
people_names = [name.strip() for name in people_input.split(",") if name.strip()]
num_people = len(people_names)
num_items = st.number_input("Number of Items", min_value=1, value=3, step=1)

if st.button("Generate Input Form"):
    # Use a form to collect item details.
    with st.form("item_form"):
        st.write("Enter details for each item:")
        item_names = []
        divisible_flags = []
        # valuations[(i, j)] will store the valuation for item i by person j.
        valuations = {}
        for i in range(num_items):
            st.markdown(f"#### Item {i+1}")
            # Text input for item name.
            item_name = st.text_input(f"Name for Item {i+1}", value=f"Item {i+1}", key=f"item_name_{i}")
            # Numeric spinner for divisible flag.
            divisible = st.number_input(f"Divisible for Item {i+1} (1 if yes, 0 if no)", 
                                        min_value=0, max_value=1, value=0, step=1, key=f"divisible_{i}")
            item_names.append(item_name)
            divisible_flags.append(divisible)
            # For each person, add a numeric spinner for their valuation.
            for j, person in enumerate(people_names):
                valuation = st.number_input(f"Valuation for **{person}** for Item {i+1}", 
                                            min_value=0, value=0, step=1, key=f"valuation_{i}_{j}")
                valuations[(i, j)] = valuation

        submitted = st.form_submit_button("Submit Data")
        if submitted:
            # Build separate matrices for indivisible and divisible items.
            indivisible_valuations = []
            divisible_valuations = []
            indivisible_item_names = []
            divisible_item_names = []
            for i in range(num_items):
                # Build the row for this item: one value per person.
                row = [valuations[(i, j)] for j in range(num_people)]
                if divisible_flags[i] == 1:
                    divisible_valuations.append(row)
                    divisible_item_names.append(item_names[i])
                else:
                    indivisible_valuations.append(row)
                    indivisible_item_names.append(item_names[i])
            
            # Transpose the matrices so that rows correspond to people.
            if indivisible_valuations:
                indivisible_matrix = list(map(list, zip(*indivisible_valuations)))
            else:
                indivisible_matrix = []
            if divisible_valuations:
                divisible_matrix = list(map(list, zip(*divisible_valuations)))
            else:
                divisible_matrix = []
            
            st.write("### Input Data")
            if indivisible_matrix:
                st.write("**Indivisible Items:**")
                st.write(pd.DataFrame(indivisible_matrix, index=people_names, columns=indivisible_item_names))
            else:
                st.write("No indivisible items.")
            if divisible_matrix:
                st.write("**Divisible Items:**")
                st.write(pd.DataFrame(divisible_matrix, index=people_names, columns=divisible_item_names))
            else:
                st.write("No divisible items.")
            
            # Run the optimization model.
            allocation, worst_val = solve_fair_division_mixed(indivisible_matrix, divisible_matrix, scale=100)
            if allocation is not None:
                st.write("## Optimization Result")
                worst_percent = worst_val / 100  # Convert scaled value to percentage
                st.write(f"Worst satisfaction value (percentage): {worst_percent:.1f}%")
                st.write("### Allocation:")
                for i, person in enumerate(people_names):
                    st.write(f"**{person}**:")
                    if 'indivisible' in allocation[i]:
                        st.write("Indivisible Allocation:", allocation[i]['indivisible'])
                    if 'divisible' in allocation[i]:
                        st.write("Divisible Allocation:", allocation[i]['divisible'])
            else:
                st.error("No solution found.")
