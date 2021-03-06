#!/usr/bin/env python3

from setuptools import setup, Extension
import sysconfig
import os
import shutil
import subprocess
import sys

gnofract4d_version = '4.3'

_DEBUG = False

if sys.version_info < (3, 6):
    print("Sorry, you need Python 3.6 or higher to run Gnofract 4D.")
    print("You have version %s. Please upgrade." % sys.version)
    sys.exit(1)

if not os.path.exists(os.path.join(sysconfig.get_config_var("INCLUDEPY"), "Python.h")):
    print("Python header files are required.")
    print("Please install libpython3-dev")
    sys.exit(1)

# by default python uses all the args which were used to compile it. But Python is C and some
# extension files are C++, resulting in annoying '-Wstrict-prototypes is not supported' messages.
# tweak the cflags to override
os.environ["CFLAGS"] = sysconfig.get_config_var(
    "CFLAGS").replace("-Wstrict-prototypes", "")
os.environ["OPT"] = sysconfig.get_config_var(
    "OPT").replace("-Wstrict-prototypes", "")

# Extensions need to link against appropriate libs
# We use pkg-config to find the appropriate set of includes and libs


def call_package_config(package, option, optional=False):
    '''invoke pkg-config, if it exists, to find the appropriate arguments for a library'''
    try:
        cp = subprocess.run(["pkg-config", package, option],
                            universal_newlines=True, stdout=subprocess.PIPE)
    except FileNotFoundError:
        print(
            "Unable to check for '%s', pkg-config not installed" % package, file=sys.stderr)
        if optional:
            return []
        else:
            sys.exit(1)

    if cp.returncode != 0:
        if optional:
            print("Can't find '%s'" % package, file=sys.stderr)
            print("Some functionality will be disabled", file=sys.stderr)
            return []
        else:
            print(
                "Development files not found for '%s'" % package, file=sys.stderr)
            sys.exit(1)

    return cp.stdout.split()


png_flags = call_package_config("libpng", "--cflags")
png_libs = call_package_config("libpng", "--libs")
define_macros = [('PNG_ENABLED', 1)]

jpeg_flags = call_package_config("libjpeg", "--cflags", True)
jpeg_libs = call_package_config("libjpeg", "--libs", True)
if jpeg_flags + jpeg_libs:
    define_macros.append(('JPG_ENABLED', 1))

fract4d_sources = [
    'fract4d/c/fract4dmodule.cpp',

    'fract4d/c/fract4dc/colormaps.cpp',
    'fract4d/c/fract4dc/loaders.cpp',
    'fract4d/c/fract4dc/sites.cpp',
    'fract4d/c/fract4dc/images.cpp',
    'fract4d/c/fract4dc/calcs.cpp',
    'fract4d/c/fract4dc/workers.cpp',
    'fract4d/c/fract4dc/functions.cpp',
    'fract4d/c/fract4dc/arenas.cpp',
    'fract4d/c/fract4dc/utils.cpp',
    'fract4d/c/fract4dc/calcargs.cpp',
    'fract4d/c/fract4dc/pysite.cpp',

    'fract4d/c/fract4dc/controllers.cpp',

    'fract4d/c/model/calcfunc.cpp',
    'fract4d/c/model/fractfunc.cpp',
    'fract4d/c/model/site.cpp',
    'fract4d/c/model/image.cpp',
    'fract4d/c/model/imagewriter.cpp',
    'fract4d/c/model/imagereader.cpp',
    'fract4d/c/model/colormap.cpp',
    'fract4d/c/model/worker.cpp',
    'fract4d/c/model/STFractWorker.cpp',
    'fract4d/c/model/MTFractWorker.cpp',
    'fract4d/c/model/pointfunc.cpp',
    'fract4d/c/model/stats.cpp',
    'fract4d/c/model/colorutils.cpp',
    'fract4d/c/model/imageutils.cpp',

    'fract4d/c/fract_stdlib.cpp'
]

define_macros.append(('THREADS', 1))
extra_compile_args = ['-std=c++17', '-Wall',
                      '-Wextra', '-Wpedantic', '-Wno-attributes']

# from https://pythonextensionpatterns.readthedocs.io/en/latest/compiler_flags.html?highlight=python3-dev
if _DEBUG:
    extra_compile_args += ["-g3", "-O0", "-UNDEBUG"]
    define_macros += [
        # ('STATIC_CALC',1),
        # ('NO_CALC', 1),  # set this to not calculate the fractal
        # ('DEBUG_CREATION',1), # debug spew for allocation of objects
        # ('DEBUG_ALLOCATION',1), # debug spew for array handling
        # ('DEBUG_PIXEL',1), # debug spew for array handling
        # ('EXPERIMENTAL_OPTIMIZATIONS',1), # enables some experimental optimizations
    ]
else:
    extra_compile_args += ["-DNDEBUG", "-O3"]

module_fract4dc = Extension(
    name='fract4d.fract4dc',
    sources=fract4d_sources,
    include_dirs=['fract4d/c', 'fract4d/c/fract4dc', 'fract4d/c/model'],
    libraries=['stdc++'],
    extra_compile_args=extra_compile_args + png_flags + jpeg_flags,
    extra_link_args=png_libs + jpeg_libs,
    define_macros=define_macros,
)



def get_files(dir, ext):
    return [os.path.join(dir, x) for x in os.listdir(dir) if x.endswith(ext)]


def get_icons():
    icons = []
    for size in 16, 32, 48, 64, 128, 256:
        icons.append(('share/icons/hicolor/{0}x{0}/apps'.format(size),
                      ['pixmaps/logo/{0}x{0}/gnofract4d.png'.format(size)]))
    return icons


so_extension = sysconfig.get_config_var("EXT_SUFFIX")

setup(
    name='gnofract4d',
    version=gnofract4d_version,
    description='A program to draw fractals',
    long_description='''Gnofract 4D is a fractal browser. It can generate many different fractals,
including some which are hybrids between the Mandelbrot and Julia sets,
and includes a Fractint-compatible parser for your own fractal formulas.''',
    author='Edwin Young',
    author_email='edwin@bathysphere.org',
    maintainer='Edwin Young',
    maintainer_email='edwin@bathysphere.org',
    keywords="fractal mandelbrot julia",
    url='http://github.com/fract4d/gnofract4d/',
    packages=['fract4d_compiler', 'fract4d', 'fract4dgui'],
    package_data={
        'fract4dgui': ['shortcuts-gnofract4d.ui', 'ui.xml', 'gnofract4d.css'],
        'fract4d': ['c/pf.h', 'c/fract_stdlib.h', 'c/model/imageutils.h', 'c/model/colorutils.h']
    },
    ext_modules=[module_fract4dc],
    scripts=['gnofract4d'],
    data_files=[
        # color maps
        (
            'share/gnofract4d/maps',
            get_files("maps", ".map") +
            get_files("maps", ".cs") +
            get_files("maps", ".ugr")
        ),
        # formulas
        (
            'share/gnofract4d/formulas',
            get_files("formulas", "frm") +
            get_files("formulas", "ucl") +
            get_files("formulas", "uxf")
        ),
        # documentation
        (
            'share/gnofract4d/help',
            get_files("help", "html") +
            get_files("help", "png") +
            get_files("help", "css")
        ),
        # internal pixmaps
        (
            'share/gnofract4d/pixmaps',
            [
                'pixmaps/improve_now.png',
                'pixmaps/explorer_mode.png',
                'pixmaps/mail-forward.png',
                'pixmaps/draw-brush.png',
                'pixmaps/face-sad.png',
                'pixmaps/autozoom.png',
                'pixmaps/randomize_colors.png'
            ]
        ),
        # icon
        ('share/pixmaps', ['pixmaps/logo/48x48/gnofract4d.png']),
        # theme icons
        *get_icons(),
        # .desktop file
        ('share/applications', ['gnofract4d.desktop']),
        # MIME type registration
        ('share/mime/packages', ['gnofract4d-mime.xml']),
        # doc files
        ('share/doc/gnofract4d/', ['LICENSE', 'README.md'])
    ],
)

# I need to find the file I just built and copy it up out of the build
# location so it's possible to run without installing. Can't find a good
# way to extract the actual target directory out of distutils, hence
# this egregious hack

lib_targets = {
    "fract4dc" + so_extension: "fract4d",
}


def copy_libs(root, dirlist, namelist):
    for name in namelist:
        target = lib_targets.get(name)
        if target is not None:
            shutil.copy(os.path.join(root, name), target)


for root, dirs, files in os.walk("build"):
    copy_libs(root, dirs, files)
