#####################################################################
####                   FUTURE (POISSON / CORRECTOR)              ####
#####################################################################

import numpy
from numba import jit # type: ignore

@jit(nopython=True)
def boundary2d(field, xtype, ytype):
    if xtype == 'dirichlet':
        field[1:-1, 0] = -field[1:-1, 1]
        field[1:-1,-1] = -field[1:-1,-2]
    elif xtype == 'neumann':
        field[1:-1, 0] = field[1:-1, 1]
        field[1:-1,-1] = field[1:-1,-2]
    elif xtype == 'periodic':
        field[1:-1, 0] = field[1:-1,-2]
        field[1:-1,-1] = field[1:-1, 1]
    else:
        pass
    if ytype == 'dirichlet':
        field[ 0,1:-1] = -field[ 1,1:-1]
        field[-1,1:-1] = -field[-2,1:-1]
    elif ytype == 'neumann':
        field[ 0,1:-1] = field[ 1,1:-1]
        field[-1,1:-1] = field[-2,1:-1]
    elif ytype == 'periodic':
        field[ 0,1:-1] = field[-2,1:-1]
        field[-1,1:-1] = field[ 1,1:-1]
    else:
        pass

@jit(nopython=True)
def boundary3d(field, xtype, ytype, ztype):
    if xtype == 'dirichlet':
        field[1:-1,1:-1, 0] = -field[1:-1,1:-1, 1]
        field[1:-1,1:-1,-1] = -field[1:-1,1:-1,-2]
    elif xtype == 'neumann':
        field[1:-1,1:-1, 0] = field[1:-1,1:-1, 1]
        field[1:-1,1:-1,-1] = field[1:-1,1:-1,-2]
    elif xtype == 'periodic':
        field[1:-1,1:-1, 0] = field[1:-1,1:-1,-2]
        field[1:-1,1:-1,-1] = field[1:-1,1:-1, 1]
    else:
        pass
    if ytype == 'dirichlet':
        field[1:-1, 0,1:-1] = -field[1:-1, 1,1:-1]
        field[1:-1,-1,1:-1] = -field[1:-1,-2,1:-1]
    elif ytype == 'neumann':
        field[1:-1, 0,1:-1] = field[1:-1, 1,1:-1]
        field[1:-1,-1,1:-1] = field[1:-1,-2,1:-1]
    elif ytype == 'periodic':
        field[1:-1, 0,1:-1] = field[1:-1,-2,1:-1]
        field[1:-1,-1,1:-1] = field[1:-1, 1,1:-1]
    else:
        pass
    if ztype == 'dirichlet':
        field[ 0,1:-1,1:-1] = -field[ 1,1:-1,1:-1]
        field[-1,1:-1,1:-1] = -field[-2,1:-1,1:-1]
    elif ztype == 'neumann':
        field[ 0,1:-1,1:-1] = field[ 1,1:-1,1:-1]
        field[-1,1:-1,1:-1] = field[-2,1:-1,1:-1]
    elif ztype == 'periodic':
        field[ 0,1:-1,1:-1] = field[-2,1:-1,1:-1]
        field[-1,1:-1,1:-1] = field[ 1,1:-1,1:-1]
    else:
        pass

def correct(*, ndim = 2, delp, u, v, w = None, xfaces, yfaces, zfaces = None, xtype, ytype, ztype = None):
    """Correct a velocity distribution to be diveregence free using a forcing pressure field."""
    if ndim == 2:
        correct2d(delp, u, v, xfaces, yfaces, xtype, ytype)
    elif ndim == 3:
        correct3d(delp, u, v, w, xfaces, yfaces, zfaces, xtype, ytype, ztype)
    else:
        pass

def correct2d(delp, u, v, xfaces, yfaces, xtype, ytype):

    xfac, xcnt, yfac, ycnt = grids2d(xfaces, yfaces)
    ddxe, _, ddxw, ddyn, _, ddys = metrics2d(xfac, xcnt, yfac, ycnt)

    u[:,1:-1] = u[:,1:-1] - ddxe[None,:-1] * (delp[:,1:] - delp[:,:-1])
    v[1:-1,:] = v[1:-1,:] - ddyn[:-1,None] * (delp[1:,:] - delp[:-1,:])

    if xtype == 'dirichlet':
        u[:, 0] = 0.0
        u[:,-1] = 0.0
    elif xtype == 'neumann':
        u[:, 0] = u[:, 1]
        u[:,-1] = u[:,-2]
    elif xtype == 'periodic':
        u[:, 0] = u[:, 0] - ddxw[None, 0] * (delp[:,0] - delp[:,-1])
        u[:,-1] = u[:,-1] - ddxe[None,-1] * (delp[:,0] - delp[:,-1])
    else:
        pass
    
    if ytype == 'dirichlet':
        v[ 0,:] = 0.0
        v[-1,:] = 0.0
    elif ytype == 'neumann':
        v[ 0,:] = v[ 1,:]
        v[-1,:] = v[-2,:]
    elif ytype == 'periodic':
        v[ 0,:] = v[ 0,:] - ddys[ 0,None] * (delp[0,:] - delp[-1,:])
        v[-1,:] = v[-1,:] - ddyn[-1,None] * (delp[0,:] - delp[-1,:])
    else:
        pass

def correct3d(delp, u, v, w, xfaces, yfaces, zfaces, xtype, ytype, ztype):

    xfac, xcnt, yfac, ycnt, zfac, zcnt = grids3d(xfaces, yfaces, zfaces)
    ddxe, _, ddxw, ddyn, _, ddys, ddzt, _, ddzb = metrics3d(xfac, xcnt, yfac, ycnt, zfac, zcnt)

    u[:,:,1:-1] = u[:,:,1:-1] - ddxe[None,None,:-1] * (delp[:,:,1:] - delp[:,:,:-1])
    v[:,1:-1,:] = v[:,1:-1,:] - ddyn[None,:-1,None] * (delp[:,1:,:] - delp[:,:-1,:])
    w[1:-1,:,:] = w[1:-1,:,:] - ddzt[:-1,None,None] * (delp[1:,:,:] - delp[:-1,:,:])

    if xtype == 'dirichlet':
        u[:,:, 0] = 0.0
        u[:,:,-1] = 0.0
    elif xtype == 'neumann':
        u[:,:, 0] = u[:,:, 1]
        u[:,:,-1] = u[:,:,-2]
    elif xtype == 'periodic':
        u[:,:, 0] = u[:,:, 0] - ddxw[None,None, 0] * (delp[:,:,0] - delp[:,:,-1])
        u[:,:,-1] = u[:,:,-1] - ddxe[None,None,-1] * (delp[:,:,0] - delp[:,:,-1])
    else:
        pass
    
    if ytype == 'dirichlet':
        v[:, 0,:] = 0.0
        v[:,-1,:] = 0.0
    elif ytype == 'neumann':
        v[:, 0,:] = v[:, 1,:]
        v[:,-1,:] = v[:,-2,:]
    elif ytype == 'periodic':
        v[:, 0,:] = v[:, 0,:] - ddys[None, 0,None] * (delp[:,0,:] - delp[:,-1,:])
        v[:,-1,:] = v[:,-1,:] - ddyn[None,-1,None] * (delp[:,0,:] - delp[:,-1,:])
    else:
        pass
    
    if ztype == 'dirichlet':
        w[ 0,:,:] = 0.0
        w[-1,:,:] = 0.0
    elif ztype == 'neumann':
        w[ 0,:,:] = w[ 1,:,:]
        w[-1,:,:] = w[-2,:,:]
    elif ztype == 'periodic':
        w[ 0,:,:] = w[ 0,:,:] - ddzb[ 0,None,None] * (delp[0,:,:] - delp[-1,:,:])
        w[-1,:,:] = w[-1,:,:] - ddzt[-1,None,None] * (delp[0,:,:] - delp[-1,:,:])
    else:
        pass

def divergence(*, ndim = 2, u, v, w = None, xfaces, yfaces, zfaces = None):
    """Calculate the divergance of a face centered field."""
    if ndim == 2:
        return divergence2d(u, v, xfaces, yfaces)
    elif ndim == 3:
        return divergence3d(u, v, w, xfaces, yfaces, zfaces)
    else:
        pass

def divergence2d(u, v, xfaces, yfaces):
    _, ddxo, _, _, ddyo, _ = metrics2d(*grids2d(xfaces, yfaces))
    return ddxo[None,:] * (u[:,1:] - u[:,:-1]) + ddyo[:,None] * (v[1:,:] - v[:-1,:])

def divergence3d(u, v, w, xfaces, yfaces, zfaces):
    _, ddxo, _, _, ddyo, _, _, ddzo, _ = metrics3d(*grids3d(xfaces, yfaces, zfaces))
    return ddxo[None,None,:] * (u[:,:,1:] - u[:,:,:-1]) + ddyo[None,:,None] * (v[:,1:,:] - v[:,:-1,:]) + ddzo[:,None,None] * (w[1:,:,:] - w[:-1,:,:])

@jit(nopython=True)
def grids2d(xfaces, yfaces):
    nyb, nxb = len(yfaces), len(xfaces)

    xfac = numpy.zeros(nxb + 2)
    xfac[1:-1] = xfaces.copy()
    xfac[0] = xfac[2] + 2 * (xfac[1] - xfac[2])
    xfac[-1] = xfac[-3] + 2 * (xfac[-2] - xfac[-3])
    
    xcnt = numpy.zeros(nxb - 1 + 2)
    xcnt[1:-1] = (xfac[2:-1] + xfac[1:-2]) / 2
    xcnt[0] = xcnt[2] + 2 * (xcnt[1] - xcnt[2])
    xcnt[-1] = xcnt[-3] + 2 * (xcnt[-2] - xcnt[-3])

    yfac = numpy.zeros(nyb + 2)
    yfac[1:-1] = yfaces.copy()
    yfac[0] = yfac[2] + 2 * (yfac[1] - yfac[2])
    yfac[-1] = yfac[-3] + 2 * (yfac[-2] - yfac[-3])

    ycnt = numpy.zeros(nyb - 1 + 2)
    ycnt[1:-1] = (yfac[2:-1] + yfac[1:-2]) / 2
    ycnt[0] = ycnt[2] + 2 * (ycnt[1] - ycnt[2])
    ycnt[-1] = ycnt[-3] + 2 * (ycnt[-2] - ycnt[-3])

    return xfac, xcnt, yfac, ycnt

@jit(nopython=True)
def grids3d(xfaces, yfaces, zfaces):
    nzb, nyb, nxb = len(zfaces), len(yfaces), len(xfaces)

    xfac = numpy.zeros(nxb + 2)
    xfac[1:-1] = xfaces.copy()
    xfac[0] = xfac[2] + 2 * (xfac[1] - xfac[2])
    xfac[-1] = xfac[-3] + 2 * (xfac[-2] - xfac[-3])
    
    xcnt = numpy.zeros(nxb - 1 + 2)
    xcnt[1:-1] = (xfac[2:-1] + xfac[1:-2]) / 2
    xcnt[0] = xcnt[2] + 2 * (xcnt[1] - xcnt[2])
    xcnt[-1] = xcnt[-3] + 2 * (xcnt[-2] - xcnt[-3])

    yfac = numpy.zeros(nyb + 2)
    yfac[1:-1] = yfaces.copy()
    yfac[0] = yfac[2] + 2 * (yfac[1] - yfac[2])
    yfac[-1] = yfac[-3] + 2 * (yfac[-2] - yfac[-3])

    ycnt = numpy.zeros(nyb - 1 + 2)
    ycnt[1:-1] = (yfac[2:-1] + yfac[1:-2]) / 2
    ycnt[0] = ycnt[2] + 2 * (ycnt[1] - ycnt[2])
    ycnt[-1] = ycnt[-3] + 2 * (ycnt[-2] - ycnt[-3])

    zfac = numpy.zeros(nzb + 2)
    zfac[1:-1] = zfaces.copy()
    zfac[0] = zfac[2] + 2 * (zfac[1] - zfac[2])
    zfac[-1] = zfac[-3] + 2 * (zfac[-2] - zfac[-3])

    zcnt = numpy.zeros(nzb - 1 + 2)
    zcnt[1:-1] = (zfac[2:-1] + zfac[1:-2]) / 2
    zcnt[0] = zcnt[2] + 2 * (zcnt[1] - zcnt[2])
    zcnt[-1] = zcnt[-3] + 2 * (zcnt[-2] - zcnt[-3])

    return xfac, xcnt, yfac, ycnt, zfac, zcnt

@jit(nopython=True)
def l2norm2d(new, old, ddxo, ddyo):
    nyb, nxb = new.shape
    normal, scaled = 0.0, 0.0
    for j in range(nyb - 2):
        for i in range(nxb - 2):
            l, m = j+1, i+1
            local = 1 / (ddxo[i] * ddyo[j])
            normal += (new[l,m] - old[l,m])**2 * local
            scaled += old[l,m]**2 * local
    return numpy.sqrt(normal / scaled)

@jit(nopython=True)
def l2norm3d(new, old, ddxo, ddyo, ddzo):
    nzb, nyb, nxb = new.shape
    normal, scaled = 0.0, 0.0
    for k in range(nzb - 2):
        for j in range(nyb - 2):
            for i in range(nxb - 2):
                l, m, n = k+1, j+1, i+1
                local = 1 / (ddxo[i] * ddyo[j] * ddzo[k])
                normal += (new[l,m,n] - old[l,m,n])**2 * local
                scaled += old[l,m,n]**2 * local
    return numpy.sqrt(normal / scaled)

@jit(nopython=True)
def normalize2d(field, ddxo, ddyo):
    nyb, nxb = field.shape
    normal, volume = 0.0, 0.0
    for j in range(nyb - 2):
        for i in range(nxb - 2):
            l, m = j+1, i+1
            local = 1 / (ddxo[i] * ddyo[j])
            normal += field[l,m] * local
            volume += local
    normal = normal / volume
    field[1:-1,1:-1] = field[1:-1,1:-1] - normal

@jit(nopython=True)
def normalize3d(field, ddxo, ddyo, ddzo):
    nzb, nyb, nxb = field.shape
    normal, volume = 0.0, 0.0
    for k in range(nzb - 2):
        for j in range(nyb - 2):
            for i in range(nxb - 2):
                l, m, n = k+1, j+1, i+1
                local = 1 / (ddxo[i] * ddyo[j] * ddzo[k])
                normal += field[l,m,n] * local
                volume += local
    normal = normal / volume
    field[1:-1,1:-1,1:-1] = field[1:-1,1:-1,1:-1] - normal
    
@jit(nopython=True)
def magnitude2d(u, v):
    return numpy.sqrt(0.25 * (u[:,1:] + u[:,:-1])**2 + 0.25 * (v[1:,:] + v[:-1,:])**2)

@jit(nopython=True)
def magnitude3d(u, v, w):
    return numpy.sqrt(0.25 * (u[:,:,1:] + u[:,:,:-1])**2 + 0.25 * (v[:,1:,:] + v[:,:-1,:])**2 + 0.25 * (w[1:,:,:] + w[:-1,:,:])**2)

@jit(nopython=True)
def metrics2d(xfac, xcnt, yfac, ycnt):

    ddxw = 1 / (xcnt[1:-1] - xcnt[:-2])
    ddxo = 1 / (xfac[2:-1] - xfac[1:-2])
    ddxe = 1 / (xcnt[2:] - xcnt[1:-1])

    ddys = 1 / (ycnt[1:-1] - ycnt[:-2])
    ddyo = 1 / (yfac[2:-1] - yfac[1:-2])
    ddyn = 1 / (ycnt[2:] - ycnt[1:-1])

    return ddxe, ddxo, ddxw, ddyn, ddyo, ddys

@jit(nopython=True)
def metrics3d(xfac, xcnt, yfac, ycnt, zfac, zcnt):

    ddxw = 1 / (xcnt[1:-1] - xcnt[:-2])
    ddxo = 1 / (xfac[2:-1] - xfac[1:-2])
    ddxe = 1 / (xcnt[2:] - xcnt[1:-1])

    ddys = 1 / (ycnt[1:-1] - ycnt[:-2])
    ddyo = 1 / (yfac[2:-1] - yfac[1:-2])
    ddyn = 1 / (ycnt[2:] - ycnt[1:-1])

    ddzb = 1 / (zcnt[1:-1] - zcnt[:-2])
    ddzo = 1 / (zfac[2:-1] - zfac[1:-2])
    ddzt = 1 / (zcnt[2:] - zcnt[1:-1])

    return ddxe, ddxo, ddxw, ddyn, ddyo, ddys, ddzt, ddzo, ddzb

def poisson(*, ndim = 2, source, xfaces, yfaces, zfaces = None, xtype, ytype, ztype = None, tolerance = 1E-5, check = 20, itermax = 1E6):
    """Solve the poisson equation using cell centered finite differences and a simple stational method."""
    if ndim == 2:
        return poisson2d(source, xfaces, yfaces, xtype, ytype, tolerance, check, itermax)
    elif ndim == 3:
        return poisson3d(source, xfaces, yfaces, zfaces, xtype, ytype, ztype, tolerance, check, itermax)
    else:
        pass

@jit(nopython=True)
def poisson2d(source, xfaces, yfaces, xtype, ytype, tolerance, check, itermax):

    ny, nx = source.shape
    field = numpy.zeros(((ny + 2), (nx + 2)))
    xfac, xcnt, yfac, ycnt = grids2d(xfaces, yfaces)
    ddxe, ddxo, ddxw, ddyn, ddyo, ddys = metrics2d(xfac, xcnt, yfac, ycnt)

    norm = relax2d(source, field, xtype, ytype, ddxe, ddxo, ddxw, ddyn, ddyo, ddys, tolerance, check, itermax)

    if xtype in ('periodic', 'neumann') and ytype in ('periodic', 'neumann'):
        normalize2d(field, ddxo, ddyo)
        boundary2d(field, xtype, ytype)

    return field[1:-1,1:-1], norm

@jit(nopython=True)
def poisson3d(source, xfaces, yfaces, zfaces, xtype, ytype, ztype, tolerance, check, itermax):

    nz, ny, nx = source.shape
    field = numpy.zeros(((nz + 2), (ny + 2), (nx + 2)))
    xfac, xcnt, yfac, ycnt, zfac, zcnt = grids3d(xfaces, yfaces, zfaces)
    ddxe, ddxo, ddxw, ddyn, ddyo, ddys, ddzt, ddzo, ddzb = metrics3d(xfac, xcnt, yfac, ycnt, zfac, zcnt)

    norm = relax3d(source, field, xtype, ytype, ztype, ddxe, ddxo, ddxw, ddyn, ddyo, ddys, ddzt, ddzo, ddzb, tolerance, check, itermax)

    if xtype in ('periodic', 'neumann') and ytype in ('periodic', 'neumann') and ztype in ('periodic', 'neumann'):
        normalize3d(field, ddxo, ddyo, ddzo)
        boundary3d(field, xtype, ytype, ztype)

    return field[1:-1,1:-1,1:-1], norm

@jit(nopython=True)
def relax2d(source, field, xtype, ytype, ddxe, ddxo, ddxw, ddyn, ddyo, ddys, tolerance, check, itermax):

    update2d(source, field, ddxe, ddxo, ddxw, ddyn, ddyo, ddys)
    boundary2d(field, xtype, ytype)
    copy = field.copy()
    
    norm = []
    count = 1
    delta =  1.0
    while delta >= tolerance and count <= itermax:

        update2d(source, field, ddxe, ddxo, ddxw, ddyn, ddyo, ddys)
        boundary2d(field, xtype, ytype)

        if count % check == 0:
            delta = l2norm2d(field, copy, ddxo, ddyo)
            norm.append(delta)
            copy = field.copy()
            
        count += 1

    return norm 

@jit(nopython=True)
def relax3d(source, field, xtype, ytype, ztype, ddxe, ddxo, ddxw, ddyn, ddyo, ddys, ddzt, ddzo, ddzb, tolerance, check, itermax):

    update3d(source, field, ddxe, ddxo, ddxw, ddyn, ddyo, ddys, ddzt, ddzo, ddzb)
    boundary3d(field, xtype, ytype, ztype)
    copy = field.copy()
    
    norm = []
    count = 1
    delta =  1.0
    while delta >= tolerance and count <= itermax:

        update3d(source, field, ddxe, ddxo, ddxw, ddyn, ddyo, ddys, ddzt, ddzo, ddzb)
        boundary3d(field, xtype, ytype, ztype)

        if count % check == 0:
            delta = l2norm3d(field, copy, ddxo, ddyo, ddzo)
            norm.append(delta)
            copy = field.copy()
            
        count += 1

    return norm 

@jit(nopython=True)
def update2d(source, field, ddxe, ddxo, ddxw, ddyn, ddyo, ddys):
    nyb, nxb = field.shape
    for j in range(nyb - 2):
        for i in range(nxb - 2):
            l, m = j+1, i+1
            field[l,m] = - source[j,i]
            field[l,m] += ddxo[i] * (ddxe[i] * field[l,m+1] + ddxw[i] * field[l,m-1])
            field[l,m] += ddyo[j] * (ddyn[j] * field[l+1,m] + ddys[j] * field[l-1,m])
            field[l,m] /= ddxo[i] * (ddxe[i] + ddxw[i]) + ddyo[j] * (ddyn[j] + ddys[j])

@jit(nopython=True)
def update3d(source, field, ddxe, ddxo, ddxw, ddyn, ddyo, ddys, ddzt, ddzo, ddzb):
    nzb, nyb, nxb = field.shape
    for k in range(nzb - 2):
        for j in range(nyb - 2):
            for i in range(nxb - 2):
                l, m, n = k+1, j+1, i+1
                field[l,m,n] = - source[k,j,i]
                field[l,m,n] += ddxo[i] * (ddxe[i] * field[l,m,n+1] + ddxw[i] * field[l,m,n-1])
                field[l,m,n] += ddyo[j] * (ddyn[j] * field[l,m+1,n] + ddys[j] * field[l,m-1,n])
                field[l,m,n] += ddzo[k] * (ddzt[k] * field[l+1,m,n] + ddzb[j] * field[l-1,m,n])
                field[l,m,n] /= ddxo[i] * (ddxe[i] + ddxw[i]) + ddyo[j] * (ddyn[j] + ddys[j]) + ddzo[k] * (ddzt[k] + ddzb[k])