# mm-des - discrete event simulator
# - base events: Generator,Service,Sink,ConditionalEvent
# - bpmn events: Start,Task,End,Timer,XorGate,AndGate,Condition,Terminate
# MM 31.1.2024, 13.9.2025 (adopted for pyodide in js)

# ---- simulation on an abstract event ----
class Event():
      cnt = 0                         # used for event identifier
      def __init__(self, time, name=None):
            self.time = time;
            Event.cnt += 1
            self.id = Event.cnt
            self.name = ((name==None) and "Event" or name) + "_"+str(self.id)
      def exec(self, sim): pass      # abstract 
      def __str__(self):
            return self.name+ " "+ str(self.id) +" "+str(self.time)
class Simulator():
      def __init__(self):
            self.time = 0
            self.events = []
            self.conditions = []
      def now(self):
            return self.time
      def add(self,e):
            self.events.append(e)
            return(self)
      def add_condition(self,e):
            self.conditions.append(e)
            return(self)
      def run(self):
            while self.events:
                  e = min(self.events, key=lambda e: e.time)
                  self.events.remove(e)
                  self.time = e.time         # update simulator time
                  e.exec(self)
                  for c in self.conditions:  # test conditions
                        if c.exec(self):
                              self.conditions.remove(c)
# ---- utils ----
import math,random
def _print(s):                # own print
      #print(s)               # comment if no verbous printing
      pass
def E(mean=[1.0]):            # exponential random generator
      # -mean[0]*math.log(random.random())
      return random.expovariate(1/mean[0]) 
def U(minmax=[1.0]):          # uniform random generator
      return random.uniform(minmax[0],len(minmax)>1 and minmax[1] or minmax[0])
def N(meanstd=[3.0]):        # gaussian random generator
      return random.normalvariate(meanstd[0],len(meanstd)>1 and meanstd[1] or 1.0)
def B(p=0.5):                # binomial (0,1)
      return random.random()<p
def C(p=[1,1,1]):            # choice (0,1,2,...)
      return random.choices(list(range(len(p))),weights=p)[0]
def T(minmax=[1.0]):          # semi truncated gaussian random generator
      mi,ma = minmax[0],len(minmax)>1 and minmax[1] or minmax[0]
      mean,std = (ma+mi)/2,(ma-mi)/2
      while True:
            x = N([mean,std])
            if mi <= x <= ma: break
      return x

# ---- primitive classes ----
class Customer():    # anonymous customer with a automatic name
      cnt = 0        # counter class variable for customer name
      def __init__(self):
            Customer.cnt += 1
            self.name = str(Customer.cnt)
            self.attr = {"cname":self.name} # Customer attributes
      def __str__(self):
            return str(self.name)
class Queue():       # fifo of customers
      def __init__(self):
            self.objects = []
      def push(self,obj):
            self.objects.append(obj)
      def pop(self):
            return self.objects.pop(0)
      def __len__(self):
            return len(self.objects)
      def __str__(self):
            return str([str(o) for o in self.objects])
class QueuedEvent(Event):
      instances=[]
      def __init__(self,name=None):
            Event.__init__(self,0.0,name)  # preinit time
            self.queue = Queue()      # own queue
            self.output = []          # no connected objects
            self.customer = None      # none being served
            QueuedEvent.instances.append(self)
      def setName(self,name):
            self.name=name+"_"+self.name.split("_")[1] #.replace("Event",name).replace("Activity",name)
      def out(self,sim):              # pass to connected objects
            if self.customer!=None:
                  if len(self.output)>0 and isinstance(self,XorGate):  
                        idx = 1  # send to second output
#                        if self.customer.attr["value"] or len(self.output)<2:
                        if ("value" in self.customer.attr and self.customer.attr["value"]) or len(self.output)<2:
                              idx=0 # send rather to first output
                        if len(self.output)>2:  # more than 2 outputs
                              idx=int(self.customer.attr["value"])
                        self.output[idx].insert(self.customer, sim)
                  else:
                        for i in range(len(self.output)):  # split to all
                              self.output[i].insert(self.customer, sim)
      def prev(self):
            ep=[]
            for e0 in QueuedEvent.instances:
                  for i in range(len(e0.output)):
                        if e0.output[i]==self:
                              ep.append(e0)
            return ep

# ---- basic model classes (QueueEvent derived) ----
class BpmnEvent(QueuedEvent):
      S = {}
      def __init__(self,name=None,code=None):
            QueuedEvent.__init__(self,name)
            self.fun,self.param,self.code = None,None,code
            self.A,self.pp,self.pp2,self.title = {"A.n":0},[-1,0],[-1,-1],''
      def _fun(self):
            p = self.param
            if isinstance(p,list):
                  p = [float(eval(self.attr_replace(str(s)))) for s in p]
            else:
                  p = float(eval(self.attr_replace(str(p))))
            #print("_fun:",self.fun,p,len(self.queue))
            return self.fun(p) if self.fun!=None else p
      def attr_replace(self,cc):
            if self.customer!=None:
                  for k,v in self.customer.attr.items():
                        cc = cc.replace(k,str(v))
            for k,v in BpmnEvent.S.items():
                  cc = cc.replace(k,str(v))
            for k,v in self.A.items():
                  cc = cc.replace(k,str(v))
            return cc
      def _eval(self,code,n=-1):
            codes=self.code.split(";")
            if n!=-1:
                  codes=len(codes)>n and [codes[n]] or []
            for code in codes:
                  cc = code.split("=")
                  cc[0] = cc[0].strip()
                  if len(cc)==1:
                        cc=["dummy"]+cc
                  if len(cc)>1:
                        cc[0] = len(cc[0])>0 and cc[0] or "value"
                        cc[1] = self.attr_replace("=".join(cc[1:])) # rejoin
                        try:
                              ev=eval(cc[1])
                              if cc[0].startswith("S."):
                                    BpmnEvent.S[cc[0]]=ev
                              elif cc[0].startswith("A."):
                                    self.E[cc[0]]=ev
                              else:
                                    self.customer.attr[cc[0]]=ev
                        except:
                              self.customer.attr[cc[0]]=False
class ConditionalEvent(BpmnEvent):
      def __init__(self, code=None):
            BpmnEvent.__init__(self, None, code)
      def insert(self, cust, sim):
            cust.attr["__t"+str(self.id)+"a"] = sim.now()
            cust.attr["__t"+str(self.id)+"e"] = -1
            if self.customer == None : # if free add to simulator conditions
                  self.customer = cust
                  self.customer.attr["value"]=False
                  self.customer.attr["__t"+str(self.id)+"b"] = sim.now()
                  sim.add_condition(self)
            else:
                  self.queue.push(cust)                                    
      def exec(self, sim):
            b = False
            if self.code!=None:
                  self._eval(self.code,0)
                  if self.customer.attr["value"]==True:
                        cc=self.code.split(';')
                        if len(cc)>1:
                              self._eval(";".join(cc[1:]))
                        self.customer.attr["__t"+str(self.id)+"e"] = sim.now()
                        self.out(sim)
                        self.customer = None    # mark that now the service is free !!!
                        if len(self.queue)>0 :  # but if anybody in queue
                              self.insert(self.queue.pop(), sim)  # get and insert into simulator
                        b = True  # ready to be removed from simulator conditions
            return b
class Generator(BpmnEvent):
      def __init__(self, fun, param, tmax=0.0, code=None):
            BpmnEvent.__init__(self, None, code)
            self.fun, self.param, self.tmax, self.n = fun, param, tmax, 0
            if self.code!=None :
                  self._eval(self.code)   # evaluate script code ([var]=<value>)
      def exec(self, sim):
            self.customer = Customer()
            self.customer.attr["__t"+str(self.id)+"a"] = sim.now()
            self.customer.attr["__t"+str(self.id)+"b"] = sim.now()
            self.customer.attr["__t"+str(self.id)+"e"] = sim.now()
            self.A["A.n"] += 1
            _print("Registering: " + str(self.customer) + " ("+str(self.time)+")")
            self.out(sim)             # pass customer to connected object
            self.time += self._fun()
            if self.tmax>0 and self.time <= self.tmax or self.n<-self.tmax-1:
                  self.n += 1
                  sim.add(self)       # next one in random time
class Service(BpmnEvent):
      def __init__(self, fun, param, code=None): 
            BpmnEvent.__init__(self,"Activity",code)  
            self.fun, self.param = fun, param 
            self.N = 1 # N number of tokens to wait (used for AndGate)
      def insert(self, cust, sim):
            if isinstance(self,XorGate):
                  if len(self.output)>1 and self.code==None:
                        self.code="=B(0.5)"
            if self.customer == None: # if free add to simulator with end time
                  self.customer,t = cust,self._fun()
                  if isinstance(t,list):  # [cycle,begin=0] cyclic timer (MM 1.11.2024)
                        if len(t)<2: t.append(0)
                        self.time = t[1]+math.ceil((sim.now()-t[1])/t[0])*t[0]
                        #_print("# "+str(self.customer)+": "+str(sim.now())+" "+str(self.time))
                  else:
                        self.time = sim.now() + t
                  _print("#"+str(self.id)+" starts serving "+
                         str(cust)+" ("+str(sim.now())+","+str(self.time)+")")
                  self.customer.attr["__t"+str(self.id)+"b"]=sim.now()
                  if "__n"+str(self.id) not in self.customer.attr:
                        self.customer.attr["__n"+str(self.id)] = 0 # first time
                  if "__t"+str(self.id)+"a" not in self.customer.attr:
                        cust.attr["__t"+str(self.id)+"a"]=sim.now() # if not from queue
                  if isinstance(self,Timer) and not isinstance(t,list):  # modify required final execution time
                        ta=cust.attr["__t"+str(self.id)+"a"]  
                        tb=cust.attr["__t"+str(self.id)+"b"]
                        cust.attr["__t"+str(self.id)+"b"] -= (tb-ta) # decrease begin time
                        self.time -= (tb-ta)  # ... by the difference elapsed already
                        #_print("# "+str(self.customer)+": "+str(self.time))
                  sim.add(self)
            else:                     # else insert into queue
                  cust.attr["__t"+str(self.id)+"a"]=sim.now()  # with a queue adding timstamp
                  self.queue.push(cust)
      def exec(self, sim):
            if self.customer!=None:
                  self.customer.attr["__t"+str(self.id)+"e"]=sim.now()
                  self.A["A.n"] += 1
            _print("#"+str(self.id)+" finished serving " + str(self.customer) + " at " + str(self.time))
            if self.code!=None :      
                  self._eval(self.code)   # evaluate script code ([var]=<value>)
            if self.customer!=None:
                  self.customer.attr["__n"+str(self.id)] += 1
                  if (self.customer.attr["__n"+str(self.id)]%self.N) == 0: #self.N:
                        self.out(sim)     # pass customer to connected object
            self.customer = None    # mark that now the service is free !!!
            if len(self.queue)>0 :  # but if anybody in queue
                  Service.insert(self,self.queue.pop(), sim)  # get and insert into simulator
class Sink(BpmnEvent):
      def insert(self, cust, sim):    
            _print("Sinking "+str(cust)+" : "+str(sim.now()))
            cust.attr["__t"+str(self.id)+"a"] = sim.now()  # mark time in customer attributes
            cust.attr["__t"+str(self.id)+"b"] = sim.now()  # mark time in customer attributes
            cust.attr["__t"+str(self.id)+"e"] = sim.now()  # mark time in customer attributes
            self.A["A.n"] += 1
            self.queue.push(cust)     # insert only to its queue
            self.customer=cust
            if self.code!=None :
                  self._eval(self.code)   # evaluate script code
# ---- bpmn derived classes (from Generator, Service, ConditionalEvent or Sink) ----
class XorGate(Service):    # random output if two outputs 
      def __init__(self,code=None):  # defaults to binary random selection
            Service.__init__(self,None,0,code)
            self.setName("exclusiveGateway")
class AndGate(Service):    
      def __init__(self,code=None):
            Service.__init__(self,None,0,code)
            self.setName("parallelGateway")
      def insert(self, cust, sim):
            ids=[e.id for e in self.prev()] # ids of inputs
            self.N=len(set(ids)) # set number of inputs (with unique ids) to wait
            Service.insert(self,cust,sim)
class Start(Generator):
      def __init__(self,fun=E,param=[1],tnmax=50.0,code=None):
            Generator.__init__(self,fun,param,tnmax,code)
            self.setName("startEvent")
class Task(Service):
      def __init__(self,fun=U,param=[1,2],code=None,M=1):
            Service.__init__(self,fun,param,code)
            self.setName("task")
            self.servers, self.nserver, self.M = [], 0, M
            for i in range(self.M-1):
                  Event.cnt -=1
                  self.servers.append(Service(fun,param,code))
      def insert(self, cust, sim):
            if(self.nserver==0):  # myself
                  Service.insert(self,cust,sim)
            else:              # otherselfs
                  self.servers[self.nserver-1].insert(cust,sim)
            self.nserver = (self.nserver+1)%self.M
class Timer(Service):
      def __init__(self,fun=1,param=None,code=None):
            if not callable(fun):  # when passing fixed delay value
                  fun,param,code = None,fun,param
            Service.__init__(self,fun,param,code)
            self.setName("intermediateCatchEvent")
class End(Sink):
      #def __init__(self):
      #      Sink.__init__(self)
      #      self.setName("endEvent")
      def __init__(self,code=None):
            Sink.__init__(self,"endEvent",code)
class Throw(Service):
      def __init__(self):
            Service.__init__(self,None,0)
            self.setName("intermediateThrowEvent")
class Terminate(End):
      def __init__(self,code=None):
            End.__init__(self,code)
            self.setName("terminateEndEvent")
class Script(Service):
      def __init__(self,code=None):
            Service.__init__(self,None,0,code)
            self.setName("scriptTask")
class Condition(ConditionalEvent):
      def __init__(self,code=None):
            ConditionalEvent.__init__(self,code)
            self.setName("intermediateCatchEvent")

# ---- util2 --------      
def connect(a, b):
      a.output.append(b)
      if isinstance(a,Task):
            for i in range(len(a.servers)):  # first server is already connected
                  a.servers[i].output.append(b)
def dict_tostring(a):
      return "\n".join([k+":\t"+str(v) for k,v in a.items()])
"""
def hist(a=[0,1], b=20, c='orange'):
      import matplotlib.pyplot as plt
      plt.hist(a,b,color=c)
      #plt.savefig("des_plot.svg", format="svg")
      #plt.show()
      import io, base64
      buf = io.BytesIO()
      plt.savefig(buf, format='svg')
      buf.seek(0)
      return 'data:image/svg+xml;base64,' + base64.b64encode(buf.read()).decode('UTF-8')
def from_file(fname):
      with open(fname,"r") as fp:
            return fp.read()
"""
# ---- conversions --------      
def attr_tostring(a):
      s="name: "+a["name"]+"\n"
      for i in range(1,100):
            t="__t"+str(i)
            if t+"b" in a:
                  s+=t+" "+"%.3f"%a[t+"b"]+" "+"%.3f"%a[t+"e"]+"\n"
      return s
def attr_tosvgstring(o,wmax,w=16,h=24):
      global ne
      a,s = o.attr,""
      c=['hotpink','limegreen','cornflowerblue','coral','mediumseagreen','mediumpurple']
      for i in range(100):
            t="__t"+str(i)
            if t+"b" in a:
                  s+='<text x="8" y="'+str(32+h*i)+'">'+str(i)+'<title>'+str(ne.ee[i-1].name)+' '+str(ne.ee[i-1].title)+'</title></text>\n'
                  s+='<text class="t1" style="display:none;fill:gray" x="32" y="'+str(32+h*i)+'">'+str(ne.ee[i-1].title)+'<title>'+str(ne.ee[i-1].name)+'</title></text>\n'
                  t0,t1,t2 = a[t+"a"],a[t+"b"],a[t+"e"]
                  s+='<rect y="'+str(20+h*i)+'" x="'+str(20+w*t1)
                  s+='" width="'+str(t2-t1==0 and 1 or w*(t2-t1))+'" height="'+str(h-2)+'" stroke="black" fill-opacity="0.7" fill="'
                  s+=(c[int(a["cname"].split(' ')[0])%len(c)])+'"><title>'+a["cname"]+' ['+("%.2f, "%t0)+("%.2f, "%t1)+("%.2f"%t2)+']'+'</title></rect>\n'
                  if t2-t1>0.5:
                        s+='<text x="'+str(20+w*t1+2)+'" y="'+str(20+h*i+18)+'">'+a["cname"]+'</text>'
                  if w*t1>wmax[0]:
                        wmax[0] = w*t1
      return s
def to_svg(ee=QueuedEvent.instances):
      w,h,W,H = 16,24,[160],40  # W[0] for passing by reference!!!
      s = '<svg onclick="on_click()" xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">\n'
      for e in ee:
            if isinstance(e,End):
                  for c in e.queue.objects:
                        s += attr_tosvgstring(c,W,w,h)
            H += 24
      H+=24
      s+= '<rect x="20" y="10" width="%d" height="2"/>\n'%(W[0]+w)
      s+= '<rect x="20" y="%d" width="%d" height="2"/>\n'%(H+10,W[0]+w)
      for i in range(int(W[0]/w+2)):
            s += '<rect x="'+str(20+w*i)+'" y="10" width="1" height="10"/>\n'
            s += '<rect x="'+str(20+w*i)+'" y="%d" width="1" height="10"/>\n'%(H)
            if (i%10)==0:
                  s+='<text x="'+str(20+w*i-8)+'" y="32">'+str(i)+'</text>\n'
                  s+='<text x="'+str(20+w*i-8)+'" y="%d">'%(H)+str(i)+'</text>\n'
      s += "<script>function on_click() {[...document.getElementsByClassName('t1')].forEach(e=>e.style.display=(e.style.display=='none'?'':'none'));}</script>"
      return s%(W[0]+80,H+20) + '</svg>\n'
def to_dot0(ee=QueuedEvent.instances):
      s ='digraph BPMN { rankdir="LR" ranksep=1 nodesep=1\n'
      for i in range(len(ee)):
            s1 = '  {rank=same; '
            for j in range(len(ee[i].output)):
                  s += "  "+str(ee[i].id) + " -> " + str(ee[i].output[j].id) +"\n"
                  s1 += str(ee[i].output[j].id) +"; "
            if len(ee[i].output)>1:
                  if abs(ee[i].output[0].id-ee[i].output[1].id)<2: s += s1 +'}\n'
      return s+'}'
def to_dot(ee=QueuedEvent.instances):
      s ='digraph BPMN2 { rankdir="LR" nodesep=0.6\n'
      for i in range(len(ee)):
            label,xlabel,shape,style,color,pen = str(ee[i].id),"","rect","","","1"
            size=""
            if "vent" in ee[i].name: shape="circle"
            elif "ateway" in ee[i].name: shape="diamond"; size="height=0.7"
            if "intermediate" in ee[i].name: shape="doublecircle"
            if shape=="rect": style="rounded,filled"; color="lightblue"; size="width=1.1 height=0.8"
            elif "end" in ee[i].name: style="filled"; pen="3"
            if "exclusive" in ee[i].name: xlabel=label; label="X"
            elif "parallel" in ee[i].name: xlabel=label; label="+"
            s += '  '+ee[i].name +' [label="'+label+'" xlabel="'+xlabel
            s += '" style="'+style+'" shape="'+shape+'" fillcolor="'
            s += color+'" penwidth="'+pen+'" '+size+']' +'\n'
      for i in range(len(ee)):
            s1 = '  {rank=same; '
            for j in range(len(ee[i].output)):
                  s += "  "+ee[i].name + " -> " + ee[i].output[j].name +"\n"
                  s1 += ee[i].output[j].name +"; "
            if len(ee[i].output)>1:
                  if abs(ee[i].output[0].id-ee[i].output[1].id)<2: s += s1 +'}\n'
      return s+'}'
def to_position(ee=QueuedEvent.instances):
      pp=[]
      for i in range(len(ee)):   # set x position to tree level
            x,ep = 0,ee[i].prev()
            for idx in range(len(ep)-1,-1,-1):
                  if ep[idx].pp[0]!=-1:
                        x=ep[idx].pp[0]+1
                        break
            ee[i].pp=[x,0]
            pp.append(ee[i].pp)
      #print([_.pp for _ in ee])
      for i in range(1,len(pp)): # increase y position for all at the same level
            if pp[i][0]==pp[i-1][0]:
                  pp[i][1] = pp[i-1][1]+1
                  ee[i].pp=pp[i]
      #print([_.pp for _ in ee])
      #"""
      for i in range(len(ee)-1,-1,-1):   # set y position to the level of previous 
            e = ee[i].prev()
            if len(e)>0 and e[0].output[0]==ee[i]:
                  pp[i][1] = e[0].pp[1]
                  ee[i].pp=pp[i]
            if len(e)>0 and len(e[0].output)>1 and e[0].output[1]==ee[i] and len(ee[i].output)==0:
                  pp[i][0] = ee[i].pp[0]-1  # when it is the second and has no ouput
                  ee[i].pp=pp[i]
      #print([_.pp for _ in ee])
      #"""
      for i in range(len(ee)-1,-1,-1): # move previous to the level of its first next
            ep=ee[i].prev()
            if len(ep)>0 and ep[0].output[0]==ee[i] and ep[0].pp[0]==ee[i].pp[0]-1:
                  if ep[0].pp[1]!=ee[i].pp[1]:
                        ep[0].pp[1]=ee[i].pp[1]
      #print([_.pp for _ in ee])      
      for i in range(len(ee)):  # force position from pp2
            if ee[i].pp2[0]!=-1:
                  ee[i].pp[0]=ee[i].pp2[0]
            if ee[i].pp2[1]!=-1:
                  ee[i].pp[1]=ee[i].pp2[1]
      for e in ee:   # correct position of boundary events 
            #if(e.pp[0]==0 and e.pp[1]==0):
            if(e.id!=e.id2):
                  id2=int(str(e.id2).split(".")[1])
                  e.pp[0],e.pp[1] = ee[id2-1].pp[0],ee[id2-1].pp[1]
      return [e.pp for e in ee]
def to_bpmn(ee=QueuedEvent.instances,pp=None):
      s ='<?xml version="1.0" encoding="UTF-8"?>\n'
      s+='<bpmn:definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
      s+=' xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"'
      s+=' xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"'
      s+=' xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"'
      s+=' xmlns:di="http://www.omg.org/spec/DD/20100524/DI"'
      s+=' targetNamespace="http://bpmn.io/schema/bpmn"'
      s+=' id="Definitions_1" exporter="des" exporterVersion="1.0">\n'
      s1=' <bpmn:process id="Process_1">\n'
      s2=' <bpmndi:BPMNDiagram id="BPMNDiagram_1">\n'
      s2+='  <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">\n'
      s1a=''
      j1 = 0  # flow counter
      W,H,W0,H0 = 100,100,40,30
      if not pp:
            pp = [e.pp for e in ee]
            if pp[0][0]==-1:
                  pp = to_position(ee)
      for i in range(len(ee)):
            name = ee[i].name
            if "terminate" in name:
                  name=name[len("terminate"):]
            ename = ee[i].__class__.__name__+'_'+str(ee[i].fun and ee[i].fun.__name__ or None)+'_'
            import base64
            ename += base64.b16encode(bytearray(str(ee[i].param)+'_'+str(ee[i].code),'ascii')).decode('ascii') # requires encoding!
            type=name.split("_")[0]
            gt={"wi":80,"h":60,"ox":0,"oy":0,"e":(80,30),"w":(0,30),"n":(40,0),"s":(40,60)}
            gg={"wi":36,"h":36,"ox":22,"oy":12,"e":(58,30),"w":(22,30),"n":(40,12),"s":(40,48)}
            g1 = gt if "ask" in type else gg
            w,h = g1["wi"],g1["h"]  # icon size
            xb,yb = W0+W*pp[i][0], H0+H*pp[i][1]
            xo,yo = xb+g1["ox"], yb+g1["oy"] # icon offset
            if "task" in type:
                  if len(ee[i].output)>1: type = "sendTask"
                  if len(set([e.id for e in ee[i].prev()]))>1: type = "receiveTask"
            if ee[i].id != ee[i].id2:  # for boundary events
                  id2 = int(str(ee[i].id2).split('.')[1])
                  xo,yo = ee[id2-1].x+22.5,ee[id2-1].y+42.5
                  type = "boundaryEvent"
            ee[i].x,ee[i].y = xo,yo
            s1+='  <bpmn:'+type+' id="'+name+'" name="'+name.split("_")[1]+'\n'+ee[i].title+'">\n'
            s2+='   <bpmndi:BPMNShape id="'+name+'_'+ename+'" bpmnElement="'+name+'">\n'
            s2+='    <dc:Bounds x="'+str(xo)+'" y="'+str(yo)+'" width="'+str(w)+'" height="'+str(h)+'" />\n'
            s2+='   </bpmndi:BPMNShape>\n'
            for j2 in range(len(ee[i].output)):
                  j1 += 1
                  flow,eflow='Flow_'+str(j1),"di"
                  ii = ee[i].output[j2].id-1
                  #print(ee[i],j2,ee[i].output[j2],ii,pp)
                  xe,ye = W0+W*pp[ii][0], H0+H*pp[ii][1]
                  name2=ee[i].output[j2].name
                  if "terminate" in name2:
                        name2=name2[len("terminate"):]
                  type2=name2.split("_")[0]
                  g2 = gt if "ask" in type2 else gg
                  if xe>xb: # two edges
                        dx1,dy1 = g1["s"] if yb<ye else g1["e"]
                        dx2,dy2 = g2["s"] if yb>ye else g2["w"]
                  else :    # three edges
                        dx1,dy1 = g1["s"] if yb<ye else g1["n"]
                        dx2,dy2 = g2["s"] if yb>ye else g2["n"]
                  x1,y1 = xb+dx1,yb+dy1
                  x2,y2 = xe+dx2,ye+dy2
                  s1+='   <bpmn:outgoing>'+flow+'</bpmn:outgoing>\n'
                  if "intermediateCatch" in name:
                        if "ondition" in ename:
                              s1+='   <bpmn:conditionalEventDefinition/>\n'
                        else:
                              s1+='   <bpmn:timerEventDefinition/>\n'
                  s1a+='    <bpmn:sequenceFlow id="'+flow+'" sourceRef="'+name+'" targetRef="'+name2+'" />\n'
                  s2+='   <bpmndi:BPMNEdge id="'+flow+'_'+eflow+'" bpmnElement="'+flow+'">\n'
                  s2+='    <di:waypoint x="'+str(x1)+'" y="'+str(y1)+'" />\n'
                  xx,yy = 0,0
                  if y1!=y2: # requires additional points (one or two implemented)
                        xx, yy = y2>y1 and x1 or x2, y2>y1 and y2 or y1
                        if x1>x2: # back connection requires two additional
                              if y1>y2: # from lower position
                                    yy -= 35
                                    s2+='    <di:waypoint x="'+str(x1)+'" y="'+str(yy)+'" />\n'                      
                              elif y1<y2: # from upper position
                                    yy -= 25
                                    s2+='    <di:waypoint x="'+str(xx)+'" y="'+str(yy)+'" />\n'
                                    xx = x2
                        s2+='    <di:waypoint x="'+str(xx)+'" y="'+str(yy)+'" />\n'
                  elif y1==y2 and x1>x2: # loopback - requires two additional points
                        s2+='    <di:waypoint x="'+str(x1)+'" y="'+str(y1-30)+'" />\n'
                        s2+='    <di:waypoint x="'+str(x2)+'" y="'+str(y2-30)+'" />\n'                   
                  if xx!=x2 or yy!=y2:
                        s2+='    <di:waypoint x="'+str(x2)+'" y="'+str(y2)+'" />\n'
                  s2+='   </bpmndi:BPMNEdge>\n'
            if "terminate" in ee[i].name:
                  s1+='   <bpmn:terminateEventDefinition/>\n'
            s1+='  </bpmn:'+type+'>\n'
            pass
      s2+='  </bpmndi:BPMNPlane>\n'
      s2+=' </bpmndi:BPMNDiagram>\n'
      s1+=s1a+' </bpmn:process>\n'
      return s+s1+s2+'</bpmn:definitions>\n'

en_title = ""
class EventNetwork():
      def __init__(self,s):
            Event.cnt, Customer.cnt = 0, 0
            QueuedEvent.instances.clear()
            BpmnEvent.S = {}
            self.ee = self.from_string(s)
            self.pp = to_position(self.ee)
      def __getitem__(self,i):
            return self.ee[i]
      def from_string(self,s):
            global en_title
            ee, Event.cnt, ylevel, en_title = [], 0, -1, ''
            ss = s.split('\n')
            for s0 in ss:
                  s1 = s0.strip()
                  if len(s1)<2 or s1[0]=='#':
                        if s1==ss[0]: # title in first line
                              en_title = ss[0][1:]
                        continue
                  if "->" in s1: # connection definition
                        ylevel += 1   # used for marking required y position
                        for s1a in s1.split(";"):
                                code = s1a.strip().split("->")
                                if len(code)>1:
                                        code[1]=code[1].split("#")[0]
                                        i,j = int(code[0])-1, int(code[1])-1
                                        if i>-1 and j>-1:
                                              connect(ee[i],ee[j])
                                        if i>-1 and ee[i].pp2[1]==-1: # if not set yet
                                              ee[i].pp2[1]=ylevel # force y position
                                        if j>-1 and ee[j].pp2[1]==-1: # if not set yet
                                              ee[j].pp2[1]=ylevel # force y position                  
                  else:          # event definition
                        code=s1.split(" ")
                        if len(code)>1:
                                code1=" ".join(code[1:]).split('#')
                                ee.append(eval(code1[0]))
                                ee[-1].id2=float(code[0].split('/')[0]) # id as written in source 
                                ee[-1].title=code1[1].strip() if len(code1)>1 else ''
                                cc=code[0].split("/")  # check identifier field
                                ee[-1].pp2[0] = float(cc[1])-1 if len(cc)>1 else -1 
                                ee[-1].pp2[1] = float(cc[2])-1 if len(cc)>2 else -1
            if len(set([e.pp2[1] for e in ee]))==1: # verify if multi-line description
                  for e in ee:      # if yes
                        e.pp2[1]=-1 # clear all y-levels to unknown
            return ee
      def to_string(self):
            s=''
            for e in self.ee:
                  s += str(e.id) + " " + e.__class__.__name__+"("
                  if e.__class__.__name__!='End':
                        if "Gate" not in e.__class__.__name__:
                              s += e.fun and e.fun.__name__ or 'None'
                              s +=","+str(e.param)+","
                        if e.__class__.__name__!='Start':
                              s+= e.code!=None and "\""+str(e.code)+"\"" or "None"
                        else:
                              s+=str(e.tnmax)
                  s +=")\n"
            for e in ee:
                  for i in range(len(e.output)):
                        s += str(e.id) + "->" + str(e.output[i].id) +';'
            return s + '\n'
def svg_roundedPath(pp, r):
      import math
      s, l = "", len(pp)-1
      for i in range(l):
            a,b = pp[i], pp[i+1]
            t = min(r / math.hypot(b[0]-a[0], b[1]-a[1]+0.01), 0.5)
            if i==0:
                  s += 'M%g %g '%(a[0],a[1])
            if i>0:
                  s += 'Q%g %g %g %g '%(a[0],a[1],a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t)
            if i==l-1:
                  s += 'L%g %g '%(b[0],b[1])
            elif i<l-1:
                  s += 'L%g %g '%(a[0]*t+b[0]*(1-t),a[1]*t+b[1]*(1-t))
      return s
#NS_MAP = {
#    None: 'http://www.omg.org/spec/BPMN/20100524/MODEL',
#    'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
#    'omgdc': 'http://www.omg.org/spec/DD/20100524/DC',
#    'omgdi': 'http://www.omg.org/spec/DD/20100524/DI',
#    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
#}
def bpmn_tosvg0(bpmnfile,W=100,H=80):
      s = '<defs><marker id="triangle" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="strokeWidth" markerWidth="10" markerHeight="10" orient="auto"> <path d="M 0 0 L 10 5 L 0 10 z" fill="black" /></marker></defs>\n'
      import xml.etree.ElementTree as ET
      for e in ET.parse(bpmnfile).getroot():
            if "BPMNDiagram" in e.tag:
                  for d in e:
                        items=[p for p in d if "BPMNPlane" in d.tag]
      return items
#def bpmn_tosvg(bpmnfile,W=100,H=80):
def bpmn_tosvg(bpmnstring,isanim,iscomments,isscripts,W=100,H=80):
      s = '<defs><marker id="triangle" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="strokeWidth" markerWidth="10" markerHeight="10" orient="auto"> <path d="M 0 0 L 10 5 L 0 10 z" fill="black" /></marker></defs>\n'
      s += '<text x="10" y="12">'+en_title+'</text>\n';
      import xml.etree.ElementTree as ET
      #for e in ET.parse(bpmnfile).getroot():  # collect named processes
      for e in ET.fromstring(bpmnstring):  # collect named processes
            if "process" in e.tag:
                  elems=[d for d in e if "name" in d.attrib]
      #for e in ET.parse(bpmnfile).getroot():  # collect diagram elements
      for e in ET.fromstring(bpmnstring):  # collect named processes
            if "BPMNDiagram" in e.tag:
                  for d in e:
                        items=[p for p in d if "BPMNPlane" in d.tag]
      for it in items:
            pp,name = [],""
            for e in elems:
                  if it.attrib["bpmnElement"]==e.attrib["id"]:
                        name=" ".join(e.attrib["name"].split(" ")[1:]) # assume "id\ntext"
            for j in range(len(it)):
                  x,y = float(it[j].attrib["x"]),float(it[j].attrib["y"])
                  w,h = (float(it[j].attrib["width"]),float(it[j].attrib["height"])) if "Bounds" in it[j].tag else (0,0)
                  W,H = max(W,x+w),max(H,y+h)
                  #print(it.attrib["id"],":",x,y,w,h)
                  if w==0: # bpmn flow
                        pp.append([x,y])
                  else:    # bpmn event
                        ids=it.attrib["id"].split("_")
                        id=ids[1]
                        if len(ids)>4:
                              import base64
                              ids[4]=base64.b16decode(ids[4],'ascii').decode('ascii')
                        id2="_".join(ids[2:]).replace('<','&lt;').replace('>','&gt;')
                        s+='<text x="'+str(x-6)+'" y="'+str(y+h+12)+'">'+id+'</text>\n'
                        if iscomments:
                              s+='<text font-size="smaller" style="fill:gray" x="'+str(x-12)+'" y="'+str(y-6)+'"><tspan xml:space="preserve">'+name+'</tspan></text>\n'
                        id3=id2.split("_")
                        #if len(id3)>3 and id3[3] != "None" : s+='<text class="t1" font-size="smaller" style="fill:gray" x="'+str(x+18)+'" y="'+str(y+h+12+("Event" in it.attrib["id"] and 12 or 0))+'"><tspan xml:space="preserve">'+id3[3]+'</tspan></text>\n'
                        if isscripts:
                              id3a="_".join(ids[2:]).split("_")
                              if len(id3a)>3 and id3a[3] != "None": s+='<text class="t1" font-size="smaller" style="fill:gray" x="'+str(x+18)+'" y="'+str(y+h+12)+'"><tspan xml:space="preserve">'+id3a[3].split(';')[0].replace('<','&lt;').replace('>','&gt;')+'</tspan></text>\n'
                        if "Event" in it.attrib["id"]:
                              stroke = "end" in it.attrib["id"] and "3" or "1"
                              color = "end" in it.attrib["id"] and "red" or "darkgreen"
                              s+= '<ellipse cx="'+str(x+w/2)+'" cy="'+str(y+h/2)+'" rx="'+str(w/2)+'" ry="'+str(h/2)+'" stroke-width="'+stroke+'" stroke="'+color+'" fill-opacity="0.6" fill="white"><title>'+id2+'</title></ellipse>\n'
                              if "intermediate" in it.attrib["id"]:
                                    s+= '<ellipse cx="'+str(x+w/2)+'" cy="'+str(y+h/2)+'" rx="'+str(w/2-3)+'" ry="'+str(h/2-3)+'" stroke-width="'+stroke+'" stroke="darkgreen" fill="white"/>\n'
                                    if "Catch" in it.attrib["id"]:
                                          if "ondition" in it.attrib["id"]:
                                                s+= '<rect x="%g" y="%g" width="%g" height="%g" stroke="black" fill="none" />'%(x+w/2-7,y+h/2-9,w/2-4,h/2)
                                                s+= '<path d="'
                                                for i in range(5):
                                                      s+= 'M%g %g L%g %g '%(x+w/2-5,y+h/2-6+3*i,x+w/2+5,y+h/2-6+3*i)
                                          else:
                                                s+= '<ellipse cx="'+str(x+w/2)+'" cy="'+str(y+h/2)+'" rx="'+str(w/2-6)+'" ry="'+str(h/2-6)+'" stroke-width="'+stroke+'" stroke="black" fill="white"/>\n'
                                                s+= '<path d="M%g %g L%g %g %g %g '%(x+w/2-5,y+h/2-3,x+w/2,y+h/2,x+w/2+6,y+h/2-6)
                                                for i in range(12):
                                                      from math import sin,cos,pi
                                                      s+= "M%g %g L%g %g "%(x+w/2+(w/2-6)*cos(i*2*pi/12),y+h/2+(h/2-6)*sin(i*2*pi/12),x+w/2+(w/2-9)*cos(i*2*pi/12),y+h/2+(h/2-9)*sin(i*2*pi/12))
                                          s+= '" stroke="black" stroke-width="1" fill="none"/>'   
                              if "erminate" in it.attrib["id"]:
                                    s+= '<ellipse cx="'+str(x+w/2)+'" cy="'+str(y+h/2)+'" rx="'+str(w/2-6)+'" ry="'+str(h/2-6)+'" stroke-width="'+stroke+'" stroke="red" fill="red" fill-opacity="0.6"/>\n'
                        elif "Gateway" in it.attrib["id"]:
                              color = "orange"
                              s+= '<path d="M%g %g L%g %g L%g %g L%g %g Z" stroke="%s" fill="white"><title>%s</title></path>\n'%(x,y+h/2,x+w/2,y,x+w,y+h/2,x+w/2,y+h,color,id2) 
                              if "exclusive" in it.attrib["id"]:
                                    s+='<path d="M%g %g L%g %g M%g %g L%g %g" stroke="black" stroke-width="3" />\n'%(x+w/2-6,y+h/2-6,x+w/2+6,y+h/2+6,x+w/2+6,y+h/2-6,x+w/2-6,y+h/2+6)
                              elif "parallel" in it.attrib["id"]:
                                    s+='<path d="M%g %g L%g %g M%g %g L%g %g" stroke="black" stroke-width="3" />\n'%(x+w/2-8,y+h/2,x+w/2+8,y+h/2,x+w/2,y+h/2-8,x+w/2,y+h/2+8)
                        else:
                              s+= '<rect rx="7" ry="7" x="'+str(x)+'" y="'+str(y)+'" width="'+str(w)+'" height="'+str(h)+'" stroke="darkblue" fill="white"><title>'+id2+'</title></rect>\n'
                              if "script" in it.attrib["id"]:
                                    for i in range(4):
                                          s +='<path d="M%g %g L%g %g" stroke="black" stroke-width="1" />'%(x+10+0*i,y+10+4*i,x+22+0*i,y+10+4*i)
            if len(pp)>0: # s1!='': # add whole flow
                  s1=svg_roundedPath(pp,12)
                  s += '<path marker-end="url(#triangle)" d="'+s1+'" style="fill:none;stroke:brown;stroke-width:1"/>\n'
      s += "<script>function on_click() {[...document.getElementsByClassName('t1')].forEach(e=>e.style.display=(e.style.display=='none'?'':'none'));}</script>"
      s = '<svg onclick="on_click()" xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">\n'%(W+40+60,H+30)+s
      return s + (to_anim() if isanim else '') + '</svg>\n'
def to_anim():
      #return s
      global ne
      s =  '<defs><filter x="0" y="0" width="1" height="1" id="fi">\n'
      s += '<feFlood flood-color="white"/>\n'
      s += '<feComposite in="SourceGraphic" operator="atop"/></filter></defs>\n'
      for e in ne.ee:
            if isinstance(e,End):
                  for c in e.queue.objects:
                        for i in range(len(ne.ee)):
                              x, y, a = ne.ee[i].x, ne.ee[i].y, c.attr 
                              s +='<text class="t1" filter="url(#fi)" style="font-size:small;fill:red" x="'+str(x-20)+'" y="'+str(y+13)+'" visibility="hidden">'+str(c.name)+'\n'
                              t="__t"+str(i+1)
                              if t+"a" in a:
                                    t0 = a[t+"a"]
                                    s += '<animate attributeName="visibility" from="hidden" to="visible" begin="'+str(t0)+'s" dur="0.01s" fill="freeze"/>\n'
                                    if t+"b" in a:
                                          t1 = a[t+"b"] 
                                          s += '<animate attributeName="x" to="'+str(x+38)+'" begin="'+str(t1)+'s" dur="0.5s" fill="freeze"/>\n'
                                          if t+"e" in a:
                                                t2 = a[t+"e"]
                                                s += '<animate attributeName="visibility" from="visible" to="hidden" begin="'+str(t2)+'s" dur="0.01s" fill="freeze"/>\n'
                              s +='</text>\n'
      return s

ne=[]
# ---- simulation -----
def main_fun(exn,n,anim,comments,scripts): # string representation, number of simulation
      data=[]  # list of events, array of results
      s = ''
      for i in range(n):
            global ne
            ne = EventNetwork(exn)
            sim = Simulator()
            for e in ne:
                  if isinstance(e,Generator):  # add generating events
                        sim.add(e)  
            sim.run()
            data.append([sim.time,BpmnEvent.S])   # save end time of simulation
            
            #if exn==ex5:
            #      data.append(BpmnEvent.S["S.bA"]) # save global variable S.bA
            #else:
            #      data.append(sim.time)   # save end time of simulation
            if i==0:
                  s1 = to_bpmn(ne.ee,ne.pp)
                  s2 = bpmn_tosvg(s1,anim,comments,scripts)
                  s3 = to_svg()
      s += "#n\tt\t"+"\t".join(data[0][1].keys())+"\n"
      s += "\n".join(["%d\t%.2f\t%s"%(i+1,data[i][0],"\t".join([str(v) for v in [*data[i][1].values()]])) for i in range(len(data))])
      #for e in ne:
      #      if len(e.queue)>0:
      #            s += str(e.id) + ("(%d):"%len(e.queue)) + str(e.queue)+'\n'
      #s += str(sum(data)/len(data))+'\n'
      #s += str(BpmnEvent.S)+'\n'
      #for e in ne:
      #      s += str(e.id)+str(e.A)+' '
      #      if isinstance(e,Task):
      #            for i in range(len(e.servers)):
      #                  s += str(e.servers[i].id)+'/'+str(i+1)+str(e.servers[i].A)+' '
      s4=''
      if len(data)>=100:
            #if exn==ex4:
            #      s4 = hist(data,7)
            #else:
            #      s4 = hist(data)
            pass # s4 = hist(data)
      return (s,s1,s2,s3,s4) # s2+'<br>\n'+(s3 if n==1 else '')+'<br>\n'+'<pre>'+s+'</pre>'


"""
if __name__=="__main__":
      import sys
      #import ex
      ex30 = '1 Start()\n2 Task()\n3 End()\n1->2;2->3\n'
      s = len(sys.argv)>1 and from_file(sys.argv[1]) or eval('ex%d'%(30))
      n = len(sys.argv)>2 and int(sys.argv[2]) or 100
      s = main_fun(s,n)
      print(s[3])
"""
s = input[0]
n = int(input[1])
anim = int(input[2])
comments = int(input[3])
scripts = int(input[4])
output = main_fun(s, n, anim, comments, scripts)
s = ''
#s += '<div id="div1" hidden>'+output[1]+'</div><br>\n'
s += '<div id="div2" tabindex="-1">'+output[2]+'</div><br>\n'
#s +='<input type=button value="Save bpmn to xml file" onclick="writeFile1();"></input>\n'
s +='<input type=button value="Save bpmn to svg file" onclick="writeFile2();"></input>\n'
s +='<input type=button value="Save bpmn to xml file" onclick="writeFile5();"></input><br><br>\n'
if n==1:
      s += '<div id="div3">'+output[3] +'</div><br>\n'
      s +='<input type=button value="Save timeline to svg file" onclick="writeFile3();"></input><br><br>\n'
s +='<textarea id="ta4" rows="10" cols="80">'+output[0]+'</textarea><br>\n' #+'<img src="'+output[3]+'">'
s +='<input type=button value="Save results to txt file" onclick="writeFile4();"></input><br><br>\n'
s +='<textarea hidden id="ta5" rows="10" cols="80">'+output[1]+'</textarea><br>\n' #+'<img src="'+output[3]+'">'
s


