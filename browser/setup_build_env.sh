#!/bin/bash
set -e

echo "Firefox 构建环境说明"
echo "1) 国内版构建："
echo "   ./browser/build-domestic.sh"
echo "   - 使用 browser/mozconfig-domestic"
echo "   - 输出目录 obj-domestic"
echo
echo "2) 国际版构建："
echo "   ./browser/build-international.sh"
echo "   - 使用 browser/mozconfig-international"
echo "   - 输出目录 obj-international"
echo
echo "你也可以手动设置："
echo "   export MOZCONFIG=browser/mozconfig-domestic|browser/mozconfig-international"
echo "   export BROWSER_VARIANT=domestic|international"
echo "   ./mach build"
