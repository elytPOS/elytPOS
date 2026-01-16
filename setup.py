from setuptools import setup, find_packages

setup(
    name="elytpos",
    version="1.0.0",
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
