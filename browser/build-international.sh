#!/bin/bash
set -e
export MOZCONFIG=browser/mozconfig-international
export BROWSER_VARIANT=international
./mach build
