# -*- mode: python ; coding: utf-8 -*-
"""
Spec file para empaquetar Gestión de Obras como .exe standalone.
Incluye: Python, Streamlit, altair, pandas y todos los archivos de la app.
"""
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Recolectar todos los archivos de Streamlit y altair
st_datas,  st_bins,  st_hidden  = collect_all('streamlit')
alt_datas, alt_bins, alt_hidden = collect_all('altair')
pd_datas = collect_data_files('pandas')

a = Analysis(
    ['main_frozen.py'],
    pathex=['.'],
    binaries=st_bins + alt_bins,
    datas=(
        # Archivos de la aplicación
        [
            ('app.py',      '.'),
            ('database.py', '.'),
            ('utils.py',    '.'),
            ('pages',       'pages'),
            ('.streamlit',  '.streamlit'),
        ]
        # Archivos de paquetes
        + st_datas + alt_datas + pd_datas
    ),
    hiddenimports=(
        st_hidden + alt_hidden
        + [
            # pandas
            'pandas', 'pandas._libs', 'pandas._libs.tslibs',
            'pandas._libs.tslibs.np_datetime',
            'pandas._libs.tslibs.nattype',
            'pandas._libs.tslibs.timedeltas',
            # streamlit extras
            'streamlit.runtime.scriptrunner.magic_funcs',
            'streamlit.components.v1',
            'streamlit.runtime.caching.cache_data_api',
            'streamlit.runtime.caching.cache_resource_api',
            # servidor web
            'tornado', 'tornado.web', 'tornado.httpserver',
            'tornado.websocket', 'tornado.ioloop',
            # serialización
            'pyarrow', 'pyarrow.pandas_compat',
            'google.protobuf', 'google.protobuf.descriptor',
            # validación y esquemas
            'jsonschema', 'jsonschema.validators',
            'jsonschema._validators',
            'validators',
            # utilidades
            'packaging', 'packaging.version',
            'click', 'click.core',
            'toolz', 'attr', 'attrs',
            'blinker', 'cachetools',
            'typing_extensions',
            'numpy', 'numpy.core',
            # git (streamlit lo usa para el número de versión)
            'git',
            # PIL (imágenes en streamlit)
            'PIL', 'PIL.Image',
            # stdlib
            'sqlite3', 'pathlib', 'threading', 'webbrowser', 'tkinter',
        ]
    ),
    hookspath=[],
    runtime_hooks=[],
    # Excluir paquetes científicos pesados que no usamos
    excludes=['matplotlib', 'scipy', 'IPython', 'notebook', 'pytest'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GestionObras',
    debug=False,
    strip=False,
    upx=False,
    console=False,      # Sin ventana de consola
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='GestionObras',
)
