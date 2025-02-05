import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model

# ---------------------------
# CP-SAT Optimization Model
# ---------------------------
def solve_fair_division(indivItems):
    """
    Solve a fair division problem for indivisible items.
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
    
    # Create decision variables: y[i, j] is 1 if agent i is assigned item j.
    y = {}
    for i in range(nPeople):
        for j in range(nItems):
            y[i, j] = model.NewBoolVar(f'y_{i}_{j}')
    
    # Each item must be assigned to exactly one agent.
    for j in range(nItems):
        model.Add(sum(y[i, j] for i in range(nPeople)) == 1)
    
    # For each agent, compute the satisfaction (sum of values for items they get).
    satisfaction = []
    for i in range(nPeople):
        sat_expr = sum(indivItems[i][j] * y[i, j] for j in range(nItems))
        satisfaction.append(sat_expr)
    
    # Define worst satisfaction variable and bound it.
    max_possible = max(sum(indivItems[i][j] for j in range(nItems)) for i in range(nPeople))
    worst = model.NewIntVar(0, max_possible, 'worst')
    
    # Ensure each agent's satisfaction is at least worst.
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
- The **first column** is reserved for item names.
- The remaining columns are for each person’s valuations.
""")

# Session state for table generation and storage.
if 'table_generated' not in st.session_state:
    st.session_state.table_generated = False
if 'df' not in st.session_state:
    st.session_state.df = None

# If the table has not been generated, show the header inputs.
if not st.session_state.table_generated:
    people_input = st.text_input("Enter names of People (comma-separated)", "Alice, Bob, Clare")
    items_input = st.text_input("Enter names of Items (comma-separated)", "apple, pear, orange")
    
    if st.button("Generate Table"):
        # Parse header strings into lists.
        people_names = [name.strip() for name in people_input.split(",") if name.strip()]
        items_names = [item.strip() for item in items_input.split(",") if item.strip()]
        
        if not people_names or not items_names:
            st.error("Please ensure you have at least one person and one item.")
        else:
            # Build a DataFrame with the first column as Items and one column per person.
            columns = ["Items"] + people_names
            data = {"Items": items_names}
            for person in people_names:
                data[person] = [0] * len(items_names)
            df = pd.DataFrame(data, columns=columns)
            
            st.session_state.df = df
            st.session_state.table_generated = True
            if hasattr(st, "experimental_rerun"):
                st.experimental_rerun()

# Once the table is generated, display it for editing.
if st.session_state.table_generated:
    st.subheader("Edit Valuations")
    edited_df = st.data_editor(st.session_state.df, use_container_width=True)
    st.session_state.df = edited_df
    st.write("### Current Table")
    st.write(edited_df)
    
    # Button to trigger the optimization.
    if st.button("Solve Optimization"):
        # The table: first column is "Items" (names), subsequent columns are valuations.
        # We ignore the "Items" column when building the indivItems parameter.
        df_val = edited_df.iloc[:, 1:]
        
        try:
            # Convert the valuation entries to integers.
            indivItems = df_val.T.astype(int).values.tolist()
            # Now, indivItems is a list of lists where each row corresponds to a person.
            # For example, if there are 3 people and 4 items, indivItems is 3 x 4.
        except Exception as e:
            st.error("Error converting valuations to integers: " + str(e))
            indivItems = None
        
        if indivItems is not None:
            allocation, worst_val = solve_fair_division(indivItems)
            
            if allocation is not None:
                st.write("## Optimization Result")
                st.write("Worst satisfaction value:", worst_val)
                st.write("### Allocation")
                # Prepare a result DataFrame for display:
                # Rows: People; Columns: Items.
                result_df = pd.DataFrame(allocation).T
                # Use the people names from the header (excluding the first "Items" column)
                result_df.index = list(df_val.columns)
                # Use the item names from the first column of the table.
                result_df.columns = edited_df["Items"].tolist()
                st.write(result_df)
            else:
                st.error("No solution found.")
