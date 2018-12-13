# -*- coding: utf-8 -*-
# !/usr/bin/python
import ast
import logging
import os
import re
import shutil
import subprocess
from os.path import join as oj
from shutil import copytree

from jinja2 import FileSystemLoader, Environment

_logger = logging.getLogger(__name__)


class RepoMigrator(object):

    def __init__(self, name, src_path, dst_path, company, contributor):
        self._name = name
        self.src_path = src_path
        self.dst_path = dst_path
        self._company = company
        self._contributor = contributor
        template_loader = FileSystemLoader(searchpath=oj(os.path.dirname(__file__), 'templates'))
        self._template_env = Environment(loader=template_loader)
        self._migrated_modules = False

    def migrate(self):
        if not os.path.isdir(self.src_path):
            return

        _logger.info('Starting migration of repository %s', self._name)
        self._migrated_modules = self._migrate_modules()
        bug_path = oj(self.dst_path, '.gitlab', 'issue_templates')
        bug_file_path = oj(bug_path, 'Bug.md')
        os.makedirs(bug_path, exist_ok=True)
        shutil.copy(oj(os.path.dirname(__file__), 'templates', 'Bug.md'), bug_file_path)

        # Generate README.md based on modules
        template_file = 'README.md'
        template = self._template_env.get_template(template_file)
        name = self._name
        description = ''
        content = template.render(
                project_title=name,
                project_intro=description,
                modules=self._migrated_modules
        )
        out = open(oj(self.dst_path, 'README.md'), 'w')
        out.write(content)
        out.close()

        # copy requirements.txt if exists
        self._has_requirements = False
        if os.path.exists(oj(self.src_path, 'requirements.txt')):
            shutil.copy(oj(self.src_path, 'requirements.txt'), oj(self.dst_path, 'requirements.txt'))
            self._has_requirements = True

        return self._migrated_modules

    def generate_gitlab_ci(self):
        template_file = 'gitlab-ci.yml'
        template = self._template_env.get_template(template_file)

        content = template.render(
            modules=self._migrated_modules,
            repository=self._name,
            pip=self._has_requirements)
        out = open(oj(self.dst_path, '.gitlab-ci.yml'), 'w')
        out.write(content)
        out.close()

    def _migrate_modules(self):
        migrated_modules = {}
        for file_name in os.listdir(self.src_path):
            if file_name[:1] == '.':
                continue
            src_path = os.path.join(os.path.abspath(self.src_path), file_name)
            if os.path.isdir(src_path) and file_name not in ['setup', 'docs', 'doc', 'client_tools']:
                dst_path = os.path.join(os.path.abspath(self.dst_path), file_name)
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)
                module = ModuleMigrator(src_path, dst_path, '1.0', self._company, self._contributor).migrate()
                migrated_modules = {**migrated_modules, **module}
        return migrated_modules

    def cleanup(self):
        shutil.rmtree(self.src_path)
        shutil.rmtree(self.dst_path)


class ModuleMigrator(object):
    _readme_intro = u''

    _replacements = {
        'odoo': 'flectra',
        'Odoo': 'Flectra',
        'ODOO': 'FLECTRA',
        '8069': '7073',
        'Part of Flectra.': 'Part of Odoo, Flectra.',
        'openerp': 'flectra',
        'Openerp': 'Flectra',
        'OpenERP': 'Flectra',
        'OpenErp': 'Flectra',
        'OPENERP': 'FLECTRA',
        'Part of Flectra.': 'Part of Openerp, Flectra.',
        'Part of Flectra.': 'Part of OpenERP, Flectra.',
    }

    _xml_replacements = {
        'odoo': 'flectra',
        'Odoo': 'Flectra',
        'ODOO': 'FLECTRA',
        'Part of Odoo.': 'Part of Odoo, Flectra.',
        'openerp': 'flectra',
        'Openerp': 'Flectra',
        'OpenERP': 'Flectra',
        'OpenErp': 'Flectra',
        'OPENERP': 'FLECTRA',
        'Part of Flectra.': 'Part of Openerp, Flectra.',
        'Part of Flectra.': 'Part of OpenERP, Flectra.',
    }

    _init_replacements = {
        'Odoo.': 'Odoo, Flectra.',
        'odoo': 'flectra',
        'openerp': 'flectra',
        'Openerp': 'Flectra',
        'OpenERP': 'Flectra',
        'OpenErp': 'Flectra',
    }

    _manifest_replacements = {
        'Odoo.': 'Odoo, Flectra.',
        'odoo': 'flectra',
        'openerp': 'flectra',
        'Openerp': 'Flectra',
        'OpenERP': 'Flectra',
        'OpenErp': 'Flectra',
    }

    _readme_regex_patterns = [
        '(.. image:: https://odoo-community.org.*?)^(Bug)',
        '(Bug Tracker.*)^(Credits)',
        '(Maintainer.*)',
        '(.. \|badge.*\|)',
    ]

    _obsolete_line_patterns = [
        '-*- coding: utf-8 -*-',
    ]
    _copyright_line_patterns = [
        'copyright',
        'Copyright',
        '©',
    ]

    _ingnore_dir = [
        'cla',
        'doc',
    ]

    _delete_dir = [
        'readme',
    ]

    _ingnore_files = [
        'LICENSE',
        'COPYRIGHT',
        'README.md',
        'CONTRIBUTING.md',
        'Makefile',
        'MANIFEST.in'
    ]

    _ingnore_py_words = [
        'OpenERPSession'
    ]

    _ignore_xml_words = [
        'provider_openerp'
    ]

    _website_replacements = {
        'https://www.odoo.com': 'https://flectrahq.com',
        'www.odoo.com': 'https://flectrahq.com',
        'https://www.openerp.com': 'https://flectrahq.com',
        'www.opernerp.com': 'https://flectrahq.com',
    }

    _replace_email = {
        'info@odoo.com': 'info@flectrahq.com',
        'info@openerp.com': 'info@flectrahq.com',
    }
    _copyright_list = []

    def __init__(self, src, destination, flectra_release, company, contributor):
        self._src = src
        self._destination = destination
        self._module_name = os.path.basename(destination)
        self._repo_name = os.path.basename(os.path.dirname(self._destination))
        self._release = flectra_release.split('.')[:2]
        self._company = company
        self._contributor = contributor
        self._copyright_list = []
        self._manifest = False

        self._contributor_part = u'''Contributors
        ------------

        * %s''' % self._contributor

    def migrate(self):
        _logger.info('Starting migration of module %s', self._module_name)
        copytree(self._src, self._destination, symlinks=True, ignore_dangling_symlinks=True)
        subprocess.call(['2to3', '-w', self._destination])
        for base, odoo_dirs, odoo_files in os.walk(self._destination, topdown=True):
            odoo_files = [f for f in odoo_files if not f[0] == '.']
            odoo_dirs[:] = [d for d in odoo_dirs if not d[0] == '.']
            self._rename_files(base, odoo_files)
            self._rename_dir(base, odoo_dirs)
        self._render_templates()
        return {self._module_name: self._manifest}

    def _render_templates(self):
        # COPYRIGHT file
        cr_file = oj(self._destination, 'COPYRIGHT')
        if os.path.exists(cr_file):
            os.remove(cr_file)
        shutil.copy(oj(os.path.dirname(__file__), 'templates', 'COPYRIGHT'), self._destination)
        for cr in self._copyright_list:
            if not re.match('(copyright[ ]*[0-9-]+)', cr, re.IGNORECASE):
                self._copyright_list.remove(cr)
        copyright_list = list(set(self._copyright_list))
        copyright_list = sorted(copyright_list)
        existing_copyright = '\n  '.join(copyright_list)
        infile = self._open_read(self._destination, 'COPYRIGHT')
        out = self._open_write(self._destination, 'COPYRIGHT')
        infile = infile.replace('{% existing %}', existing_copyright)
        out.write(infile)
        out.close()

        # LICENSE file
        license_exists = False
        if os.path.exists(oj(self._destination, 'LICENSE')):
            if os.path.isdir(oj(self._destination, 'LICENSE')):
                shutil.rmtree(oj(self._destination, 'LICENSE'))
            else:
                os.remove(oj(self._destination, 'LICENSE'))

        shutil.copy(oj(os.path.dirname(__file__), 'templates', 'LICENSE'), self._destination)

        # Module icon
        desc_path = oj(self._destination, 'static', 'description')
        os.makedirs(desc_path, exist_ok=True)
        if not os.path.exists(oj(desc_path, 'icon.png')) and \
                not os.path.exists(oj(desc_path, 'icon.jpg')):
            shutil.copy(oj(os.path.dirname(__file__), 'templates', 'icon.jpg'), desc_path)

    def _rename_files(self, base, items):
        for name in items:
            if name in self._ingnore_files:
                continue

            if name == '__openerp__.py':
                os.rename(oj(base, name), oj(base, '__manifest__.py'))
                name = '__manifest__.py'
            if name == '__init__.py':
                self._init_files(base)
                self._remove_obsolete_lines(base, name)
            elif name == '__manifest__.py':
                self._manifest_files(base)
                self._remove_obsolete_lines(base, name)
            elif name.lower() == 'readme.rst':
                self._readme_files(base, name)
            else:
                sp_name = name.split('.')
                if len(sp_name) >= 2:
                    if sp_name[-1] in ['xml', 'csv', 'json', 'html']:
                        self._remove_obsolete_lines(base, name)
                        self._xml_csv_json_files(base, name)
                    elif sp_name[-1] in ['py', 'css', 'less', 'js', 'yml']:
                        self._python_files(base, name)
                        self._remove_obsolete_lines(base, name)
            try:
                for old, new in self._replacements.items():
                    if name != (name.replace(old, new)):
                        os.rename(oj(base, name), oj(base, name.replace(old, new)))
            except OSError:
                pass

    def _rename_dir(self, base, items):
        for folder in items:
            if folder in self._delete_dir:
                shutil.rmtree(oj(base, folder))
                continue
            if folder in self._ingnore_dir:
                continue
            for new_base, odoo_dirs, odoo_files in os.walk(oj(base, folder), topdown=True):
                if odoo_files:
                    self._rename_files(new_base, odoo_files)
                if odoo_dirs:
                    self._rename_dir(new_base, odoo_dirs)
            if 'odoo' in folder:
                os.rename(oj(base, folder), oj(base, folder.replace('odoo', 'flectra')))

    def _init_files(self, base):
        infile = self._open_read(base, '__init__.py')
        out = self._open_write(base, '__init__.py')
        for old, new in self._init_replacements.items():
            infile = infile.replace(old, new)
        out.write(infile)
        out.close()

    def _manifest_files(self, base):
        temp = {**self._replace_email, **self._website_replacements}
        infile = self._open_read(base, '__manifest__.py')
        out = self._open_write(base, '__manifest__.py')
        for old, new in temp.items():
            infile = infile.replace(old, new)
        out.write(infile)
        out.close()
        self._content_replacements(base, '__manifest__.py', self._manifest_replacements)
        infile = self._open_read(base, '__manifest__.py')
        out = self._open_write(base, '__manifest__.py')
        manifest = ast.literal_eval(infile)
        manifest['author'] += ', %s' % self._company
        version_parts = manifest['version'].split('.')
        if len(version_parts) <= 3:
            version_parts = ['0', '0'] + version_parts
        if len(version_parts) < 5:
            version_parts += ['0'] * (5 - len(version_parts))
        version_parts[0] = self._release[0]
        version_parts[1] = self._release[1]

        manifest['version'] = '.'.join(version_parts)
        manifest['website'] = 'https://gitlab.com/flectra-community/%s' % self._repo_name
        self._manifest = manifest
        m = re.search('''["']version["']:[ '"]*([0-9a-zA-Z.]+)["']''', infile)
        if m and m.group(1):
            infile = infile.replace(m.group(1), manifest['version'])
        m = re.search('''["']website["']:[ '"]*(.*?)["']''', infile)
        if m and m.group(1):
            infile = infile.replace(m.group(1), manifest['website'])
        m = re.search('''["']author["']:[\n '"]*(.*?)["']''', infile, re.MULTILINE | re.DOTALL)
        if m and m.group(1):
            infile = infile.replace(m.group(1), m.group(1) + ', %s' % self._company)
        out.write(infile)
        out.close()

    def _xml_csv_json_files(self, base, name):
        infile = self._open_read(base, name)
        out = self._open_write(base, name)
        for old, new in self._replace_email.items():
            infile = infile.replace(old, new)
        for old, new in self._xml_replacements.items():
            must_replace = True
            for ignore_word in self._ignore_xml_words:
                if ignore_word in old:
                    must_replace = False
                    break
            if must_replace:
                infile = infile.replace(old, new)
        out.write(infile)
        out.close()

    def _python_files(self, base, name):
        infile = self._open_read(base, name)
        out = self._open_write(base, name)
        for old, new in self._replace_email.items():
            infile = infile.replace(old, new)
        out.write(infile)
        out.close()
        self._content_replacements(base, name, self._replacements)

    def _content_replacements(self, base, name, replace_dict):
        infile = self._open_read_lines(base, name)
        lines = []
        if infile:
            for line in infile:
                words = line.split(' ')
                line_parts = []
                for word in words:
                    if word.startswith('info@') or word.startswith("'info@") or word.startswith('"info@'):
                        line_parts.append(word)
                        continue
                    for old, new in replace_dict.items():
                        must_replace = True
                        for ignore_word in self._ingnore_py_words:
                            if ignore_word in word:
                                must_replace = False
                        if must_replace:
                            word = word.replace(old, new)
                    line_parts.append(word)
                lines.append(line_parts)

        with open(oj(self._destination, 'temp'), 'a') as temp_file:
            for line in lines:
                for word in line:
                    word = word if word.endswith('\n') else word + ' ' if word else ' '
                    temp_file.write(word)
            os.rename(oj(self._destination, 'temp'), oj(base, name))

    def _open_read_lines(self, base, name):
        return open(oj(base, name), 'r').readlines()

    def _open_write(self, base, filename):
        return open(oj(base, filename), 'w')

    def _open_read(self, base, filename):
        return open(oj(base, filename), 'r').read()

    def _remove_obsolete_lines(self, base, name):
        infile = self._open_read_lines(base, name)
        lines = []
        if not infile:
            return

        temp = self._obsolete_line_patterns + self._copyright_line_patterns
        for line in infile:
            remove_line = False
            for pattern in temp:
                if pattern in line:
                    if pattern in self._copyright_line_patterns:
                        cr_line = line.replace('#', '').strip()
                        self._copyright_list.append(cr_line)
                    else:
                        remove_line = True
            if not remove_line:
                lines.append(line)

        with open(oj(self._destination, 'temp'), 'a') as temp_file:
            for line in lines:
                temp_file.write(line)
            os.rename(oj(self._destination, 'temp'), oj(base, name))

    def _readme_files(self, base, name):
        infile = self._open_read(base, name)
        out = self._open_write(base, name)
        infile = self._readme_intro + infile

        for pattern in self._readme_regex_patterns:
            infile = self._regex_replace(infile, pattern)
        infile = self._regex_replace(infile,
                                     '(Contributors\n[-|~]*[\n|\n\n])',
                                     self._contributor_part)
        infile = infile.rstrip('\n')
        out.write(infile)
        out.close()

    def _regex_replace(self, source, pattern, replace=''):
        m = re.search(pattern, source, re.MULTILINE | re.DOTALL)
        if not m or not m.group(1):
            return source
        return source.replace(m.group(1), replace)
