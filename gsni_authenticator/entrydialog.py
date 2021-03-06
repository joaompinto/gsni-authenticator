# -*- coding: utf-8 -*-
#!/usr/bin/env python

# http://stackoverflow.com/a/8303883/401041

import gtk
class EntryDialog(gtk.MessageDialog):
    def __init__(self, *args, **kwargs):
        '''
        Creates a new EntryDialog. Takes all the arguments of the usual
        MessageDialog constructor plus one optional named argument
        "default_value" to specify the initial contents of the entry.
        '''
        if 'visibility' in kwargs:
            visibility = kwargs['visibility']
            del kwargs['visibility']
        else:
            visibility = True
        if 'default_value' in kwargs:
            default_value = kwargs['default_value']
            del kwargs['default_value']
        else:
            default_value = ''
        super(EntryDialog, self).__init__(*args, **kwargs)
        self.set_skip_taskbar_hint(False)
        entry = gtk.Entry()
        entry.set_text(str(default_value))
        entry.set_visibility(visibility)
        entry.connect("activate",
                      lambda ent, dlg, resp: dlg.response(resp),
                      self, gtk.RESPONSE_OK)
        self.vbox.pack_end(entry, True, True, 0)
        self.vbox.show_all()
        self.entry = entry
    def set_value(self, text):
        self.entry.set_text(text)
    def run(self):
        result = super(EntryDialog, self).run()
        if result == gtk.RESPONSE_OK:
            text = self.entry.get_text()
        else:
            text = None
        return text
