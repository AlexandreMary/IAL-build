IAL-build
=========

*Tools for Source Code Management and build of IAL code.*

This packages wraps around IAL git repo management, bundling (ecbundle package) and build systems
(for now gmkpack only) to help transitioning from source code to IAL binary executables.

Dependancies
------------

* `ecbundle` : https://github.com/ecmwf/ecbundle
* Some functionalities may also clone and use [IAL-bundle](https://github.com/ACCORD-NWP/IAL-bundle). If you don't have internet connection at time of use, you may have to specify a local, pre-cloned, origin repository for IAL-bundle, using env variable `DEFAULT_IALBUNDLE_REPO`, e.g. `DEFAULT_IALBUNDLE_REPO=~/repositories/IAL-bundle`

Installation
------------

* on `belenos`:

  ```
  module use ~mary/public/modulefiles
  module load ecbundle
  module load IAL-build
  ```

* at CNRM:
  - install `ecbundle`, e.g. `pip3 install --user git+https://github.com/ecmwf/ecbundle`
  - ```
    IAL_BUILD_PACKAGE=/home/common/epygram/public/IAL-build/default
    export PATH=$IAL_BUILD_PACKAGE/bin:$PATH
    export PYTHONPATH=$IAL_BUILD_PACKAGE/src:$PYTHONPATH
    ```
  
* in general:
  - install `ecbundle`, e.g. `pip3 install git+https://github.com/ecmwf/ecbundle`
  - Clone this repo, then add paths to the package:
    ```
    export PATH=<path to package>/bin:$PATH
    export PYTHONPATH=<path to package>/src:$PYTHONPATH
    ```

Tools
-----

In the `bin/` directory, the `ial-*` commands can help finding bundles, create IAL branches and make packs (gmkpack) from bundles or IAL branches.
They are auto-documented, see their argument `-h`.
