import streamlit as st
import pandas as pd

# Configure the page
st.set_page_config(page_title="Fair Division Calculator", layout="wide")

st.title("Fair Division Calculator")
st.write("""
Enter the names of the people and items below. When you're ready, click **Generate Table** 
to create a spreadsheet-like input where:
- The **first column** is for the item names.
- The remaining columns use the people’s names as headers for entering valuations.
""")

# Input fields for header information
people_input = st.text_input("Enter names of People (comma-separated)", "Alice, Bob, Clare")
items_input = st.text_input("Enter names of Items (comma-separated)", "apple, pear, orange")

# Generate button to create the table
if st.button("Generate Table"):
    # Parse the comma-separated inputs into lists, stripping any extra whitespace
    people_names = [name.strip() for name in people_input.split(",") if name.strip()]
    items_names = [item.strip() for item in items_input.split(",") if item.strip()]

    # Basic validation: ensure there is at least one person and one item
    if not people_names or not items_names:
        st.error("Please ensure you have entered at least one person and one item.")
    else:
        # Prepare the DataFrame columns: the first column is "Items", followed by the people names
        columns = ["Items"] + people_names

        # Build the initial data:
        # - The "Items" column is populated with the entered item names.
        # - Each person column is initialized with a default value (0) for every item.
        data = {"Items": items_names}
        for person in people_names:
            data[person] = [0] * len(items_names)
        
        df = pd.DataFrame(data, columns=columns)

        st.subheader("Edit Valuations")
        st.write("You can now edit the table below to input the valuations:")
        # Display the DataFrame as an editable data editor table
        edited_df = st.data_editor(df, use_container_width=True)
        
        # For debugging or further processing, you can display the resulting DataFrame:
        st.write("### Current Data")
        st.write(edited_df)
