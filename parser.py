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
        commit()
        return "Object overwritten successfully"
