# simple wx console

import wx
import Queue

class Console(wx.Frame):
    def __init__(self, *args, **kwargs):
        self.input_queue = kwargs.pop('input_queue')
        self.output_queue = kwargs.pop('output_queue')
        wx.Frame.__init__(self, *args, **kwargs)

        self.output = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.input = wx.TextCtrl(self, -1, style=wx.TE_PROCESS_ENTER)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.output, 1, wx.EXPAND)
        sizer.Add((5, 5))
        sizer.Add(self.input, 0, wx.EXPAND)

        self.input.Bind(wx.EVT_TEXT_ENTER, self.on_input)
        self.Bind(wx.EVT_IDLE, self.idle)

        self.SetSizer(sizer)
        self.Show()

    def on_input(self, evt):
        print "got", self.input.Value
        self.input_queue.put(self.input.Value)
        self.output_queue.put("> " + self.input.Value)
        self.input.Value = ""

    def idle(self, evt):
        try:
            line = self.output_queue.get(True, 0.05)
        except Queue.Empty:
            pass
        else:
            self.output.Value += "\n%s" % line


def start_console(input_queue, output_queue):
    app = wx.App(False)
    frame = Console(None, title="test", input_queue=input_queue, output_queue=output_queue)
    app.MainLoop()

if __name__ == '__main__':
    start_console(1, 2)
