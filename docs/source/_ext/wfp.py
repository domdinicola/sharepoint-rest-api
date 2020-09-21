import re
from docutils.parsers.rst.roles import register_local_role
from sphinx import addnodes
import docutils.nodes
from sphinx.util.compat import Directive
import wfp


def setup(app):
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )
    app.add_crossref_type(
        directivename="permission",
        rolename="permission",
        indextemplate="pair: %s; permission",
    )
    app.add_description_unit('bug', 'bug', 'pair: %s; Defect')
    app.add_node(wfp.permission)
    app.add_directive('permrequire', PermRequireDirective)


RELEASE_INFO = '<p><span class="%(class)s">Permission required : %(perm)s</span></p>'


def _parse_ref(rawtext, text, link, inliner):
    uri, name = resolve_name(link, inliner, postpone=True)
    if uri:
        return docutils.nodes.reference(text, text, refuri=uri)
    else:
        # postpone resolution to generate warnings about failing links
        ref = docutils.nodes.reference(text, text, name=link, refname=':ref:`%s`' % link)
        return ref


def ref_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    link = text

    m = re.compile(r'^(.*)\n*<(.*?)>\s*$', re.S).match(text)
    if m:
        text, link = m.group(1).strip(), m.group(2).strip()
    elif text.startswith('~'):
        link = text[1:]
        text = text[1:].split('.')[-1]
    else:
        m = re.compile(r'^([a-zA-Z0-9._-]*)(.*?)$', re.S).match(text)
        link = m.group(1)

    ref = _parse_ref(rawtext, text, link, inliner)
    return [ref], []


register_local_role('permission', ref_role)


def resolve_name(link, inliner, postpone=False):
    _resolve = inliner.document.settings.resolve_name

    if hasattr(inliner, '_current_module'):
        try:
            new_link = inliner._current_module + '.' + link
            uri, name = _resolve(new_link)
            return uri, name
        except ValueError:
            pass

    if postpone:
        return None, link

    uri, name = _resolve(link)
    return uri, name


class permission(docutils.nodes.BackLinkable, docutils.nodes.Admonition, docutils.nodes.TextElement):
    """Custom "see also" admonition."""
    child_text_separator = '11111111111111111'


class PermRequireDirective(Directive):
    """Directive for embedding "latest release" info in the form of a list of
    release file links.
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        node = addnodes.seealso

        perms = []
        if self.arguments:
            perms = [' :permission:`%s`' % p.strip() for p in self.arguments[0].split(',')]

        node = docutils.nodes.emphasis('permission')
        node['classes'] = ['permission']
        textnodes, messages = self.state.paragraph(['Permissions: %s' % ', '.join(perms)], self.lineno)
        node += docutils.nodes.paragraph('', '', *textnodes)

        return [node]
