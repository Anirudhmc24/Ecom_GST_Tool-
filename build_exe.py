import PyInstaller.__main__
import os

# Define paths
entry_point = 'run_app.py'
main_script = 'main.py'

# PyInstaller command arguments
args = [
    entry_point,
    '--onefile',
    '--name=EcomGSTTool',
    '--collect-all=streamlit',
    '--add-data=main.py;.',
    '--add-data=database;database',
    '--add-data=ui;ui',
    '--add-data=services;services',
    '--add-data=config;config',
    '--add-data=USER_MANUAL_ECOM_GST.md;.',
    '--hidden-import=streamlit',
    '--hidden-import=pandas',
    # Exclude heavy modules to shrink the exe and speed up build
    '--exclude-module=torch',
    '--exclude-module=torchvision',
    '--exclude-module=scipy',
    '--exclude-module=sympy',
    '--exclude-module=plotly',
    '--exclude-module=matplotlib',
    '--clean',
]

# Run PyInstaller
PyInstaller.__main__.run(args)
