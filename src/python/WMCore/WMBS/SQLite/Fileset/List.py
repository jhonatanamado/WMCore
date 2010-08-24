#!/usr/bin/env python
"""
_List_

SQLite implementation of ListFileset

"""
__all__ = []
__revision__ = "$Id: List.py,v 1.2 2008/11/20 21:54:26 sryu Exp $"
__version__ = "$Revision: 1.2 $"

from WMCore.WMBS.MySQL.Fileset.List import List as ListFilesetMySQL

class List(ListFilesetMySQL):
    sql = ListFilesetMySQL.sql
    
    def format(self, result):
        """
        Some standardised formatting
        """
        out = []
        for r in result:
            for i in r.fetchall():
                res = i
                j = i[0], str(i[1]), self.truefalse(i[2]), i[3]
                out.append(j)
        return out