## mm-fem 

The minimalistic FEM code in html+wasm, python+numpy and freefem for the calculation of piezoelectric circular disk vabrations in the air (free vibrations). It implements variational equations in axisymetric mode. As material coefficients it uses PIC255 piezoelectric data. The default frequency is defined to be close to the thickness resonanse mode for circular disk with radius of R=1.9cm and thickness of T=1.41cm. 

![](mm-fem2-html.png)

**Fig.1. Html screendump.**


![](mm-fem2-py.png)

**Fig.2. Python matplotlib generated vibrations**


![](mm-fem-edp_126_19_14.png)

**Fig.3. Freefem generated vibrations.**

There is also code for axisymmetric transducer design prepared in freefem:

- circular disk design **(mm-fem2.5a.edp)**
- circular dick with sonic crystals **(mm-fem2.5b.edp)**
