#!/usr/bin/env python
"""
_Exists_

SQLite implementation of Files.Exists

"""

__all__ = []
__revision__ = "$Id: Exists.py,v 1.2 2008/11/20 21:54:25 sryu Exp $"
__version__ = "$Revision: 1.2 $"

from WMCore.WMBS.MySQL.Files.Exists import Exists as FilesExistsMySQL

class Exists(FilesExistsMySQL):
    sql = FilesExistsMySQL.sql
