import streamlit as st

# Custom CSS to hide the running man and hamburger menu
hide_streamlit_style = """
    <style>
        /* Hide the running man loading icon */
        div.stSpinner > div {
            display: none;
        }
        /* Hide the hamburger menu */
        #MainMenu {
            visibility: hidden;
        }
        /* Hide the footer */
        footer {
            visibility: hidden;
        }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# List of blog posts
BLOG_POSTS = {
    "My First Blog Post": "blog/first.md",
    "Another Blog Post": "blog/second.md",
}

def load_blog_post(post_path):
    """Load a blog post from a Markdown file."""
    with open(post_path, "r", encoding="utf-8") as file:
        return file.read()



# Landing Page
def landing_page():
    st.title("Welcome to the Fair Division App!")
    st.write("Explore our calculators and blog posts below.")

    # Section 1: Calculators
    st.header("Calculators")
    if st.button("Fair Division Calculator"):
        # Initialize session state variables for the calculator
        st.session_state.people_names = []
        st.session_state.item_names = []
        st.session_state.page = "Fair Division Calculator"
        st.rerun()  # Refresh the app to navigate to the calculator

    # Section 2: Blog Posts
    st.header("Blog Posts")
    st.write("Coming soon! Stay tuned for insightful articles on fair division and related topics.")
# Sidebar for navigation
    st.sidebar.title("Blog Posts")
    selected_post = st.sidebar.selectbox("Choose a post", list(BLOG_POSTS.keys()))

# Link to the Markdown file
    st.markdown("[Read My First Blog Post](first.md)")

    # Display the selected blog post
    st.title(selected_post)
    post_content = load_blog_post(BLOG_POSTS[selected_post])
    st.markdown(post_content)    
    st.markdown("[My First Blog Post](https://optamam-18b97cb6d0b0.herokuapp.com/blog/my-first-blog-post.html)")
# Initialize session state for page navigation
if "page" not in st.session_state:
    st.session_state.page = "Landing Page"

# Navigation logic
if st.session_state.page == "Landing Page":
    landing_page()
elif st.session_state.page == "Fair Division Calculator":
    # Import the fair division calculator code here
    from fair_division_calculator import fair_division_calculator
    fair_division_calculator()


