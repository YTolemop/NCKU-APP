"""Import a dated public NCKU catalogue snapshot and verified map destinations.
No student accounts, enrolments, cookies or private data are published.
Run with Python + lxml; network access is required for a refresh.
"""
from pathlib import Path
from lxml import html
import urllib.request, urllib.parse, http.cookiejar, re, json, time, concurrent.futures

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.cache'; CACHE.mkdir(exist_ok=True)
OUT=ROOT/'dist'; OUT.mkdir(exist_ok=True)
OLD=CACHE/'prior-research'
BASE='https://course.ncku.edu.tw/'
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def read(url,data=None,client=op):
    headers={'User-Agent':'Mozilla/5.0','Referer':BASE+'index.php?c=qry_all'}
    if data: headers['X-Requested-With']='XMLHttpRequest'
    req=urllib.request.Request(url,data=urllib.parse.urlencode(data).encode() if data else None,headers=headers)
    with client.open(req,timeout=25) as r: return r.read().decode('utf-8')
def txt(el): return ' '.join(' '.join(el.itertext()).split())
periods=list('01234N56789ABCD')
def sessions(cell):
    chunks=re.split(r'<br\s*/?>',html.tostring(cell,encoding='unicode'))
    out=[]
    for chunk in chunks:
        el=html.fromstring('<div>'+chunk+'</div>'); s=txt(el)
        match=re.search(r'\[([1-7])\]\s*([0-9NABCD])(?:\s*[~～-]\s*([0-9NABCD]))?',s)
        locs=[]
        for a in el.xpath('.//a[starts-with(@href,"javascript:maps")]'):
            m=re.search(r"maps\('([^']*)','([^']*)'",a.get('href'))
            if m: locs.append({'key':m[1]+':'+m[2],'label':txt(a),'location':m[1],'room':m[2]})
        if match:
            start=periods.index(match[2]); end=periods.index(match[3] or match[2])
            out.append({'day':int(match[1]),'periods':periods[start:end+1],'room':locs[0] if locs else None})
        elif locs: out.append({'day':None,'periods':[],'room':locs[0]})
    return out

depts={'F7':'資訊工程','A9':'通識課程','A1':'外國語言','A7':'大學國文','A2':'體育','AF':'踏溯台南'}
landing=read(BASE+'index.php?c=qry_all')
crypt=re.search(r"'crypt'\s*:\s*'([^']+)'",landing)[1]
assert '115' in landing, 'Verify semester before importing'
courses=[]
for dept,label in depts.items():
    p=CACHE/f'courses_{dept}.html'
    if not p.exists():
        if dept in ['F7','A9'] and (OLD/p.name).exists(): p.write_bytes((OLD/p.name).read_bytes())
        else:
            d=json.loads(read(BASE+'index.php?c=qry_all&m=result_init',{'dept_no':dept,'crypt':crypt}))
            assert not d.get('err'),d
            p.write_text(read(BASE+'index.php?c=qry_all&m=result&i='+urllib.parse.quote(d['id'])),encoding='utf-8')
    root=html.fromstring(p.read_text(encoding='utf-8')); current=None; seen=set()
    for row in root.xpath('//tr'):
        t=row.xpath('./td'); name=row.xpath('.//*[@class="course_name"]')
        if len(t)!=10 or not name: continue
        name=txt(name[0]); seq=t[1].xpath('.//*[@class="dept_seq"]'); seq=txt(seq[0]) if seq else ''
        if not name:
            if current and '習' in txt(t[3]):
                current['tutorials'].append({'label':txt(t[2]),'teacher':txt(t[6]),'sessions':sessions(t[8])})
            continue
        if not seq or seq in seen: current=None; continue
        seen.add(seq)
        credit=re.match(r'(\d+(?:\.\d+)?)',txt(t[5])); links=row.xpath('.//a[contains(@href,"syllabus.php")]/@href')
        current={'id':seq,'name':name,'code':txt(t[1]),'department':dept,'departmentLabel':label,'year':txt(t[2]),'category':txt(t[3]),'credits':float(credit[1]) if credit else 0,'teacher':txt(t[6]),'notes':txt(t[4]),'sessions':sessions(t[8]),'timeText':txt(t[8]),'tutorials':[],'syllabus':links[0] if links else None}
        courses.append(current)
    print(dept,len(seen),flush=True)

rooms={}
for c in courses:
    for s in c['sessions']+sum([x['sessions'] for x in c['tutorials']],[]):
        if s['room']: rooms[s['room']['key']]=s['room']
mapfile=CACHE/'rooms.json'
maps=json.loads(mapfile.read_text(encoding='utf-8')) if mapfile.exists() else {}
if OLD.exists():
    for x in json.loads((OLD/'location_results.json').read_text(encoding='utf-8'))['locations']:
        key=x['location']+':'+x['room']; d=x.get('coordinates',{}).get('data',[])
        qs=urllib.parse.parse_qs(urllib.parse.urlparse(x['response']['url']).query)
        maps[key]={'url':x['response']['url'],'bid':qs.get('bid',[''])[0],'floor':qs.get('floor',[''])[0],'lat':float(d[0]['lat']) if d else None,'lng':float(d[0]['lon']) if d else None,'building':d[0]['name'] if d else ''}
def resolve(item):
    key,room=item
    try:
        client=urllib.request.build_opener()
        d=json.loads(read(BASE+'index.php?c=portal&m=maps',{'time':int(time.time()),'location':room['location'],'room_no':room['room']},client))
        url=d.get('url','')
        if not url.startswith('https://nckumap.ncku.edu.tw/'): return key,{'error':'官方地圖尚無位置'}
        qs=urllib.parse.parse_qs(urllib.parse.urlparse(url).query); bid=qs.get('bid',[''])[0]
        dest={'url':url,'bid':bid,'floor':qs.get('floor',[''])[0],'lat':None,'lng':None,'building':''}
        if bid:
            coord=json.loads(read('https://db.nckumap.ncku.edu.tw/nckugis/public/buildinfo.htm?'+urllib.parse.urlencode({'action':'getCentroidByBuildId','buildId':bid,'proj':'EPSG:4326'}),client=client)).get('data',[])
            if coord: dest.update(lat=float(coord[0]['lat']),lng=float(coord[0]['lon']),building=coord[0]['name'])
        return key,dest
    except Exception as e: return key,{'error':'位置待確認'}
pending=[(k,v) for k,v in rooms.items() if k not in maps]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    for i,(key,d) in enumerate(pool.map(resolve,pending)):
        maps[key]=d
        if i%25==0: print('Resolved maps',i+1,'/',len(pending),flush=True)
mapfile.write_text(json.dumps(maps,ensure_ascii=False),encoding='utf-8')
for key,room in rooms.items(): room.update(maps.get(key,{}))
data={'semester':'115-1','updatedAt':'2026-10-02','source':BASE+'index.php?c=qry_all','departments':depts,'courses':courses,'rooms':rooms}
(OUT/'data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('FINAL',len(courses),'courses',len(rooms),'rooms',sum(bool(x.get('lat')) for x in rooms.values()),'mapped',flush=True)
