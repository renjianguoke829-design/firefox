#!/bin/bash
set -e
export MOZCONFIG=browser/mozconfig-domestic
export BROWSER_VARIANT=domestic
./mach build
