#!/Users/ahsan_admin/Documents/OpenInterpreterChat/venv/bin/python
# -*- coding: utf-8 -*-
import re
import sys
from interpreter import cli
if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(cli())
