"""Mezcla de audio 7.4: voz maestra real + 36 sfx + musica calida (ukelele Karplus-Strong). 0 creditos."""
import numpy as np, wave, json, subprocess, os
os.chdir("/home/user/misionlectura-media/ronda-05/7.4")
SR=44100; DUR=25.62; N=int(DUR*SR)
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
def ding():  # campanita doble
    t=tt(.9); b=lambda f:(np.sin(2*np.pi*f*t)+.35*np.sin(2*np.pi*f*2.76*t))*env(t,.003,.25)
    o=np.zeros(len(t)); o+=b(1318.5); s=int(.16*SR); o[s:]+=b(1760)[:len(t)-s]; return o
S={"whoosh":whoosh(),"swish":swish(),"vib":vib(),"click":click(),"ping":ping(),"ding":ding(),
   "pop":rd(D+"pop.wav"),"tic":rd(D+"tic.wav"),"tin":rd(D+"tin.wav"),"confeti":rd(D+"brillo.wav")}
ev=[(0.0,"ding","campanita doble ¡Atención!",-12)]
for t in (3.70,5.30,6.78,8.10,12.30,14.15,16.20,18.50,22.18): ev.append((t,"whoosh","cortes de plano mayor",-12))
for t in (0.96,2.50,10.50,11.40,17.00,19.60,23.65): ev.append((t,"swish","punch-in / cambio de encuadre",-12))
for t in (4.2,4.35,4.5,4.65,4.8,4.95): ev.append((t,"pop","cae tarjeta M·A·P·S·L·T",-16))
ev.append((6.20,"click","toc: M y A chocan",-16)); ev.append((6.50,"swish","boing: rebote",-16))
ev.append((8.90,"click","entra la portada del método",-16))
for t,w in ((12.65,"hito Sonido"),(13.45,"hito Sílabas")): ev.append((t,"tic",w,-16))
ev.append((14.20,"vib","vibración bajo el «mmm» (0,7 s)",-12))
ev.append((14.97,"click","tarjeta A",-16))
ev.append((15.55,"tin","¡tin! fusión MA",-10)); ev.append((15.55,"confeti","confeti de la fusión MA",-16))
for t in (20.18,20.45,20.72,20.99): ev.append((t,"tic","portada de bonus",-16))
ev.append((22.28,"ping","entra la flecha ↓ (único del CTA)",-12))
n_plan=len([e for e in ev if e[1]!="confeti"]); print("eventos plan:",n_plan)
voz=rd("voz/voz_maestra.wav"); voz=np.pad(voz,(0,max(0,N-len(voz))))[:N]
act=np.abs(voz)>0.02; vr=np.sqrt(np.mean(voz[act]**2))
db=lambda x:10**(x/20)
sfx=np.zeros(N)
for t,k,_,g in ev:
    s=S[k]; s=s/(np.sqrt(np.mean(s**2))+1e-9)*vr*db(g); i=int(t*SR); sfx[i:i+len(s)]+=s[:max(0,N-i)]
# musica: ukelele calido (Karplus-Strong), 100 bpm, Do-Sol-Lam-Fa, rasgueo suave
def ks(f,d=.9,damp=.4):
    n=int(SR*d); L=int(SR/f); buf=rng.uniform(-1,1,L); buf=np.convolve(buf,np.ones(3)/3,"same"); out=np.zeros(n)
    for i in range(n):
        out[i]=buf[i%L]; buf[i%L]=(buf[i%L]+buf[(i+1)%L])*0.5*(1-damp*0.01)
    return out*np.exp(-np.arange(n)/SR/0.55)
bpm=100; beat=60/bpm; mus=np.zeros(N)
ch=[[261.63,329.63,392.0,523.25],[196.0,293.66,392.0,493.88],[220.0,261.63,329.63,440.0],[174.61,261.63,349.23,440.0]]
cache={}
k=0; t=0.0
pat=[1,0,.6,0,.9,.5,.6,0]   # rasgueo por corchea
while t<DUR:
    bar=int(t/(beat*4))%4; c=ch[bar]; amp=pat[k%8]
    if amp>0:
        for j,f in enumerate(c):
            key=(round(f,2))
            if key not in cache: cache[key]=ks(f)
            s=cache[key]*amp*(0.9 if k%8 in (0,4) else 0.6); i=int((t+j*0.012)*SR); mus[i:i+len(s)]+=s[:max(0,N-i)]
    t+=beat/2; k+=1
mus=mus/(np.sqrt(np.mean(mus**2))+1e-9)*vr*db(-18)
duck=np.ones(N)
def ramp(a,b,v0,v1): i,j=int(a*SR),int(b*SR); duck[i:j]=np.linspace(v0,v1,j-i)
d6=db(-6); ramp(14.05,14.15,1,d6); duck[int(14.15*SR):int(16.20*SR)]=d6; ramp(16.20,16.40,d6,1)
fo=int(.2*SR); fade=np.ones(N); fade[-fo:]=np.linspace(1,0,fo)
mus=mus*duck*fade
mix=voz+sfx+mus
wr("work/mix_pre.wav",mix)
subprocess.run(["ffmpeg","-v","error","-y","-i","work/mix_pre.wav","-af","loudnorm=I=-16:TP=-1.5:LRA=7","-ar","44100","work/mix.wav"],check=True)
json.dump({"duracion":DUR,"formato":"1080x1920 30 fps","voz":{"pista":"voz/voz_maestra.wav","toma":"t3 + variante d2 del demo (ElevenLabs eleven_v3, Daniela)"},
 "sfx":[{"t":t,"efecto":k,"que":w,"db_vs_voz":g} for t,k,w,g in ev],"eventos_sfx_plan":n_plan,
 "musica":{"tipo":"ukelele calido sintetizado (Karplus-Strong, 100 bpm, Do-Sol-Lam-Fa)","nivel_db_vs_voz":-18,"ducking_db":-6,"ducking_desde":14.15,"ducking_hasta":16.2,"cola_24_77_a_25_62":"musica baja sola, fundido de salida 0,2 s"}},
 open("montaje.json","w"),ensure_ascii=False,indent=1)
