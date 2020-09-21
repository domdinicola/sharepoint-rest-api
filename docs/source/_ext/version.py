import re
from sphinx import addnodes, roles
# from sphinx.util.console import bold
from sphinx.util.compat import Directive

# RE for option descriptions without a '--' prefix
simple_option_desc_re = re.compile(
    r'([-_a-zA-Z0-9]+)(\s*.*?)(?=,\s+(?:/|-|--)|$)')


def setup(app):
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )
    app.add_crossref_type(
        directivename="templatetag",
        rolename="ttag",
        indextemplate="pair: %s; template tag"
    )
    app.add_crossref_type(
        directivename="templatefilter",
        rolename="tfilter",
        indextemplate="pair: %s; template filter"
    )
    app.add_crossref_type(
        directivename="fieldlookup",
        rolename="lookup",
        indextemplate="pair: %s; field lookup type",
    )
    app.add_config_value('next_version', '0.0', True)
    app.add_directive('versionadded', VersionDirective)
    app.add_directive('versionchanged', VersionDirective)
    app.add_crossref_type(
        directivename="release",
        rolename="release",
        indextemplate="pair: %s; release",
    )


class VersionDirective(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        arg0 = self.arguments[0]
        is_nextversion = env.config.next_version == arg0
        ret = []
        node = addnodes.versionmodified()
        ret.append(node)
        if is_nextversion:
            # node['version'] = "Development version"
            arg0 = "Development version"

        else:
            if len(self.arguments) == 1:
                linktext = 'Please, see the Changelog <changes>'
                xrefs = roles.XRefRole()('doc', linktext, linktext, self.lineno, self.state)
                node.extend(xrefs[0])
        node['version'] = arg0
        node['type'] = self.name
        if len(self.arguments) == 2:
            inodes, messages = self.state.inline_text(self.arguments[1], self.lineno + 1)
            node.extend(inodes)
            if self.content:
                self.state.nested_parse(self.content, self.content_offset, node)
            ret = ret + messages
        env.note_versionchange(node['type'], node['version'], node, self.lineno)
        return ret
