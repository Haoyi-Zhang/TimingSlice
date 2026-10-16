"""Vector drawing primitives; copied into each independent project generator."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch

plt.rcParams.update({'font.family':'STIXGeneral', 'mathtext.fontset':'stix',
                     'font.size':9, 'pdf.fonttype':42, 'ps.fonttype':42,
                     'text.usetex':False, 'axes.unicode_minus':False})
CM = 1 / 2.54

class Drawing:
    def __init__(self, bounds):
        x0,y0,x1,y1 = bounds
        self.fig = plt.figure(figsize=((x1-x0)*CM,(y1-y0)*CM))
        self.ax = self.fig.add_axes([0,0,1,1], xlim=(x0,x1), ylim=(y0,y1))
        self.ax.set_aspect('equal'); self.ax.axis('off')
        self.nodes = {}
        self.labels = []

    def text(self,x,y,label,size=9,ha='center',va='center'):
        artist=self.ax.text(x,y,label,fontsize=size,ha=ha,va=va,
                            linespacing=1.15,clip_on=False,zorder=4)
        self.labels.append([artist,None])
        return artist

    def box(self,name,x,y,w,h,label,dashed=False,shape='rect',size=9):
        style = {'edgecolor':'black','facecolor':'white','linewidth':.55,
                 'linestyle':(0,(4,3)) if dashed else 'solid', 'zorder':2}
        if shape == 'diamond':
            obj = Polygon([(x-w/2,y),(x,y+h/2),(x+w/2,y),(x,y-h/2)],**style)
        elif shape == 'circle': obj = Circle((x,y),w/2,**style)
        else: obj = Rectangle((x-w/2,y-h/2),w,h,**style)
        self.ax.add_patch(obj); self.text(x,y,label,size)
        self.labels[-1][1]=(x-w/2,y-h/2,x+w/2,y+h/2)
        self.nodes[name] = (x,y,w,h,shape)

    def point(self,name,side):
        x,y,w,h,_ = self.nodes[name]
        return {'n':(x,y+h/2),'s':(x,y-h/2),'e':(x+w/2,y),
                'w':(x-w/2,y),'nw':(x-w/2,y+h/2),
                'ne':(x+w/2,y+h/2),'c':(x,y)}[side]

    def line(self,points,dashed=False):
        xs,ys=zip(*points)
        self.ax.plot(xs,ys,color='black',linewidth=.55,
                     linestyle=(0,(4,3)) if dashed else 'solid',zorder=1)

    def arrow(self,p,q,dashed=False,via=()):
        points=[p,*via,q]
        if via:self.line(points[:-1],dashed)
        self.ax.add_patch(FancyArrowPatch(points[-2],points[-1],
                         arrowstyle='-|>',mutation_scale=7.5,linewidth=.55,
                         color='black',shrinkA=0,shrinkB=0,
                         linestyle=(0,(4,3)) if dashed else 'solid',zorder=1))

    def edge(self,a,b,sa='s',sb='n',**kwargs):
        self.arrow(self.point(a,sa),self.point(b,sb),**kwargs)

    def frame(self,x,y,w,h):
        self.ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor='black',
                                   linewidth=.55,linestyle=(0,(4,3)),zorder=0))

    def save(self,out,name):
        # Fixed physical canvas: do not enlarge or rasterize the scientific figure.
        self.fig.canvas.draw()
        renderer=self.fig.canvas.get_renderer()
        x0,x1=self.ax.get_xlim();y0,y1=self.ax.get_ylim()
        for artist,node in self.labels:
            b=artist.get_window_extent(renderer).transformed(self.ax.transData.inverted())
            if b.x0<x0-.02 or b.x1>x1+.02 or b.y0<y0-.02 or b.y1>y1+.02:
                raise ValueError(name+': clipped label '+repr(artist.get_text()))
            if node and (b.x0<node[0]-.02 or b.x1>node[2]+.02 or b.y0<node[1]-.02 or b.y1>node[3]+.02):
                raise ValueError(name+': label exceeds node '+repr(artist.get_text()))
        self.fig.savefig(out/(name+'.pdf'),format='pdf',
                         metadata={'Creator':'Python Matplotlib','Producer':None,
                                   'CreationDate':None,'ModDate':None})
        plt.close(self.fig)

NAMES=('observer','pipeline')
def draw_all(out):
    out.mkdir(parents=True,exist_ok=True)
    d=Drawing((-.1,-.75,8.6,4.2))
    d.box('pending',4.25,2.3,2.35,.9,'Pending pair\n'+r'$(s,a)\in F_t$')
    for name,x,label in [('first',1.15,'First completion\n'+r'$\tau_H=t$'),('sentinel',4.25,'No completion\n'+r'$\tau_H=H+1$'),('reject',7.35,'Disagreement\nReject')]:d.box(name,x,.1,2.2,.85,label)
    d.arrow((3.075,1.85),d.point('first','n'));d.text(2.05,1.3,'11')
    d.edge('pending','sentinel','s','n');d.text(4.85,1.15,'00\n'+r'$t=H$')
    d.arrow((5.425,1.85),d.point('reject','n'));d.text(6.55,1.3,'01,10')
    d.arrow(d.point('pending','w'),d.point('pending','e'),via=[(2.55,2.3),(2.55,3.45),(5.95,3.45),(5.95,2.3)])
    d.text(4.25,3.9,r'$00,\ t<H$; all next pairs in $F_{t+1}$');d.save(out,'observer')
    d=Drawing((.05,.45,8.55,9.1))
    labels=[('rtl',8.35,'Pinned public RTL source +\nexplicit transaction harness',False),('front',6.95,'Restricted source-to-equation\ntranslator',True),('ir',5.55,'Accepted typed equation system $M$\nindependent source/harness '+r'$\leftrightarrow M$'+' validation',False),('prod',4.15,'Slice producer: retained set $K$,\nmodel $P$, and evidence',True),('bundle',2.75,'Timing model + preservation, necessity,\ncanonicality, and output-binding certificates',False),('check',1.35,'Independent equation/certificate checker',False)]
    for name,y,label,dashed in labels:d.box(name,2.9,y,5.5,.95,label,dashed=dashed,size=8.5)
    for (a,*_), (b,*_) in zip(labels,labels[1:]):d.edge(a,b,'s','n')
    d.arrow(d.point('rtl','e'),d.point('ir','e'),via=[(6.2,8.35),(6.2,5.55)]);d.text(7.2,7.6,'independent\nvalidator',size=8.5)
    d.arrow(d.point('ir','e'),d.point('check','e'),via=[(6.45,5.55),(6.45,1.35)]);d.text(7.4,3.6,'reparsed',size=8.5);d.save(out,'pipeline')

def main():
    import tempfile
    ap=argparse.ArgumentParser(description='Direct Python vector drawings of the timing-slice acceptance contract.')
    ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'figures');ap.add_argument('--check',action='store_true');a=ap.parse_args()
    if a.check:
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);draw_all(out)
            for name in NAMES:
                p=a.output/(name+'.pdf')
                if not p.is_file() or p.read_bytes()!=(out/(name+'.pdf')).read_bytes():raise SystemExit('Missing/stale schematic: '+name)
        print('Both schematics reproduce byte-for-byte.')
    else:draw_all(a.output)
if __name__=='__main__':main()
