"""Pipeline edit: Pool(source.txt) -> anti-fingerprint + mix bgm + strip metadata -> pages/*/edited (xoa nguon Pool chong trung)."""
import os, sys, subprocess, random, datetime, hashlib
BASE=os.path.dirname(os.path.abspath(__file__))
PAGES_DIR=os.path.join(os.path.dirname(BASE),"pages")
BGM_DIR=os.path.join(BASE,"bgm")
EXTS=(".mp4",".mov",".mkv",".avi")
FFMPEG=os.environ.get("FFMPEG_BIN","")
if not FFMPEG:
 try:
  import imageio_ffmpeg; FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
 except Exception: FFMPEG="ffmpeg"
def ensure():
 os.makedirs(BGM_DIR,exist_ok=True)
 os.makedirs(PAGES_DIR,exist_ok=True)
# GUI note: ensure() chi chay khi mo truc tiep (CLI). Import tu GUI khong
# tu tao thu muc trong repo; GUI tu tao edited/ khi can, khong xoa gi.
if __name__ == "__main__":
 ensure()
def log(m):
 print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {m}",flush=True)
def run(cmd,timeout=900):
 log("$ "+" ".join(cmd[:6])+(f" ... ({len(cmd)} args)" if len(cmd)>6 else ""))
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
 if r.returncode!=0: raise RuntimeError(f"LENH LOI {cmd[0]}: {(r.stderr or r.stdout)[-1500:]}")
 return r
def list_videos(folder):
 if not os.path.exists(folder): return []
 return sorted([os.path.join(folder,f) for f in os.listdir(folder) if f.lower().endswith(EXTS) and os.path.isfile(os.path.join(folder,f))])
def ffprobe_dur(path):
 import re
 candidates=[FFMPEG.replace("ffmpeg","ffprobe"),FFMPEG.replace("ffmpeg-win-x86_64-v7.1","ffprobe")]
 for fp in candidates:
  try:
   if fp and os.path.exists(fp):
    r=subprocess.run([fp,"-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",path],capture_output=True,text=True,timeout=30)
    v=float((r.stdout or "0").strip() or 0)
    if v>0: return v
  except Exception: pass
 try:
  r=subprocess.run([FFMPEG,"-i",path],capture_output=True,text=True,timeout=30)
  m=re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)",(r.stderr or "")+(r.stdout or ""))
  if m: return int(m.group(1))*3600+int(m.group(2))+float(m.group(3))
 except Exception: pass
 return 0.0
# ---------- Tham so pipeline (mac dinh = dung hang so goc) ----------
DEFAULT_PARAMS={
 "speed": 1.045,      # tang toc nhe
 "zoom": 1.06,        # phong to truoc khi crop
 "crop_w": 0.94, "crop_h": 0.93,
 "hflip": True,       # lat ngang
 "contrast": 1.04, "saturation": 1.03,
 "noise": 6,          # hat nhieu alls
 "trim_head": 1,      # cat bo 1s dau (giay)
 "trim_tail": 2.5,    # cat bo 2.5s cuoi (giay)
 "bgm_vol": 0.18,     # muc tron nhac nen
 "use_bgm": True,     # co tron nhac nen neu co file trong bgm/
}
def _fmt(v):
 """Format so cho filter ffmpeg: int -> '6', 1.045 -> '1.045' (khop chuoi goc)."""
 if isinstance(v, bool):
  return "1" if v else "0"
 if isinstance(v, int):
  return str(v)
 f = float(v)
 if f.is_integer():
  return str(int(f))
 return repr(round(f, 4))
def build_filter_complex(p):
 """Ham thuan: params -> (vf, filter_complex, co_dung_bgm).
 Voi DEFAULT_PARAMS phai tra ve dung chuoi filter cua ban goc."""
 speed=_fmt(p["speed"]); zoom=_fmt(p["zoom"])
 cw=_fmt(p["crop_w"]); ch=_fmt(p["crop_h"])
 head=_fmt(p["trim_head"])
 vf=(f"trim=start={head},setpts=PTS-STARTPTS,"
     f"setpts=PTS/{speed},scale=iw*{zoom}:ih*{zoom},crop=iw*{cw}:ih*{ch},"
     + ("hflip," if p["hflip"] else "")
     + f"eq=contrast={_fmt(p['contrast'])}:saturation={_fmt(p['saturation'])},"
     f"noise=alls={_fmt(p['noise'])}:allf=t")
 if p.get("use_bgm"):
  fc=(f"[0:v]{vf}[v];[0:a]atrim=start={head},asetpts=PTS-STARTPTS,atempo={speed}[a0];"
      f"[1:a]volume={_fmt(p['bgm_vol'])},aresample=44100,aformat=channel_layouts=stereo[a1];"
      f"[a0][a1]amix=inputs=2:normalize=0[aout]")
 else:
  fc=f"[0:v]{vf}[v];[0:a]atrim=start={head},asetpts=PTS-STARTPTS,atempo={speed}[aout]"
 return vf, fc, bool(p.get("use_bgm"))
# ---------- EDIT: anti-fingerprint + mix bgm + hardcode + strip metadata ----------
def pick_bgm():
 cands=[os.path.join(BGM_DIR,f) for f in os.listdir(BGM_DIR)] if os.path.exists(BGM_DIR) else []
 cands=[c for c in cands if c.lower().endswith((".mp3",".wav",".m4a"))]
 return random.choice(cands) if cands else None
def step56_final(src,out_path,params=None,speed=None):
 """params: dict theo DEFAULT_PARAMS. speed=... (cu) van dung duoc: chi doi toc do."""
 p=dict(DEFAULT_PARAMS)
 if params:
  p.update(params)
 if speed is not None:
  p["speed"]=speed
 dur=max(0.5,ffprobe_dur(src)-float(p["trim_tail"]))
 vf,fc,use_bgm_flag=build_filter_complex(p)
 bgm=pick_bgm() if use_bgm_flag else None
 if bgm is None and use_bgm_flag:
  # khong co file nhac -> dung filter khong-bgm (giong ban goc)
  _,fc,_=build_filter_complex({**p,"use_bgm":False})
 inputs=["-y","-i",src]
 if bgm: inputs+=["-i",bgm]
 run([FFMPEG,*inputs,"-filter_complex",fc,"-map","[v]","-map","[aout]","-t",str(dur),
  "-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
  "-map_metadata","-1","-movflags","+faststart",out_path])
 return out_path
# ---------- PIPELINE + MENU ----------
def process_one(src,out_dir,overwrite=False,params=None):
 ensure()
 name,_=os.path.splitext(os.path.basename(src))
 stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
 digest=hashlib.md5(f"{name}{os.path.getsize(src)}".encode()).hexdigest()[:6]
 os.makedirs(out_dir,exist_ok=True)
 out=os.path.join(out_dir,f"{name}_edit_{stamp}_{digest}.mp4")
 if os.path.exists(out) and not overwrite: return out
 log(f"[EDIT] {name}: anti-fingerprint + mix bgm + strip metadata")
 try:
  step56_final(src,out,params=params)
 except Exception:
  if os.path.exists(out):  # xoa file loi nua de khong upload phai
   try: os.remove(out)
   except: pass
  raise
 return out
def pages_info():
 """Tra (PAGES_DIR, [page,...]). Tu quet pages/ neu khong import duoc Uploadvideo_multipage."""
 sys.path.insert(0,os.path.dirname(BASE))
 try:
  import Uploadvideo_multipage as m; return m.PAGES_DIR,m.list_local_pages()
 except Exception as e:
  log(f"Khong load Uploadvideo_multipage ({e}), quet pages/ thu cong")
  lps=[]
  if os.path.isdir(PAGES_DIR):
   for d in sorted(os.listdir(PAGES_DIR)):
    dd=os.path.join(PAGES_DIR,d)
    if os.path.isdir(dd): lps.append({"id":"","name":d,"folder":d,"dir":dd})
  return PAGES_DIR,lps
def read_source_dir(page_dir):
 sf=os.path.join(page_dir,"source.txt")
 if not os.path.isfile(sf): return None
 try:
  for raw in open(sf,encoding="utf-8-sig"):
   l=raw.strip().strip('"').strip("'")
   if not l or l.startswith("#"): continue
   return l
 except Exception: return None
 return None
def collect_pool(pages=None):
 if pages is None: _,pages=pages_info()
 items=[]
 for pg in pages:
  sdir=read_source_dir(pg["dir"])
  if not sdir: continue
  if os.path.isfile(sdir) and sdir.lower().endswith(EXTS):
   items.append((pg,sdir,"pool")); continue
  if not os.path.isdir(sdir):
   log(f"[{pg.get('folder',pg.get('dir'))}] source khong ton tai: {sdir} (bo qua)")
   continue
  for v in list_videos(sdir): items.append((pg,v,"pool"))
 return items
def collect_all(pages=None):
 if pages is None: _,pages=pages_info()
 return collect_pool(pages)
def pick_per_page(pages=None,per_page=1):
 """Moi page chi lay toi da per_page video Pool.
 De xoay vong: moi luot chay chi edit 1 video/page roi nhay sang page khac."""
 if pages is None: _,pages=pages_info()
 items=[]
 for pg in pages:
  sdir=read_source_dir(pg["dir"])
  pool_list=[]
  if sdir:
   if os.path.isfile(sdir) and sdir.lower().endswith(EXTS): pool_list=[sdir]
   elif os.path.isdir(sdir): pool_list=list_videos(sdir)
  for v in pool_list[:max(1,per_page)]:
   items.append((pg,v,"pool"))
 return items
def run_edit(target_pages=None,per_page=1):
 """Moi luot: moi page edit toi da per_page video Pool -> edited/ cung page, xoa nguon chong trung."""
 items=pick_per_page(target_pages,per_page)
 if not items:
  print("[!] Khong co video trong Pool(source.txt) cua page nao."); return
 npages=len(set(pg["dir"] for pg,_,_ in items))
 print(f"[+] {len(items)} video cho edit: {npages} page x {per_page} video (xoay vong)")
 ok=0
 for i,(pg,v,kind) in enumerate(items,1):
  log(f"[{i}/{len(items)}][POOL] {pg['folder']}: {os.path.basename(v)}")
  try:
   out=process_one(v,os.path.join(pg["dir"],"edited"))
   try: os.remove(v)
   except Exception as e: print(f"  [!] Khong xoa duoc nguon {v}: {e}"); continue
   ok+=1
   print("  ->",os.path.basename(out),"(da xoa nguon)")
  except Exception as e:
   print("  LOI:",str(e)[-400:],"(giu nguon de chay lai)")
 print("="*55); print(f" XONG: {ok}/{len(items)} thanh cong"); print("="*55)
def main():
 ensure()
 print("="*55); print(" VIDEO EDIT: Pool(source.txt) -> pages/*/edited"); print("="*55)
 while True:
  print("\n--- MENU ---"); print(" 1. Xem trang thai tung page (Pool / edited)")
  print(" 2. Edit XOAY VONG: moi page 1 video (Pool -> edited, xoa nguon)")
  print(" 3. Edit Pool cua 1 page (1 video)")
  print(" 0. Thoat")
  c=input("Chon: ").strip()
  if c=="1":
   _,lps=pages_info()
   print(f"[+] pages/: {len(lps)} page")
   tot=0
   for p in lps:
    sd=read_source_dir(p["dir"])
    n0=len(list_videos(sd)) if sd and os.path.isdir(sd) else (1 if sd and os.path.isfile(sd) else 0)
    n2=len(list_videos(os.path.join(p["dir"],"edited"))); tot+=n0
    src=sd if sd else "WAITING(khong co source.txt)"
    print(f"  - {p['folder']}: Pool {n0} | edited {n2}\n    src: {src}")
   print(f"[+] Con la {tot} video chua edit")
  elif c=="2":
   run_edit(None)
  elif c=="3":
   _,lps=pages_info()
   if not lps: print("[!] Chua co pages/."); continue
   for i,p in enumerate(lps,1): print(f" {i}. {p['folder']}")
   s=input("Chon so page: ").strip()
   if not (s.isdigit() and 1<=int(s)<=len(lps)): print("Sai."); continue
   run_edit([lps[int(s)-1]])
  elif c=="0": break
  else: print("Chon 0-3.")
if __name__=="__main__": main()
