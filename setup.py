"""Setup and install witch-ver

Typical usage:
  python setup.py develop
  python setup.py install
  python setup.py test
"""

import setuptools

from witch_ver import __version__

module_folder = "witch_ver"
module_name = "witch-ver"

with open("README.md", encoding="utf-8") as file:
  longDescription = file.read()

required = ["colorama"]
extras_require = {"test": ["AutoDict", "coverage", "pylint"]}
extras_require["dev"] = extras_require["test"] + ["toml", "yapf>=0.40.0"]

setuptools.setup(
    name=module_name,
    version=__version__,
    description="git tag based versioning",
    long_description=longDescription,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=setuptools.find_packages(
        include=[module_folder, f"{module_folder}.*"]),
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
    # include_package_data=True, # Leave out cause wacky
    zip_safe=False,
    entry_points={
        "distutils.setup_keywords": [
            "use_witch_ver = witch_ver.integration:use_witch_ver"
        ]
    })
