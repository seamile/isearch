#!/bin/bash

echo 'Will delete:
  - __pycache__
  - builds
  - dist
  - *.egg-ingo
'
read -p "Continue? (y/n) " -n 1 sure


if [[ $sure =~ [yY] ]]; then
    echo -e '\x1b[1;31m\ndeleting...\x1b[0m'
    proj=$(dirname $0)
    rm -rfv $proj/{__pycache__,build,dist,*.egg-info}
else
    echo -e '\nBye'
fi
