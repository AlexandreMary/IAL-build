IAL-build
=========

*Tools for Source Code Management and build of IAL code.*

This packages wraps around IAL git repo management, bundling (ecbundle package) and build systems
(for now gmkpack only) to help transitioning from source code to IAL binary executables.

Dependancies
------------

* `ecbundle` : https://github.com/ecmwf/ecbundle

Installation
------------

* in general:
  - install `ecbundle`, e.g. `pip3 install git+https://github.com/ecmwf/ecbundle`
  - Clone this repo, then add paths to the package:
    ```
    export PATH=<path to package>/bin:$PATH
    export PYTHONPATH=<path to package>/src:$PYTHONPATH
    ```

* on `belenos`:

  - module use ~mary/public/modulefiles
  - module load IAL-build

* at CNRM:
  - install `ecbundle`, e.g. `pip3 install git+https://github.com/ecmwf/ecbundle`
  - ```
    IAL_BUILD_PACKAGE=/home/common/epygram/public/IAL-build/default
    export PATH=$IAL_BUILD_PACKAGE/bin:$PATH
    export PYTHONPATH=$IAL_BUILD_PACKAGE/src:$PYTHONPATH
    ```
  
