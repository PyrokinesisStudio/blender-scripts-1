import bpy
import sys
import os
import logging

try:
    from PyQt5 import QtWidgets, QtCore
except ImportError:
    raise ImportError('Cannot find the PyQt module')

logger = logging.getLogger('qtutils')


class QtWindowEventLoop(bpy.types.Operator):
    '''
    This class is a modal operator that behave like QEventLoop and allows
    PyQt to run inside Blender.
    '''

    bl_idname = 'screen.qt_event_loop'
    bl_label = 'PyQt Event Loop'

    def __init__(self, widget, *args, **kwargs):
        self._widget = widget
        self._args = args
        self._kwargs = kwargs

    def modal(self, context, event):
        wm = context.window_manager

        if not self.widget.isVisible():
            # if widget is closed
            logger.debug('finish modal operator')
            wm.event_timer_remove(self._timer)
            return {'FINISHED'}
        else:
            logger.debug('process the events for Qt window')
            self.event_loop.processEvents()
            self.app.sendPostedEvents(None, 0)

        return {'PASS_THROUGH'}

    def execute(self, context):
        logger.debug('execute operator')

        self.app = QtWidgets.QApplication.instance()
        # instance() gives the possibility to have multiple windows
        # and close it one by one

        if not self.app:
            # create the first instance
            self.app = QtWidgets.QApplication(['blender'])

        if 'stylesheet' in self._kwargs:
            stylesheet = self._kwargs['stylesheet']
            self.set_stylesheet(self.app, stylesheet)

        self.event_loop = QtCore.QEventLoop()
        self.widget = self._widget(*self._args, **self._kwargs)

        logger.debug(self.app)
        logger.debug(self.widget)

        # run modal
        wm = context.window_manager
        self._timer = wm.event_timer_add(1/120, context.window)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def set_stylesheet(self, app, filepath):
        file_qss = QtCore.QFile(filepath)
        if file_qss.exists():
            file_qss.open(QtCore.QFile.ReadOnly)
            stylesheet = QtCore.QTextStream(file_qss).readAll()
            app.setStyleSheet(stylesheet)
            file_qss.close()
