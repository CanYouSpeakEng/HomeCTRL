"""
build_exe.py - Builds the standalone HomeCTRL.exe executable using PyInstaller.
"""

import os
import sys
import subprocess

def build():
    print("=" * 60)
    print("       Building Standalone HomeCTRL.exe (Release)")
    print("=" * 60)

    icon_path = os.path.join("assets", "app_icon.ico")
    if not os.path.exists(icon_path):
        print("Generating icon first...")
        import generate_icon
        generate_icon.generate_icons()

    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=HomeCTRL",
        "--noconsole",             # No terminal / command prompt window
        "--onefile",               # Bundle everything into a single .exe
        f"--icon={icon_path}",     # Embed custom high-res application icon
        "--clean",
        "--add-data=assets;assets",
        "--hidden-import=tinytuya",
        "--hidden-import=tinytuya.wizard",
        "--hidden-import=cryptography",
        "--hidden-import=colorsys",
        "--hidden-import=requests",
        "--hidden-import=winreg",
        "main.py",
    ]

    print(f"Running PyInstaller command:\n{' '.join(pyinstaller_cmd)}\n")
    res = subprocess.run(pyinstaller_cmd)

    if res.returncode == 0:
        exe_path = os.path.abspath(os.path.join("dist", "HomeCTRL.exe"))
        print("\n" + "=" * 60)
        print("          BUILD COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Your standalone executable is ready at:\n  {exe_path}")
        print("\nYou can double-click HomeCTRL.exe to run it without Python or PowerShell!")
    else:
        print(f"\n[ERROR] Build failed with exit code: {res.returncode}")

if __name__ == "__main__":
    build()
