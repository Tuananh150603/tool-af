import os, sys, time, random, re, requests
TOKEN = os.environ.get("FB_USER_TOKEN", "PASTE_YOUR_TOKEN_HERE")
VER="v21.0"
PAGE_ID="991676960687614"
PAGE_NAME="The Art Of Fear"
BASE=os.path.dirname(os.path.abspath(__file__))
VDIR=os.path.join(BASE,"videos")
CAPF=os.path.join(BASE,"captions.txt")
CMTF=os.path.join(BASE,"comments.txt")
PAGES_DIR=os.path.join(BASE,"pages")
CAPS=["Video moi len song ca nha oi!","Sieu pham hom nay, dung bo lo nha!","Clip hay moi ngay, follow page nhe!","Video hot nhat hom nay! #xuhuong","Cay view giup ad voi!"]
CMTS=["Hay qua moi nguoi oi","Xem di xem lai van cuon","Ai xem toi day comment so 1 nao!","Clip nay xung dang trieu view","Follow page de xem them nhe!"]
EXTS=(".mp4",".mov",".mkv",".avi")
# GUI doc: loi API gan nhat (de GUI phan loai checkpoint / rate-limit / token).
# CLI goc khong doc bien nay nen hanh vi CLI khong doi.
LAST_API_ERROR=None
def _note_api_error(where, resp=None, payload=None, status=None):
    """Ghi lai loi Facebook API (neu co) vao LAST_API_ERROR. Khong raise."""
    global LAST_API_ERROR
    try:
        if payload is None and resp is not None:
            try: payload = resp.json()
            except Exception:
                try: payload = {"error": {"message": (resp.text or "")[:300]}}
                except Exception: payload = {}
        if status is None and resp is not None:
            status = getattr(resp, "status_code", None)
        err = (payload or {}).get("error") if isinstance(payload, dict) else None
        if err and isinstance(err, dict):
            LAST_API_ERROR = {"where": where, "status": status,
                              "code": err.get("code"), "subcode": err.get("error_subcode"),
                              "message": str(err.get("message", ""))[:300]}
    except Exception:
        pass
def clear_api_error():
    global LAST_API_ERROR
    LAST_API_ERROR = None
def sanitize(n):
 s=re.sub(r'[\\/:*?"<>|]','',n or '').strip().replace(' ','_')
 s=re.sub(r'_+','_',s).strip('_')
 return s[:50] or 'Page'
def retrofit_all_pages():
 n=0
 if not os.path.exists(PAGES_DIR): return 0
 for d in sorted(os.listdir(PAGES_DIR)):
  p=os.path.join(PAGES_DIR,d)
  if not os.path.isdir(p): continue
  edited=os.path.join(p,"edited")
  os.makedirs(edited,exist_ok=True)
  # xoa Non_edit cu (khong dung tu 2026-10-07, Pool -> edited truc tiep)
  for _d in [os.path.join(p,"Non_edit"),os.path.join(p,"videos")]:
   try:
    import shutil
    if os.path.isdir(_d): shutil.rmtree(_d,ignore_errors=True)
   except: pass
  capf=os.path.join(p,"captions.txt"); cmtf=os.path.join(p,"comments.txt")
  for _f in [capf,cmtf]:
   try:
    if os.path.isfile(_f): os.remove(_f)
   except: pass
  n+=1
 return n
def ensure():
 os.makedirs(VDIR,exist_ok=True); os.makedirs(PAGES_DIR,exist_ok=True)
 if not os.path.exists(CAPF): open(CAPF,"w",encoding="utf-8").write("\n".join(CAPS))
 if not os.path.exists(CMTF): open(CMTF,"w",encoding="utf-8").write("\n".join(CMTS))
def load(p):
 try: r=[l.strip() for l in open(p,encoding="utf-8-sig")]; return [x for x in r if x]
 except: return []
def load_page_token():
 try:
  p=os.path.join(BASE,"page_tok.txt"); t=open(p,encoding="utf-8").read().strip()
  return t if len(t)>50 else ""
 except: return ""
PAGE_TOKEN=load_page_token()
def fetch_pages(user_tok):
 pages=[]; url=f"https://graph.facebook.com/{VER}/me/accounts"
 params={"access_token":user_tok,"fields":"id,name,access_token","limit":100}
 while url:
  try: j=requests.get(url,params=params,timeout=20).json()
  except Exception as e: print("Loi ket noi:",e); break
  if "error" in j: print(" [!] API loi:",j); _note_api_error("fetch_pages", payload=j); break
  pages+=j.get("data",[])
  nxt=(j.get("paging") or {}).get("next"); url=nxt; params={}
  if not nxt: break
 return pages
def ensure_page_folder(pid,name,ptok=""):
 dname=f"{pid}_{sanitize(name)}"; pdir=os.path.join(PAGES_DIR,dname)
 os.makedirs(os.path.join(pdir,"edited"),exist_ok=True)
 for _f in [os.path.join(pdir,"captions.txt"),os.path.join(pdir,"comments.txt")]:
  try:
   if os.path.isfile(_f): os.remove(_f)
  except: pass
 if ptok: open(os.path.join(pdir,"token.txt"),"w",encoding="utf-8").write(ptok.strip())
 open(os.path.join(pdir,"info.txt"),"w",encoding="utf-8").write(f"{name}\nID: {pid}\nFolder: {dname}\n")
 return pdir
def list_local_pages():
 out=[]
 if not os.path.exists(PAGES_DIR): return out
 # lay user token tu page_tok.txt de fetch token page moi moi lan chay
 user_tok=""
 try:
  t=open(os.path.join(BASE,"page_tok.txt"),encoding="utf-8").read().strip()
  if len(t)>50: user_tok=t
 except: pass
 # fetch tat ca page token moi tu user token
 page_tokens={}
 if user_tok:
  try:
   pages=fetch_pages(user_tok)
   for pg in pages:
    page_tokens[pg["id"]]=pg.get("access_token","")
  except Exception as e:
   print(f"[!] Khong fetch duoc page tokens: {e}")
 for d in sorted(os.listdir(PAGES_DIR)):
  p=os.path.join(PAGES_DIR,d)
  if not os.path.isdir(p): continue
  pid=d.split("_")[0]
  try:
   info=open(os.path.join(p,"info.txt"),encoding="utf-8").read().strip().splitlines()[0] if os.path.exists(os.path.join(p,"info.txt")) else d
  except: info=d
  # uu tien token page moi vua fetch, fallback token cu trong token.txt, fallback PAGE_TOKEN
  tok=page_tokens.get(pid,"")
  if not tok:
   try:
    t=open(os.path.join(p,"token.txt"),encoding="utf-8").read().strip()
    if len(t)>50: tok=t
   except: pass
  if not tok:
   tok=PAGE_TOKEN or TOKEN
  vdir=os.path.join(p,"edited")
  nv=len([f for f in os.listdir(vdir) if f.lower().endswith(EXTS)]) if os.path.exists(vdir) else 0
  out.append({"id":pid,"name":info,"dir":p,"folder":d,"token":tok,"nvids":nv,"nnonedit":0})
 return out
def setup_all_pages(user_tok):
 print("[*] Dang quet danh sach Page...")
 pages=fetch_pages(user_tok)
 if not pages:
  print("[!] Token nay khong lay duoc /me/accounts (co the la Page token). Thu lay /me...")
  try:
   me=requests.get(f"https://graph.facebook.com/{VER}/me",params={"access_token":user_tok,"fields":"id,name"},timeout=20).json()
   print(" -> ",me)
   if "id" in me: pages=[{"id":me["id"],"name":me.get("name","Page"),"access_token":user_tok}]
  except Exception as e: print(e)
 print(f"[+] Tim thay {len(pages)} Page:")
 for pg in pages:
  pdir=ensure_page_folder(pg["id"],pg.get("name","Page"),pg.get("access_token",""))
  print(f"  - {pg.get('name')} ({pg['id']}) -> pages/{os.path.basename(pdir)}/edited/")
 if pages and os.path.exists(VDIR) and os.listdir(VDIR):
  print("[*] Giu nguyen thu muc videos/ cu de tuong thich nguoc.")
 return pages
def up_simple(pid,tok,path,title,desc):
 url=f"https://graph-video.facebook.com/{VER}/{pid}/videos"
 print(f"[*] Upload {os.path.basename(path)} ({os.path.getsize(path)/1024/1024:.1f}MB)")
 with open(path,"rb") as f:
  r=requests.post(url,files={"source":(os.path.basename(path),f,"video/mp4")},data={"access_token":tok,"title":title,"description":desc},timeout=900)
 print(" <-",r.text[:800])
 _note_api_error("up_simple", r)
 try: return r.json().get("id")
 except: return None
def up_resumable(pid,tok,path,title,desc):
 print(f"[*] Resumable {os.path.basename(path)}")
 sz=os.path.getsize(path); fn=os.path.basename(path)
 j1=requests.post(f"https://graph.facebook.com/{VER}/{pid}/uploads",data={"access_token":tok,"file_name":fn,"file_length":str(sz),"file_type":"video/mp4"},timeout=60).json()
 print(" session:",j1)
 _note_api_error("up_resumable:session", payload=j1)
 if "id" not in j1: return None
 sid=j1["id"]
 with open(path,"rb") as f:
  r2=requests.post(f"https://graph.facebook.com/{VER}/{sid}",headers={"Authorization":f"OAuth {tok}","file_offset":"0"},data=f,timeout=1200)
 print(" handle:",r2.text[:500])
 try: h=r2.json().get("h")
 except: return None
 if not h: _note_api_error("up_resumable:upload", r2); return None
 j3=requests.post(f"https://graph-video.facebook.com/{VER}/{pid}/videos",data={"access_token":tok,"title":title,"description":desc,"fbuploader_video_file_chunk":h},timeout=120).json()
 print(" publish:",j3)
 _note_api_error("up_resumable:publish", payload=j3)
 return j3.get("id")
def comment(vid,tok,msg,delay=15):
 if delay>0: print(f"[*] Cho {delay}s roi comment..."); time.sleep(delay)
 r=requests.post(f"https://graph.facebook.com/{VER}/{vid}/comments",data={"access_token":tok,"message":msg},timeout=30)
 print(" cmt:",r.text[:500])
 _note_api_error("comment", r)
 try: return "id" in r.json()
 except: return False
def upload_for_page(pg,d1=10,d2=15,big=False):
 pid=pg["id"]; tok=pg["token"]; pdir=pg["dir"]
 vdir=os.path.join(pdir,"edited")
 caps=load(CAPF) or CAPS; cmts=load(CMTF) or CMTS  # chi boc root D:\Tool AF\captions.txt + comments.txt
 print("="*55); print(f" PAGE: {pg['name']} ({pid})"); print(f" Folder: {pdir} -> lay video tu edited/")
 print(f" [*] {len(caps)} caption, {len(cmts)} comment"); print("="*55)
 vids=[os.path.join(vdir,f) for f in os.listdir(vdir) if f.lower().endswith(EXTS)] if os.path.exists(vdir) else []
 if not vids:
  print(f"[!] Chua co video trong {vdir} - copy video da edit vao do (con video tho de o Non_edit)!")
  l=input("Hoac nhap duong dan 1 file (Enter=bo qua page nay): ").strip().strip('"')
  vids=[l] if l and os.path.exists(l) else []
  if not vids: return 0,0
 print(f"[*] Co {len(vids)} video:"); [print(" -",v) for v in vids]
 random.shuffle(vids); ok=0
 for i,vp in enumerate(vids,1):
  cap=random.choice(caps); cmt=random.choice(cmts)
  print("-"*55); print(f"[{i}/{len(vids)}] {os.path.basename(vp)}"); print(" Caption:",cap); print(" Comment:",cmt)
  vid=None
  try:
   vid=(up_resumable(pid,tok,vp,cap[:90],cap) or up_simple(pid,tok,vp,cap[:90],cap)) if big else (up_simple(pid,tok,vp,cap[:90],cap) or up_resumable(pid,tok,vp,cap[:90],cap))
  except Exception as e: print("Loi upload:",e)
  if vid: ok+=1; print("[+] Video ID:",vid); comment(vid,tok,cmt,d2)
  else: print("[!] Upload that bai, bo comment.")
  if i<len(vids): print(f"[*] Nghi {d1}s..."); time.sleep(d1)
 print(f"[XONG {pg['name']}: {ok}/{len(vids)} OK]")
 return ok,len(vids)
def upload_legacy(pid,tok,d1,d2,big):
 caps=load(CAPF) or CAPS; cmts=load(CMTF) or CMTS
 vids=[os.path.join(VDIR,f) for f in os.listdir(VDIR) if f.lower().endswith(EXTS)] if os.path.exists(VDIR) else []
 random.shuffle(vids); ok=0
 for i,vp in enumerate(vids,1):
  cap=random.choice(caps); cmt=random.choice(cmts)
  print(f"[{i}/{len(vids)}] {vp}")
  try: vid=(up_resumable(pid,tok,vp,cap[:90],cap) or up_simple(pid,tok,vp,cap[:90],cap)) if big else (up_simple(pid,tok,vp,cap[:90],cap) or up_resumable(pid,tok,vp,cap[:90],cap))
  except Exception as e: print(e); vid=None
  if vid: ok+=1; comment(vid,tok,cmt,d2)
 print(f"[XONG legacy: {ok}/{len(vids)}]")
 return ok,len(vids)
def main():
 ensure(); retrofit_all_pages()
 print("="*55); print(" TOOL AF - MULTI-PAGE MANAGER"); print("="*55)
 tok0=PAGE_TOKEN or TOKEN
 user_tok=input("User Token (Enter=dung token luu san): ").strip() or tok0
 while True:
  print("\n--- MENU ---")
  print(" 1. Quet Page -> tu tao thu muc pages/<ID>_<Ten>/")
  print(" 2. Xem cac Page da co (tu dem so luong + so video)")
  print(" 3. Upload cho 1 Page")
  print(" 4. Upload cho TAT CA Page")
  print(" 0. Thoat")
  c=input("Chon: ").strip()
  if c=="1":
   setup_all_pages(user_tok)
  elif c=="2":
   lps=list_local_pages()
   print(f"[+] Co {len(lps)} Page trong pages/:")
   for i,p in enumerate(lps,1): print(f" {i}. {p['name']} ({p['id']}) - edited: {p['nvids']} video, Non_edit: {p.get('nnonedit',0)} - {p['folder']}")
   if not lps: print(" -> Chua co. Chay menu 1 de quet tu token.")
  elif c in ("3","4"):
   lps=list_local_pages()
   if not lps:
    print("[!] Chua co pages/. Dung che do cu videos/...")
    u=input("Upload videos/ cu cho Page mac dinh? (y/N): ").strip().lower()
    if u!="y": continue
    d1=input("Nghi giua cac video (mac dinh 10): ").strip(); d1=int(d1) if d1.isdigit() else 10
    d2=input("Cho truoc khi comment (mac dinh 15): ").strip(); d2=int(d2) if d2.isdigit() else 15
    big=input("File lon? resumable truoc (y/N): ").strip().lower()=="y"
    upload_legacy(PAGE_ID,user_tok,d1,d2,big); continue
   d1=input("Nghi giua cac video (mac dinh 10): ").strip(); d1=int(d1) if d1.isdigit() else 10
   d2=input("Cho truoc khi comment (mac dinh 15): ").strip(); d2=int(d2) if d2.isdigit() else 15
   big=input("File lon? resumable truoc (y/N): ").strip().lower()=="y"
   targets=lps
   if c=="3":
    for i,p in enumerate(lps,1): print(f" {i}. {p['name']} ({p['id']}) - edited: {p['nvids']} video, Non_edit: {p.get('nnonedit',0)}")
    s=input("Chon so Page: ").strip()
    if not (s.isdigit() and 1<=int(s)<=len(lps)): print("Sai."); continue
    targets=[lps[int(s)-1]]
   toks=tok_sum=0
   for pg in targets:
    ok,n=upload_for_page(pg,d1,d2,big); toks+=ok; tok_sum+=n
   print("="*55); print(f" TONG: {toks}/{tok_sum} video OK"); print("="*55)
  elif c=="0": break
  else: print("Chon 0-4.")
if __name__=="__main__": main()

