#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
from glob import glob

setup(name='gsni-authenticator',
      version='0.8.4',
      description='GSNI Authenticator Applet',
      author='João Pinto',
      author_email='lamego.pinto@gmail.com',
      packages=['gsni_authenticator'],
      scripts=['bin/gsni-authenticator'],
      data_files=[
                  ('/usr/share/gsni-authenticator/ui/', glob('ui/*')),
                  ('/usr/share/gsni-authenticator/ui_pt/', glob('ui_pt/*')),
                  ('/usr/share/gsni-authenticator/ui_es/', glob('ui_es/*')),
                  ('/etc/xdg/autostart', ['gsni-authenticator.desktop']),
                  ('/usr/share/applications', ['gsni-authenticator.desktop'])
                  ]
      )
