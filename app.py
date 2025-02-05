import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Fair Division Calculator", layout="wide")

st.title("Fair Division Calculator")
st.write(
    """
    Enter the item names and the corresponding valuations.
    - **Items**: In the first column, enter the names of the items.
    - **Valuations**: In the remaining columns, enter the valuations for each participant.
    
    For example, after entering your data you might have:
    
    | Items  | Alice | Bobs | Clare |
    |--------|-------|------|-------|
    | apple  | 10    | 20   | 30    |
    | Pear   | 20    | 30   | 10    |
    | Orange | 30    | 10   | 20    |
    """
)

# Sidebar: configure number of items and participants
st.sidebar.header("Input Settings")
num_items = st.sidebar.number_input("Number of Items", min_value=1, max_value=50, value=3, step=1)
num_participants = st.sidebar.number_input("Number of Participants", min_value=1, max_value=20, value=3, step=1)

# Create default participant names and column headers
participant_names = [f"Participant {i+1}" for i in range(num_participants)]
columns = ["Items"] + participant_names

# Build default data
default_data = {
    "Items": [f"Item {i+1}" for i in range(num_items)]
}
# Initialize valuation columns with default zeros
for name in participant_names:
    default_data[name] = [0] * num_items

df_default = pd.DataFrame(default_data)

st.subheader("Enter Items and Valuations")
st.write("Fill in the table below. In the first column, enter the names of the items. In the remaining columns, enter the valuations for each participant.")
# Use Streamlit's data editor to allow the user to modify the table
edited_df = st.data_editor(df_default, use_container_width=True)

if st.button("Process Data"):
    # Validate that the items column has no empty names
    if edited_df["Items"].isnull().any() or (edited_df["Items"] == "").any():
        st.error("Please ensure all items have names.")
    else:
        st.write("### Processed Data")
        st.write(edited_df)
        
        # At this point, you can integrate your fair division optimization logic.
        # For example:
        # results = my_fair_division_algorithm(edited_df)
        # st.write("### Fair Division Results")
        # st.write(results)
        st.info("Fair division optimization algorithm goes here.")
