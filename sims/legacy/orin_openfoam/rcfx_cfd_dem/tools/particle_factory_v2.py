import numpy as np, json
TRUNC_CENTERS = [60, 87.5, 125, 200, 375, 750]
TRUNC_MF_RAW = [0.20, 0.12, 0.18, 0.15, 0.08, 0.02]
s = sum(TRUNC_MF_RAW)
TRUNC_MF = [f/s for f in TRUNC_MF_RAW]
d = np.array(TRUNC_CENTERS)
fm = np.array(TRUNC_MF)
nf = (fm/d**3) / (fm/d**3).sum()
d32 = (fm*d**3).sum() / (fm*d**2).sum()
print(f"d32 Sauter = {d32:.1f} um")
print(f"d50 mass ~ {np.interp(0.5, np.cumsum(fm), d):.1f} um")
for di,m,n in zip(d,fm,nf): print(f"  {di:>6.0f} um  mass {m*100:5.1f}%  number {n*100:6.2f}%")
bed_vol = 0.30*0.01*0.15
solid = bed_vol*0.55
v_avg = (nf * (np.pi/6) * (d*1e-6)**3).sum()
for cg in [1,3,5,10,20]:
    dc = d*cg
    va = (nf * (np.pi/6) * (dc*1e-6)**3).sum()
    print(f"  CG={cg:>2}x: {int(solid/va):>12,} particles")
json.dump({"bins_um":TRUNC_CENTERS,"mass_frac":TRUNC_MF,"number_frac":nf.tolist(),"d32":d32},
          open("rcfx_psd.json","w"), indent=2)
print("Exported rcfx_psd.json")
