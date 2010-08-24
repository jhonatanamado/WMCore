#!/usr/bin/env python
#-*- coding: ISO-8859-1 -*-
"""
Common utilities module used by REST services
"""

__author__ = "Valentin Kuznetsov <vkuznet at gmail dot com>"
__revision__ = "$Id:"
__version__ = "$Revision:"

# import system modules
import logging
import logging.handlers

def setsqlalchemylogger(hdlr, level):
    """Set up logging for SQLAlchemy"""
    logging.getLogger('sqlalchemy.engine').setLevel(level)
    logging.getLogger('sqlalchemy.orm.unitofwork').setLevel(level)
    logging.getLogger('sqlalchemy.pool').setLevel(level)

    logging.getLogger('sqlalchemy.engine').addHandler(hdlr)
    logging.getLogger('sqlalchemy.orm.unitofwork').addHandler(hdlr)
    logging.getLogger('sqlalchemy.pool').addHandler(hdlr)

def setcherrypylogger(hdlr, level):
    """Set up logging for CherryPy"""
    logging.getLogger('cherrypy.error').setLevel(level)
    logging.getLogger('cherrypy.access').setLevel(level)

    logging.getLogger('cherrypy.error').addHandler(hdlr)
    logging.getLogger('cherrypy.access').addHandler(hdlr)

