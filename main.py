import streamlit as st
from parser import * 
import os       
from pathlib import Path
from bs4 import NavigableString      
from datetime import datetime                                                                                                                                                                                        
                                                                                                                                                                    
SAVE_DIRECTORY = "Images"
BANNER_DIRECTORY = "img"

st.title("Miracles post creator")
sample = '''
# This is how you create a header
## This creates a subheader
Bullet points: 
    * Are created like this
And checklists:
    [] Like this
If you want something in *bold* or _italic_ ...
Or even ~striken~
When you are quoting someone: 
> Put their quote like this...

This is the general gist!
'''


with st.sidebar:
    st.info("Here's a simple markdown cheat sheet:")
    st.text(sample)
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
        if banner: 
            try:
                 # Create a unique filename based on the original name 
                file_extension = os.path.splitext(banner.name)[1]
                file_name      = Path(os.path.splitext(banner.name)[0]).name                                                                                                                                                                  
                banner_path = os.path.join(BANNER_DIRECTORY, f"{file_name}{file_extension}") 
                file_bytes = banner.read()
                # Write the bytes to the specified local path                                                                                                                                                                            
                with open(banner_path, "wb") as f:                                                                                                                                                                                         
                    f.write(file_bytes) 
            except Exception as e:                                                                                                                                                                                                       
                st.error(f"An error occurred while saving the file: {e}")  

        print('Received post')
        # Replace publication information  
        new_post = Parser('post.html', title, ['div', 'parent-post-preview'], ['div', 'child'])
        new_post.load_original()
        new_post_path = new_post.path # Store it to pass it href
        new_post.make_new_soup(post_content, True)# True -> we want to parse from MD to HTML 
        new_post.make_family(True) # True -> we want to create a new file 
        print('Created new post')
        st.info('Created new post ...')
        # Replace banner image and title on post
        new_post_update_title = Parser(new_post.path, title, ['div', 'parent-post-preview'], ['div', 'child'])
        new_post_update_title.load_original()
        new_post_soup = new_post_update_title.soup
        background_image = new_post_soup.find('header', class_='intro-header')
        background_image['style'] = f"background-image: url('{banner_path}')"
        post_heading = new_post_soup.find('h1', id='h1')
        post_heading.string = title
        post_heading = new_post_soup.find('h2', class_='subheading')
        post_heading.string = sub_title
        post_heading = new_post_soup.find('span', class_='meta')
        post_heading.string = str(datetime.today())
        print('Updated banner and title')
        st.info('Updated banner and title...')
        new_post_update_title.make_new_soup(new_post_soup.prettify())
        new_post_update_title.overwrite_html_file()
        

        # Update index information 
        index = Parser('index.html', title, ['div', 'parent-post-preview'], ['div', 'child'])
        index.load_original()
        reference_index = index.soup
        # Get first post-preview format 
        post_preview = reference_index.find('div', id='post-preview')
        new_post_preview = index.soup.new_tag('div', id='post-preview')
        post_preview.append(new_post_preview)
        post_preivew_div = post_preview.find('div', id='post-preview')
        new_post_link = post_preview.new_tag('a', href=new_post_path)
        post_preivew_div.append(new_post_link)
        # Here we are creating a new div
        # HR - separator
        p = new_post_link.new_tag('hr')
        new_post_link.append(p)
        # H2
        h2 = new_post_link.new_tag('h2', class_='post-title')
        h2.insert(0, NavigableString(title))
        new_post_link.append(h2)
        # H3
        h3 = new_post_link.new_tag('h3', class_='post-subtitle')
        h3.insert(0, NavigableString(sub_title))
        new_post_link.append(h3)
        # P (small)
        p = new_post_link.new_tag('small',  class_='post-meta')
        p.insert(0, NavigableString(f'Publicado por Diogo Faria {datetime.today()}'))
        new_post_link.append(p)
        
        index.make_new_soup(index.soup.prettify())
        index.overwrite_html_file()
        print('Updated index to contain new post')
        st.info('Updated index to contain new post...')
               

        # Replace index
        st.info(f"✅ Story submitted successully")
