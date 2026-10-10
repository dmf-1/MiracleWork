import pathlib
import re
from bs4 import BeautifulSoup as bs
from markdown_it import MarkdownIt
from copy import copy

PATH = pathlib.Path(__file__).parent.resolve()
class Parser:

    def __init__(self, template_file, title, parent=[], child=[]):
        self.template = template_file
        # parent and child expect lists or tuples: [tag_name, id_name]
        self.parent = parent
        self.child = child
        dst_dir = PATH
        dst_dir.mkdir(parents=True, exist_ok=True)
        fname = str(title).strip().replace(" ", "_")
        self.path = pathlib.Path(dst_dir / f"post_{fname}.html")

    def load_html(self):
        """
        Loads an html file into object
        """
        with open(self.template, "r", encoding="utf-8") as op:
            html = op.read()
        self.soup = bs(html, "html5lib")

    def convert_images(self, content):
        images_in_content = re.findall(r"IMG\s+(.*?)\s+", content)
        img_n = 1
        if images_in_content:
            for img in images_in_content:
                content = content.replace(
                    img, f"![image_not_loaded](/Images/A{img_n}.png)"
                )
                img_n += 1
        return content

    def parse_new_html(self, content, parse=False):
        """
        Receives new content (html / markdown) an parses into html 
        """
    
        if parse:
            md = MarkdownIt("gfm-like", {"maxNesting": 10})
            content = md.render(content)
        return bs(content, "html5lib")

    def overwrite_html_file(self, new_file=False):
        path = self.path if new_file else self.template
        with open(path, "w", encoding="utf-8") as ov:
            ov.write(self.soup.prettify())

    def append_post_content(self, content):
        """
        Appends content to convert it to post default structure
        Identifies base tag in html and appends the content rendered in newly parsed html
        """
        child_tag_name = self.child[0] if self.child else "div"
        child_id = (
            self.child[1]
            if len(self.child) > 1 and self.child[1]
            else "markdown-content"
        )

        # Create wrapper tag directly bound to self.soup so elements attach seamlessly
        new_child_tag = self.soup.new_tag(
            child_tag_name,
            id=child_id,
            class_="col-lg-8 col-lg-offset-2 col-md-10 col-md-offset-1",
        )

        # Extract parsed body contents from converted Markdown HTML
        parsed_body = content.find("body")
        if parsed_body:
            # Transfer top-level elements into the new child tag
            for node in list(parsed_body.children):
                new_child_tag.append(node)

        return new_child_tag
    
    def create_new_post(self, fields):
        """
        Encapsulates post logic 
        Loads base html 
        Edits fields based on content
        Overwrites original HTML with new one
        """
        self.load_html()
        self.edit_page_contents(fields['title'], 'h1', 'editable')
        self.edit_page_contents(fields['sub_title'], 'h2', 'editable')
        self.edit_page_contents(f'Publicado por {fields["publisher_name"]} a {fields["date"]}', 'small', 'editable')
        self.update_new_post_banner(fields['banner_path']) 
        post_content = self.parse_new_html(fields['post_content'], True)# True -> we want to parse from MD to HTML 
        prepared_post_content = self.append_post_content(post_content)
        post_parent = self.soup.find(self.parent[0], id=self.parent[1])
        if post_parent:
            post_parent.clear()
            post_parent.append(prepared_post_content)
            self.overwrite_html_file(True) # True -> we want to create a new file
            return 'Posted successfully'
        return 'Publication failed'

    def update_new_post_banner(self, banner_path):
        """
            Updates banner on header in page
        """
        background_image = self.soup.find('header', class_='intro-header')
        background_image['style'] = f"background-image: url('{banner_path}')"
        
    def check_index (self, title, sub_title):
        """
        To avoid duplicating index entries new index updates need to pass this check
        This is a preliminary measure - better implementation will come
        """
        titles = [i.text.strip() for i in self.soup.find_all('h1', type="editable") if i.text.strip() == title]
        sub_titles = [i.text.strip() for i in self.soup.find_all('h2', type="editable") if i.text.strip()  == sub_title]
        h2 = self.soup.find_all('h2')
        for i in h2:
            print('TITLE', i.string.strip(), title.strip())
            if i.string.strip() == title.strip():
                print('Title found')
                return False
        print('Title NOT found')
        return True
        
    
    def find_editable_fields(self, type):
        """
        Identify editable fields in "editable" pages - include About me, Contact
        """
        post_heading = self.soup.find_all(type=type)
        return post_heading
        
    def edit_page_contents(self, content, tag, type):
        """
        Encapsulates page editing code
        """
        post_heading = self.soup.find(tag, type=type)
        if post_heading:
            post_heading.string = content


    def duplicate_post(self, title, sub_title, name, date_):
        post_preview = self.soup.find('div', id='post-preview-latest')
        if post_preview == None:
            return Exception('Failed to find base div')
        post_preview['id'] = 'post-preview-'+post_preview.find('h2').string.replace(' ', '')
        
        parent_post_preview = post_preview.parent
        new_child_post_preview = self.soup.new_tag('div', id='post-preview-latest')
        
        new_child_post_href = self.soup.new_tag('a', href='post_'+title.replace(' ', '_')+'.html')
        new_child_post_title = self.soup.new_tag('h2', type='editable', string=title)
        new_child_post_subtitle = self.soup.new_tag('h3', type='editable', string=sub_title)
        new_child_post_small = self.soup.new_tag('small', type='editable', class_='post-meta', string=f'Publicado por {name} a {date_}')
       
        new_child_post_href.append(new_child_post_title)
        new_child_post_href.append(new_child_post_subtitle)
        new_child_post_href.append(new_child_post_small)
        
        new_child_post_preview.append(new_child_post_href)
        parent_post_preview.insert(0, new_child_post_preview)
        
        
        
        
