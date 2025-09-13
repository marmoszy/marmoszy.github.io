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
8 XorGate("=B(0.5)")    # decision review requested (20/80)
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
