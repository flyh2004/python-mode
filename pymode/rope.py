""" Rope support in pymode. """

from __future__ import absolute_import, print_function

import vim # noqa
import site
import os.path
import sys
import re
import json
from .utils import (
    message, PY2, error, pymode_input, pymode_inputlist, pymode_y_n)

if PY2:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))
else:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs3'))

from rope.base import project, libutils, exceptions, change # noqa
from rope.base.fscommands import FileSystemCommands # noqa
from rope.contrib import autoimport, codeassist, findit # noqa
from rope.refactor import ModuleToPackage, ImportOrganizer, rename, extract, inline, usefunction # noqa
from rope.base.taskhandle import TaskHandle # noqa


def get_assist_params(cursor=None, base=''):
    """ Prepare source and get offset.

    :return source, offset:

    """
    if cursor is None:
        cursor = vim.current.window.cursor

    row, column = cursor
    source = ""
    offset = 0

    for i, line in enumerate(vim.current.buffer, 1):
        if i == row:
            source += line[:column] + base
            offset = len(source)
            source += line[column:]
        else:
            source += line
        source += '\n'
    return source, offset


def look_ropeproject(path):
    """ Search for ropeproject in current and parent dirs.

    :return str|None: A finded path

    """
    p = os.path.abspath(path)

    while True:
        if '.ropeproject' in os.listdir(p):
            return p

        new_p = os.path.abspath(os.path.join(p, ".."))
        if new_p == p:
            return '.'

        p = new_p


def completions():
    """ Search completions. """

    row, column = vim.current.window.cursor
    if vim.eval('a:findstart') == '1':
        count = 0
        for char in reversed(vim.current.line[:column]):
            if not re.match(r'[\w\d]', char):
                break
            count += 1
        vim.command('return %i' % (column - count))
        return

    base = vim.eval('a:base')
    source, offset = get_assist_params((row, column), base)
    proposals = get_proporsals(source, offset, base)
    vim.command("return %s" % json.dumps(proposals))


def complete():
    """ Ctrl+Space completion.

    :return bool: success

    """
    row, column = vim.current.window.cursor
    source, offset = get_assist_params((row, column))
    proposals = get_proporsals(source, offset)
    if not proposals:
        return False

    prefix = proposals[0]['word']

    # Find common part
    for p in proposals:
        common = len([
            c1 for c1, c2 in zip(prefix, p['word']) if c1 == c2 and c1 != ' '
        ])
        prefix = prefix[:common]
    s_offset = codeassist.starting_offset(source, offset)
    p_prefix = prefix[offset - s_offset:]
    line = vim.current.buffer[row - 1]
    vim.current.buffer[row - 1] = line[:column] + p_prefix + line[column:] # noqa
    vim.current.window.cursor = (row, column + len(p_prefix))
    vim.command('call complete(%s, %s)' % (
        column - len(prefix) + len(p_prefix) + 1, json.dumps(proposals)))

    return True


def get_proporsals(source, offset, base=''):
    """ Code assist.

    :return str:

    """

    with RopeContext() as ctx:

        try:
            proposals = codeassist.code_assist(
                ctx.project, source, offset, ctx.resource, maxfixes=3,
                later_locals=False)

        except exceptions.ModuleSyntaxError:
            proposals = []

        proposals = sorted(proposals, key=_sort_proporsals)

        out = []
        preview = 'preview' in ctx.completeopt
        for p in proposals:
            out.append(dict(
                word=p.name,
                menu=p.type,
                kind=p.scope + ':',
                info=p.get_doc() or "No docs." if preview else "",
            ))

    return out


def goto():
    """ Goto definition. """

    with RopeContext() as ctx:
        source, offset = get_assist_params()
        found_resource = None

        try:
            found_resource, line = codeassist.get_definition_location(
                ctx.project, source, offset, ctx.resource, maxfixes=3)

        except exceptions.BadIdentifierError as e:
            pass

        except Exception as e:
            print(e)

        if not found_resource:
            return

        if not os.path.abspath(found_resource.path) == vim.current.buffer.name:
            vim.command("%s +%s %s" % (
                ctx.options.get('goto_definition_cmd'),
                line, found_resource.path))

        else:
            vim.current.window.cursor = (
                line, int(vim.eval('indent(%s)' % line)))


def show_doc():
    """ Show documentation. """

    with RopeContext() as ctx:
        source, offset = get_assist_params()
        try:
            doc = codeassist.get_doc(
                ctx.project, source, offset, ctx.resource, maxfixes=3)
            if not doc:
                raise exceptions.BadIdentifierError
            vim.command('let l:output = %s' % json.dumps(doc.split('\n')))
        except exceptions.BadIdentifierError:
            error("No documentation found.")


def find_it():
    """ Find occurrences. """

    with RopeContext() as ctx:
        _, offset = get_assist_params()
        try:
            occurrences = findit.find_occurrences(
                ctx.project, ctx.resource, offset)
        except exceptions.BadIdentifierError:
            occurrences = []

    lst = []
    for oc in occurrences:
        lst.append(dict(
            filename=oc.resource.path,
            lnum=oc.lineno,
        ))
    vim.command('let l:output = %s' % json.dumps(lst))


def update_python_path(paths):
    """ Update sys.path and make sure the new items come first. """

    old_sys_path_items = list(sys.path)

    for path in paths:
        # see if it is a site dir
        if path.find('site-packages') != -1:
            site.addsitedir(path)

        else:
            sys.path.insert(0, path)

    # Reorder sys.path so new directories at the front.
    new_sys_path_items = set(sys.path) - set(old_sys_path_items)
    sys.path = list(new_sys_path_items) + old_sys_path_items


def organize_imports():
    """ Organize imports in current file. """

    with RopeContext() as ctx:
        organizer = ImportOrganizer(ctx.project)
        changes = organizer.organize_imports(ctx.resource)
        if changes is not None:
            progress = ProgressHandler('Organize imports')
            ctx.project.do(changes, task_handle=progress.handle)
            reload_changes(changes)


def regenerate():
    """ Clear cache. """
    with RopeContext() as ctx:
        ctx.project.pycore._invalidate_resource_cache(ctx.resource) # noqa
        ctx.importer.generate_cache(resources=[ctx.resource])
        ctx.project.sync()


def new():
    """ Create a new project. """
    root = vim.eval('input("Enter project root: ", getcwd())')
    prj = project.Project(projectroot=root)
    prj.close()
    message("Project is opened: %s" % root)


def undo():
    """ Undo last changes.

    :return bool:

    """

    with RopeContext() as ctx:
        changes = ctx.project.history.tobe_undone
        if changes is None:
            error('Nothing to undo!')
            return False

        if pymode_y_n(yes=False, msg='Undo [%s]?' % str(changes)):
            progress = ProgressHandler('Undo %s' % str(changes))
            for c in ctx.project.history.undo(task_handle=progress.handle):
                reload_changes(c)


def redo():
    """ Redo last changes.

    :return bool:

    """

    with RopeContext() as ctx:
        changes = ctx.project.history.tobe_redone
        if changes is None:
            error('Nothing to redo!')
            return False

        if pymode_y_n(yes=False, msg='Redo [%s]?' % str(changes)):
            progress = ProgressHandler('Redo %s' % str(changes))
            for c in ctx.project.history.redo(task_handle=progress.handle):
                reload_changes(c)


def cache_project(cls):
    """ Cache projects.

    :return func:

    """
    projects = dict()

    def get_ctx(*args, **kwargs):
        path = vim.current.buffer.name
        project_path = look_ropeproject(os.path.dirname(path))
        ctx = projects.get(project_path)
        if not ctx:
            projects[project_path] = ctx = cls(path, project_path)
        return ctx
    return get_ctx


@cache_project
class RopeContext(object):

    """ A context manager to have a rope project context. """

    projects = dict()

    def __init__(self, path, project_path):

        self.path = path
        self.project = project.Project(
            project_path, fscommands=FileSystemCommands())

        self.importer = autoimport.AutoImport(project=self.project,
                                              observe=False)

        update_python_path(self.project.prefs.get('python_path', []))

        self.resource = None
        self.completeopt = vim.eval('&completeopt')
        self.options = dict(
            goto_definition_cmd=vim.eval('g:pymode_rope_goto_definition_cmd')
        )
        self.encoding = vim.eval('&encoding')

        if os.path.exists("%s/__init__.py" % project_path):
            sys.path.append(project_path)

    def __enter__(self):
        self.project.validate(self.project.root)
        self.resource = libutils.path_to_resource(
            self.project, vim.current.buffer.name, 'file')
        return self

    def __exit__(self, t, value, traceback):
        if t is None:
            self.project.close()

    def generate_modules_cache(self, modules):
        """ Generate modules cache. """
        message("Generate Modules cache ...")
        self.importer.generate_modules_cache(modules)
        self.project.sync()


class ProgressHandler(object):

    """ Handle task progress. """

    def __init__(self, msg):
        self.handle = TaskHandle(name="refactoring_handle")
        self.handle.add_observer(self)
        self.message = msg

    def __call__(self):
        """ Show current progress. """
        percent_done = self.handle.current_jobset().get_percent_done()
        message('%s - done %s%%' % (self.message, percent_done))


_scope_weight = {
    'local': 10, 'attribute': 20, 'global': 30, 'imported': 40, 'builtin': 50}


def _sort_proporsals(p):
    return (
        _scope_weight.get(p.scope, 100), int(p.name.startswith('_')), p.name)


class Refactoring(object): # noqa

    """ Base class for refactor operations. """

    def run(self):
        """ Run refactoring.

        :return bool:

        """

        with RopeContext() as ctx:
            try:
                refactor = self.get_refactor(ctx)
                input_str = self.get_input_str(refactor, ctx)
                if not input_str:
                    return False

                changes = self.get_changes(refactor, input_str)

                action = pymode_inputlist(
                    'Choose what to do:', ['perform', 'preview'])

                if not action:
                    return False

                if action == 'preview':
                    print("\n   ")
                    print("-------------------------------")
                    print("\n%s\n" % changes.get_description())
                    print("-------------------------------\n\n")
                    if not pymode_y_n(False):
                        return False

                progress = ProgressHandler('Apply changes ...')
                ctx.project.do(changes, task_handle=progress.handle)
                reload_changes(changes)
            except exceptions.RefactoringError as e:
                error(str(e))

            except Exception as e:
                error('Unhandled exception in Pymode: %s' % e)

    @staticmethod
    def get_refactor(ctx):
        """ Get refactor object. """

        raise NotImplementedError

    @staticmethod
    def get_input_str(refactor, ctx):
        """ Get user input. """

        raise NotImplementedError

    @staticmethod
    def get_changes(refactor, ctx):
        """ Get changes. """

        raise NotImplementedError


class RenameRefactoring(Refactoring):

    """ Rename var/function/method/class. """

    def __init__(self, module=False):
        self.module = module
        super(RenameRefactoring, self).__init__()

    def get_refactor(self, ctx):
        """ Function description.

        :return Rename:

        """
        offset = None
        if not self.module:
            _, offset = get_assist_params()
        return rename.Rename(ctx.project, ctx.resource, offset)

    def get_input_str(self, refactor, ctx):
        """ Return user input. """

        oldname = str(refactor.get_old_name())
        msg = 'Renaming method/variable. New name:'
        if self.module:
            msg = 'Renaming module. New name:'
        newname = pymode_input(msg, oldname)

        if newname == oldname:
            message("Nothing to do.")
            return False

        return newname

    @staticmethod
    def get_changes(refactor, input_str):
        """ Get changes.

        :return Changes:

        """

        progress = ProgressHandler('Calculate changes ...')
        return refactor.get_changes(
            input_str, task_handle=progress.handle)


class ExtractMethodRefactoring(Refactoring):

    """ Extract method. """

    @staticmethod
    def get_input_str(refactor, ctx):
        """ Return user input. """

        return pymode_input('New method name:')

    @staticmethod
    def get_refactor(ctx):
        """ Function description.

        :return Rename:

        """
        buf = vim.current.buffer
        cursor1, cursor2 = buf.mark('<'), buf.mark('>')
        _, offset1 = get_assist_params(cursor1)
        _, offset2 = get_assist_params(cursor2)
        return extract.ExtractMethod(
            ctx.project, ctx.resource, offset1, offset2)

    @staticmethod
    def get_changes(refactor, input_str):
        """ Get changes.

        :return Changes:

        """

        return refactor.get_changes(input_str)


class ExtractVariableRefactoring(Refactoring):

    """ Extract variable. """

    @staticmethod
    def get_input_str(refactor, ctx):
        """ Return user input. """

        return pymode_input('New variable name:')

    @staticmethod
    def get_refactor(ctx):
        """ Function description.

        :return Rename:

        """
        buf = vim.current.buffer
        cursor1, cursor2 = buf.mark('<'), buf.mark('>')
        _, offset1 = get_assist_params(cursor1)
        _, offset2 = get_assist_params(cursor2)
        return extract.ExtractVariable(
            ctx.project, ctx.resource, offset1, offset2)

    @staticmethod
    def get_changes(refactor, input_str):
        """ Get changes.

        :return Changes:

        """

        return refactor.get_changes(input_str)


class InlineRefactoring(Refactoring):

    """ Inline variable/method. """

    @staticmethod
    def get_input_str(refactor, ctx):
        """ Return user input. """

        return True

    @staticmethod
    def get_refactor(ctx):
        """ Function description.

        :return Rename:

        """
        _, offset = get_assist_params()
        return inline.create_inline(ctx.project, ctx.resource, offset)

    @staticmethod
    def get_changes(refactor, input_str):
        """ Get changes.

        :return Changes:

        """
        progress = ProgressHandler('Calculate changes ...')
        return refactor.get_changes(task_handle=progress.handle)


class UseFunctionRefactoring(Refactoring):

    """ Use selected function as possible. """

    @staticmethod
    def get_input_str(refactor, ctx):
        """ Return user input. """

        return True

    @staticmethod
    def get_refactor(ctx):
        """ Function description.

        :return Rename:

        """
        _, offset = get_assist_params()
        return usefunction.UseFunction(ctx.project, ctx.resource, offset)

    @staticmethod
    def get_changes(refactor, input_str):
        """ Get changes.

        :return Changes:

        """
        progress = ProgressHandler('Calculate changes ...')
        return refactor.get_changes(
            resources=[refactor.resource], task_handle=progress.handle)


class ModuleToPackageRefactoring(Refactoring):

    """ Convert module to package. """

    @staticmethod
    def get_input_str(refactor, ctx):
        """ Return user input. """

        return True

    @staticmethod
    def get_refactor(ctx):
        """ Function description.

        :return Rename:

        """
        return ModuleToPackage(ctx.project, ctx.resource)

    @staticmethod
    def get_changes(refactor, input_str):
        """ Get changes.

        :return Changes:

        """
        return refactor.get_changes()


def reload_changes(changes):
    """ Reload changed buffers. """

    resources = changes.get_changed_resources()
    moved = _get_moved_resources(changes) # noqa
    current = vim.current.buffer.number

    for f in resources:
        try:
            bufnr = vim.eval('bufnr("%s")' % f.real_path)
            if bufnr == '-1':
                continue
            vim.command('buffer %s' % bufnr)

            if f in moved:
                vim.command('e! %s' % moved[f].real_path)
            else:
                vim.command('e!')

            vim.command('echom "%s has been changed."' % f.real_path)

        except vim.error:
            continue
    vim.command('buffer %s' % current)


def _get_moved_resources(changes):

    moved = dict()

    if isinstance(changes, change.ChangeSet):
        for c in changes.changes:
            moved.update(_get_moved_resources(c))

    if isinstance(changes, change.MoveResource):
        moved[changes.resource] = changes.new_resource

    return moved
