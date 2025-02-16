import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model

# Optimization logic
def solve_fair_division_mixed(indivisible_matrix, divisible_matrix, scale=100):
    # (Copy the entire solve_fair_division_mixed function here)
    pass

# Streamlit UI for the calculator
def fair_division_calculator():
    st.title("Fair Division Calculator")
    
    # Initialize session state for header data if not already initialized
    if "people_names" not in st.session_state:
        st.session_state.people_names = []
    if "item_names" not in st.session_state:
        st.session_state.item_names = []

    # Sidebar for navigation.
    page = st.sidebar.radio("Navigation", ["Header", "Valuation Input"],
                              index=0 if st.session_state.get("subpage", "Header") == "Header" else 1)
    st.session_state.subpage = page

    if page == "Header":
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
            st.session_state.subpage = "Valuation Input"
            st.rerun()  # Refresh the app to navigate to the valuation input page

    elif page == "Valuation Input":
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
            
            # Move the results and download button outside the form
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

                    # Add a download button for the results (outside the form)
                    csv = allocation_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Results as CSV",
                        data=csv,
                        file_name="fair_division_results.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("No solution found.")