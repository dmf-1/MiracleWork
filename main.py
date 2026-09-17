import streamlit as st
from parser import * 
import os       
from pathlib import Path
from bs4 import NavigableString      
from datetime import datetime                                                                                                                                                                                        
                                                                                                                                                                    
SAVE_DIRECTORY = "Images"
BANNER_DIRECTORY = "img"
now = datetime.now()
date_ = now.strftime("%Y-%m-%d")

st.title("Silver-Postato")
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
    st.info("Here's a simple markdown cheat sheet:")
    for s in sample:
        st.text(s)
        st.markdown(s)
        st.divider()


with st.form("page_form"):

    # Publication header
    banner = st.file_uploader(
        "Upload banner image", type=["jpg", "png"]
    )
    
    #Publication title
    title = st.text_input("Publication title (will appear on links and page name)")
    
    #Publication sub_title
    sub_title = st.text_input("Subtitle")

    # Define paragraph inputs
    post_content = st.text_area("Your next story here....")

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
            new_post_update_title.update_new_post_contents(banner_path, title, sub_title, date_)
            new_post_update_title.make_new_soup(new_post.soup.prettify())
            new_post_update_title.overwrite_html_file()
            print('Updated banner and title')
            st.info('Updated banner and title...')
            

            # Update index information 
            index = Parser('index.html', title, ['div', 'parent-post-preview'], ['div', 'child'])
            index.load_original()
            reference_index = index.soup
            
            # Check if is duplicated or not
            if not index.check_index(title, sub_title):
                # Get first post-preview format 
                post_preview = reference_index.find('div', id='post-preview')
                new_post_preview = index.soup.new_tag('div', id='post-preview')
                post_preview.append(new_post_preview)
                post_preivew_div = post_preview.find('div', id='post-preview')
                new_post_link = post_preview.new_tag('a', href=str(new_post_path).split("/")[-1])
                post_preivew_div.append(new_post_link)
                # Here we are creating a new div
                # HR - separator
                p = new_post_link.new_tag('hr')
                new_post_link.append(p)
                # H2
                h2 = new_post_link.new_tag('h2', id='post-title')
                h2.insert(0, NavigableString(title))
                new_post_link.append(h2)
                # H3
                h3 = new_post_link.new_tag('h3', id='post-subtitle')
                h3.insert(0, NavigableString(sub_title))
                new_post_link.append(h3)
                # P (small)
                p = new_post_link.new_tag('small',  class_='post-meta')
                p.insert(0, NavigableString(f'Publicado por Diogo Faria {date_}'))
                new_post_link.append(p)
                
                index.make_new_soup(index.soup.prettify())
                index.overwrite_html_file()
                print('Updated index to contain new post')
                st.info('Updated index to contain new post...')
            else:
                st.info('Home page not updated as it was a duplicated / edit post')

            # Replace index
            st.info(f"✅ Story submitted successully")
        else:
            st.error('Please fill all fields to submit')