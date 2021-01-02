# Ocrlayout Library Packaging

Below the instructions to build a new ocrlayout package. 

# Package the new version
## Open a bash terminal
## Go to the directory ocrlayout_pkg
## Set a new version number in the setup.py script 
```python
setuptools.setup(
    name='ocrlayout',  
    version='0.4.1',
```
## Document the version change in the README.md 
```
# Release History
## 0.4.1 (2020-06-01)
- ...
```
## Export the version as variable 
```bash
export version="0.9"
```
## Build a new package version
```bash
python3 setup.py sdist bdist_wheel
```
# Local Install for testing-only

## Install the ocrlayout pkg locally 
```bash
python3 -m pip install dist/ocrlayout_pkg_puthurr-0.1-py3-none-any.whl
```
## Upgrade existing version locally
```bash
pip3 install dist/ocrlayout_pkg_puthurr-0.1-py3-none-any.whl --upgrade
```
# Remote PYPI Repository

## Upload to testpypi with twine
```bash
python3 -m twine upload --repository testpypi dist/ocrlayout-$version* --verbose
```
## Upload to pypi with twine
```bash
python3 -m twine upload dist/ocrlayout-$version* --verbose
```
# Install or upgrade the released package - ocrlayout
From thetest pypi repository
```bash
pip3 install -i https://test.pypi.org/simple/ ocrlayout==0.9
```
From the main pypi repository
```bash
pip3 install ocrlayout --upgrade
```