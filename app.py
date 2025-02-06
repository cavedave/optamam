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
# Streamlit Web Form & Integration
# ---------------------------
st.title("Fair Division Calculator - Mixed Items")
st.write("""
Enter the names of the people and items below. Then edit the table to fill in each person's valuation for each item.
- The **first column** (Items) is used to enter item names.
- The **second column** (Divisible) is used to indicate if the item is divisible (enter 1 for divisible, 0 for non divisible).
- The remaining columns correspond to each person's valuation of the item.
""")

# Initialize session state for table generation.
if 'table_generated' not in st.session_state:
    st.session_state.table_generated = False
if 'df' not in st.session_state:
    st.session_state.df = None

# Header inputs: if table not yet generated.
if not st.session_state.table_generated:
    people_input = st.text_input("Enter names of People (comma-separated)", "Alice, Bob, Clare")
    items_input = st.text_input("Enter names of Items (comma-separated)", "apple, pear, orange")
    if st.button("Generate Table"):
        people_names = [name.strip() for name in people_input.split(",") if name.strip()]
        items_names  = [item.strip() for item in items_input.split(",") if item.strip()]
        if not people_names or not items_names:
            st.error("Please ensure you have at least one person and one item.")
        else:
            # Create a DataFrame with columns: Items, Divisible, then one column per person.
            columns = ["Items", "Divisible"] + people_names
            data = {"Items": items_names,
                    "Divisible": [0] * len(items_names)}
            for person in people_names:
                data[person] = [0] * len(items_names)
            df = pd.DataFrame(data, columns=columns)
            st.session_state.df = df
            st.session_state.table_generated = True
            if hasattr(st, "experimental_rerun"):
                st.experimental_rerun()

# Show the data editor once the table is generated.
if st.session_state.table_generated:
    st.subheader("Edit Valuations")
    edited_df = st.data_editor(st.session_state.df, use_container_width=True)
    st.session_state.df = edited_df
    st.write("### Current Table")
    st.write(edited_df)
    
    if st.button("Solve Optimization"):
        # The table columns:
        #   Column 0: Items, Column 1: Divisible, Columns 2+ are valuations for each person.
        df_val = edited_df.iloc[:, 2:]
        divisible_flags = edited_df["Divisible"]
        item_names = edited_df["Items"]
        
        # Separate the rows into indivisible and divisible items.
        indivisible_mask = (divisible_flags != 1)
        divisible_mask   = (divisible_flags == 1)
        
        indivisible_valuation_data = df_val[indivisible_mask]
        indivisible_item_names   = item_names[indivisible_mask]
        divisible_valuation_data   = df_val[divisible_mask]
        divisible_item_names     = item_names[divisible_mask]
        
        # Convert the valuation data to matrices.
        try:
            indivisible_matrix = (indivisible_valuation_data.T.astype(int).values.tolist()
                                  if not indivisible_valuation_data.empty else [])
        except Exception as e:
            st.error("Error converting indivisible valuations to integers: " + str(e))
            indivisible_matrix = None
        
        try:
            divisible_matrix = (divisible_valuation_data.T.astype(int).values.tolist()
                                if not divisible_valuation_data.empty else [])
        except Exception as e:
            st.error("Error converting divisible valuations to integers: " + str(e))
            divisible_matrix = None
        
        if (indivisible_matrix is None or divisible_matrix is None) and not (indivisible_matrix or divisible_matrix):
            st.error("No valid valuation data found.")
        else:
            # If one type is missing, replace with an empty list.
            if indivisible_matrix is None:
                indivisible_matrix = []
            if divisible_matrix is None:
                divisible_matrix = []
            allocation, worst_val = solve_fair_division_mixed(indivisible_matrix, divisible_matrix, scale=100)
            if allocation is not None:
                st.write("## Optimization Result")
                st.write("Worst satisfaction value (scaled):", worst_val)
                st.write("### Allocation")
                result_md = ""
                people_names_list = list(df_val.columns)  # names of people from the valuation columns
                for i, person in enumerate(people_names_list):
                    result_md += f"**{person}**\n"
                    if 'indivisible' in allocation[i]:
                        # Build a table for indivisible items.
                        df_indiv = pd.DataFrame({indivisible_item_names.iloc[k]: [allocation[i]['indivisible'][k]]
                                                  for k in range(len(allocation[i]['indivisible']))})
                        result_md += "Indivisible Items:\n" + df_indiv.to_markdown() + "\n"
                    if 'divisible' in allocation[i]:
                        df_div = pd.DataFrame({divisible_item_names.iloc[k]: [allocation[i]['divisible'][k]]
                                                for k in range(len(allocation[i]['divisible']))})
                        result_md += "Divisible Items:\n" + df_div.to_markdown() + "\n"
                st.markdown(result_md)
            else:
                st.error("No solution found.")
