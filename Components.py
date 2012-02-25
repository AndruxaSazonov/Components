import wx
import math
import cPickle

exit_MENU  = wx.NewId()
about_MENU = wx.NewId()
help_MENU  = wx.NewId()
open_MENU  = wx.NewId()
save_MENU  = wx.NewId()

Component_Width  = 100
Component_Height = 60
Positive = "Positive"
Neutral  = "Neutral"
Negative = "Negative"

class Component:
    def __init__(self, x, y, selected = False):
        self.x = x
        self.y = y
        self.selected = selected
        self.text = "New"
        self.costs = 0
        self.income = 0
        self.duration = 1
        self.labour = 0
        self.start_month = 0
        self.scenarios = [Positive, Neutral, Negative]
        self.group = "New group"

class Months:
    def __init__(self, components):
        self.components = components
    def getMaxMonth(self):
        if 0 == len(self.components):
            return 0
        max = self.components[0].start_month
        for i in self.components:
            if (i.start_month + i.duration) > max:
                max = i.start_month + i.duration
        return max
        
    def getMinMonth(self):
        if 0 == len(self.components):
            return 0
        min = self.components[0].start_month
        for i in self.components:
            if i.start_month < min:
                min = i.start_month
        return min
        
    def getMonthFinRes(self, month):
        finres = 0.0
        for i in self.components:
            duration = i.duration
            if duration == 0: duration = 1
            if (i.start_month <= month) and ((i.start_month + i.duration) > month):
                fr = float((i.income - i.costs))/duration
                p1 = Positive in i.scenarios
                p2 = Neutral  in i.scenarios
                p3 = Negative in i.scenarios
                finres = finres + (float(p1)/6+4*float(p2)/6+float(p3)/6)*fr
        return finres
        
    def getMonthLabour(self, month):
        labour = 0
        for i in self.components:
            duration = i.duration
            if duration == 0: duration = 1
            if (i.start_month <= month) and ((i.start_month + i.duration) > month):
                p1 = Positive in i.scenarios
                p2 = Neutral  in i.scenarios
                p3 = Negative in i.scenarios
                labour = labour + float(i.labour)*(float(p1)/6+4*float(p2)/6+float(p3)/6)/duration
        return labour

    def costs_at(self, month):
        cos = 0
        for i in self.components:
            duration = i.duration
            if duration == 0: duration = 1
            if (i.start_month <= month) and ((i.start_month + i.duration) > month):
                c =  float(i.costs)/duration
                p1 = Positive in i.scenarios
                p2 = Neutral  in i.scenarios
                p3 = Negative in i.scenarios
                cos = cos + (float(p1)/6+4*float(p2)/6+float(p3)/6)*c
        return cos
    
    def getFinResultAndROI(self):
        pfr = 0
        roi = 0
        cos = 0
        for i in xrange(self.getMinMonth(), self.getMaxMonth()):
            pfr = pfr + float(self.getMonthFinRes(i))
            cos = cos + float(self.costs_at(i))
        if cos <> 0: roi = pfr/cos
        return [pfr, roi]
        
    def getLossesProbability(self, pfr):
        groups = {}
        disp = 0.0
        for i in self.components:
            if groups.has_key(i.group):
                if len(groups[i.group])==0: groups[i.group]=[]
            else:
                groups[i.group] = []
            groups[i.group].append(i)
        
        for h in groups.keys():
            gr = groups[h]
            posfr = 0
            neufr = 0
            negfr = 0
            for j in gr:
                if Positive in j.scenarios:
                    posfr = posfr + float(j.income) - j.costs
                if Neutral  in j.scenarios:
                    neufr = neufr + float(j.income) - j.costs
                if Negative in j.scenarios:
                    negfr = negfr + float(j.income) - j.costs
            medfr = float(posfr)/6 + 4*float(neufr)/6 + float(negfr)/6
            disp = disp + math.pow(posfr-medfr,2)/6 + 4*math.pow(neufr-medfr,2)/6 + math.pow(negfr-medfr,2)/6
        if disp == 0:
            return 0
        return 1/math.pow(pfr/math.sqrt(disp),2)/2
            

class Roadmap(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(Roadmap, self).__init__(*args, **kwargs)

class Profile(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(Profile, self).__init__(*args, **kwargs)
    
class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title,
                          pos=(100, 100), size=(800, 600))

        menuBar = wx.MenuBar()

        mainmenu = wx.Menu()
        helpmenu = wx.Menu()

        mainmenu.Append(open_MENU,  "&Open...", "Open saved file")
        mainmenu.Append(save_MENU,  "&Save as...", "Save current work")
        mainmenu.AppendSeparator()
        mainmenu.Append(exit_MENU,  "E&xit\tAlt-X", "Exit program")
        helpmenu.Append(help_MENU,  "&Help", "Help about work in program")
        helpmenu.Append(about_MENU, "&About", "About program")

        self.Bind(wx.EVT_MENU, self.OnTimeToClose, id=exit_MENU)
        self.Bind(wx.EVT_MENU, self.OnTimeToAbout, id=about_MENU)
        self.Bind(wx.EVT_MENU, self.OnHelpMenu,    id=help_MENU)
        self.Bind(wx.EVT_MENU, self.onLoad,        id=open_MENU)
        self.Bind(wx.EVT_MENU, self.onSave,        id=save_MENU)

        menuBar.Append(mainmenu, "&File")
        menuBar.Append(helpmenu, "&Help")
        self.SetMenuBar(menuBar)

        self.CreateStatusBar()

        notebook = wx.Notebook(self)
        
        self.roadmap = Roadmap(notebook)
        self.profile = Profile(notebook)
    
        notebook.AddPage(self.roadmap,'Roadmap')
        notebook.AddPage(self.profile,'Profile')        

        self.SetMaxSize([800, 600])
        self.SetMinSize([800, 600])
        
        self.drawPanel = wx.Window(self.roadmap, -1, style=wx.BORDER_NONE | wx.FULL_REPAINT_ON_RESIZE)
        self.drawPanel.SetBackgroundColour(wx.WHITE)
        self.drawPanel.SetSize([self.GetClientSize().x - 10, self.GetClientSize().y - 30])
        self.drawPanel.Bind(wx.EVT_PAINT, self.onPaint)
        
        self.drawPanel.Bind(wx.EVT_MOUSE_EVENTS, self.onRoadmapMouseEvent)
        self.cur_obj = None
        self.last_menuPt = None
        self.components = []
        
        self.plotPanel = wx.Panel(self.profile, -1, style=wx.BORDER_NONE | wx.FULL_REPAINT_ON_RESIZE)
        self.plotPanel.Bind(wx.EVT_PAINT, self.onProfilePaint)
        self.plotPanel.SetBackgroundColour(wx.WHITE)
        self.plotPanel.SetSize([self.GetClientSize().x - 10, self.GetClientSize().y - 30])
        
    def onLoad(self, event):
        filename = wx.FileSelector("Open File", default_extension="cmp", \
                                  flags = wx.OPEN | wx.FILE_MUST_EXIST)
        if filename == "": return
        try:
            f = open (filename, "rb")
            self.components = cPickle.load(f)
            f.close()
        except:
            wx.MessageBox("Unable to load " + filename + ".", "Error", wx.OK|wx.ICON_ERROR, self)
        self.Refresh()
        
    def onSave(self, event):
        filename = wx.FileSelector("Save File As", "Saving", \
                                          default_extension="cmp",\
                                          wildcard="*.cmp",\
                                          flags = wx.SAVE | wx.OVERWRITE_PROMPT)
        if filename == "": return
        try:
            f = open(filename, "wb")
            cPickle.dump(self.components, f)
            f.close()
        except:
            wx.MessageBox("Unable to save " + filename + ".", "Error", wx.OK|wx.ICON_ERROR, self)
    
    def onProfilePaint(self, event):
        dc = wx.PaintDC(self.plotPanel)
        
        months = Months(self.components)
        min = months.getMinMonth()
        max = months.getMaxMonth()
        maxFR = 0
        frpts = []
        maxLB = 0
        lbpts = []
        for x in xrange(min, max):
            fr = months.getMonthFinRes(x)
            if self.abs(fr) > maxFR: maxFR = abs(fr)
            frpts.append(fr)
            lb = months.getMonthLabour(x)
            if self.abs(lb) > maxLB: maxLB = abs(lb)
            lbpts.append(lb)
        self.plotPanel.PrepareDC(dc)
        dc.BeginDrawing()
        dc.DrawLine(10, self.plotPanel.GetClientSize().y-10, 10, 10)
        dc.DrawLine(10, (self.plotPanel.GetClientSize().y-10)/2, self.plotPanel.GetClientSize().x-10, (self.plotPanel.GetClientSize().y-10)/2)
        prevx = 10
        prevy = (self.plotPanel.GetClientSize().y-10)/2
        brevx = 10
        brevy = (self.plotPanel.GetClientSize().y-10)/2
        if maxFR < 1: maxFR = 1
        if maxLB < 1: maxLB = 1
        dc.SetTextBackground(wx.WHITE)
        for i in xrange(0, len(frpts)):
            dc.SetPen(wx.GREEN_PEN)
            dc.DrawLine(prevx, prevy, \
                        10+(i+1)*(self.plotPanel.GetClientSize().x-10)/len(frpts), \
                        (self.plotPanel.GetClientSize().y-10)/2-(self.plotPanel.GetClientSize().y-20)*frpts[i]/2/maxFR)
            prevx=10+(i+1)*(self.plotPanel.GetClientSize().x-10)/len(frpts)
            prevy=(self.plotPanel.GetClientSize().y-10)/2-(self.plotPanel.GetClientSize().y-20)*frpts[i]/2/maxFR
            dc.SetTextForeground(wx.RED)
            dc.DrawText("%0.1f"%frpts[i], prevx - 30, prevy)
            
            dc.SetPen(wx.CYAN_PEN)
            dc.DrawLine(brevx, brevy, \
                        10+(i+1)*(self.plotPanel.GetClientSize().x-10)/len(lbpts), \
                        (self.plotPanel.GetClientSize().y-10)/2-(self.plotPanel.GetClientSize().y-20)*lbpts[i]/2/maxLB)
            brevx=10+(i+1)*(self.plotPanel.GetClientSize().x-10)/len(lbpts)
            brevy=(self.plotPanel.GetClientSize().y-10)/2-(self.plotPanel.GetClientSize().y-20)*lbpts[i]/2/maxLB
            dc.SetTextForeground(wx.BLUE)
            dc.DrawText("%0.1f"%lbpts[i], brevx - 30, brevy + 14)

            dc.SetTextForeground(wx.BLACK)
            dc.DrawText(str(i), brevx, (self.plotPanel.GetClientSize().y-10)/2+2)
            dc.SetPen(wx.BLACK_PEN)
            dc.DrawLine(brevx, (self.plotPanel.GetClientSize().y-10)/2-2, brevx, (self.plotPanel.GetClientSize().y-10)/2+2)
        dc.EndDrawing()
        res = months.getFinResultAndROI()
        prob = months.getLossesProbability(res[0])
        if prob < 0.5:
            self.GetStatusBar().SetStatusText("Financial result = %0.3f" % res[0] + "; ROI = %0.3f" % res[1] + "; Losses probability: %0.3f" % prob)
        else:
            self.GetStatusBar().SetStatusText("Financial result = %0.3f" % res[0] + "; ROI = %0.3f" % res[1] + "; Losses probability > 50%")
                
    def onPaint(self, event):
        dc = wx.PaintDC(self.drawPanel)
        self.drawComponents(dc)
        self.GetStatusBar().SetStatusText("Use right click to add or delete components or double click to edit")
    
    def abs(self, x):
        if x > 0: return x
        else: return -x

    def have_collision(self, x1, y1, x2, y2):
        if (self.abs(x1-x2) < Component_Width) and (self.abs(y1-y2) < Component_Height): return True
        return False
        
    def collides(self, obj, x, y):
        for i in self.components:
            if i is not obj:
                if self.have_collision(i.x,i.y,x,y): return True
        if (x < 0) or (y < 0) or (x + Component_Width > self.drawPanel.GetClientSize().x) or (y + Component_Height > self.drawPanel.GetClientSize().y):
            return True
        return False

    def onRoadmapMouseEvent(self, event):   
        if event.GetEventType() == wx.EVT_LEFT_DOWN.evtType[0]:
            obj = self.getObjectAt([event.X, event.Y])
            if (obj is None): 
                for i in self.components:
                    if i.selected: i.selected = False
                self.Refresh()
                return
            self.startPt = [event.X,event.Y]
            self.cur_obj = obj
            for j in self.components:
                j.selected = False
            self.cur_obj.selected = True
            self.deltax = event.X - obj.x
            self.deltay = event.Y - obj.y
            self.Refresh()
            return
        if event.GetEventType() == wx.EVT_MOTION.evtType[0]:
            if (self.cur_obj is None): return
            if (not self.collides(self.cur_obj, event.X - self.deltax, event.Y - self.deltay)):
                self.cur_obj.x = event.X - self.deltax
                self.cur_obj.y = event.Y - self.deltay
                self.Refresh()
            return
        if event.GetEventType() == wx.EVT_LEFT_UP.evtType[0]:
            self.cur_obj = None
        if event.RightDown():
            self.last_mouse_event = event
            self.doPopupContextMenu(event)
            return
        if event.GetEventType() == wx.EVT_LEFT_DCLICK.evtType[0]:
            obj = self.getObjectAt([event.X, event.Y])
            if (obj is None): return
            self.clicked_object = obj
            self.OnEditComponent(event)
            pass
            
    def OnAddNewComponent(self, event):
        self.components.append(Component(self.last_mouse_event.X, self.last_mouse_event.Y))
        self.Refresh()
        
    def scenarios_condition(self, i, j):
        if (i == j):
            return True
        for x in self.components[i].scenarios:
            if x in self.components[j].scenarios:
                return True
        return False

    def exists_medium(self, i, j):
        for x in xrange(0,len(self.components)):
            if (self.components[i].start_month < self.components[x].start_month and \
               self.components[j].start_month > self.components[x].start_month):
               return True
        return False

    def connect_condition(self, i, j):
        if (i == j):
            return False
        return self.components[i].start_month <> self.components[j].start_month and \
        not self.exists_medium(i,j) and \
        self.components[i].group == self.components[j].group

    def drawComponents(self, dc = None):
        if not dc: 
            dc = wx.ClientDC(self.drawPanel)
        self.drawPanel.PrepareDC(dc)
        dc.BeginDrawing()
        for i in xrange(0,len(self.components)):
            for j in xrange(i, len(self.components)):
                if self.connect_condition(i,j) and self.scenarios_condition(i,j):
                    dc.DrawLine(self.components[i].x+Component_Width/2, \
                                self.components[i].y+Component_Height/2,\
                                self.components[j].x+Component_Width/2, \
                                self.components[j].y+Component_Height/2)
        for i in self.components:
            if (i.selected):
                dc.SetBrush(wx.GREY_BRUSH)
            else:
                dc.SetBrush(wx.LIGHT_GREY_BRUSH)
            dc.DrawRectangle(i.x, i.y, Component_Width, Component_Height)
            if   (Positive in i.scenarios):
                 dc.SetBrush(wx.BLUE_BRUSH)
                 dc.DrawRectangle(i.x + Component_Width - 10, i.y + Component_Height - 10, 10, 10)
            elif (Neutral in i.scenarios):
                 dc.SetBrush(wx.GREEN_BRUSH)
                 dc.DrawRectangle(i.x + Component_Width - 10, i.y + Component_Height - 10, 10, 10)
            elif (Negative in i.scenarios):
                 dc.SetBrush(wx.RED_BRUSH)
                 dc.DrawRectangle(i.x + Component_Width - 10, i.y + Component_Height - 10, 10, 10)
            dc.DrawText(i.text[0:10], i.x + 2, i.y+10)
            dc.DrawText("Month: " + str(i.start_month), i.x + 2, i.y + 25)
            dc.DrawText(i.group[0:10], i.x + 2, i.y + 40)
        dc.EndDrawing()
        
    def OnDeleteComponent(self, event):
        if self.last_menuPt is None: return
        obj = self.getObjectAt([self.last_menuPt[0], self.last_menuPt[1]])
        if obj is None: return
        for x in xrange(0, len(self.components)):
            if self.components[x] is obj:
                del self.components[x]
                self.last_menuPt = None
                self.Refresh()
                return

    def getObjectAt(self, point):
        x = point[0]
        y = point[1]
        for i in self.components:
            if (x > i.x) and (x < i.x + Component_Width) and (y > i.y) and (y < i.y + Component_Height):
                return i
        return None
        
    def OnEditComponent(self, event):
        dialog = wx.Dialog(self, -1, "Edit component", style=wx.DIALOG_MODAL)
        dialog.SetBackgroundColour(wx.WHITE)

        panel = wx.Panel(dialog, -1)
        panel.SetBackgroundColour(wx.WHITE)

        panelSizer = wx.GridSizer(rows = 7, cols = 2, vgap = 10, hgap = 10)
        
        obj = None
        if self.clicked_object is not None:
                obj = self.clicked_object
        else: 
            return

        lab2 = wx.StaticText(panel, label = "Component Name")
        inp2 = wx.TextCtrl(panel, value = str(obj.text))
        inp2.SetMaxLength(10)
        lab3 = wx.StaticText(panel, -1, "Component income")
        inp3 = wx.TextCtrl(panel, value = str(obj.income))
        lab4 = wx.StaticText(panel, -1, "Component Costs")
        inp4 = wx.TextCtrl(panel, value = str(obj.costs))
        lab5 = wx.StaticText(panel, -1, "Component Labour costs (men/months)")
        inp5 = wx.TextCtrl(panel, value = str(obj.labour))        
        lab6 = wx.StaticText(panel, -1, "Component Duration")        
        inp6 = wx.TextCtrl(panel, value = str(obj.duration))        
        lab7 = wx.StaticText(panel, -1, "Component Start (month number)")
        inp7 = wx.TextCtrl(panel, value = str(obj.start_month))
        lab8 = wx.StaticText(panel, -1, "Component group")
        inp8 = wx.TextCtrl(panel, value = obj.group)
        inp8.SetMaxLength(10)
        CBPos = wx.CheckBox(panel, label = "Positive scenario")
        CBPos.SetValue(Positive in obj.scenarios)        
        CBNeu = wx.CheckBox(panel, label = "Neutral scenario")
        CBNeu.SetValue(Neutral in obj.scenarios)
        CBNeg = wx.CheckBox(panel, label = "Negative scenario")
        CBNeg.SetValue(Negative in obj.scenarios)
        btnCN = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btnOK = wx.Button(panel, wx.ID_OK, "OK")

        panelSizer.Add(lab2, flag = wx.EXPAND)
        panelSizer.Add(inp2, flag = wx.EXPAND)
        panelSizer.Add(lab3, flag = wx.EXPAND)
        panelSizer.Add(inp3, flag = wx.EXPAND)
        panelSizer.Add(lab4, flag = wx.EXPAND)
        panelSizer.Add(inp4, flag = wx.EXPAND)
        panelSizer.Add(lab5, flag = wx.EXPAND)
        panelSizer.Add(inp5, flag = wx.EXPAND)
        panelSizer.Add(lab6, flag = wx.EXPAND)
        panelSizer.Add(inp6, flag = wx.EXPAND)
        panelSizer.Add(lab7, flag = wx.EXPAND)
        panelSizer.Add(inp7, flag = wx.EXPAND)
        panelSizer.Add(lab8,  flag = wx.EXPAND)
        panelSizer.Add(inp8,  flag = wx.EXPAND)
        
        panelSizer.Add(CBPos, flag = wx.EXPAND)
        panelSizer.Add((1,1))                
        panelSizer.Add(CBNeu, flag = wx.EXPAND)
        panelSizer.Add((1,1))
        panelSizer.Add(CBNeg, flag = wx.EXPAND)
        panelSizer.Add((1,1))
                
        panelSizer.Add(btnCN, 0, wx.ALL | wx.ALIGN_LEFT,  5)
        panelSizer.Add(btnOK, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        panel.SetAutoLayout(True)
        panel.SetSizer(panelSizer)
        panelSizer.Fit(panel)

        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(panel, 0, wx.ALL, 10)

        dialog.SetAutoLayout(True)
        dialog.SetSizer(topSizer)
        topSizer.Fit(dialog)
        
        dialog.Centre()

        btn = dialog.ShowModal()
        dialog.Destroy()
        if btn == wx.ID_OK:
            obj.text = inp2.GetValue()
            try: obj.costs = float(inp4.GetValue())
            except: obj.costs = 0
            try: obj.income = float(inp3.GetValue())
            except: obj.income = 0
            try: obj.duration = int(inp6.GetValue())
            except: obj.duration = 0
            try: obj.labour = float(inp5.GetValue())
            except: obj.labour = 0
            try: obj.start_month = int(inp7.GetValue())
            except: obj.start_month = 0
            obj.scenarios = []
            if CBPos.GetValue(): obj.scenarios.append(Positive)
            if CBNeu.GetValue(): obj.scenarios.append(Neutral)
            if CBNeg.GetValue(): obj.scenarios.append(Negative)
            obj.group = inp8.GetValue()       
        self.clicked_obj = None
        self.Refresh()
        
    def doPopupContextMenu(self, event):
        mousePt = [event.X, event.Y]
        obj = self.getObjectAt(mousePt)
        
        menu = wx.Menu()
        menu_NEW = wx.NewId()
        menu_EDIT = wx.NewId()
        menu_DELETE = wx.NewId()
        menu.Append(menu_NEW, "Add")
        menu.Append(menu_EDIT, "Edit")
        menu.AppendSeparator()
        menu.Append(menu_DELETE, "Delete")
        
        menu.Enable(menu_NEW, not self.collides(None, event.X, event.Y))
        menu.Enable(menu_EDIT, obj is not None)   
        menu.Enable(menu_DELETE, obj is not None)     

        self.clicked_object = obj
        
        self.Bind(wx.EVT_MENU, self.OnAddNewComponent,   id=menu_NEW)
        self.Bind(wx.EVT_MENU, self.OnEditComponent,     id=menu_EDIT)
        self.Bind(wx.EVT_MENU, self.OnDeleteComponent,   id=menu_DELETE)
        
        clickPt = wx.Point(mousePt[0] + self.drawPanel.GetPosition().x,
                          mousePt[1] + self.drawPanel.GetPosition().y)
        if (obj is not None):
            self.last_menuPt = [mousePt[0], mousePt[1]]
        self.drawPanel.PopupMenu(menu, mousePt)
        menu.Destroy()

    def OnTimeToClose(self, evt):
        self.Close()
        
    def OnTimeToAbout(self, evt):
        dialog = wx.Dialog(self, -1, "About Components") #, style=wx.DIALOG_MODAL | wx.STAY_ON_TOP)
        dialog.SetBackgroundColour(wx.WHITE)

        panel = wx.Panel(dialog, -1)
        panel.SetBackgroundColour(wx.WHITE)

        panelSizer = wx.BoxSizer(wx.VERTICAL)

        boldFont = wx.Font(panel.GetFont().GetPointSize(),
                          panel.GetFont().GetFamily(),
                          wx.NORMAL, wx.BOLD)

        lab1 = wx.StaticText(panel, -1, "Components")
        lab1.SetFont(wx.Font(36, boldFont.GetFamily(), wx.ITALIC, wx.BOLD))
        lab1.SetSize(lab1.GetBestSize())

        imageSizer = wx.BoxSizer(wx.HORIZONTAL)
        imageSizer.Add(lab1, 0, wx.ALL | wx.ALIGN_CENTRE_VERTICAL, 5)

        lab2 = wx.StaticText(panel, -1, "A simple cost-profit profiling " + \
                                       "program. Version 0.2")
        lab2.SetFont(boldFont)
        lab2.SetSize(lab2.GetBestSize())

        lab3 = wx.StaticText(panel, -1, "Components is completely free " + \
                                       "software; please")
        lab3.SetFont(boldFont)
        lab3.SetSize(lab3.GetBestSize())

        lab4 = wx.StaticText(panel, -1, "feel free to use this " + \
                                       "in any way you like.")
        lab4.SetFont(boldFont)
        lab4.SetSize(lab4.GetBestSize())

        lab5 = wx.StaticText(panel, -1,
                             "Author: Sazonov Andrey " + \
                             "(sazonov.andrey@gmail.com)\n")

        lab5.SetFont(boldFont)
        lab5.SetSize(lab5.GetBestSize())

        btnOK = wx.Button(panel, wx.ID_OK, "OK")

        panelSizer.Add(imageSizer, 0, wx.ALIGN_CENTRE)
        panelSizer.Add((10, 10)) # Spacer.
        panelSizer.Add(lab2, 0, wx.ALIGN_CENTRE)
        panelSizer.Add((10, 10)) # Spacer.
        panelSizer.Add(lab3, 0, wx.ALIGN_CENTRE)
        panelSizer.Add(lab4, 0, wx.ALIGN_CENTRE)
        panelSizer.Add((10, 10)) # Spacer.
        panelSizer.Add(lab5, 0, wx.ALIGN_CENTRE)
        panelSizer.Add((10, 10)) # Spacer.
        panelSizer.Add(btnOK, 0, wx.ALL | wx.ALIGN_CENTRE, 5)

        panel.SetAutoLayout(True)
        panel.SetSizer(panelSizer)
        panelSizer.Fit(panel)

        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(panel, 0, wx.ALL, 10)

        dialog.SetAutoLayout(True)
        dialog.SetSizer(topSizer)
        topSizer.Fit(dialog)

        dialog.Centre()

        btn = dialog.ShowModal()
        dialog.Destroy()

    def OnHelpMenu(self, evt):
        dialog = wx.Dialog(self, -1, "Components help") #, style=wx.DIALOG_MODAL | wx.STAY_ON_TOP)
        dialog.SetBackgroundColour(wx.WHITE)

        panel = wx.Panel(dialog, -1)
        panel.SetBackgroundColour(wx.WHITE)

        panelSizer = wx.BoxSizer(wx.VERTICAL)

        lab1 = wx.StaticText(panel, -1, \
"""You enter components (projects maybe or programs). Each component has properties.
Properties such as income, costs and labour are divided uniformly during 'duration'.
Blue rectangle means that positive scenario is checked for component, green - 
neutral, and red - for negative scenario only. Connection between components
only in case if they are sequenced by start month and they have one or more
common scenarios. If no scenario selected for component - this component is
not calculated in result. Component group means group of independent from 
each other groups of components (like independent projects). Independent
groups' components cannot be connected with line. Look at the status bar on 
the profile canvas, to find the integral results of calculations. Also on the
profile panel, by green is shown financial result at month, and in blue - the
labour. Good luck in modelling!""")
        lab1.SetSize(lab1.GetBestSize())

        btnOK = wx.Button(panel, wx.ID_OK, "OK")

        panelSizer.Add(lab1, 0, wx.ALIGN_LEFT)

        panel.SetAutoLayout(True)
        panel.SetSizer(panelSizer)
        panelSizer.Fit(panel)

        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(panel, 0, wx.ALL, 10)

        dialog.SetAutoLayout(True)
        dialog.SetSizer(topSizer)
        topSizer.Fit(dialog)

        dialog.Centre()

        btn = dialog.ShowModal()
        dialog.Destroy()
        
        
class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "Components")
        self.SetTopWindow(frame)
        frame.Show(True)
        return True
        
app = MyApp(redirect=False)
app.MainLoop()
