import PyInstaller.__main__
import os
import shutil

if __name__ == '__main__':
    for d in ['dist', 'build']:
        if os.path.exists(d):
            shutil.rmtree(d)

    PyInstaller.__main__.run([
        'src/python/main.py',
        '--name=CS2Farmer',
        '--onefile',
        '--windowed',
        '--add-data=src/node;node',
        '--add-data=mafiles;mafiles',
        '--hidden-import=win32timezone',
        '--collect-all=customtkinter',
        '--collect-all=plotly',
        '--icon=icon.ico'
    ])