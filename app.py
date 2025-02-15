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
# Multipage Layout Using Sidebar Navigation
# ---------------------------

# Initialize session state for page navigation and header data.
if "page" not in st.session_state:
    st.session_state.page = "Header"
if "people_names" not in st.session_state:
    st.session_state.people_names = []
if "item_names" not in st.session_state:
    st.session_state.item_names = []

# Sidebar for navigation.
page = st.sidebar.radio("Navigation", ["Header", "Valuation Input"],
                          index=0 if st.session_state.page == "Header" else 1)
st.session_state.page = page


if page == "Header":
    st.title("Fair Division Calculator")
    st.write("Welcome! This app helps you fairly divide items among people based on their valuations.")
    st.write("Enter the names of the people and the items below to get started.")

    # Use columns to organize inputs side by side
    col1, col2 = st.columns(2)
    with col1:
        people_input = st.text_input("Names of People (comma-separated)", "Alice, Bob, Clare", 
                                     help="Enter the names of the people involved, separated by commas.")
    with col2:
        items_input = st.text_input("Names of Items (comma-separated)", "apple, pear, orange", 
                                    help="Enter the names of the items to be divided, separated by commas.")

    if st.button("Proceed to Valuation Input"):
        # Store header info in session state.
        st.session_state.people_names = [name.strip() for name in people_input.split(",") if name.strip()]
        st.session_state.item_names = [item.strip() for item in items_input.split(",") if item.strip()]
        st.session_state.page = "Valuation Input"
        # Instead of st.experimental_rerun(), use a flag to force a re-render
        st.session_state.force_rerun = True

# Add a flag to force a re-render
if st.session_state.get("force_rerun", False):
    st.session_state.force_rerun = False
    st.write("Input form generated. Use the navigation sidebar to switch pages.")

elif page == "Valuation Input":
    st.title("Fair Division Calculator - Valuation Input")
    
    # Retrieve header info.
    people_names = st.session_state.get("people_names", [])
    item_names = st.session_state.get("item_names", [])
    num_people = len(people_names)
    num_items = len(item_names)
    
    if num_people == 0 or num_items == 0:
        st.error("Please return to the Header page and enter valid names for people and items.")
    else:
        st.write("Enter valuation data for each item:")
        with st.form("valuation_form"):
            divisible_flags = []
            valuations = {}
            for i in range(num_items):
                with st.expander(f"Item: {item_names[i]}"):
                    # Numeric spinner for divisible flag.
                    divisible = st.number_input(
                        f"Is **{item_names[i]}** divisible? (1 for yes, 0 for no)",
                        min_value=0, max_value=1, value=0, step=1, key=f"divisible_{i}"
                    )
                    divisible_flags.append(divisible)
                    # For each person, add a numeric spinner for their valuation.
                    for j, person in enumerate(people_names):
                        valuation = st.number_input(
                            f"Valuation for **{person}** for **{item_names[i]}**",
                            min_value=0, value=10, step=1, key=f"valuation_{i}_{j}"
                        )
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
                    worst_percent = worst_val / 100  # Convert scaled value to percentage
                    st.success("Optimization completed successfully!")
                    st.write(f"**Worst satisfaction value (percentage):** {worst_percent:.1f}%")
                    st.write("### Allocation:")

                    # Create a DataFrame for the allocation results
                    allocation_data = []
                    for i, person in enumerate(people_names):
                        indivisible_allocation = allocation[i].get('indivisible', [])
                        divisible_allocation = allocation[i].get('divisible', [])
                        allocation_data.append({
                            "Person": person,
                            "Indivisible Allocation": ", ".join([item_names[j] for j, val in enumerate(indivisible_allocation) if val == 1]),
                            "Divisible Allocation": ", ".join([f"{item_names[j]}: {val*100:.1f}%" for j, val in enumerate(divisible_allocation)])
                        })

                    allocation_df = pd.DataFrame(allocation_data)
                    st.table(allocation_df)

                    # Add a download button for the results
                    csv = allocation_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Results as CSV",
                        data=csv,
                        file_name="fair_division_results.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("No solution found.")