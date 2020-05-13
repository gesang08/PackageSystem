#!/usr/bin/env python
# _*_ coding: UTF-8 _*

import wx
import wx.aui as aui
class MyFrame(wx.Frame):
    def __init__(self, parent, id=-1, title='wx.aui Test',
                 pos=wx.DefaultPosition, size=(800, 600),
                 style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        self._mgr = wx.aui.AuiManager(self)

        # create several text controls
        text1 = wx.TextCtrl(self, -1, 'Pane 1 - sample text',
                            wx.DefaultPosition, wx.Size(200, 150),
                            wx.NO_BORDER | wx.TE_MULTILINE)

        text2 = wx.TextCtrl(self, -1, 'Pane 2 - sample text',
                            wx.DefaultPosition, wx.Size(200, 150),
                            wx.NO_BORDER | wx.TE_MULTILINE)

        text3 = wx.TextCtrl(self, -1, 'Main content window',
                            wx.DefaultPosition, wx.Size(200, 150),
                            wx.NO_BORDER | wx.TE_MULTILINE)

        # add the panes to the manager
        self._mgr.AddPane(text1, wx.aui.AuiPaneInfo().Left().MaximizeButton(True))
        self._mgr.AddPane(text2, wx.aui.AuiPaneInfo().Bottom().MaximizeButton(True))
        self._mgr.AddPane(text3, wx.aui.AuiPaneInfo().Center())

        # Create toolbar
        toolbar = wx.ToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize,
                             wx.TB_FLAT | wx.TB_NODIVIDER | wx.TB_HORZ_TEXT)
        toolbar.SetToolBitmapSize(wx.Size(16, 16))
        toolbar_bmp1 = wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, wx.Size(16, 16))
        toolbar.AddTool(101, "Item 1", toolbar_bmp1)
        toolbar.AddTool(101, "Item 2", toolbar_bmp1)
        toolbar.AddTool(101, "Item 3", toolbar_bmp1)
        toolbar.AddTool(101, "Item 4", toolbar_bmp1)
        toolbar.AddSeparator()
        toolbar.AddTool(101, "Item 5", toolbar_bmp1)
        toolbar.AddTool(101, "Item 6", toolbar_bmp1)
        toolbar.AddTool(101, "Item 7", toolbar_bmp1)
        toolbar.AddTool(101, "Item 8", toolbar_bmp1)
        toolbar.Realize()
        self._mgr.AddPane(toolbar,
                          wx.aui.AuiPaneInfo().Name("toolbar").Caption("Toolbar Demo").ToolbarPane().Top().LeftDockable(
                              False).RightDockable(False))

        # tell the manager to 'commit' all the changes just made
        self._mgr.Update()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, event):
        # deinitialize the frame manager
        self._mgr.UnInit()
        # delete the frame
        self.Destroy()


if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame(None)
    frame.Show()
    app.MainLoop()
