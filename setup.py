from setuptools import setup, find_packages
from version import __version__

setup(
    name="elytpos",
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PySide6",
        "psycopg2-binary",
        "pycups",
    ],
    entry_points={
        "console_scripts": [
            "elytpos=main:main",
        ],
    },
)
