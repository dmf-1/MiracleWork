import streamlit as st
import streamlit.components.v1 as components
from parser import Parser, Site, PATH, POST_TEMPLATE, BANNER_TEMPLATE
from helper import Helper
import os
import base64
import re
from pathlib import Path
from bs4 import BeautifulSoup as bs
from datetime import datetime

SAVE_DIRECTORY = "Images"
BANNER_DIRECTORY = "img"
now = datetime.now()
date_ = now.strftime("%Y-%m-%d")

st.title("Silver-potato")

# Create helper object - check credentials
helper = Helper()
helper.load_credentials()
site = Site()
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

# Messages that must survive an st.rerun()
for message in st.session_state.pop('flash', []):
    st.success(message)

def flash(message):
    st.session_state.setdefault('flash', []).append(message)

tag_to_label = {
    'h1':'Header',
    'h2':'Sub-header 2',
    'h3':'Sub-header 3',
    'h4':'Sub-header 4',
    'h5':'Sub-header 5',
    'span':'Sub-header <span>',
    'small':'Sub-sub-info <small>',
    'p':'Content',
}

PAGE_NAMES = {'index': 'Home', 'about': 'About me', 'contact': 'Contact'}
# Editable tags that accept markdown, per page
MARKDOWN_PAGES = {'about': {'p', 'div'}}



sample = [
    '# This is how you create a header',
    '## Here is a subheader',
    '''* These are
* Bullet points''',
    '~~This is how you strike a sentence~~',
    '*This is how you set text in italic* (or _like this_)',
    '**This is how you bold** (or __like this__)',
    '> And this is how you quote someone!'
]

def upload_changes():
    helper.git_add()
    helper.git_commit()
    helper.git_push()

def settings():
    if st.button('Upload'):
        upload_changes()
        st.rerun()

    elif st.button('Clear'):
        helper.git_discard()
        st.rerun()

    elif st.button('Change user name'):
        helper.load_credentials()
        helper.toggle_password_set()
        st.rerun()
    st.divider()
    results = helper.git_status().split("\n")[:-1]
    st.text(f"Modified files - not uploaded:")
    for r in results:
        st.markdown(f"* {r}")


def image_uploader():
    st.info('Add images and it converts them to markdown path')
    images = st.file_uploader('Upload publication images', type=["jpg", "png"], accept_multiple_files = True)
    if images:
        for i in images:
            image_path = save_image(i)
            if image_path:
                st.text(f'![publication_image]({image_path})')
    st.text('Copy the links above in the sections in which you wish to add an image')
    if st.button('Upload images', type='primary'):
            upload_changes()
            st.rerun()



def save_image(image):
    try:
        # Create a unique filename based on the original name
        stem, file_extension = os.path.splitext(Path(image.name).name)
        file_name      = f"{Helper.sanitize_filename(stem)}{Helper.sanitize_filename(file_extension, '')}"
        image_path     = Path(helper.path, BANNER_DIRECTORY, file_name)
        file_bytes     = image.getvalue()
        # Write the bytes to the specified local path
        with open(image_path, "wb") as of:
            of.write(file_bytes)
        # Return a web path (forward slashes) - os.path.join would produce img\file.jpg on windows
        return Helper.web_path(BANNER_DIRECTORY, file_name)

    except Exception as e:
        st.error(f"An error occurred while saving the file: {e}")


def uploaded_data_uri(uploaded):
    """
    Lets the preview show an image that was uploaded but not saved yet
    """
    return f"data:{uploaded.type};base64,{base64.b64encode(uploaded.getvalue()).decode()}"


def show_preview(html, height=900, width='stretch'):
    st.caption('Preview - links to other pages are disabled here.')
    # st.iframe is only available in recent streamlit versions
    if hasattr(st, 'iframe'):
        st.iframe(html, height=height, width=width)
    else:
        components.html(html, height=height, scrolling=True)


def banner_warning():
    message = f'No banner was provided - the template banner ({BANNER_TEMPLATE}) will be used. You can change it later in "Published posts".'
    if not Path(PATH, BANNER_TEMPLATE).is_file():
        message += f' Note: {BANNER_TEMPLATE} is not in the project yet, so the banner will be empty until it is added.'
    st.warning(message)


with st.sidebar:
    tab1, tab2, tab3 = st.tabs(['Settings', 'Image uploader', 'Markdown Cheat sheet'])
    with tab1:
        settings()
    with tab2:
        image_uploader()
    with tab3:
        st.markdown("## Here's a simple markdown cheat sheet:")
        st.space()
        for s in sample:
            st.text(s)
            st.markdown(s)
            st.divider()



def field_label(page, element):
    """
    Describes an editable element in plain words, based on where it is in the page
    """
    if element.find_parent('div', id=re.compile('^post-preview-')):
        return {'h2': 'Post title', 'h3': 'Post subtitle', 'small': 'Author and date',
                'hr': 'Hide the divider line below this post'}.get(element.name, tag_to_label.get(element.name, 'Text'))
    if element.find_parent(class_=['site-heading', 'page-heading']):
        heading = 'Site' if page == 'index' else 'Page'
        if element.name == 'h1':
            return f'{heading} title (top of the page)'
        return f'{heading} subtitle (below the title)'
    if element.name == 'h5':
        return 'Contact name (e.g. Email, LinkedIn)'
    contact_name = element.find_previous_sibling('h5', type='editable')
    if contact_name:
        return f'Contact details for "{contact_name.get_text().strip()}"'
    if element.name == 'hr':
        return 'Hide the divider line at the end of the post list' if page == 'index' else 'Hide divider line'
    if page in MARKDOWN_PAGES and element.name in MARKDOWN_PAGES[page]:
        return 'Main text (Markdown allowed - see the cheat sheet in the sidebar)'
    if element.name in ('p', 'div'):
        return 'Introduction text' if page == 'contact' else 'Text'
    return tag_to_label.get(element.name, 'Text')


def generic_form(page):
    st.subheader(f'Edit "{PAGE_NAMES.get(page, page)}" page')
    with st.form(f'{page}_page_form'):
        parser = Parser(f'{page}.html', 'Title')
        parser.load_html()
        previous_titles = {e['href']: e['title'] for e in parser.index_entries()}
        editable_fields = parser.find_editable_fields(type='editable')
        markdown_tags = MARKDOWN_PAGES.get(page, set())
        n = 0
        post_number = 0
        if editable_fields:
            for i in editable_fields:
                if i.name == 'h2' and i.find_parent('div', id=re.compile('^post-preview-')):
                    # Group the fields of each post listed on the home page
                    post_number += 1
                    st.markdown(f'**Post {post_number}: {i.get_text().strip()}**')
                label = field_label(page, i)
                if i.name == 'hr':
                    is_hidden = 'hidden' in i.get('style', '')
                    i['style'] = "visibility:hidden" if st.checkbox(label, value=is_hidden, key=f"id_{page}_checkbox_{n}") else ""
                elif i.name in markdown_tags:
                    # Plain text is valid markdown, so older text can be edited the same way
                    markdown = i.get('data-markdown', i.get_text().strip())
                    new_markdown = st.text_area(label, value=markdown, key=f"id_{page}_{n}", height=300)
                    if new_markdown != markdown or not i.has_attr('data-markdown'):
                        parser.set_markdown_block(i, new_markdown)
                elif i.string:
                    i.string = st.text_area(label, value = i.string.strip(), key=f"id_{page}_{n}", placeholder=i.string, height='content')
                n += 1
        save = st.form_submit_button('Save')
        if save:
            parser.overwrite_html_file()
            if page == 'index':
                # Titles edited on the home page are copied into the posts themselves
                changed = site.sync_index_titles_to_posts(previous_titles)
                if changed:
                    flash(f'Home page saved. Title updated in {len(changed)} post(s): {", ".join(changed)}')
            st.rerun()


def template_form():
    st.subheader('Edit post template')
    st.info('Changes to the template are applied to every published post. Each post keeps its own title, subtitle, banner and content.')
    parser = Parser(POST_TEMPLATE, 'Title')
    parser.load_html()
    original_html = str(parser.soup)
    soup = parser.soup

    with st.form('template_form'):
        st.markdown('**Navigation bar**')
        for n, link in enumerate(soup.select('nav a.navbar-brand, nav ul.nav a')):
            link.string = st.text_input(f'Menu link text (opens {link.get("href", "")})', value=link.get_text().strip(), key=f'template_nav_{n}')

        st.markdown('**Footer**')
        for n, link in enumerate(soup.select('footer ul.list-inline a')):
            icon = link.find('i', class_=lambda c: c and c.startswith('fa-') and c not in ('fa-circle', 'fa-stack-2x', 'fa-stack-1x', 'fa-inverse'))
            network = icon['class'][1].removeprefix('fa-').capitalize() if icon else f'Social link {n + 1}'
            link['href'] = st.text_input(f'{network} link', value=link.get('href', ''), key=f'template_social_{n}') or '#'
        copyright = soup.select_one('footer p.copyright')
        if copyright:
            copyright.string = st.text_input('Copyright text', value=copyright.get_text().strip(), key='template_copyright')

        with st.expander('Advanced: edit the template HTML directly'):
            st.caption('If you change the HTML here, the fields above are ignored.')
            raw_html = st.text_area('Template HTML', value=original_html, height=400, key='template_raw')

        col1, col2 = st.columns(2)
        save = col1.form_submit_button('Save template and update all posts', type='primary')
        preview = col2.form_submit_button('Preview template')

    if not (save or preview):
        return
    if raw_html != original_html:
        soup = bs(raw_html, 'html5lib')
    missing = site.validate_template(soup)
    if missing:
        st.error('The template is missing parts needed to build posts: ' + ', '.join(missing))
        return
    if preview:
        show_preview(site.preview_html(soup))
        return
    parser.soup = soup
    parser.overwrite_html_file()
    updated = site.apply_template_to_posts()
    flash(f'Template saved and applied to {len(updated)} post(s).')
    st.rerun()


def post_page_form():
    st.subheader(f'Submit new post')
    st.caption('To change a post that is already published, use the "Published posts" page.')

    with st.form("post_page_form"):
        # Publication header
        banner = st.file_uploader(
            "Upload banner image (optional)", type=["jpg", "png"], accept_multiple_files = False
        )

        #Publication title
        title = st.text_input("Publication title (will appear on links and page name)").strip()

        #Publication sub_title
        sub_title = st.text_input("Subtitle").strip()

        # Define paragraph inputs
        post_content = st.text_area("Your next story here....", height=300).strip()

        col1, col2, col3 = st.columns(3)
        save = col1.form_submit_button("Save", type='primary', help='Saves the post on this computer')
        upload = col2.form_submit_button("Upload", help='Saves the post and publishes it online')
        preview = col3.form_submit_button("Preview", help='Shows the post without saving it')

    if not (save or upload or preview):
        return

    fields = {
       'title'          : title,
       'sub_title'      : sub_title,
       'post_content'   : post_content,
       'publisher_name' : PUBLISHER_NAME,
       'date'           : date_
    }
    if not all(fields.values()): # Every field except the banner is required
        st.error('Please fill the title, subtitle and content (and set your publisher name) to continue')
        return
    if not banner:
        banner_warning()

    if preview:
        new_post = Parser(POST_TEMPLATE, title, Site.POST_PARENT, Site.POST_CHILD)
        new_post.load_html()
        extra_files = {}
        if banner:
            fields['banner_path'] = banner.name
            extra_files[banner.name] = uploaded_data_uri(banner)
        else:
            fields['banner_path'] = None
        new_post.build_post(fields)
        show_preview(site.preview_html(new_post.soup, extra_files))
        return

    # Only the post created in this session may be overwritten from here (e.g. Save then Upload)
    file_name = Parser.post_file_name(title)
    own_draft = st.session_state.get('saved_post') == file_name
    if not own_draft and site.title_in_use(title):
        st.error('A post with this title already exists. Choose another title, or edit the existing post in the "Published posts" page.')
        return

    fields['banner_path'] = save_image(banner) if banner else None

    # Replace publication information
    new_post = Parser(POST_TEMPLATE, title, Site.POST_PARENT, Site.POST_CHILD)
    post_message = new_post.create_new_post(fields)
    st.info(f'{post_message}')
    if post_message != 'Posted successfully':
        return
    st.session_state['saved_post'] = file_name

    # Update index information
    index = Parser('index.html', title, Site.POST_PARENT, Site.POST_CHILD)
    index.load_html()
    meta = f'Publicado por {PUBLISHER_NAME} a {date_}'
    if not index.update_index_entry(file_name, title, sub_title, meta):
        index.duplicate_post(title, sub_title, PUBLISHER_NAME, date_)
        st.info('Updated home page to contain new post...')
    index.overwrite_html_file()
    st.info(f"Story saved successfully")

    if upload:
        upload_changes()
        st.info(f"✅ Site updated successfully")


def main_page():
    # Section to edit other page contents
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Post", "Post template", "About me", "Contact", "Home"])

    with tab1:
        post_page_form()

    with tab2:
        template_form()

    with tab3:
        generic_form('about')

    with tab4:
        generic_form('contact')

    with tab5:
        generic_form('index')


def posts_page():
    st.subheader('Published posts')
    posts = site.list_posts()
    st.dataframe(
        [{'Title': p['title'], 'Subtitle': p['sub_title'], 'Info': p['meta'],
          'On home page': p['on_home'] and not p['hidden'], 'File': p['href']} for p in posts],
        hide_index=True,
    )
    missing_files = [p['href'] for p in posts if not p['file']]
    if missing_files:
        st.warning('These home page entries link to posts that do not exist: ' + ', '.join(missing_files))

    editable = [p for p in posts if p['file']]
    if not editable:
        return
    choice = st.selectbox('Select a post to edit', editable,
                          format_func=lambda p: p['title'] + ('  (hidden from home page)' if p['hidden'] else ''))
    file_name = choice['file']
    fields = site.post_parser(file_name).get_post_fields()
    if choice['on_home'] and choice['title'] != fields['title']:
        st.info(f'The home page shows this post as "{choice["title"]}". Saving will use the title below on both.')

    key = f'edit_{file_name}'
    with st.form(key):
        title = st.text_input('Title (post and home page)', value=fields['title'], key=f'{key}_title').strip()
        sub_title = st.text_input('Subtitle on the post', value=fields['sub_title'], key=f'{key}_sub_title').strip()
        meta = st.text_input('Author and date on the post', value=fields['meta'], key=f'{key}_meta').strip()

        if fields['banner_path'] and Path(PATH, fields['banner_path']).is_file():
            st.image(str(Path(PATH, fields['banner_path'])), caption='Current banner', width=300)
        else:
            st.caption(f'Current banner: {fields["banner_path"] or "none"}')
        banner = st.file_uploader('Replace banner (optional)', type=["jpg", "png"], key=f'{key}_banner')

        if fields['post_content'] is not None:
            content = st.text_area('Content (markdown)', value=fields['post_content'], height=400, key=f'{key}_content')
        else:
            st.info('This post was published before the markdown text was kept, so its content is shown as HTML.')
            content = st.text_area('Content (HTML)', value=fields['post_html'], height=400, key=f'{key}_html')

        st.markdown('**Home page**')
        if choice['on_home']:
            home_sub_title = st.text_input('Subtitle on the home page', value=choice['sub_title'], key=f'{key}_home_sub_title').strip()
            home_meta = st.text_input('Author and date on the home page', value=choice['meta'], key=f'{key}_home_meta').strip()
            hidden = st.checkbox('Hide from home page', value=choice['hidden'], key=f'{key}_hidden')
        else:
            st.caption('This post is not listed on the home page.')

        col1, col2, col3 = st.columns(3)
        save = col1.form_submit_button('Save', type='primary', help='Saves the changes on this computer')
        upload = col2.form_submit_button('Upload', help='Saves the changes and publishes them online')
        preview = col3.form_submit_button('Preview', help='Shows the post without saving it')

    if not (save or upload or preview):
        return
    if not (title and sub_title and meta and content.strip()):
        st.error('Title, subtitle, author and date and content cannot be empty')
        return
    new_fields = {'title': title, 'sub_title': sub_title, 'meta': meta, 'banner_path': fields['banner_path']}
    if fields['post_content'] is not None:
        new_fields['post_content'] = content
    else:
        new_fields['post_html'] = content

    if preview:
        parser = site.post_parser(file_name)
        extra_files = {}
        if banner:
            new_fields['banner_path'] = banner.name
            extra_files[banner.name] = uploaded_data_uri(banner)
        parser.build_post(new_fields)
        show_preview(site.preview_html(parser.soup, extra_files))
        return

    if title != fields['title'] and site.title_in_use(title, ignore_file=file_name):
        st.error('Another post already uses this title.')
        return
    if banner:
        new_fields['banner_path'] = save_image(banner)
    home = {'sub_title': home_sub_title, 'meta': home_meta, 'hidden': hidden} if choice['on_home'] else None
    if not site.save_post(file_name, new_fields, home):
        st.error('Could not save the post - its page is missing the content section.')
        return
    message = 'Post saved (home page updated too).'
    if upload:
        upload_changes()
        message += ' ✅ Site updated successfully.'
    flash(message)
    st.rerun()


def preview_page():
    st.subheader('Page preview')
    st.caption('See how any page of the site looks before uploading it.')
    pages = {'Home': 'index.html', 'About me': 'about.html', 'Contact': 'contact.html', 'Post template': POST_TEMPLATE}
    pages.update({f'Post: {p["title"]}': p['file'] for p in site.list_posts() if p['file']})
    col1, col2 = st.columns([3, 1])
    page = col1.selectbox('Page', list(pages))
    device = col2.radio('View as', ['Computer', 'Phone'], horizontal=True)
    parser = Parser(pages[page], 'Title')
    parser.load_html()
    show_preview(site.preview_html(parser.soup), width='stretch' if device == 'Computer' else 390)


navigation = st.navigation([
    st.Page(main_page, title='Main', default=True),
    st.Page(posts_page, title='Published posts', url_path='posts'),
    st.Page(preview_page, title='Page preview', url_path='preview'),
])
navigation.run()
