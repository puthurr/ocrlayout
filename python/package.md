# Ocrlayout Library Packaging

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
Make sure to clean old versions in the dist folder. 
```
python3 -m twine upload --repository testpypi dist/* --verbose
```

# Upload to pypi with twine
Make sure to clean old versions in the dist folder. 
```
python3 -m twine upload dist/* --verbose
```

# Test the installed version 

```
pip3 install -i https://test.pypi.org/simple/ ocrlayout-pkg==0.1.1
```