import subprocess, numpy as np, json, wave
SR=44100
def piece(f, ss=0, to=None, tempo=1.0, gain=1.0, fade=0.01):
    cmd=["ffmpeg","-v","error","-ss",str(ss)]
    if to: cmd+=["-to",str(to)]
    cmd+=["-i",f"voz/{f}.mp3"]
    flt=[]
    t=tempo
    while t<0.5: flt.append("atempo=0.5"); t/=0.5
    while t>2: flt.append("atempo=2"); t/=2
    flt.append(f"atempo={t:.4f}")
    cmd+=["-af",",".join(flt),"-f","f32le","-ac","1","-ar",str(SR),"-"]
    a=np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,dtype=np.float32).copy()
    n=int(fade*SR)
    if len(a)>2*n: a[:n]*=np.linspace(0,1,n); a[-n:]*=np.linspace(1,0,n)
    return a*gain
def cat(*ps): return np.concatenate(ps)
def place(track, a, t):
    i=int(t*SR); track[i:i+len(a)]+=a[:max(0,len(track)-i)]
def save(name,x):
    x=np.clip(x,-1,1)
    with wave.open(name,"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype("<i2").tobytes())
# piezas
P={}
P["V1a"]=cat(piece("V1c",0,0.26),np.zeros(int(.03*SR)),piece("V1c",0.50,1.55)); 
P["V1a"]=piece("V1c",0,2,1.0) if False else P["V1a"]
# aplicar tempo 1.07 a la unión
def tempo_arr(a,t):
    import tempfile,os
    save("_t.wav",a)
    r=subprocess.run(["ffmpeg","-v","error","-i","_t.wav","-af",f"atempo={t}","-f","f32le","-ac","1","-ar",str(SR),"-"],capture_output=True).stdout
    return np.frombuffer(r,dtype=np.float32).copy()
P["V1a"]=tempo_arr(P["V1a"],1.07)
P["V1b"]=piece("S2b",0,1.55,1.03)                  # acabo de decir una letra
P["V1c"]=piece("S3b",0,None,1.15)              # ese mmm abre mamá y mesa
P["V2a"]=piece("V2a",0,1.45)                  # primero, el sonido
P["mmm"]=piece("Mm1",0,0.6,0.86)           # mmm largo
P["a"]=piece("Ah2",0,0.34)                    # a
P["ma"]=piece("Ma3",0.0,0.5)                  # ma
P["V3"]=piece("V3a",0,1.85,1.1)               # misión lectura es el método
P["V4"]=piece("V4b",0,1.6)
P["V5"]=piece("V5a",0,1.9)
P["V6"]=piece("V6a",0,2.1,0.92)
for k,v in P.items(): print(k, round(len(v)/SR,3))
# tiempos de colocación (línea de tiempo final) -> pista maestra
M=[("V1a",0.0),("V1b",1.2),("V1c",2.72),("V2a",5.0),("mmm",6.4),("a",7.1),("ma",7.6),("V3",8.3),("V4",10.0),("V5",12.1),("V6",13.9)]
master=np.zeros(int(16.8*SR))
for k,t in M: place(master,P[k],t)
save("master_voz.wav",master)
json.dump({k:[t,len(P[k])/SR] for k,t in M},open("voz_tiempos.json","w"))
# audios de clip (referencia Seedance), 5 s
def clip(items,name):
    tr=np.zeros(5*SR)
    for k,t in items: place(tr,P[k],t)
    save(name+".wav",tr)
clip([("V1a",0.0),("V1b",1.2),("V1c",2.72)],"clip1_audio")
clip([("V2a",0.0),("mmm",1.4),("a",2.1),("ma",2.6),("V3",3.3)],"clip2_audio")
clip([("V4",0.0),("V6",2.1)],"clip3_audio")
