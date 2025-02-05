import streamlit as st
import pandas as pd

# Configure the page
st.set_page_config(page_title="Fair Division Calculator", layout="wide")

# Initialize session state variables if they don't exist
if 'table_generated' not in st.session_state:
    st.session_state.table_generated = False
if 'df' not in st.session_state:
    st.session_state.df = None

st.title("Fair Division Calculator")
st.write("""
Enter the names of the people and items below. When you're ready, click **Generate Table** 
to create a spreadsheet-like input where:
- The **first column** is for the item names.
- The remaining columns use the people’s names as headers for entering valuations.
""")

# Only show the header input section if the table hasn't been generated yet.
if not st.session_state.table_generated:
    people_input = st.text_input("Enter names of People (comma-separated)", "Alice, Bob, Clare")
    items_input = st.text_input("Enter names of Items (comma-separated)", "apple, pear, orange")

    if st.button("Generate Table"):
        # Parse the comma-separated strings into lists, stripping any extra whitespace.
        people_names = [name.strip() for name in people_input.split(",") if name.strip()]
        items_names = [item.strip() for item in items_input.split(",") if item.strip()]

        # Basic validation: ensure there's at least one person and one item.
        if not people_names or not items_names:
            st.error("Please ensure you have entered at least one person and one item.")
        else:
            # The first column will be "Items" and the rest will be the people names.
            columns = ["Items"] + people_names

            # Build the data: the "Items" column is populated with the item names,
            # and each person column is initialized with 0 for each item.
            data = {"Items": items_names}
            for person in people_names:
                data[person] = [0] * len(items_names)
            df = pd.DataFrame(data, columns=columns)

            # Store the DataFrame and a flag in session state.
            st.session_state.df = df
            st.session_state.table_generated = True

            # Debug: print to console (will show in your terminal)
            print("DEBUG: Table generated")
            print(df)

            # Force a rerun so that the generated table appears immediately.
            st.experimental_rerun()

# Once the table is generated, display the editable data editor.
if st.session_state.table_generated:
    st.subheader("Edit Valuations")
    st.write("You can now edit the table below to input the valuations:")
    
    # Use the stored DataFrame from session state.
    edited_df = st.data_editor(st.session_state.df, use_container_width=True)

    # Update session state with the edited DataFrame.
    st.session_state.df = edited_df

    st.write("### Current Data")
    st.write(edited_df)

    # Debug: print edited DataFrame to console
    print("DEBUG: Edited DataFrame")
    print(edited_df)
