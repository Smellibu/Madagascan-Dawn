#!/usr/bin/env python3
"""One-shot source-photo importer for the Madagascar leader roster.

Creates 156x210 main and 38x51 small DXT1 DDS assets; records credits and rights notes.
It does not imply that copyrighted photographs are licensed for public redistribution.
"""
from __future__ import annotations
import io, re, sys, subprocess, json, html
from pathlib import Path
from urllib.parse import urljoin, quote_plus
import cv2, numpy as np, requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps

ROOT=Path.cwd()
MAIN=ROOT/"gfx/leaders/MAD"
SMALL=MAIN/"small"
CHAR_FILE=ROOT/"common/characters/MAD.txt"
EVENT_FILE=ROOT/"events/MAD_events.txt"
session=requests.Session()
session.verify=False
requests.packages.urllib3.disable_warnings()
session.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"})

SOURCES=[
 {"base":"Andry_Rajoelina","kind":"direct","url":"https://upload.wikimedia.org/wikipedia/commons/0/08/Andry_Rajoelina_%282023%29.jpg","source":"https://commons.wikimedia.org/wiki/File:Andry_Rajoelina_(2023).jpg","rights":"CC BY 4.0","credit":"Rijasolo / European Union","terms":["andry","rajoelina"]},
 {"base":"Marcel_Ranjeva","kind":"direct","url":"https://commons.wikimedia.org/wiki/Special:Redirect/file/Marcel_Ranjeva,_12th_AU_Summit,_090203-N-0506A-616.jpg","source":"https://commons.wikimedia.org/wiki/File:Marcel_Ranjeva,_12th_AU_Summit,_090203-N-0506A-616.jpg","rights":"Public domain, U.S. Navy official-duty photograph","credit":"MC2 Jesse B. Awalt / U.S. Navy","terms":["marcel","ranjeva"]},
 {"base":"Andrianome_Ranivo_Dieudonne","kind":"image_search","query":"General Andrianome Ranivo Dieudonne Madagascar military portrait","source":"https://www.madagate.org/madagascar-informations-politiques/flash-infos/3797-madagascar-general-andrianome-lofficier-superieur-de-la-neutralite-active-est-decede.pdf","rights":"Copyright / permission not established","credit":"Madagate / alternate image source must be verified","terms":["andrianome","dieudonne","ranaivo"]},
 {"base":"Jules_Mamizara","kind":"page","url":"https://www.2424.mg/news/disparition-le-general-jules-mamizara-tire-sa-reverence/","source":"https://www.2424.mg/news/disparition-le-general-jules-mamizara-tire-sa-reverence/","rights":"Copyright / permission not established","credit":"InfoCom Seg / 2424.mg","terms":["jules","mamizara"]},
 {"base":"Sylvain_Razafimandimby","kind":"page","url":"https://www.lexpress.mg/2024/03/deces-le-general-sylvain-razafimandimby.html","source":"https://www.lexpress.mg/2024/03/deces-le-general-sylvain-razafimandimby.html","rights":"Copyright / permission not established","credit":"L’Express de Madagascar","terms":["sylvain","razafimandimby"]},
 {"base":"Raonenantsoamampianina","kind":"page","url":"https://www.madagascar-tribune.com/Deux-autres-ministres,11146.html","fallback":"https://www.2424.mg/news/60-ans-de-larmee-malgache-une-stele-pour-rendre-hommage-aux-anciens-chefs-detat-major-general-de-larmee-malagasy/","source":"https://www.madagascar-tribune.com/Deux-autres-ministres,11146.html","rights":"Copyright / permission not established","credit":"Madagascar-Tribune.com","terms":["raonenantsoamampianina","raonenantsomampianina","cemgam"]},
 {"base":"Petera_Behajaina","kind":"page","url":"https://www1.rfi.fr/actufr/articles/059/article_31466.asp","source":"https://www1.rfi.fr/actufr/articles/059/article_31466.asp","rights":"AFP/RFI copyright; permission required for redistribution","credit":"Olivier Péguy / RFI","terms":["petera behajaina","général petera"]},
 {"base":"Noel_Girardin_Rakotonandrasana","kind":"page","url":"https://www1.rfi.fr/actuen/articles/112/article_3609.asp","source":"https://www1.rfi.fr/actuen/articles/112/article_3609.asp","rights":"AFP/RFI copyright; permission required for redistribution","credit":"AFP via RFI","terms":["noel","rakotonandrasana"]},
 {"base":"Edmond_Rasolomahandry","kind":"pdf_face","page":13,"region":"lower_right","url":"https://dkiapcss.edu/wp-content/uploads/2010/PDFs/currents2009-alumni.pdf","source":"https://dkiapcss.edu/wp-content/uploads/2010/PDFs/currents2009-alumni.pdf","rights":"Copyright / permission not established","credit":"Currents, APCSS Fall 2009 alumni report","terms":["edmond","rasolomahandry"]},
 {"base":"Andre_Ndriarijaona","kind":"direct","url":"https://latribune.cyber-diego.com/images/stories/2012/juin/labuse2012_07.jpg","source":"https://latribune.cyber-diego.com/actualites/677-exercice-de-lutte-contre-la-piraterie-dans-la-baie-de-diego-suarez.html","rights":"Copyright / permission not established","credit":"La Tribune de Diego","terms":["andre","ndriarijaona"]},
 {"base":"Charles_Andrianasoavina","kind":"direct","url":"https://www.agencemalagasydepresse.com/media/2023/10/colonel-charles-andrianasoavina.jpg","source":"https://www.agencemalagasydepresse.com/politique/raharaham-pirenena-fanambaranny-colonel-charles-andrianasoavina/","rights":"Copyright / permission not established","credit":"Agence Malagasy de Presse","terms":["charles","andrianasoavina"]},
 {"base":"Mamy_Solofoniaina_Ranaivoniarivo","kind":"direct","url":"https://commons.wikimedia.org/wiki/Special:Redirect/file/Mamy_Ranaivoniarivo.jpg","source":"https://commons.wikimedia.org/wiki/File:Mamy_Ranaivoniarivo.jpg","rights":"CC BY-SA 3.0","credit":"PixEye","terms":["mamy","ranaivoniarivo"]},
 {"base":"Hyppolite_Rarison_Ramaroson","kind":"direct","url":"https://latribune.cyber-diego.com/images/stories/2011/mar/50-ans-marine-madagascar_04.jpg","source":"https://latribune.cyber-diego.com/actualites/326-50eme-anniversaire-de-la-creation-de-la-marine-de-madagascar.html","rights":"Copyright / permission not established","credit":"La Tribune de Diego","terms":["hyppolite","ramaroson"]},
 {"base":"Andre_Lucien_Rakotoarimasy","kind":"direct","url":"https://ceds-madagascar.com/media/promotions/2-rakoto-ratsimamanga/vignettes/general-de-brigade-rakotoarimasy-andre-lucien.webp","source":"https://ceds-madagascar.com/promotions/2-rakoto-ratsimamanga/","rights":"Copyright / permission not established","credit":"C.E.D.S Madagascar","terms":["andre","lucien","rakotoarimasy"]},
]

CHAR_IDS={
 "Marcel_Ranjeva":("MAD_marcel_ranjeva","army"),
 "Andrianome_Ranivo_Dieudonne":("MAD_andrianome_dieudonne","army"),
 "Jules_Mamizara":("MAD_jules_mamizara","army"),
 "Sylvain_Razafimandimby":("MAD_sylvain_razafimandimby","army"),
 "Raonenantsoamampianina":("MAD_raonenantsoamampianina","army"),
 "Petera_Behajaina":("MAD_petera_behajaina","army"),
 "Noel_Girardin_Rakotonandrasana":("MAD_noel_rakotonandrasana","army"),
 "Edmond_Rasolomahandry":("MAD_edmond_rasolomahandry","army"),
 "Andre_Ndriarijaona":("MAD_andre_andriarijaona","army"),
 "Charles_Andrianasoavina":("MAD_charles_andrianasoavina","army"),
 "Mamy_Solofoniaina_Ranaivoniarivo":("MAD_mamy_ranaivoniarivo","navy"),
 "Hyppolite_Rarison_Ramaroson":("MAD_hyppolite_ramaroson","navy"),
 "Andre_Lucien_Rakotoarimasy":("MAD_andre_lucien_rakotoarimasy","army"),
}

def get_bytes(url):
    r=session.get(url,timeout=25,allow_redirects=True)
    r.raise_for_status()
    return r.content,r.headers.get("Content-Type","").lower()

def page_image(url, terms):
    body,_=get_bytes(url)
    soup=BeautifulSoup(body,"html.parser")
    needles=[x.casefold() for x in terms]
    ranked=[]
    def add(u,label,kind):
        u=urljoin(url,u)
        text=(u+" "+label+" "+kind).casefold()
        score=0
        if any(n in text for n in needles): score+=100
        if any(bad in text for bad in ("logo","avatar","icon","gravatar","spinner","placeholder")): score-=150
        if re.search(r"\.(jpe?g|png|webp)(?:[?#]|$)",u,re.I): score+=15
        if kind=="og:image": score+=5
        ranked.append((score,u))
    for meta in soup.find_all("meta"):
        k=(meta.get("property") or meta.get("name") or "").lower()
        if k in ("og:image","twitter:image","twitter:image:src") and meta.get("content"):
            add(meta["content"],meta.get("alt",""),"og:image")
    for img in soup.find_all("img"):
        u=img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not u and img.get("srcset"): u=img["srcset"].split(",")[0].strip().split(" ")[0]
        if u:
            add(u," ".join(str(img.get(k,"")) for k in ("alt","title","class","id")),"img")
    for _,u in sorted(ranked,key=lambda a:a[0],reverse=True)[:12]:
        try:
            data,ctype=get_bytes(u)
            if ctype.startswith("image/") or data[:4] in (b"\xff\xd8\xff\xdb",b"\xff\xd8\xff\xe0",b"\x89PNG",b"RIFF"):
                im=Image.open(io.BytesIO(data))
                if im.width>=120 and im.height>=120: return data
        except Exception: pass
    raise RuntimeError("No usable image found on " + url)

def pdf_face(src):
    data,_=get_bytes(src["url"])
    pdf=Path("/tmp")/(src["base"]+".pdf")
    pdf.write_bytes(data)
    prefix=Path("/tmp")/(src["base"]+"_page")
    subprocess.run(["pdftoppm","-f",str(src["page"]),"-l",str(src["page"]),"-r","600","-png","-singlefile",str(pdf),str(prefix)],check=True)
    page=Image.open(str(prefix)+".png").convert("RGB")
    cropped,found=crop_face(page,src.get("region","full"))
    if not found: raise RuntimeError("No face found in the requested PDF portrait region")
    buf=io.BytesIO(); cropped.save(buf,format="PNG"); return buf.getvalue()
def search_image(query, terms):
    needles=[x.casefold() for x in terms]
    candidates=[]
    def add(url, label, source):
        if not url:
            return
        label=(label+" "+source).casefold()
        score=sum(100 for n in needles if n in label)
        if "bahajaina" in label:
            score+=300
        if "andrianome" in label:
            score+=300
        if any(bad in label for bad in ("logo","avatar","icon","placeholder")):
            score-=250
        candidates.append((score,url,label))
    try:
        url="https://www.bing.com/images/search?q="+quote_plus(query)
        page,_=get_bytes(url)
        soup=BeautifulSoup(page,"html.parser")
        for item in soup.select("a.iusc"):
            try:
                meta=json.loads(html.unescape(item.get("m","{}")))
            except Exception:
                continue
            add(meta.get("murl")," ".join(str(meta.get(k,"")) for k in ("t","desc","purl")),"bing")
    except Exception as exc:
        print("Bing image search error: "+str(exc))
    try:
        url="https://www.google.com/search?tbm=isch&q="+quote_plus(query)
        page,_=get_bytes(url)
        soup=BeautifulSoup(page,"html.parser")
        for img in soup.find_all("img"):
            label=(img.get("alt") or "")
            u=img.get("src") or img.get("data-src")
            if u and u.startswith("http") and not u.startswith("data:"):
                parent=img.parent
                add(u,label+" "+(parent.get_text(" ",strip=True)[:500] if parent else ""),"google-image")
        decoded=page.decode("utf-8","ignore").replace("\\u003d","=").replace("\\u0026","&").replace("\\/","/")
        for u in re.findall(r'https?://[^"\\\s<>]+?\.(?:jpg|jpeg|png|webp)(?:\?[^"\\\s<>]*)?',decoded,re.I):
            add(u," ".join(needles),"google-json")
    except Exception as exc:
        print("Google image search error: "+str(exc))
    try:
        url="https://duckduckgo.com/?q="+quote_plus(query)+"&iax=images&ia=images"
        page,_=get_bytes(url)
        soup=BeautifulSoup(page,"html.parser")
        from urllib.parse import urlparse, parse_qs
        for img in soup.find_all("img"):
            label=img.get("alt") or ""
            u=img.get("src") or img.get("data-src")
            if not u:
                continue
            parsed=urlparse(urljoin(url,u))
            q=parse_qs(parsed.query)
            original=q.get("u",[None])[0]
            if original:
                add(original,label,"duckduckgo")
    except Exception as exc:
        print("DuckDuckGo image search error: "+str(exc))
    candidates.sort(key=lambda row:row[0],reverse=True)
    seen=set()
    print("Image search candidates for "+query+": "+str(len(candidates)))
    for score,imgurl,label in candidates:
        if score < 100 or imgurl in seen:
            continue
        seen.add(imgurl)
        try:
            data,ctype=get_bytes(imgurl)
            im=Image.open(io.BytesIO(data))
            if im.width>=120 and im.height>=120:
                print("Image search match score="+str(score)+" label="+label[:180]+" url="+imgurl)
                return data
        except Exception as exc:
            print("Image candidate rejected: "+imgurl+" :: "+str(exc)[:160])
    raise RuntimeError("No identifiable image result found for query: "+query)

def crop_face(image, region="full"):
    rgb=ImageOps.exif_transpose(image).convert("RGB")
    arr=cv2.cvtColor(np.array(rgb),cv2.COLOR_RGB2BGR)
    h,w=arr.shape[:2]; ox=oy=0
    if region=="lower_right":
        ox,oy=int(w*.48),int(h*.42); arr=arr[oy:,ox:]
    gray=cv2.cvtColor(arr,cv2.COLOR_BGR2GRAY)
    cascade=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
    faces=cascade.detectMultiScale(gray,scaleFactor=1.03,minNeighbors=2,minSize=(10,10))
    if len(faces)==0: return rgb,False
    fx,fy,fw,fh=max(faces,key=lambda f:int(f[2])*int(f[3]))
    fx+=ox; fy+=oy
    crop_h=max(int(fh*3.25),120); crop_w=max(int(crop_h*156/210),90)
    cx=fx+fw//2; cy=fy+int(fh*1.15)
    left=max(0,min(cx-crop_w//2,w-crop_w)); top=max(0,min(cy-int(fh*1.7),h-crop_h))
    crop_w=min(crop_w,w-left); crop_h=min(crop_h,h-top)
    return rgb.crop((left,top,left+crop_w,top+crop_h)),True

def create_dds(data,base):
    img=Image.open(io.BytesIO(data))
    crop,found=crop_face(img)
    if not found:
        ratio=156/210; w,h=img.size
        if w/h>ratio:
            nw=int(h*ratio); x=max(0,(w-nw)//2); crop=img.crop((x,0,x+nw,h))
        else:
            nh=int(w/ratio); y=max(0,(h-nh)//2); crop=img.crop((0,y,w,y+nh))
    crop=ImageOps.fit(crop,(156,210),method=Image.Resampling.LANCZOS,centering=(.5,.42)).convert("RGB")
    tmp=Path("/tmp")/(base+".png"); crop.save(tmp)
    sm=Path("/tmp")/(base+"_small.png"); crop.resize((38,51),Image.Resampling.LANCZOS).save(sm)
    for source,dest in ((tmp,MAIN/(base+".dds")),(sm,SMALL/(base+"_small.dds"))):
        subprocess.run(["convert",str(source),"-strip","-colorspace","sRGB","-type","TrueColor","-define","dds:compression=dxt1",str(dest)],check=True)

def add_char_portrait(text,char_id,base,role):
    pattern=re.compile(r"(\t"+re.escape(char_id)+r"\s*=\s*\{\n)(.*?)(\n\t\})",re.S)
    m=pattern.search(text)
    if not m: print("WARNING character block not found: "+char_id); return text
    block=m.group(0)
    if "portraits = {" in block: return text
    name=re.search(r'(\t\tname\s*=\s*"[^"]*"\n)',block)
    if not name: return text
    fields=(f'\t\tportraits = {{\n\t\t\t{role} = {{\n'
            f'\t\t\t\tsmall = "gfx/leaders/MAD/small/{base}_small.dds"\n'
            f'\t\t\t\tlarge = "gfx/leaders/MAD/{base}.dds"\n\t\t\t}}\n\t\t}}\n')
    pos=name.end()
    new=block[:pos]+fields+block[pos:]
    return text[:m.start()]+new+text[m.end():]

def add_event_pictures(text,available):
    leaders=[("Andry Rajoelina","Andry_Rajoelina"),
             ("Noël Girardin Rakotonandrasana","Noel_Girardin_Rakotonandrasana"),
             ("Edmond Rasolomahandry","Edmond_Rasolomahandry")]
    starts=[m.start() for m in re.finditer(r"create_country_leader\s*=\s*\{",text)]
    for start in reversed(starts):
        depth=0; end=None
        for i in range(start,text.__len__()):
            if text[i]=="{": depth+=1
            elif text[i]=="}":
                depth-=1
                if depth==0: end=i+1; break
        if end is None: continue
        block=text[start:end]
        n=re.search(r'name\s*=\s*"([^"]+)"',block)
        if not n or re.search(r'\bpicture\s*=',block): continue
        base=next((b for name,b in leaders if n.group(1)==name and b in available),None)
        if base:
            pos=start+n.end()
            text=text[:pos]+f'\n\t\t\tpicture = "{base}.dds"'+text[pos:]
    return text

def main():
    MAIN.mkdir(parents=True,exist_ok=True); SMALL.mkdir(parents=True,exist_ok=True)
    good=[]; bad=[]
    for src in SOURCES:
        try:
            if (MAIN/(src["base"]+".dds")).exists() and (SMALL/(src["base"]+"_small.dds")).exists():
                good.append(src)
                print("EXISTING "+src["base"]+": reusing committed DDS assets")
                continue
            if src["kind"]=="direct":
                data,ctype=get_bytes(src["url"])
                if "text/html" in ctype or data.lstrip().lower().startswith(b"<!doctype"):
                    data=page_image(src["url"],src.get("terms",[]))
            elif src["kind"]=="page":
                try: data=page_image(src["url"],src.get("terms",[]))
                except Exception:
                    if not src.get("fallback"): raise
                    data=page_image(src["fallback"],src.get("terms",[])); src["used_fallback"]=True
            elif src["kind"]=="pdf_face": data=pdf_face(src)
            elif src["kind"]=="image_search": data=search_image(src["query"],src.get("terms",[]))
            else: raise RuntimeError("Unknown source kind")
            im=Image.open(io.BytesIO(data))
            if im.width<80 or im.height<80: raise RuntimeError("source image too small")
            create_dds(data,src["base"])
            good.append(src)
            print("OK "+src["base"]+": "+src["source"]+"; "+src["rights"])
        except Exception as exc:
            bad.append((src["base"],str(exc)))
            print("FAILED "+src["base"]+": "+str(exc))
    available={s["base"] for s in good}
    chartext=CHAR_FILE.read_text(encoding="utf-8-sig")
    for base,(char_id,role) in CHAR_IDS.items():
        if base in available: chartext=add_char_portrait(chartext,char_id,base,role)
    CHAR_FILE.write_text(chartext,encoding="utf-8")
    evtext=EVENT_FILE.read_text(encoding="utf-8-sig")
    EVENT_FILE.write_text(add_event_pictures(evtext,available),encoding="utf-8")
    rows=["# Madagascar leader portrait sources","","Portrait dimensions: 156x210 main and 38x51 small, DDS DXT1.","Copyright notes are not licences. Non-CC photographs require permission before public redistribution.","","| Portrait | Source / credit | Rights status |","|---|---|---|"]
    for s in good:
        source=s["source"]+(" (fallback page used)" if s.get("used_fallback") else "")
        rows.append("| "+s["base"]+" | ["+s["credit"]+"]("+source+") | "+s["rights"]+" |")
    if bad:
        rows += ["","## Failed imports requiring another source",""]
        rows += ["- "+base+": "+why for base,why in bad]
    (MAIN/"portrait_sources.md").write_text("\n".join(rows)+"\n",encoding="utf-8")
    print("SUMMARY: "+str(len(good))+" imported; "+str(len(bad))+" unresolved.")
    for base,why in bad: print("UNRESOLVED "+base+": "+why)
    if "Andry_Rajoelina" not in available: return 2
    return 0

if __name__=="__main__": sys.exit(main())
