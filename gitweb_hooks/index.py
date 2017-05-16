#!bin/bash
import sys

from mod_python import apache

def handler(req):
  req.content_type = 'text/plain'
  req.write("hello world! " + sys.version)
  return apache.OK