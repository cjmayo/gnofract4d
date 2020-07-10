project('gnofract4d', 'cpp',
    license : 'BSD',
    default_options : ['cpp_std=c++17',
        'buildtype=release',
        'warning_level=3',
        'b_ndebug=if-release',
        'b_lto=true',
        'strip=true',
    ],
    meson_version : '>= 0.50',
    version : '4.3_pre1',
)

project_datadir = get_option('datadir') /  meson.project_name()

pymod = import('python')
py = pymod.find_installation()

py_version = py.language_version()
if py_version.version_compare('< 3.5')
    error('Sorry, you need Python 3.5 or higher to run Gnofract 4D.'
          + ' You have version ' + py_version + '. Please upgrade.')
endif

py_dep = py.dependency(required : true)

install_data('gnofract4d',
    install_dir: get_option('bindir'),
)

subdir('fract4d/c')

packages = ['fract4d', 'fract4d_compiler', 'fract4dgui']
foreach p : packages
    install_subdir(p,
        install_dir : py.get_install_dir(),
        exclude_directories : ['tests', 'c', 'fract4d_new'],
    )
endforeach

conf_data = configuration_data()
conf_data.set('app_datadir', get_option('prefix') / project_datadir)
conf_data.set('version', meson.project_version())
configure_file(input : '_conf_data.py.in',
   output : '_conf_data.py',
   configuration : conf_data,
   install : true,
   install_dir: py.get_install_dir() / 'fract4d',
)

# Application Data

install_subdir('manual/public',
    exclude_directories : 'svg',
    install_dir : project_datadir / 'help',
    strip_directory : true,
)

install_subdir('formulas',
    install_dir : project_datadir,
)

install_subdir('maps',
    install_dir : project_datadir,
)

install_data(
    'pixmaps/improve_now.png',
    'pixmaps/explorer_mode.png',
    'pixmaps/mail-forward.png',
    'pixmaps/draw-brush.png',
    'pixmaps/face-sad.png',
    'pixmaps/autozoom.png',
    'pixmaps/randomize_colors.png',
    install_dir : project_datadir / 'pixmaps',
)

# Desktop Environment Data

install_data('pixmaps/logo/48x48/gnofract4d.png',
    install_dir: 'share/pixmaps',
)

icon_sizes = [16, 32, 48, 64, 128, 256]
icon_template = 'pixmaps/logo/@0@x@0@/gnofract4d.png'
icon_dir_template = '@0@x@0@/apps/gnofract4d.png'
icons = []
icon_dirs = []

foreach s : icon_sizes
    icons += icon_template.format(s)
    icon_dirs += icon_dir_template.format(s)
endforeach

install_data(icons,
    rename : icon_dirs,
    install_dir : 'share/icons/hicolor',
)

install_data('gnofract4d.desktop',
    install_dir : 'share/applications',
)

install_data('gnofract4d-mime.xml',
    install_dir : 'share/mime/packages',
)

# Test

cp = find_program('cp')
custom_target('cp',
    command : [cp,
        fract4dc.full_path(),
        meson.source_root() / 'fract4d/',
    ],
    output : 'none',
    build_by_default : true,
    depends: fract4dc,
)

test('testing',
    find_program('pytest'),
    args : ['-v',
        'fract4d',
        'fract4dgui',
        'fract4d_compiler',
        'test.py',
    ],
    timeout : 60,
    workdir : meson.source_root(),
)
