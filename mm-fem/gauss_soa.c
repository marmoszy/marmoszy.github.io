/* Linear equations solver using gauss elimination for complex numbers in structure of arrays */
/* MM 30.1.2026 and earlier */

/* Complex mul and div */

static inline void c_mul_soa(double ar,double ai, double br,double bi, double *rr,double *ri) {
    *rr = ar*br - ai*bi;
    *ri = ar*bi + ai*br;
}
static inline void c_div_soa(double ar,double ai, double br,double bi, double *rr,double *ri) {
    double d = br*br + bi*bi;
    *rr = (ar*br + ai*bi) / d;
    *ri = (ai*br - ar*bi) / d;
}

/* Naive Gauss factorization (SoA):  A[n×n], ld-leading dimension */

void gauss_factor_opt_ld_soa(int n, double *Are, double *Aim, int ld) {
    for (int k = 0; k < n; k++) {
        double akk_re = Are[k*ld + k];
        double akk_im = Aim[k*ld + k];
        for (int i = k + 1; i < n; i++) {
            double aik_re = Are[i*ld + k];
            double aik_im = Aim[i*ld + k];
            double mik_re, mik_im;
            c_div_soa(aik_re, aik_im, akk_re, akk_im, &mik_re, &mik_im);
            Are[i*ld + k] = mik_re;
            Aim[i*ld + k] = mik_im;
            for (int j = k + 1; j < n; j++) {
                double aij_re = Are[i*ld + j];
                double aij_im = Aim[i*ld + j];
                double akj_re = Are[k*ld + j];
                double akj_im = Aim[k*ld + j];
                double prod_re, prod_im;
                c_mul_soa(mik_re, mik_im, akj_re, akj_im, &prod_re, &prod_im);
                Are[i*ld + j] = aij_re - prod_re;
                Aim[i*ld + j] = aij_im - prod_im;
            }
        }
    }
}

/* Forward solve: L y = b (unit L) */

void solve_L_ld_soa(int n, double *Are, double *Aim, int ld, double *bre, double *bim) {
    for (int i = 0; i < n; i++) {
        double xi_re = bre[i];
        double xi_im = bim[i];
        for (int j = 0; j < i; j++) {
            double lij_re = Are[i*ld + j];
            double lij_im = Aim[i*ld + j];
            double xj_re = bre[j];
            double xj_im = bim[j];
            double prod_re, prod_im;
            c_mul_soa(lij_re,lij_im, xj_re,xj_im, &prod_re,&prod_im);
            xi_re -= prod_re;
            xi_im -= prod_im;
        }
        bre[i] = xi_re;
        bim[i] = xi_im;
    }
}

/* Backward solve: U x = y */

void solve_U_ld_soa(int n,double *Are, double *Aim, int ld,double *bre, double *bim) {
    for (int i = n - 1; i >= 0; i--) {
        double xi_re = bre[i];
        double xi_im = bim[i];
        for (int j = i + 1; j < n; j++) {
            double uij_re = Are[i*ld + j];
            double uij_im = Aim[i*ld + j];
            double xj_re = bre[j];
            double xj_im = bim[j];
            double prod_re, prod_im;
            c_mul_soa(uij_re,uij_im, xj_re,xj_im, &prod_re,&prod_im);
            xi_re -= prod_re;
            xi_im -= prod_im;
        }
        double uii_re = Are[i*ld + i];
        double uii_im = Aim[i*ld + i];
        double sol_re, sol_im;
        c_div_soa(xi_re,xi_im, uii_re,uii_im, &sol_re,&sol_im);
        bre[i] = sol_re;
        bim[i] = sol_im;
    }
}

/* Full solve: (LU) x = b */

void gauss_solve_ld_soa(int n,double *Are, double *Aim, int ld, double *bre, double *bim) {
    solve_L_ld_soa(n, Are,Aim, ld, bre,bim);
    solve_U_ld_soa(n, Are,Aim, ld, bre,bim);
}

/* WASM-friendly entry points */

/* Factorization: A = LU (in-place) */

void run_gauss0(int n, double *Are,double *Aim) { 
    gauss_factor_opt_ld_soa(n, Are,Aim, n);
}

/* Solve: (LU) x = b, overwriting b with x */

void run_gauss1(int n, double *Are,double *Aim, double *bre,double *bim) {
    gauss_solve_ld_soa(n, Are,Aim, n, bre,bim);
}


