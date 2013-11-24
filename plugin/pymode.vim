" vi: fdl=1 
let g:pymode_version = "0.6.19"

com! PymodeVersion echomsg "Current python-mode version: " . g:pymode_version
com! PymodeTroubleshooting call pymode#troubleshooting#test()

" Enable pymode by default :)
call pymode#default('g:pymode', 1)

" DESC: Disable script loading
if !g:pymode || &cp
    finish
endif

" OPTIONS: {{{

" Vim Python interpreter. Set to 'disable' for remove python features.
call pymode#default('g:pymode_python', 'python')

" Disable pymode warnings
call pymode#default('g:pymode_warning', 1)

" Modify sys.path for pymode modules loading
call pymode#default('g:pymode_path', 1)

" Additional python paths
call pymode#default('g:pymode_paths', [])

" Python documentation support
call pymode#default('g:pymode_doc', 1)
call pymode#default('g:pymode_doc_bind', 'K')

" Enable/Disable pymode PEP8 indentation
call pymode#default("g:pymode_indent", 1)

" Enable/disable pymode folding for pyfiles.
call pymode#default("g:pymode_folding", 1)

" Enable/disable python motion operators
call pymode#default("g:pymode_motion", 1)

" Auto remove unused whitespaces on save
call pymode#default("g:pymode_trim_whitespaces", 1)

" Set recomended python options
call pymode#default("g:pymode_options", 1)

" LOAD VIRTUALENV {{{
"
" Enable virtualenv support
call pymode#default('g:pymode_virtualenv', 1)

" Get path to virtualenv (by default take from shell)
call pymode#default('g:pymode_virtualenv_path', $VIRTUAL_ENV)

" Service variable (don't set it manually)
call pymode#default('g:pymode_virtualenv_enabled', '')

" }}}

" RUN PYTHON {{{
"
" Enable code running support
call pymode#default('g:pymode_run', 1)

" Key's map for run python code
call pymode#default('g:pymode_run_bind', '<leader>r')

" }}}

" CHECK CODE {{{
"
" Code checking
call pymode#default('g:pymode_lint', 1)

" Check code asynchronously
call pymode#default('g:pymode_lint_async', 1)
call pymode#default('g:pymode_lint_async_updatetime', 1000)

" Check code every save.
call pymode#default("g:pymode_lint_on_write", 1)

" Check code on fly
call pymode#default("g:pymode_lint_on_fly", 0)

" Show current line error message
call pymode#default("g:pymode_lint_message", 1)

" Hold cursor on current window when quickfix open
call pymode#default('g:pymode_lint_hold', 0)

" Minimal height of pymode quickfix window
call pymode#default('g:pymode_lint_maxheight', 6)

" Maximal height of pymode quickfix window
call pymode#default('g:pymode_lint_minheight', 3)

" Show message about error in command line
call pymode#default("g:pymode_lint_status", 1)

" Choices are: pylint, pyflakes, pep8, mccabe
call pymode#default("g:pymode_lint_checkers", "pyflakes,pep8,mccabe")

" Skip errors and warnings (e.g. E4,W)
call pymode#default("g:pymode_lint_ignore", "")

" Auto open cwindow if errors find
call pymode#default("g:pymode_lint_cwindow", 1)

" Select errors and warnings (e.g. E4,W)
call pymode#default("g:pymode_lint_select", "")

" Place error signs
call pymode#default("g:pymode_lint_signs", 1)

" Always show the errors ruller, even if there's no errors.
call pymode#default("g:pymode_lint_signs_always_visible", 0)

" Todo symbol.
call pymode#default("g:pymode_lint_todo_symbol", "WW")

" Comment symbol.
call pymode#default("g:pymode_lint_comment_symbol", "CC")

" Visual symbol.
call pymode#default("g:pymode_lint_visual_symbol", "RR")

" Error symbol.
call pymode#default("g:pymode_lint_error_symbol", "EE")

" Info symbol.
call pymode#default("g:pymode_lint_info_symbol", "II")

" PyFlakes' info symbol.
call pymode#default("g:pymode_lint_pyflakes_symbol", "FF")

if g:pymode_lint_signs && has('signs')

    " Signs definition
    execute 'sign define PymodeW text=' . g:pymode_lint_todo_symbol     . " texthl=Todo"
    execute 'sign define PymodeC text=' . g:pymode_lint_comment_symbol  . " texthl=Comment"
    execute 'sign define PymodeR text=' . g:pymode_lint_visual_symbol   . " texthl=Visual"
    execute 'sign define PymodeE text=' . g:pymode_lint_error_symbol    . " texthl=Error"
    execute 'sign define PymodeI text=' . g:pymode_lint_info_symbol     . " texthl=Info"
    execute 'sign define PymodeF text=' . g:pymode_lint_pyflakes_symbol . " texthl=Info"

endif

" }}}

" SET/UNSET BREAKPOINTS {{{
"

" Create/remove breakpoints
call pymode#default('g:pymode_breakpoint', 1)

" Key's map for add/remove breakpoint
call pymode#default('g:pymode_breakpoint_bind', '<leader>b')

" Default pattern for making breakpoints. Leave this empty for auto search available debuggers (pdb, ipdb, ...)
call pymode#default('g:pymode_breakpoint_template', '')

" }}}

" ROPE (refactoring, codeassist) {{{
"
" Rope support
call pymode#default('g:pymode_rope', 1)

" Enable Rope completion
call pymode#default('g:pymode_rope_completion', 1)

" Automatic completion on dot
call pymode#default('g:pymode_rope_complete_on_dot', 1)

" Bind keys for autocomplete (leave empty for disable)
call pymode#default('g:pymode_rope_completion_bind', '<C-Space>')

" Bind keys for goto definition (leave empty for disable)
call pymode#default('g:pymode_rope_goto_definition_bind', '<C-c>g')

" set commend for open definition (e, new, vnew)
call pymode#default('g:pymode_rope_goto_definition_cmd', 'new')

" Bind keys for show documentation (leave empty for disable)
call pymode#default('g:pymode_rope_show_doc_bind', '<C-c>d')

" Bind keys for find occurencies (leave empty for disable)
call pymode#default('g:pymode_rope_find_it_bind', '<C-c>f')

" Bind keys for organize imports (leave empty for disable)
call pymode#default('g:pymode_rope_orgazine_imports_bind', '<C-c>ro')

" Bind keys for rename variable/method/class in the project (leave empty for disable)
call pymode#default('g:pymode_rope_rename_bind', '<C-c>rr')

" Bind keys for rename module
call pymode#default('g:pymode_rope_rename_module_bind', '<C-c>r1r')

" Bind keys for convert module to package
call pymode#default('g:pymode_rope_module_to_package_bind', '<C-c>r1p')

" Creates a new function or method (depending on the context) from the selected lines
call pymode#default('g:pymode_rope_extract_method_bind', '<C-c>rm')

" Creates a variable from the selected lines
call pymode#default('g:pymode_rope_extract_variable_bind', '<C-c>rl')

" Inline refactoring
call pymode#default('g:pymode_rope_inline_bind', '<C-c>ri')

" Tries to find the places in which a function can be used and changes the
" code to call it instead
call pymode#default('g:pymode_rope_use_function_bind', '<C-c>ru')

" }}}

" }}}

" Prepare to plugin loading
if &compatible
    set nocompatible
endif
filetype plugin on

" Disable python-related functionality
" let g:pymode_python = 'disable'
" let g:pymode_python = 'python3'
if g:pymode_python != 'disable' && (g:pymode_python == 'python3' || !has('python') && has('python3'))
    let g:pymode_python = 'python3'
    command! -nargs=1 PymodePython python3 <args>

elseif g:pymode_python != 'disable' && has('python')
    let g:pymode_python = 'python'
    command! -nargs=1 PymodePython python <args>

else

    let g:pymode_doc = 0
    let g:pymode_lint = 0
    let g:pymode_path = 0
    let g:pymode_python = 'disable'
    let g:pymode_rope = 0
    let g:pymode_run = 0
    let g:pymode_virtualenv = 0

endif

com! PymodeVersion echomsg "Pymode version: " . g:pymode_version . " interpreter: " . g:pymode_python . " lint: " . g:pymode_lint . " rope: " . g:pymode_rope

augroup pymode

