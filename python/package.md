# Ocrlayout Library Packaging

Below the instructions to build a new ocrlayout package. 

# Set a new version number in the setup.py script 
```python
setuptools.setup(
    name='ocrlayout',  
    version='0.4.1',
```
# Document the change in the README.md 
```
# Release History
## 0.4.1 (2020-06-01)
- ...
```
Export the version as variable 
```
export version="0.7"
```
# Build a new package version
```
python3 setup.py sdist bdist_wheel
```
# Local Install
## Install the ocrlayout pkg locally 
```
python3 -m pip install dist/ocrlayout_pkg_puthurr-0.1-py3-none-any.whl
```
## Upgrade existing version locally
```
pip3 install dist/ocrlayout_pkg_puthurr-0.1-py3-none-any.whl --upgrade
```
# Remote PYPI Repository
# Upload to testpypi with twine
```
python3 -m twine upload --repository testpypi dist/ocrlayout-$version* --verbose
```
# Upload to pypi with twine
```
python3 -m twine upload dist/ocrlayout-$version* --verbose
```
# Test the installed version 
```
pip3 install -i https://test.pypi.org/simple/ ocrlayout-pkg==0.1.1
```
```
pip3 install ocrlayout-pkg --upgrade
```