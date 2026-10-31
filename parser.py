import base64
import mimetypes
import pathlib
import re
from bs4 import BeautifulSoup as bs
from markdown_it import MarkdownIt
from copy import copy
from helper import Helper

PATH = pathlib.Path(__file__).parent.resolve()
POST_TEMPLATE = 'post.html'
INDEX_PAGE = 'index.html'
# Used when a post is published without a banner
BANNER_TEMPLATE = 'img/banner-template.jpg'
# Hidden <script> that keeps the original markdown of a post so it can be edited later
MARKDOWN_SOURCE_ID = 'post-markdown-source'
HIDDEN_STYLE = 'display:none'

class Parser:

    def __init__(self, template_file, title, parent=[], child=[]):
        # Templates are resolved against the project folder so the app can be started from anywhere
        self.template = pathlib.Path(PATH, template_file)
        # parent and child expect lists or tuples: [tag_name, id_name]
        self.parent = parent
        self.child = child
        dst_dir = PATH
        dst_dir.mkdir(parents=True, exist_ok=True)
        self.path = pathlib.Path(dst_dir / self.post_file_name(title))

    @staticmethod
    def post_file_name(title):
        return f"post_{Helper.sanitize_filename(title)}.html"

    def load_html(self):
        """
        Loads an html file into object
        """
        with open(self.template, "r", encoding="utf-8") as op:
            html = op.read()
        self.soup = bs(html, "html5lib")

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
            # str() instead of prettify(): prettify adds line breaks inside inline tags
            # (<strong>, <em>, <a>) which shows up as extra spaces around formatted words
            ov.write(str(self.soup))

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
            attrs={"class": "col-lg-8 col-lg-offset-2 col-md-10 col-md-offset-1"},
        )

        # Extract parsed body contents from converted Markdown HTML
        parsed_body = content.find("body")
        if parsed_body:
            # Transfer top-level elements into the new child tag
            for node in list(parsed_body.children):
                new_child_tag.append(node)
            # Images were moved into the new tag, so look them up there
            for i in new_child_tag.find_all('img'):
                i['class'] = "img-responsive"

        return new_child_tag

    def create_new_post(self, fields):
        """
        Encapsulates post logic
        Loads base html
        Edits fields based on content
        Overwrites original HTML with new one
        """
        self.load_html()
        if self.build_post(fields):
            self.overwrite_html_file(True) # True -> we want to create a new file
            return 'Posted successfully'
        return 'Publication failed'

    def build_post(self, fields):
        """
        Fills the loaded template with the post fields, without writing it to disk
        Used both to publish and to preview a post
        """
        self.edit_page_contents(fields['title'], 'h1', 'editable')
        self.edit_page_contents(fields['sub_title'], 'h2', 'editable')
        self.edit_page_contents(fields.get('meta') or f'Publicado por {fields["publisher_name"]} a {fields["date"]}', 'small', 'editable')
        self.set_page_title(fields['title'])
        self.update_new_post_banner(fields['banner_path'] or BANNER_TEMPLATE)
        if fields.get('post_html') is not None:
            # Older posts have no markdown source, so their html is edited directly
            post_content = self.parse_new_html(fields['post_html'])
            self.set_markdown_source(None)
        else:
            post_content = self.parse_new_html(fields['post_content'], True)# True -> we want to parse from MD to HTML
            self.set_markdown_source(fields['post_content'])
        prepared_post_content = self.append_post_content(post_content)
        return self.set_post_body(prepared_post_content)

    def set_post_body(self, new_content):
        post_parent = self.soup.find(self.parent[0], id=self.parent[1])
        if post_parent:
            post_parent.clear()
            post_parent.append(new_content)
            return True
        return False

    def update_new_post_banner(self, banner_path):
        """
            Updates banner on header in page
        """
        background_image = self.soup.find('header', class_='intro-header')
        background_image['style'] = f"background-image: url('{banner_path}')"

    def get_post_banner(self):
        header = self.soup.find('header', class_='intro-header')
        match = re.search(r"url\(['\"]?([^'\")]+)['\"]?\)", header.get('style', '')) if header else None
        return match.group(1) if match else ''

    def set_page_title(self, title):
        if self.soup.title:
            self.soup.title.string = title

    def set_markdown_source(self, markdown):
        """
        Stores (or removes, if markdown is None) the markdown used to create the post
        It lives in an inert <script type="text/markdown"> so browsers don't display it
        """
        source = self.soup.find('script', id=MARKDOWN_SOURCE_ID)
        if markdown is None:
            if source:
                source.decompose()
            return
        if not source:
            source = self.soup.new_tag('script', id=MARKDOWN_SOURCE_ID, type='text/markdown')
            self.soup.head.append(source)
        # "</" would close the script tag early
        source.string = markdown.replace('</', '<\\/')

    def get_markdown_source(self):
        source = self.soup.find('script', id=MARKDOWN_SOURCE_ID)
        return source.string.replace('<\\/', '</') if source and source.string else None

    def get_post_fields(self):
        """
        Reads the editable information of a post page
        """
        def text(tag):
            found = self.soup.find(tag, type='editable')
            return found.get_text().strip() if found else ''

        post_parent = self.soup.find(self.parent[0], id=self.parent[1])
        content = post_parent.find(self.child[0], id=self.child[1]) if post_parent else None
        content = content or post_parent
        return {
            'title'        : text('h1'),
            'sub_title'    : text('h2'),
            'meta'         : text('small'),
            'banner_path'  : self.get_post_banner(),
            'post_content' : self.get_markdown_source(),
            'post_html'    : content.decode_contents().strip() if content else '',
        }

    def update_post_headings(self, title, sub_title=None, meta=None):
        self.edit_page_contents(title, 'h1', 'editable')
        if sub_title is not None:
            self.edit_page_contents(sub_title, 'h2', 'editable')
        if meta is not None:
            self.edit_page_contents(meta, 'small', 'editable')
        self.set_page_title(title)

    def check_index (self, title, sub_title):
        """
        To avoid duplicating index entries new index updates need to pass this check
        Compares both the titles in the home page and the post file names
        """
        file_name = self.post_file_name(title)
        for entry in self.index_entries():
            if entry['title'].strip().casefold() == title.strip().casefold() or entry['href'] == file_name:
                return False
        return True

    def index_entries(self):
        """
        Lists the post previews on the home page
        """
        entries = []
        container = self.soup.find('div', id='children-post-preview')
        if not container:
            return entries
        for div in container.find_all('div', id=re.compile('^post-preview-'), recursive=False):
            link = div.find('a', href=True)
            def text(tag):
                found = div.find(tag)
                return found.get_text().strip() if found else ''
            entries.append({
                'div'       : div,
                'href'      : link['href'] if link else '',
                'title'     : text('h2'),
                'sub_title' : text('h3'),
                'meta'      : text('small'),
                'hidden'    : HIDDEN_STYLE in div.get('style', '').replace(' ', ''),
            })
        return entries

    def update_index_entry(self, href, title=None, sub_title=None, meta=None, hidden=None):
        """
        Updates the home page preview of a post - fields left as None are not changed
        """
        for entry in self.index_entries():
            if entry['href'] != href:
                continue
            div = entry['div']
            for tag, value in (('h2', title), ('h3', sub_title), ('small', meta)):
                found = div.find(tag)
                if found and value is not None:
                    found.string = value
            if hidden is not None:
                if hidden:
                    div['style'] = HIDDEN_STYLE
                elif div.has_attr('style'):
                    del div['style']
            return True
        return False

    def set_markdown_block(self, element, markdown):
        """
        Replaces an editable element with the html rendered from markdown
        The markdown is kept in data-markdown so it can be edited again later
        """
        block = self.soup.new_tag('div', attrs={**element.attrs, 'data-markdown': markdown})
        parsed_body = self.parse_new_html(markdown, True).find('body')
        for node in list(parsed_body.children):
            block.append(node)
        for i in block.find_all('img'):
            i['class'] = "img-responsive"
        element.replace_with(block)
        return block

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


    def duplicate_post(self, title, sub_title, name, date_, meta=None):
        post_preview = self.soup.find('div', id='post-preview-latest')
        if post_preview == None:
            return Exception('Failed to find base div')
        post_preview['id'] = 'post-preview-'+''.join(post_preview.find('h2').get_text().split())

        parent_post_preview = post_preview.parent
        new_child_post_preview = self.soup.new_tag('div', id='post-preview-latest')

        new_child_post_href = self.soup.new_tag('a', href=self.post_file_name(title))
        new_child_post_title = self.soup.new_tag('h2', type='editable', string=title)
        new_child_post_subtitle = self.soup.new_tag('h3', type='editable', string=sub_title)
        new_child_post_small = self.soup.new_tag('small', type='editable', attrs={'class': 'post-meta'}, string=meta or f'Publicado por {name} a {date_}')
        new_child_post_hr = self.soup.new_tag('hr', type='editable')

        new_child_post_href.append(new_child_post_title)
        new_child_post_href.append(new_child_post_subtitle)
        new_child_post_href.append(new_child_post_small)
        new_child_post_href.append(new_child_post_hr)

        new_child_post_preview.append(new_child_post_href)
        parent_post_preview.insert(0, new_child_post_preview)


class Site:
    """
    Keeps the home page, the post template and the published posts consistent
    """
    POST_PARENT = ['div', 'parent-post-preview']
    POST_CHILD = ['div', 'child']
    # Pieces of the template that must exist so posts can be built from it
    TEMPLATE_REQUIREMENTS = (
        ('header', {'class_': 'intro-header'}, 'banner header <header class="intro-header">'),
        ('h1', {'type': 'editable'}, 'title <h1 type="editable">'),
        ('h2', {'type': 'editable'}, 'subtitle <h2 type="editable">'),
        ('small', {'type': 'editable'}, 'meta <small type="editable">'),
        ('div', {'id': 'parent-post-preview'}, 'content <div id="parent-post-preview">'),
    )

    def post_parser(self, file_name):
        parser = Parser(file_name, 'Title', self.POST_PARENT, self.POST_CHILD)
        parser.path = parser.template
        parser.load_html()
        return parser

    def index_parser(self):
        parser = Parser(INDEX_PAGE, 'Title', self.POST_PARENT, self.POST_CHILD)
        parser.load_html()
        return parser

    @staticmethod
    def post_files():
        return sorted(p.name for p in PATH.glob('post_*.html'))

    def list_posts(self):
        """
        Every published post: the ones on the home page (in order) followed by
        post files that are not linked from the home page
        """
        posts = []
        for entry in self.index_parser().index_entries():
            exists = pathlib.Path(PATH, entry['href']).is_file()
            posts.append({**{k: v for k, v in entry.items() if k != 'div'}, 'file': entry['href'] if exists else None, 'on_home': True})
        linked = {p['href'] for p in posts}
        for file_name in self.post_files():
            if file_name not in linked:
                fields = self.post_parser(file_name).get_post_fields()
                posts.append({'href': file_name, 'file': file_name, 'title': fields['title'], 'sub_title': fields['sub_title'],
                              'meta': fields['meta'], 'hidden': False, 'on_home': False})
        return posts

    def title_in_use(self, title, ignore_file=None):
        """
        True if another post already uses this title (or its file name)
        """
        file_name = Parser.post_file_name(title)
        for post in self.list_posts():
            if post['href'] == ignore_file:
                continue
            if post['href'] == file_name or post['title'].strip().casefold() == title.strip().casefold():
                return True
        return False

    def save_post(self, file_name, fields, home=None):
        """
        Saves an existing post and copies its title to the home page
        home: optional dict with the home page 'sub_title', 'meta' and 'hidden'
        (the home page subtitle / info are a summary, different from the post's own)
        The file name is kept so existing links to the post keep working
        """
        parser = self.post_parser(file_name)
        if not parser.build_post(fields):
            return False
        parser.overwrite_html_file()
        index = self.index_parser()
        if index.update_index_entry(file_name, fields['title'], **(home or {})):
            index.overwrite_html_file()
        return True

    def sync_index_titles_to_posts(self, previous_titles):
        """
        After the home page is edited, copies the titles that changed into the posts themselves
        previous_titles maps each post file to its home page title before the edit
        Returns the posts that changed
        """
        changed = []
        for entry in self.index_parser().index_entries():
            if entry['title'] == previous_titles.get(entry['href'], entry['title']):
                continue
            if not pathlib.Path(PATH, entry['href']).is_file():
                continue
            parser = self.post_parser(entry['href'])
            parser.update_post_headings(entry['title'])
            parser.overwrite_html_file()
            changed.append(entry['href'])
        return changed

    def validate_template(self, soup):
        return [label for tag, attrs, label in self.TEMPLATE_REQUIREMENTS if not soup.find(tag, **attrs)]

    def apply_template_to_posts(self):
        """
        Rebuilds every post from post.html, keeping each post's own
        title, subtitle, meta, banner, content and markdown source
        """
        updated = []
        for file_name in self.post_files():
            old = self.post_parser(file_name)
            fields = old.get_post_fields()
            old_content = old.soup.find(self.POST_PARENT[0], id=self.POST_PARENT[1])
            markdown = old.get_markdown_source()

            new = Parser(POST_TEMPLATE, 'Title', self.POST_PARENT, self.POST_CHILD)
            new.path = pathlib.Path(PATH, file_name)
            new.load_html()
            new.update_post_headings(fields['title'], fields['sub_title'], fields['meta'])
            new.update_new_post_banner(fields['banner_path'] or BANNER_TEMPLATE)
            new.set_markdown_source(markdown)
            new_parent = new.soup.find(self.POST_PARENT[0], id=self.POST_PARENT[1])
            if old_content is None or new_parent is None:
                continue
            new_parent.clear()
            for node in list(old_content.children):
                new_parent.append(node)
            new.overwrite_html_file(True)
            updated.append(file_name)
        return updated

    @staticmethod
    def file_data_uri(path):
        file_path = pathlib.Path(PATH, path)
        if not file_path.is_file() or PATH not in file_path.resolve().parents:
            return None
        mime = mimetypes.guess_type(file_path.name)[0] or 'application/octet-stream'
        return f"data:{mime};base64,{base64.b64encode(file_path.read_bytes()).decode()}"

    def preview_html(self, soup, extra_files=None):
        """
        Returns a self contained copy of a page (css and images inlined) that can be
        shown inside the app. extra_files maps paths to data uris for files not saved yet
        """
        soup = copy(soup)
        extra_files = extra_files or {}

        def inline(path):
            if path in extra_files:
                return extra_files[path]
            if re.match(r'^(https?:|data:|//)', path):
                return path
            return self.file_data_uri(path) or path

        for link in soup.find_all('link', rel='stylesheet', href=True):
            css_path = pathlib.Path(PATH, link['href'])
            if css_path.is_file() and PATH in css_path.resolve().parents:
                style = soup.new_tag('style')
                style.string = css_path.read_text(encoding='utf-8')
                link.replace_with(style)
        for img in soup.find_all('img', src=True):
            img['src'] = inline(img['src'])
        for tag in soup.find_all(style=re.compile('url')):
            tag['style'] = re.sub(r"url\(['\"]?([^'\")]+)['\"]?\)", lambda m: f"url('{inline(m.group(1))}')", tag['style'])
        # Scripts and links to other pages don't work inside the preview
        for script in soup.find_all('script'):
            script.decompose()
        for a in soup.find_all('a', href=True):
            if re.match(r'^(https?:|mailto:)', a['href']):
                a['target'] = '_blank'
            else:
                a['href'] = '#'
        return str(soup)
