#%Module1.0

# path to IAL-build on belenos
set modroot ~mary/public/IAL-build

module-whatis "Environment module for IAL-build"
module-whatis "Cf. https://github.com/ACCORD-NWP/IAL-build"
module-whatis "Local installation: $modroot"

# pre-requisites
if { [module-info mode load] || [module-info mode switch2] } {
  puts stderr "Check IAL-build requirements: git, python..."
}
prereq git
prereq python
if { [module-info mode load] || [module-info mode switch2] } {
  puts stderr "...OK"
}

set modulename [module-info name]
set fields [split $modulename "/"]
set pkg_name [lindex $fields 0]
set pkg_vers [lindex $fields end]

append-path PATH $modroot/$pkg_vers/bin
append-path PYTHONPATH $modroot/$pkg_vers/src

if { [module-info mode load] || [module-info mode switch2] } {
  puts stderr "Environment for IAL-build commands loaded !"
}
