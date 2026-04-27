"""
讓使用者安裝後可以：
isd_str_sdk -V
isd_str_sdk --version
"""
from ._version import __version__

def main():
    import argparse

    parser = argparse.ArgumentParser(description="isd_str_sdk CLI")
    parser.add_argument("-V", "--version", action="store_true", help="Show version")
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    print("isd_str_sdk CLI running ...")
