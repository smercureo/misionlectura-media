import numpy as np, wave, json, subprocess
SR=44100; N=int(16.8*SR)
def rd(p):
    with wave.open(p) as w:
        x=np.frombuffer(w.readframes(w.getnframes()),dtype="<i2").astype(np.float32)/32767
        if w.getnchannels()>1: x=x.reshape(-1,w.getnchannels()).mean(1)
        assert w.getframerate()==SR; return x
def wr(p,x):
    with wave.open(p,"wb") as w: w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((np.clip(x,-1,1)*32767).astype("<i2").tobytes())
def tt(d): return np.arange(int(SR*d))/SR
def env(t,a=.004,d=.2): return np.minimum(t/a,1)*np.exp(-t/d)
D="/home/user/oficina-anuncios/oficina/animacion/sfx/"
rng=np.random.default_rng(5)
# sfx
def whoosh(d=.25):
    t=tt(d); n=np.convolve(rng.standard_normal(len(t)),np.ones(30)/30,"same"); return n*np.sin(np.pi*t/d)**2*3
def swish(d=.15):
    t=tt(d); n=np.convolve(rng.standard_normal(len(t)),np.ones(12)/12,"same"); return n*np.sin(np.pi*t/d)*2.5
def vib(d=.7):
    t=tt(d); return (np.sin(2*np.pi*70*t)+.5*np.sin(2*np.pi*140*t))*(0.6+0.4*np.sin(2*np.pi*22*t))*np.sin(np.pi*t/d)**.7
def click():
    t=tt(.05); return rng.standard_normal(len(t))*np.exp(-t/.006)
def ping():
    t=tt(.7); return (np.sin(2*np.pi*1568*t)+.3*np.sin(2*np.pi*3136*t))*env(t,.004,.22)
S={"whoosh":whoosh(),"swish":swish(),"vib":vib(),"click":click(),"ping":ping(),"pop":rd(D+"pop.wav"),"tic":rd(D+"tic.wav"),"tin":rd(D+"tin.wav"),"confeti":rd(D+"brillo.wav")}
ev=[]
for t in (1.2,2.85,5.0,10.0,12.1,13.9): ev.append((t,"whoosh","cortes de plano",-12))
ev.append((15.0,"swish","punch-in 100->118 %",-12))
for t,w in ((2.25,"tarjeta M entra"),(3.7,"MAMÁ"),(4.4,"MESA"),(5.5,"M coral sobre la tarjeta")): ev.append((t,"pop",w,-16))
ev.append((6.4,"vib","vibración bajo el «mmm» (0,7 s)",-12))
ev.append((7.1,"click","tarjeta A",-16))
ev.append((7.65,"tin","¡tin! fusión MA",-10)); ev.append((7.65,"confeti","confeti de la fusión MA",-16))
ev.append((8.4,"click","entra la portada del método",-16))
for t in (11.1,11.35,11.6,11.85): ev.append((t,"tic","portada de bonus",-16))
for t,w in ((12.3,"hito Sonido"),(13.2,"hito Sílabas")): ev.append((t,"tic",w,-16))
ev.append((14.9,"ping","entra la flecha ↓ (único del CTA)",-12))
# el confeti se cuenta junto al ¡tin! (un solo evento del plan: «¡tin!» + confeti)
n_eventos=len([e for e in ev if e[1]!="confeti"])
voz=rd("master_voz.wav"); voz=np.pad(voz,(0,max(0,N-len(voz))))[:N]
act=np.abs(voz)>0.02; vr=np.sqrt(np.mean(voz[act]**2)); print("voz rms activo",vr)
def db(x): return 10**(x/20)
sfx=np.zeros(N)
for t,k,_,g in ev:
    s=S[k]; s=s/(np.sqrt(np.mean(s**2))+1e-9)*vr*db(g); i=int(t*SR); sfx[i:i+len(s)]+=s[:N-i]
# musica marimba
bpm=104; beat=60/bpm; mus=np.zeros(N)
def mar(f,d=.55):
    t=tt(d); return (np.sin(2*np.pi*f*t)+.4*np.sin(2*np.pi*f*3.99*t)*np.exp(-t/.04)+.15*np.sin(2*np.pi*f*9.2*t)*np.exp(-t/.02))*env(t,.003,.14)
ch=[[261.63,329.63,392],[196,246.94,293.66],[220,261.63,329.63],[174.61,220,261.63]]
k=0;t=0.0
while t<16.8:
    c=ch[int(t/(beat*4))%4]; arp=[0,1,2,1,0,2,1,2]; f=c[arp[k%8]]*(2 if (k//8)%2 else 1)
    s=mar(f); i=int(t*SR); mus[i:i+len(s)]+=s[:N-i]; t+=beat/2; k+=1
mus=mus/(np.sqrt(np.mean(mus**2))+1e-9)*vr*db(-18)
duck=np.ones(N); 
def ramp(a,b,v0,v1): 
    i,j=int(a*SR),int(b*SR); duck[i:j]=np.linspace(v0,v1,j-i)
d6=db(-6); ramp(6.3,6.4,1,d6); duck[int(6.4*SR):int(8.3*SR)]=d6; ramp(8.3,8.5,d6,1)
fo=int(.2*SR); fade=np.ones(N); fade[-fo:]=np.linspace(1,0,fo)
mus=mus*duck*fade
mix=voz+sfx+mus
wr("mix_pre.wav",mix)
subprocess.run(["ffmpeg","-v","error","-y","-i","mix_pre.wav","-af","loudnorm=I=-16:TP=-1.5:LRA=7","-ar","44100","mix.wav"])
json.dump({"duracion":16.8,"formato":"1080x1920 30 fps",
 "voz":{"pista":"master_voz.wav","piezas":json.load(open("voz_tiempos.json"))},
 "sfx":[{"t":t,"efecto":k,"que":w,"db_vs_voz":g} for t,k,w,g in ev],"eventos_sfx_plan":n_eventos,
 "musica":{"tipo":"marimba ligera sintetizada (numpy, 104 bpm, Do-Sol-Lam-Fa)","nivel_db_vs_voz":-18,"ducking_db":-6,"ducking_desde":6.4,"ducking_hasta":8.3,"cola_16_1_a_16_8":"musica baja sola, fundido de salida en los ultimos 0,2 s"}},
 open("montaje_sfx.json","w"),ensure_ascii=False,indent=1)
print("eventos del plan:",n_eventos,"(+confeti como capa del ¡tin!)")
