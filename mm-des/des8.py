# DES - discrete event (micro) simulator
# - basic events: Generator,Service,Sink,ConditionalEvent
# - bpmn events: Start,Task,End,Timer,XorGate,AndGate,Condition
# MM 31.1.2024

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
                        if self.customer.attr["value"] or len(self.output)<2:
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
      def __init__(self):
            Sink.__init__(self)
            self.setName("endEvent")
class Throw(Service):
      def __init__(self):
            Service.__init__(self,None,0)
            self.setName("intermediateThrowEvent")
class Terminate(End):
      def __init__(self):
            End.__init__(self)
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
def hist(a=[0,1], b=20, c='orange'):
      import matplotlib.pyplot as plt
      plt.hist(a,b,color=c)
      plt.savefig("des_plot.svg", format="svg")
      plt.show()
def from_file(fname):
      with open(fname,"r") as fp:
            return fp.read()

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
            ee, Event.cnt, ylevel = [], 0, -1
            for s0 in s.split('\n'):
                  s1 = s0.strip()
                  if len(s1)<2 or s1[0]=='#': continue
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
                                ee[-1].id2=float(code[0]) # id as written in source 
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
def bpmn_tosvg(bpmnfile,W=100,H=80):
      s = '<defs><marker id="triangle" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="strokeWidth" markerWidth="10" markerHeight="10" orient="auto"> <path d="M 0 0 L 10 5 L 0 10 z" fill="black" /></marker></defs>\n'
      import xml.etree.ElementTree as ET
      for e in ET.parse(bpmnfile).getroot():  # collect named processes
            if "process" in e.tag:
                  elems=[d for d in e if "name" in d.attrib]
      for e in ET.parse(bpmnfile).getroot():  # collect diagram elements
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
                        s+='<text font-size="smaller" style="fill:gray" x="'+str(x-12)+'" y="'+str(y-6)+'"><tspan xml:space="preserve">'+name+'</tspan></text>\n'
                        id3=id2.split("_")
                        if len(id3)>3 and id3[3] != "None" : s+='<text class="t1" font-size="smaller" style="fill:gray" x="'+str(x+18)+'" y="'+str(y+h+12)+'"><tspan xml:space="preserve">'+id3[3]+'</tspan></text>\n'
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
      s = '<svg onclick="on_click()" xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">\n'%(W+40,H+30)+s
      return s + to_anim() + '</svg>\n'
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
                              s +='<text class="t1" filter="url(#fi)" style="font-size:small;fill:red" x="'+str(x-16)+'" y="'+str(y+13)+'" visibility="hidden">'+str(c.name)+'\n'
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

# ----- demo examples ------
# event list must be in order
# connections could be semicolon separated in one line
# two-output XorGate should have first connection for True
# n-output XorGate should have choice with n-outputs results i.e. "=C(p1,...,pn)"
# drawing is order depended and it is not perfect
ex1="""
# Two sequential tasks
1 Start(E,[2.0],20.0) # 20 units of exponential events with mean of 2 time units
2 Task(U,[2.0,3.0])    # a task with execution time from 2 to 3 units
3 Task(U,[1.0,3.0])
4 End()
1->2; 2->3; 3->4
"""
ex2="""
# Two parallel tasks - AndGate test
1 Start(E,[2.0],20.0)
2 AndGate()
3 Task(U,[2.0,3.0]) 
4 Task(U,[1.0,3.0])
5 AndGate()
6 End()
1->2; 2->3; 2->4; 3->5; 4->5; 5->6;
"""
ex3="""
# Sequential and parallel tasks
1 Start(N,[1.0],20.0)
2 Task(E,[2.0],"tsk1=1") 
3 Task(E,[3.0],"tsk2=1")
4 AndGate()
5 Task(U,[1.0,2.0])
6 Timer(1.0)
7 AndGate() 
8 End()
1->2; 2->3; 3->4; 4->5; 5->7; 4->6; 6->7; 7->8
"""
ex4="""
#Two doctors
1 Start(E,[2.0],20.0)
2 XorGate("=B(0.5)")
3 XorGate()
4 XorGate()
5 Task(U,[2.0,3.0],"tsk1=1")
6 Task(U,[1.0,3.0],"tsk2=1")
7 XorGate("=(tsk2==1)")
8 XorGate("=(tsk1==1)")
9 XorGate()
10 End()
1->2; 2->3; 2->4; 3->5; 4->6; 5->7; 6->8; 7->9; 7->4; 8->9; 8->3; 9->10
"""
ex5="""
# Bikeshare
1 Start(E,[2.0],-100.0,"S.bA=3")       # start with 3 bikes in A
2 Start(E,[2.0],-100.0,"S.bB=3")       # start with 3 bikes in B
3 XorGate("=S.bA>0;S.bA=S.bA>0 and S.bA-1 or 0")  # any bike in A?; yes: take it
4 XorGate("=S.bB>0;S.bB=S.bB>0 and S.bB-1 or 0")  # any bike in B?; yes: take it
5 Timer(U,[4.0,5.0],"S.bB=S.bB+1")     # ride and leave taken bike at B
6 Timer(U,[15.0,20.0])                 # walk to B
7 Timer(U,[4.0,5.0],"S.bA=S.bA+1")     # ride and leave taken bike at A
8 Timer(U,[15.0,20.0])                 # walk to A
9 End()                                 # end of riding from A to B
10 End()                                # end of walking from A to B
11 End()                                # end of riding from B to A
12 End()                                # end of walking from B to A
1->3; 2->4; 3->5; 3->6; 4->7; 4->8; 5->9; 6->10; 7->11; 8->12
"""
ex6="""
# Timer test
1 Start(U,[2.0],6)    
2 Timer(3.0)       # delay all events by 3.0
3 End()
1->2; 2->3
"""
ex7="""
# An activity variable test (A.n - client number)
1 Start(U,[2.0],-100.0) # hundread events every 2 time units
2 XorGate("=(A.n-1)%2") # switch every second to different task
3 Task(U,[3.0])
4 Task(U,[3.0])
5 End()
6 Terminate()
1->2; 2->3; 2->4; 3->5; 4->6;
"""
ex8="""
# A four phases process
1 Start(E,[2.0],20.0)
2 Task(U,[2.0,3.0])
3 Throw()
4 Throw()
5 End()
6 AndGate()
7 Task(U,[1.0,3.0])
8 Task(U,[1.0,3.0])
9 Task(U,[1.0,3.0])
10 Task(U,[1.0,3.0])
11 AndGate()
12 XorGate("=C([0.33,0.34,0.33])")
13 Task(U,[1.0,3.0])
14 Task(U,[1.0,3.0])
15 Task(U,[1.0,3.0])
16 XorGate()
17 Timer(1.0)
18 Script("print('Task 17 times for %s: %.2f %.2f %.2f'%(cname,__t17a,__t17b,__t17e))")
19 End()
1->2; 2->4; 4->6; 6->7; 6->8; 6->9; 6->10; 7->11; 8->11; 9->11; 10->11; 11->12; 12->13; 12->14; 12->15; 13->16; 14->16; 15->16; 16->17; 17->18; 18->19; 1->3; 3->5;
#1->2; 2->4; 4->6; 6->7; 7->11; 11->12; 12->13; 13->16; 16->17; 17->18; 18->19;
#1->3; 3->5;       6->8; 8->11;         12->14; 14->16;
#                  6->9; 9->11;         12->15; 15->16;
#                  6->10; 10->11;
"""
ex9="""
# Resources test: from three parallel tasks only two could be executed as only two resources are available
1 Start(E,[2.0],20.0,"S.x=2")     # two abstract resources
2 XorGate("=A.n%3")               # pass to 3 lines
3 Condition("=S.x>0;S.x=S.x-1")   # check availability and decrement if available
4 Condition("=S.x>0;S.x=S.x-1")   # ...
5 Condition("=S.x>0;S.x=S.x-1")   # ...
6 Task(U,[2.0,4.0],"S.x=S.x+1")   # release resource when finished
7 Task(U,[3.0,4.0],"S.x=S.x+1")   # ...
8 Task(U,[3.0,5.0],"S.x=S.x+1")   # ...
9 XorGate()
10 End()
1->2; 2->3; 2->4; 2->5; 3->6; 4->7; 5->8; 6->9; 7->9; 8->9; 9->10;
"""
ex10="""
# Credit card application - time in 10min units
1 Start(E,[1],-40)      # 2 clerks (25$/h), 3 credit officers (50$/h) 
2 AndGate()
3 Task(N,[1,2/10])      # check credit history (clerk)
4 Task(N,[2,4/10],"",1)      # check income sources  (clerk)
5 AndGate()
6 XorGate()
7 Task(E,[2])           # assess application (credit officer)
8 XorGate("=B(0.8)")    # decission review requested (20/80)
9 Task(N,[1,2/10])      # make credit offer  (credit officer)
10 Task(N,[1,2/10])     # notify rejection   (credit officer)
11/10/1 End()
12 XorGate("=B(0.8)")   # notify rejection (20/80)
13 End()
1->2; 2->3; 2->4; 3->5; 4->5; 5->6; 6->7; 7->8; 8->9; 8->10; 9->11; 10->12; 12->13; 12->6                                 
"""
ex11="""
# G/G/2 test  
1 Start(U,[1],-20)       
2 AndGate()
3 Task(U,[4])       # G/G/1
4 Task(U,[4],"",2)  # G/G/2
5 Task(U,[4])       # G/G/1
6 Task(U,[4],"",2)  # G/G/2
7 End()
8 End()
1->2; 2->3; 3->5; 5->7
      2->4; 4->6; 6->8
"""
ex12="""
# Procurement Process 
1 Start(E,[1],-40)      
2 Task(N,[1,2/10])      # handle quotation
3 Task(N,[2,4/10])      # approve order
4 XorGate()             # approved?
5 AndGate()             # approved
6 Terminate()           # not approved 
7 Task(E,[2])           # handle order
8 Task(E,[2])           # handle shipment
9 AndGate()             # 
10 Task(N,[1,2/10])     # review order
11 End()
1->2; 2->3; 3->4; 4->5; 5->7; 7->9; 9->10; 10->11;
                  4->6; 5->8; 8->9;
"""

#----test exmaples---------------
ex8a="""
1 Start(E,[2.0],20.0)
2 Task(U,[2.0,3.0])
3 XorGate("=B(0.6)")
4 Task(U,[1.0,3.0])
5 Task(U,[1.0,3.0])
6 XorGate()
7 AndGate()
8 Task(U,[1.0,3.0])
9 Task(U,[1.0,3.0])
10 Task(U,[1.0,3.0])
11 AndGate()
12 End()
1->2; 2->3; 3->4; 4->6;  6->7; 7->8;  8->11; 11->12
            3->5; 5->6;        7->9;  9->11;
                               7->10; 10->11;
"""
ex11a="""
# Event variable test
1 Start(U,[2.0],-30.0)  # 
2 Task(U,[2.0,3.0])     # regular task
3 XorGate("=A.n%3")     # switch every third to additional task
4 XorGate()             
5 Task(U,[3.0,4.0])     # additional task
6 End()
1->2; 2->3; 3->4; 3->5; 5->4; 4->6;
"""
ex11b="""
#BPMN drawing test
1 Start(E,[2.0],20.0)
2 AndGate()
3 Task(U,[2.0,3.0]) 
4 Task(U,[1.0,3.0])
5 Task(U,[1.0,3.0])
6 AndGate()
7 End()
1->2; 2->3; 2->4; 3->5; 5->6; 6->7; 4->6
"""
ex12a="""
#Minimum working example
1 Start(U,[2.0],-100.0) 
2 End()
1->2;
"""
ex13="""
# XorGate test
1 Start(U,[2.0],-20.0)
2 XorGate("=C([0.5,0.25,0.25])")
3 Task(U,[2.0])
4 Task(U,[2.0])
5 Script("print(self.customer.attr,A.n)")
6 XorGate()
7 Terminate()
1->2; 2->3; 2->4; 2->5; 3->6; 4->6; 5->6; 6->7 
"""
ex14="""
# A throw test
1 Start(E,[2.0],20.0)
2 Throw()
3 Task(U,[2.0,3.0]) 
4 Task(U,[1.0,3.0])
5 Task(U,[1.0,3.0])
6 End()
1->2; 2->3; 2->4; 3->5; 5->6; 4->6
"""
ex15="""
# Test of drawing
1 Start(E,[2.0],20.0)
2 Task(U,[2.0,3.0]) 
3 Task(U,[1.0,3.0])
4 Task(U,[1.0,3.0])
5 Task(U,[1.0,3.0])
6 Throw()
7 End()
1->2; 2->4; 1->3; 4->5; 5->6; 3->6; 6->7
"""
ex16="""
# Condition test
1 Start(U,[2.0],10,"S.x=0")     # generate 6 events, init scenario variable
2 Condition("=S.x<2")           # conditional pass on scenario variable
3 Task(U,[2.0,3.0],"S.x=S.x+1") # increase scenario variable
4 End()
1->2; 2->3; 3->4
"""
ex17="""
# Resources test
1 Start(E,[2.0],20.0,"S.x=2")
2 Condition("=S.x>0;S.x=S.x-1")
3 XorGate("=(A.n-1)%3")
4 Task(U,[2.0,4.0],"S.x=S.x+1") 
5 Task(U,[3.0,4.0],"S.x=S.x+1")
6 Task(U,[3.0,5.0],"S.x=S.x+1")
7 XorGate()
8 End()
1->2; 2->3; 3->4; 3->5; 3->6; 4->7; 5->7; 6->7; 7->8; 
"""
ex18="""
1 Start(U,[2.0],-100.0) # 
2 XorGate("=(A.n-1)%3")     # switch every third to additional task
3 XorGate()
4 Task(U,[3.0])         # additional task
5 Task(U,[3.0])         # regular task
6 End()
1->2; 2->3; 2->4; 3->5; 5->6; 4->3
"""
ex19="""
# Credit card application
1 Start(E,[10],-50,"S.nC=3;S.nCO=3") # 3 clerks (25$/h), 3 credit officers (50$/h) 
2 AndGate()
3 Task(N,[10,2])      # check credit history (clerk)
4 Task(N,[20,4])      # check income sources  (clerk)
5 AndGate()
6 XorGate()
7 Task(E,[20])        # assess application (credit officer)
8 XorGate("=B(0.2)")  # decission review requested (20/80)
9 Task(N,[10,2])     # make credit offer  (credit officer)
10 Task(N,[10,2])      # notify rejection   (credit officer)
# 11 Task(None,[0])     # receive customer feedback (system)
11 XorGate("=B(0.2)") # notify rejection (20/80)
12 XorGate()
13 End()
1->2; 2->3; 2->4; 3->5; 4->5; 5->6; 6->7; 7->8; 8->9; 8->10;
10->11; 9->12; 11->12; 11->6; 12->13 
# 9->11; 10->13; 11->12; 12->13; 12->6; 13->14
"""
ex20="""
1 Start(E,[2.0],20.0) 
2 XorGate()
3 Task(U,[2.0,3.0])
4/3/2 Task(U,[2.0,3.0])
5/4/2 Task(U,[2.0,3.0]) 
6/5/2 Task(U,[2.0,3.0]) 
7 XorGate() 
8 End()
1->2; 2->3; 3->7;             7->8
      2->4; 4->5; 5->6; 6->7;
"""
ex21="""
# Credit card application - time in 10min units
1 Start(E,[1],-40)      # 2 clerks (25$/h), 3 credit officers (50$/h) 
2 AndGate()
3 Task(N,[1,2/10])      # check credit history (clerk)
4 Task(N,[2,4/10])      # check income sources  (clerk)
5 AndGate()
6 XorGate()
7 Task(E,[2])           # assess application (credit officer)
8 XorGate("=B(0.5)")    # decission review requested (20/80)
9 Task(N,[1,2/10])      # make credit offer  (credit officer)
10 Task(N,[1,2/10])     # notify rejection   (credit officer)
11 End()
12 XorGate("=(A.n-1)%2")   # notify rejection (20/80)
13 End()
1->2; 2->3; 3->5; 5->6; 6->7; 7->8; 8->9;  9->11;   
      2->4; 4->5;                   8->10; 10->12; 12->6; 12->13;
"""
ex22="""
# G/G/2 test - 2 tasks, 3 servers 
1 Start(U,[1],-20)       
2 AndGate()
3 Task(U,[2],"print(self.id,':',A.n,len(self.queue))") # 1 task/1 server 
4 Task(U,[2],"",2)  # 1 task/2 servers
5 AndGate()
6 End()
1->2; 2->3; 3->5; 5->6
      2->4; 4->5; 
"""
ex23="""
# Procurement Process 
1 Start(E,[1],-40)      
2 Task(N,[1,2/10])      # handle quotation
3 Task(N,[2,4/10])      # approve order
4 XorGate()             # approved?
5 AndGate()             # approved
6/4.5/2 Terminate()     # not approved
7 Task(E,[2])           # handle order
8 Task(E,[2])           # handle shipment
9 AndGate()             # 
10 Task(N,[1,2/10])     # review order
11 End()
1->2; 2->3; 3->4; 4->5; 5->7; 7->9; 9->10; 10->11;
                  4->6; 5->8; 8->9;
"""
ex24="""
# SIR model
1 Start(U,[0.0],-10,"S.a=1/4/10;S.b=1/10")
2 Task(E,["1/(S.a*max(len(self.queue),1)*max(len(ne[2].queue),1))"],"print('2 %g'%self.time,' '.join([str(len(e.queue)) for e in ne]),S.a*max(len(self.queue),1)*max(len(ne[2].queue),1))") 
3 Task(E,["1/(S.b*max(len(self.queue),1))"],"print('3 %g'%self.time,' '.join([str(len(e.queue)) for e in ne]),S.b*max(len(self.queue),1))")
4 End()
1->2; 2->3; 3->4
"""
ex25="""
1 Start(E,[2.0],20.0) 
2 Task(U,[2.0,3.0])   # receive order
3 Task(U,[1.0,3.0])   # check credit
4 XorGate()           # credit ok?
5 Task(U,[2.0,3.0])   # fullfill order
6 XorGate()           # fullfilled?
7 Task(U,[2.0,3.0])   # send invoice
8 End()               # order failed
9 End()               # order complete
1->2; 2->3; 3->4; 4->5; 5->6; 6->7; 7->9
                  4->8;       6->8
"""
ex26="""
# Medicine process
1 Start()     
2 Start()
3 Task()       # send doctor request
4/2/2 Task()   # receive doctor request
5 Task()       # receive appointment
6/3/2 Task()   # send appointment
7 Task()       # send medicine request
8/4/2 Task()   # receive medicine request
9 Task()       # receive medicine
10/5/2 Task()  # send medicine
11 End()
12/6/2 End()
1->3; 3->5; 5->7; 7->9; 9->11
2->4; 3->4; 4->6; 6->5; 6->8; 7->8; 8->10; 10->9; 10->12
"""
ex27="""
1 Start(E,[10],-10)  # 10 events
2 Task()             # Default Task
3 AndGate()
4 Timer(1)           # Delay timer
5 Timer([3,10])      # Cyclic timer
6 AndGate()
7 End()              # 
1->2; 2->3; 3->4; 4->6; 6->7
            3->5; 5->6 
"""
ex28="""
# Order (one time unit -> 5 min)
1 Start(U,[2],-20.0,"S.r=100")      # 20 orders            # every 2 time units, 100 resources available
2 Task(U,[1,3],"o=int(N([10,3]))")  # order registration   # 5-15 min, normally order of 10 resources
3 AndGate()                         #                      # split into two parallel paths
4 Task(U,[1,3])                     # invoice preparation  # 5-15 min
5 Task(U,[3,4])                     # check availability   # 15-20 min
6 XorGate("=B(0.9)")                # correction needed?   # 90% is good
7 Timer(U,[8,16])                   # correction request
8 Task(U,[1,2])                     # invoice corrected
9 XorGate()                         #                      # joins XorGate 6
10 Timer(U,[0,14])                  # payment request
11 Task(U,[1,2])                    # payment registration # 5-10 min
12 AndGate()
13 XorGate("=(S.r>=o)")             # available?
14 Task(U,[3,4],"S.r=S.r-o")        # product packaging    # 15-20 min
15 AndGate() 
16 Task(U,[4,6])                    # order from supplier
17 AndGate()
18 Timer([40,24],"S.r=S.r+100")     # wait for delivery    # every 40 since 24
19 Task(U,[4,6],"S.r=S.r-o")        # repackaging          # 20-30 min
20 Task(U,[4,6])                    # preparation for shipment
21 Timer(U,[16,24])                 # delivery               
22 End()                            # order completed
23 Task(U,[1,2])                    # info to customer     # 5-10 min
24 XorGate("=B(0.1)")               # not accepted?        # 10% do not accept
25 Task(U,[1,2])                    # refund and cancel
26 XorGate()
27 Terminate()
1->2; 2->3; 3->4; 4->6;                   6->9;   9->10; 10->11;         11->12; 12->20; 20->21; 21->22;
                          6->7;   7->8;   8->9;                          
            3->5; 5->13; 13->14;                                 14->26; 26->12; 
                         13->15; 15->16; 16->17; 17->18; 18->19; 19->26;  
                                 15->23; 23->24; 24->25; 24->17; 25->27; 
"""
ex29="""
# Simple example with defualt values and printing Script
1 Start()
2 XorGate()
3 Task()
4 AndGate()
5 Task()
6 AndGate()
7 XorGate()
8 Script("import sys;sys.out.write(cname)") # # self.customer.attr
9 End()
1->2; 2->3;              3->7; 7->8;
      2->4;       4->6;  6->7;
	    4->5; 5->6;
"""
ex30="""
1 Start()
2 Task(U,[1,3])
3 End()
4.2 Condition("=A.n%4")
5 Terminate()
1->2; 2->3;
      2->5
"""
ne=[]
# ---- simulation -----
def main_fun(exn,n): # string representation, number of simulation
      data=[]  # list of events, array of results
      for _ in range(n):
            global ne
            ne = EventNetwork(exn)
            s = Simulator()
            for e in ne:
                  if isinstance(e,Generator):  # add generating events
                        s.add(e)  
            s.run()
            
            if exn==ex5:
                  data.append(BpmnEvent.S["S.bA"]) # save global variable S.bA
            else:
                  data.append(s.time)   # save end time of simulation
            if _==0:
                  pass
                  #print(to_bpmn(ne.ee,ne.pp),file=open('des.bpmn','w'))
                  #print(bpmn_tosvg('des.bpmn'),file=open('des_bpmn.svg','w'))
                  ##print(to_svg(),file=open('des.svg','w'))
                  print(to_dot(),file=open('des.dot','w'))
            #for nn in [1,2,3,4,5,6,7,8,9,10,11,12]:
            #      if eval("exn==ex"+str(nn)):
            #            print(to_svg(),file=open('ex'+str(nn)+'_des.svg','w'))
            #            print(bpmn_tosvg('des.bpmn'),file=open('ex'+str(nn)+'_bpmn.svg','w'))         
      for e in ne:
            if len(e.queue)>0:
                  print(e.id,"(%d):"%len(e.queue),e.queue)
                  #print(e.id,"(%d):"%len(e.queue),e.queue,file=open("des.out","w"))
      print(sum(data)/len(data))
      #print(sum(data)/len(data),file=open("des.out","a"))
      print(BpmnEvent.S)
      s=''
      for e in ne:
            s+=str(e.id)+str(e.A)+' '
            if isinstance(e,Task):
                  for i in range(len(e.servers)):
                        s+=str(e.servers[i].id)+'/'+str(i+1)+str(e.servers[i].A)+' '                        
      #print(s)
      if len(data)>100:
            if exn==ex4:
                  hist(data,7)
            else:
                  hist(data)
      #if len(snk.queue.objects)>0: print(dict_tostring(snk.queue.objects[0].attr)) 
      #print("\n".join([attr_tostring(c.attr) for c in snk.queue.objects]))
      #return ne
      return s

# ----- main with args ------
if __name__=="__main__":
      import sys
      s = len(sys.argv)>1 and from_file(sys.argv[1]) or eval('ex'+str(30))
      n = len(sys.argv)>2 and int(sys.argv[2]) or 1
      #print(s)
      
      #ne = main_fun(s,n)
      #for nn in range(1,12+1): print("%d:"%nn),main_fun(eval('ex'+str(nn)),n)
      #print(T([1,21]))
      s2 = main_fun(s,n)
      print(s2)
