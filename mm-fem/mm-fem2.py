# piezo axisymmetric FEM on triangles
# MM 9.9.2024, 3.2.2026
import math
import numpy as np

# ---- frequency
f0 = 126e3              
# ---- geometry
R, T, Mr, Mz  = 0.019,0.0141, 19,14   # mesh size
# ---- piezo material: PIC255
c11 = 122.9070e9*(1+1j/58.6)  # elastic
c12 =  76.6089e9*(1+1j/58.6)       
c13 =  71.1780e9*(1+1j/80)  
c33 =  97.0560e9*(1+1j/145) 
c44 =  23.5000e9*(1+1j/120)  
e31 =  -7.8417                # piezoelectric
e33 =  13.5583  
e15 =  12.2440
epsS11 = 8.234e-9*(1-1j/50)   # dielectric
epsS33 = 7.580e-9*(1-1j/50)
rho = 7800
C = np.array([[c11, c12, c13, 0  ,  0  ,  e31]\
             ,[c12, c11, c13, 0  ,  0  ,  e31]\
             ,[c13, c13, c33, 0  ,  0  ,  e33]\
             ,[0  , 0  , 0  , c44,  e15,   0 ]\
             ,[0  , 0  , 0  , e15,-epsS11, 0 ]\
             ,[e31, e31, e33, 0  ,  0  ,-epsS33]])

# ---- shape: Gauss 1-point integration for triangle
def shape(xi):
	x,y = tuple(xi)
	return np.array([1.0-x-y, x, y]),np.array([[-1, 1, 0],[-1, 0, 1]])
# ---- rectangular grid
def mesh(M, N, R, T):
        xx = np.linspace(0.0, R, M+1)
        yy = np.linspace(0.0, T, N+1)
        nodes =  np.array([[x,y] for y in yy for x in xx])
        elems = []
        for j in range(Mz):
                for i in range(M):
                        n = i + j*(M+1)
                        elems.append([n, n + 1, n + 2 + M])
                        elems.append([n, n + 2 + M, n + M + 1])
        return nodes,elems

# ---- mesh
nodes,elems = mesh(Mr,Mz,R,T)
gpn,gwn = [[1/3,1/3]], [1]       # Gauss points and weights
NN = len(nodes)
print(f"mesh:{Mr}x{Mz} nodes:{NN} elems:{len(elems)} K:{3*NN}x{3*NN}")

# ----- stiffness/mass matrix 
K,M = np.zeros((3*NN,3*NN),dtype=C.dtype), np.zeros((3*NN,3*NN),dtype=C.dtype)
B,H = np.zeros((len(C),3*len(elems[0]))), np.zeros((2,3*len(elems[0])))
for el in elems:
        xy = nodes[el,:]
        Ke = np.zeros((3*len(el),3*len(el)),dtype=C.dtype)
        Me = np.zeros((3*len(el),3*len(el)),dtype=C.dtype)
        for gp,gw in zip(gpn,gwn):
                N, dN = shape(gp)
                r, JJ = xy[:,0] @ N, xy.T @ dN.T
                dN, detJJ = np.linalg.inv(JJ).T @ dN, np.linalg.det(JJ)/2
                B[0,0::3]           = dN[0,:]
                B[1,0::3]           =  N/r
                B[2,1::3]           =          dN[1,:]
                B[3,0::3],B[3,1::3] = dN[1,:], dN[0,:]
                B[4,2::3]           =                  dN[0,:]
                B[5,2::3]           =                  dN[1,:]
                H[0,0::3]           =   N
                H[1,1::3]           =             N
                Ke +=  r * (B.T @ C @ B)   * detJJ * gw
                Me +=  r * (H.T @ H) * rho * detJJ * gw
        for i,I in enumerate(el):
                for j,J in enumerate(el):
                        for k in range(3):
                                for l in range(3):
                                        K[3*I+k,3*J+l] += Ke[3*i+k,3*j+l]
                                        M[3*I+k,3*J+l] += Me[3*i+k,3*j+l]
#------ boundary conditions
f = np.zeros(3*NN,dtype=C.dtype); idx0V,idx1V=[],[]
for i in range(NN):
        if nodes[i,0] == 0:                                # axis
                K[3*i+0,3*i+0], f[3*i+0] = 1.0e30, 0.0e30  # ur=0
        if nodes[i,1] == 0:                                # bottom
                K[3*i+2,3*i+2], f[3*i+2] = 1.0e30, 1.0e30  # phi=1V
                idx1V.append(i)
        if nodes[i,1] == T:                                # top
                K[3*i+2,3*i+2], f[3*i+2] = 1.0e30, 0.0e30  # phi=0V
                idx0V.append(i)

# ---- solution
pi = np.pi
w = 2*pi*f0
A = -w**2 * M + K
u = np.linalg.solve(A, f)
        
# ---- print admittance
Y = -2*pi*1j*w*sum([np.conj(K[i,3*j+2])*u[i] for j in idx1V for i in range(3*NN) if K[i,3*j+2]!=1e30])
print(f"f={f0/1e3}kHz Y={Y:.4g}")

# ---- plot displacements
from matplotlib import pyplot as plt
c = 1e6    # plot coefficient
ux, uy, uphi = np.zeros(NN), np.zeros(NN), np.zeros(NN)
for i in range(NN):
        x, y = nodes[i] 
        ux[i] = x + c * np.real(u[3*i])
        uy[i] = y + c * np.real(u[3*i+1])
        uphi[i] = np.abs(u[3*i+2])
plt.clf(); plt.grid(); plt.axis('equal'); plt.title(f"f={f0/1e3} [kHz]")
for i in range(len(elems)):                 # draw original mesh
        x, y = nodes[elems[i],0], nodes[elems[i],1]
        idx = [0,1,2,0] # order of triangle
        plt.plot(x[idx],y[idx],'ko-',lw=0.5,markersize=2)
        idx2 = [elems[i][_] for _ in idx]   # draw deformed mesh
        plt.plot([ux[_] for _ in idx2], [uy[_] for _ in idx2],'r-')
plt.scatter(ux, uy, marker='o', c='r', s=8) # draw deformed nodes
plt.show();

