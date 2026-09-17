import pathlib
import re
from bs4 import BeautifulSoup as bs
from markdown_it import MarkdownIt
import os

def commit():
    os.system('~/update_git.sh')

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

    def load_original(self):
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

    def make_new_soup(self, content, parse=False):
        if parse:
            md = MarkdownIt("gfm-like", {"maxNesting": 10})
            content = self.convert_images(content)
            content = md.render(content)
        self.n_soup = bs(content, "html5lib")

    def overwrite_html_file(self, new_file=False):
        path = self.path if new_file else self.template
        with open(path, "w", encoding="utf-8") as ov:
            ov.write(self.soup.prettify())

    def create_new_child(self):
        """Wraps parsed body nodes from self.n_soup into a new element defined by self.child."""
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
        parsed_body = self.n_soup.find("body")
        if parsed_body:
            # Transfer top-level elements into the new child tag
            for node in list(parsed_body.children):
                new_child_tag.append(node)

        return new_child_tag

    def make_family(self, new_file=False):
        """Locates the parent tag in reference HTML (self.soup), replaces its content

        with the newly parsed child tag, and writes to disk.
        """
        if not hasattr(self, "soup"):
            self.load_original()

        # Locate target parent element using tag name and ID
        parent_tag_name = self.parent[0] if self.parent else None
        parent_id = self.parent[1] if len(self.parent) > 1 else None

        if parent_id:
            parent_node = self.soup.find(parent_tag_name, id=parent_id)
        else:
            parent_node = self.soup.find(parent_tag_name)

        if not parent_node:
            raise ValueError(
                f"Target parent node ({parent_tag_name}, id={parent_id}) not found in target soup."
            )

        # Generate new child element tree
        new_child = self.create_new_child()

        # Replace existing content inside target parent
        parent_node.clear()
        parent_node.append(new_child)

        # Persist updated soup to HTML file
        self.overwrite_html_file(new_file=new_file)
        return "Object overwritten successfully"
    
    def create_new_post(self, post_content):
        """
        Encapsulates post creation to simplify code
            """
        self.load_original()
        self.make_new_soup(post_content, True)# True -> we want to parse from MD to HTML 
        self.make_family(True) # True -> we want to create a new file
        return self.path

    def update_new_post_contents(self, banner_path, title, sub_title, date_):
        # Fields that are updated with each new post
        fields_to_change = {
            'h1':['h1', title],
            'h2':['subheading', sub_title],
            'small':['meta', date_]
        }
        # Load new post reference html
        self.load_original()

        # Iteratively update fields
        for k, v in fields_to_change.items():
            post_heading = self.soup.find(k, class_=v[0])
            print('V1: ', v[0], v[1])
            post_heading.string = v[1]
        
        # Update background banner
        background_image = self.soup.find('header', class_='intro-header')
        background_image['style'] = f"background-image: url('{banner_path}')"
        
    def check_index (self, title, sub_title):
        """
        To avoid duplicating index entries new index updates need to pass this check
        This is a preliminary measure - better implementation will come
        """
        titles = [i.text.strip() for i in self.soup.find_all('h2', id="post-title") if i.text.strip == title]
        sub_titles = [i.text.strip() for i in self.soup.find_all('h3', id="post-subtitle") if i.text.strip == sub_title]
       
        duplicated_title = len(titles) > 0
        duplicated_sub_title = len(sub_titles) > 0

        print('Title ', duplicated_title)
        print('Sub title ', duplicated_sub_title)
        
        return duplicated_title and duplicated_sub_title
        
        
