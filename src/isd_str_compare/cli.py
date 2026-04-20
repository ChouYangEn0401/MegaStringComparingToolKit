"""
讓使用者安裝後可以：
{project_name} -V
{project_name} --version
"""
from ._version import __version__

def main():
    import argparse

    parser = argparse.ArgumentParser(description="{{project_name}} CLI")
    parser.add_argument("-V", "--version", action="store_true", help="Show version")
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    print("{{project_name}} CLI running ...")
