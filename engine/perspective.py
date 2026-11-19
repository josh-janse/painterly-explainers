# One-point ground perspective (exec after engine.py). One eye level per poster.
# RULES
#  1. The horizon is the eye level. On flat ground, an object's apparent size is proportional to (y - HZ):
#     twice as far below the horizon = twice as big. Everything standing on the ground obeys this.
#  2. Calibrate once per poster (e.g. "a 1.75 m person standing at y=0.885 is 30 mm tall"); never size objects independently.
#  3. Things lying on the ground (towels, paths, boards) are rectangles in metres projected to the page:
#     their sides converge on a vanishing point on the horizon, and their depth foreshortens.
#  4. A stylised poster may exaggerate the foreground slightly, but the ORDER of sizes must always follow rule 1.
class Ground:
    def __init__(self, HZ, ref_y, ref_mm, ref_m=1.75, F=1.3, vpx=0.5):
        self.HZ, self.F, self.vpx = HZ, F, vpx
        self.kk = (ref_mm / PAGE_MM[1]) / (ref_y - HZ) / ref_m        # page-height units per metre, per unit of (y - HZ)
        self.c = 1.0 / self.kk                                          # implied camera height in metres
    def m(self, y):        return self.kk * (y - self.HZ)               # page-height units per metre at ground row y
    def mm(self, y, metres): return metres * self.m(y) * PAGE_MM[1]     # size in mm of an object `metres` tall standing at y
    def human_mm(self, y): return self.mm(y, 1.75)
    def y_behind(self, y_near, d):
        """ground row d metres further away than y_near"""
        z = self.F / self.m(y_near)                                     # distance to that row (page-units scale)
        return self.HZ + self.c * self.F / (z + d)                      # y - HZ = camera_height * scale, and scale = F / distance
    def to_page(self, xw, y_near, d=0.0):
        """world x (metres, 0 = vanishing line) at depth d behind ground row y_near -> page (x, y)"""
        y = self.y_behind(y_near, d) if d else y_near
        return self.vpx + xw * self.m(y) * PAGE_MM[1] / PAGE_MM[0], y
    def world_x(self, px, y): return (px - self.vpx) / (self.m(y) * PAGE_MM[1] / PAGE_MM[0])
    def quad(self, cx, y_near, length_m, depth_m, x0_frac=0.0, x1_frac=1.0):
        """flat rectangle on the ground, long side across the view, near edge centred at page x=cx on row y_near"""
        xc = self.world_x(cx, y_near); a = xc - length_m / 2 + length_m * x0_frac; b = xc - length_m / 2 + length_m * x1_frac
        return [self.to_page(a, y_near), self.to_page(b, y_near), self.to_page(b, y_near, depth_m), self.to_page(a, y_near, depth_m)]

# ---- world coordinates on the ground plane (X metres to the right of the vanishing line, Z metres away from the camera)
def _to_world(self, px, py):
    m = self.m(py); return (px - self.vpx) * (PAGE_MM[0] / PAGE_MM[1]) / m, self.F / m
def _from_world(self, Xw, Zw, h=0.0):
    """ground point (Xw, Zw), optionally raised h metres above the ground -> page (x, y)"""
    m = self.F / Zw; y = self.HZ + self.c * m
    return self.vpx + Xw * m * PAGE_MM[1] / PAGE_MM[0], y - h * m
Ground.to_world = _to_world; Ground.from_world = _from_world

def sun_world(azimuth_deg, elevation_deg):
    """shadow offset on the ground, in metres per metre of height. azimuth: direction the shadows fall, measured from
    +X (right) toward +Z (away from us): 0 = right, 90 = away, 180 = left, 270 = toward us."""
    a, e = np.radians(azimuth_deg), np.radians(elevation_deg); L = 1 / np.tan(e)
    return (np.cos(a) * L, np.sin(a) * L)

def ground_shadow(G, sw, Xw, Zw, h):
    """page position of the shadow of a point h metres above ground point (Xw, Zw)"""
    return G.from_world(Xw + h * sw[0], Zw + h * sw[1])

def sun_from_page(G, sx, sy):
    """a sun disc painted at page (sx, sy) -> (azimuth, elevation) for sun_world, so every shadow agrees with the visible sun.
    A sun in the sky ahead throws shadows toward the viewer, radiating from the point on the horizon below it."""
    dx = (sx - G.vpx) * PAGE_MM[0] / PAGE_MM[1] / G.F                    # sideways per unit of forward distance
    dy = (G.HZ - sy) / G.F                                               # upward per unit of forward distance
    az_to_sun = np.degrees(np.arctan2(1.0, dx))
    return (az_to_sun + 180.0) % 360.0, float(np.degrees(np.arctan2(dy, np.hypot(dx, 1.0))))
