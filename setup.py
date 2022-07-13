"""Setup and install witch-ver

Typical usage:
  python setup.py develop
  python setup.py install
  python setup.py test
"""

import setuptools

module_name = "witch-ver"
module_folder = "witch_ver"

with open("README.md", encoding="utf-8") as file:
  longDescription = file.read()

required = ["colorama"]
extras_require = {"test": ["AutoDict", "coverage", "pylint"]}

try:
  from tools import gitsemver
  version = gitsemver.get_version()
  with open(f"{module_folder}/version.py", "w", encoding="utf-8") as file:
    file.write('"""Module version information\n"""\n\n')
    file.write(f'version = "{version}"\n')
    file.write(f'version_full = "{version.full_str()}"\n')
    file.write(f'tag = "{version.raw}"\n')
except ImportError:
  import re
  with open(f"{module_folder}/version.py", "r", encoding="utf-8") as file:
    version = re.search(r'version = "(.*)"', file.read())[1]

setuptools.setup(
    name=module_name,
    version=str(version),
    description="git tag based versioning",
    long_description=longDescription,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=setuptools.find_packages(),
    package_data={module_folder: []},
    install_requires=required,
    extras_require=extras_require,
    test_suite="tests",
    scripts=[],
    author="Bradley Davis",
    author_email="me@bradleydavis.tech",
    url="https://github.com/WattsUp/witch-ver",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    include_package_data=True,
    zip_safe=False,
)
