#! /bin/bash
export CLEANSWEEP_TEST=true
py.test cleansweep "$@"
