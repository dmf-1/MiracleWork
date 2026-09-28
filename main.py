import streamlit as st
from parser import Parser
from helper import Helper
import os       
from pathlib import Path
from bs4 import NavigableString      
from datetime import datetime                                                                                                                                                                                        
                                                                                                                                                                    
SAVE_DIRECTORY = "Images"
BANNER_DIRECTORY = "img"
now = datetime.now()
date_ = now.strftime("%Y-%m-%d")

tag_to_label = {
    'h1':'Header',
    'h2':'Sub-header',
    'span':'Sub-title',
    'p':'Content',
}


st.title("Silver-potato")

sample = [
    '# This is how you create a header',
    '## Here is a subheader',
    '''* These are 
    * Bullet points''',
    '~This is how you strike a sentence~',
    '_This is how you set text in italic_',
    '*This is how you bold*',
    '> And this is how you quote someone!'    
]

with st.sidebar:
    st.markdown("### Here's a simple markdown cheat sheet:")
    for s in sample:
        st.text(s)
        st.markdown(s)
        st.divider()

# Create helper object - check credentials
helper = Helper()
helper.load_credentials()
is_pwd_set = helper.is_password_set() # It's declared by user - but describes if git is authenticated
if not is_pwd_set:
    warning_message = f"""
    Attention ⚠️ - streamlit assumes that you do not have git authenticated.\n
    This means that you currently can't post.\n
    If you think this is a mistake (i.e. have recently posted) toggle the authentication button.
    """
    st.warning(warning_message)
    set_pwd = st.button('I confirm that GIT is authenticated in this computer', type='secondary')
    if set_pwd:
        helper.toggle_password_set()
        st.rerun()


def generic_form(page):
    st.subheader(f'Edit "{page}" content')
    with st.form(f'{page}_page_form'):
        parser = Parser(f'{page}.html', 'Title')
        parser.load_html()
        editable_fields = parser.find_editable_fields(type='editable')
        if editable_fields:
            for i in editable_fields:
                i.string = st.text_area(tag_to_label[i.name], value = i.string, placeholder=i.string, height='content')
        save = st.form_submit_button('Save')
        if save: 
            parser.overwrite_html_file()
            st.rerun()


def post_page_form():
    st.subheader(f'Submit new post')

    with st.form("post_page_form"):
        # Publication header
        banner = st.file_uploader(
            "Upload banner image", type=["jpg", "png"]
        )
        
        #Publication title
        title = st.text_input("Publication title (will appear on links and page name)")
        
        #Publication sub_title
        sub_title = st.text_input("Subtitle")

        # Define paragraph inputs
        post_content = st.text_area("Your next story here....", height=300)

        # Every form must have a submit button.
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            fields = [
                banner,
                title,
                sub_title,
                post_content
            ]
            complete = len([i for i in fields if i]) == len(fields) # Checks if all fields were submitted
            
            if complete:
                try:
                        # Create a unique filename based on the original name 
                    file_extension = os.path.splitext(banner.name)[1]
                    file_name      = Path(os.path.splitext(banner.name)[0]).name                                                                                                                                                                  
                    banner_path = os.path.join(BANNER_DIRECTORY, f"{file_name}{file_extension}") 
                    file_bytes = banner.read()
                    # Write the bytes to the specified local path                                                                                                                                                                            
                    with open(banner_path, "wb") as of:                                                                                                                                                                                         
                        of.write(file_bytes) 
                except Exception as e:                                                                                                                                                                                                       
                    st.error(f"An error occurred while saving the file: {e}")  

                print('Received post')
                # Replace publication information  
                new_post = Parser('post.html', title, ['div', 'parent-post-preview'], ['div', 'child'])
                new_post_path = new_post.create_new_post(post_content)
                print('Created new post')
                st.info('Created new post ...')
                # Update banner, title, subtitle, and date on post
                new_post_update_title = Parser(new_post.path, title, ['div', 'parent-post-preview'], ['div', 'child'])
                new_post_update_title.load_html()
                new_post_update_title.edit_page_contents(title, 'h1', 'editable')
                new_post_update_title.edit_page_contents(sub_title, 'h2', 'editable')
                new_post_update_title.edit_page_contents(date_, 'small', 'editable')
                new_post_update_title.update_new_post_banner(banner_path)
                new_post_update_title.parse_new_html(new_post.soup.prettify()) # I think i can remove this line check later 
                new_post_update_title.overwrite_html_file()
                print('Updated banner and title')
                st.info('Updated banner and title...')
                
                # Update index information 
                index = Parser('index.html', title, ['div', 'parent-post-preview'], ['div', 'child'])
                index.load_html()
                reference_index = index.soup
                index.duplicate_post(title, sub_title, helper.credentials['name'], date_)
                
                
                # Check if is duplicated or not
                if not index.check_index(title, sub_title):
                    index.overwrite_html_file()
                    print('Updated index to contain new post')
                    st.info('Updated index to contain new post...')
                else:
                    st.info('Home page not updated as it was a duplicated / edit post')

                # Replace index
                st.info(f"✅ Story submitted successully")
            else:
                st.error('Please fill all fields to submit')

# Section to edit other page contents
tab1, tab2, tab3 = st.tabs(["Post", "About me", "Contact"])

with tab1:
    post_page_form()

with tab2:
    generic_form('about')

with tab3:
    generic_form('contact')

    