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
    'h3':'Sub-header',
    'span':'Sub-header',
    'small':'Sub-sub-info',
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

def settings():
    st.subheader('Settings')
    st.divider()
    st.warning('To update code you must discard all changes')
    if st.button('Discard changes', type="primary"):
        sync.git_discard()
    if st.button('Update streamlit app', type="primary"):
        sync.git_pull

    st.info('Only to be used if failed to sync')
    if st.button('Sync new publications', type="primary"):
        sync.git_add()
        sync.git_commit()
        sync.git_push()


with st.sidebar:
    st.markdown("### Here's a simple markdown cheat sheet:")
    for s in sample:
        st.text(s)
        st.markdown(s)
        st.divider()
    sync = Helper()
    settings()
        

# Create helper object - check credentials
helper = Helper()
helper.load_credentials()
PUBLISHER_NAME = helper.credentials['name']
is_pwd_set = helper.is_password_set() # It's declared by user - but describes if git is authenticated
if not is_pwd_set or not PUBLISHER_NAME:
    warning_message = f"""
    Attention ⚠️ - You are missing either your GIT token or you publisher name.\n
    This means that you currently can't post.\n
    Confirm that you have your GIT authentication and publisher name set.
    """
    st.warning(warning_message)
    publisher_name = st.text_input('Name for publications')
    set_pwd = st.button('I confirm that GIT is authenticated in this computer', type='secondary')
    if set_pwd and publisher_name:
        helper.toggle_password_set()
        helper.set_publisher_name(publisher_name)
        st.rerun()

def generic_form(page):
    st.subheader(f'Edit "{page}" content')
    with st.form(f'{page}_page_form'):
        parser = Parser(f'{page}.html', 'Title')
        parser.load_html()
        editable_fields = parser.find_editable_fields(type='editable')
        if editable_fields:
            for i in editable_fields:
                i.string = st.text_area(tag_to_label[i.name], value = i.string.strip(), placeholder=i.string, height='content')
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
        title = st.text_input("Publication title (will appear on links and page name)").strip()
        
        #Publication sub_title
        sub_title = st.text_input("Subtitle").strip()

        # Define paragraph inputs
        post_content = st.text_area("Your next story here....", height=300).strip()
        
        # Upload button
        # Calls method that tracks number of instances externally - might need an object for that - and iteratively adds image and text box.
        # Don't care for text box id, just append content to an array that will combine everything into a single markdown block.

        # Every form must have a submit button.
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            fields = {
               'banner_path'    : banner,
               'title'          : title,
               'sub_title'      : sub_title,
               'post_content'   : post_content,
               'publisher_name' : PUBLISHER_NAME,
               'date'           : date_   
            }
            
            complete = len([v for k, v in fields.items() if v]) == len(fields) # Checks if all fields were submitted
            
            if complete:
                try:
                    # Create a unique filename based on the original name 
                    file_extension = os.path.splitext(banner.name)[1]
                    file_name      = Path(os.path.splitext(banner.name)[0]).name                                                                                                                                                                  
                    fields['banner_path'] = os.path.join(BANNER_DIRECTORY, f"{file_name}{file_extension}") 
                    file_bytes = banner.read()
                    # Write the bytes to the specified local path                                                                                                                                                                            
                    with open(fields['banner_path'], "wb") as of:                                                                                                                                                                                         
                        of.write(file_bytes) 
                except Exception as e:                                                                                                                                                                                                       
                    st.error(f"An error occurred while saving the file: {e}")  

                # Replace publication information  
                new_post = Parser('post.html', title, ['div', 'parent-post-preview'], ['div', 'child'])
                post_message = new_post.create_new_post(fields)
                st.info(f'{post_message}')
                
                # Update index information 
                index = Parser('index.html', title, ['div', 'parent-post-preview'], ['div', 'child'])
                index.load_html()
                # Check if is duplicated or not
                if index.check_index(title, sub_title):
                    index.duplicate_post(title, sub_title, PUBLISHER_NAME, date_)
                    index.overwrite_html_file()
                    st.info('Updated home page to contain new post...')
                else:
                    st.info('Home page not updated as it was a duplicated / edit post')

                # Replace index
                st.info(f"Story saved successfully")
                sync.git_add()
                sync.git_commit()
                sync.git_push()
                st.info(f"✅ Site updated successfully")
            else:
                st.error('Please fill all fields to submit')

# Section to edit other page contents
tab1, tab2, tab3, tab4 = st.tabs(["Post", "About me", "Contact", "Home"])

with tab1:
    post_page_form()

with tab2:
    generic_form('about')

with tab3:
    generic_form('contact')

with tab4:
    generic_form('index')

    