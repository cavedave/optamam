import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model

# ---------------------------
# CP-SAT Optimization Model (for Indivisible Items)
# ---------------------------
def solve_fair_division(indivItems):
    """
    Solve a fair division problem for indivisible items using max-min fairness.
    indivItems: a list of lists where indivItems[i][j] is the value that
                agent i gets if assigned item j.
    Returns a tuple (allocation, worst_value) where:
      - allocation is a dictionary: keys are agent indices (0-based) and
        values are lists (0/1) indicating if agent i gets item j.
      - worst_value is the maximized minimum satisfaction across agents.
    """
    model = cp_model.CpModel()
    
    nPeople = len(indivItems)
    if nPeople == 0:
        raise ValueError("There must be at least one person.")
    nItems = len(indivItems[0])
    if nItems == 0:
        raise ValueError("There must be at least one item.")
    
    # Decision variables: y[i, j] = 1 if agent i is assigned item j.
    y = {}
    for i in range(nPeople):
        for j in range(nItems):
            y[i, j] = model.NewBoolVar(f'y_{i}_{j}')
    
    # Each item must be assigned to exactly one agent.
    for j in range(nItems):
        model.Add(sum(y[i, j] for i in range(nPeople)) == 1)
    
    # Calculate each agent's satisfaction (sum of values for items they get).
    satisfaction = []
    for i in range(nPeople):
        sat_expr = sum(indivItems[i][j] * y[i, j] for j in range(nItems))
        satisfaction.append(sat_expr)
    
    # Create a variable for the worst (minimum) satisfaction.
    max_possible = max(sum(indivItems[i][j] for j in range(nItems)) for i in range(nPeople))
    worst = model.NewIntVar(0, max_possible, 'worst')
    
    # Constrain each agent's satisfaction to be at least worst.
    for i in range(nPeople):
        model.Add(satisfaction[i] >= worst)
    
    # Objective: maximize the worst-off agent's satisfaction.
    model.Maximize(worst)
    
    # Solve the model.
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        allocation = {}
        for i in range(nPeople):
            allocation[i] = [solver.Value(y[i, j]) for j in range(nItems)]
        return allocation, solver.Value(worst)
    else:
        return None, None

# ---------------------------
# Streamlit Web Form & Integration
# ---------------------------
st.title("Fair Division Calculator - Optimization")
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

# Show header inputs if the table hasn’t been generated.
if not st.session_state.table_generated:
    people_input = st.text_input("Enter names of People (comma-separated)", "Alice, Bob, Clare")
    items_input = st.text_input("Enter names of Items (comma-separated)", "apple, pear, orange")
    
    if st.button("Generate Table"):
        # Parse the input strings into lists.
        people_names = [name.strip() for name in people_input.split(",") if name.strip()]
        items_names = [item.strip() for item in items_input.split(",") if item.strip()]
        
        if not people_names or not items_names:
            st.error("Please ensure you have at least one person and one item.")
        else:
            # Create a DataFrame with three parts:
            # 1. "Items": item names,
            # 2. "Divisible": flag (default 0; use 1 to indicate divisible),
            # 3. One column per person for valuations (default 0).
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

# Once the table is generated, allow editing.
if st.session_state.table_generated:
    st.subheader("Edit Valuations")
    edited_df = st.data_editor(st.session_state.df, use_container_width=True)
    st.session_state.df = edited_df
    st.write("### Current Table")
    st.write(edited_df)
    
    # Button to trigger the optimization.
    if st.button("Solve Optimization"):
        # The table columns are now:
        # 0: Items, 1: Divisible, 2 and beyond: people's valuations.
        valuation_data = edited_df.iloc[:, 2:]
        divisible_flags = edited_df["Divisible"]
        item_names = edited_df["Items"]
        
        # Separate the rows into indivisible and divisible items.
        # For now, we only optimize the indivisible ones.
        indivisible_mask = (divisible_flags != 1)
        divisible_mask = (divisible_flags == 1)
        
        indivisible_valuation_data = valuation_data[indivisible_mask]
        indivisible_item_names = item_names[indivisible_mask]
        
        if indivisible_valuation_data.empty:
            st.warning("No indivisible items found to optimize.")
        else:
            try:
                # Convert the valuation values to integers.
                indivisible_matrix = indivisible_valuation_data.T.astype(int).values.tolist()
            except Exception as e:
                st.error("Error converting valuations to integers: " + str(e))
                indivisible_matrix = None
            
            if indivisible_matrix is not None:
                allocation, worst_val = solve_fair_division(indivisible_matrix)
                
                if allocation is not None:
                    st.write("## Optimization Result")
                    st.write("Worst satisfaction value:", worst_val)
                    st.write("### Allocation for Indivisible Items")
                    # Create a result DataFrame:
                    # - Rows: People (taken from the valuation columns)
                    # - Columns: Items (from the indivisible items only)
                    result_df = pd.DataFrame(allocation).T
                    result_df.index = list(indivisible_valuation_data.columns)  # people's names
                    result_df.columns = indivisible_item_names.tolist()         # item names
                    st.write(result_df)
                else:
                    st.error("No solution found for indivisible items.")
        
        # Inform the user about divisible items.
        divisible_valuation_data = valuation_data[divisible_mask]
        divisible_item_names = item_names[divisible_mask]
        if not divisible_valuation_data.empty:
            st.info("Divisible items were detected, but optimization for divisible items is not implemented yet.")
