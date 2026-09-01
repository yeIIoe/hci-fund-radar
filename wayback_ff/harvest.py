import json,re,gzip,html,time,datetime as dt,collections,random
import urllib.parse as up, urllib.request as ur
from pj import blob
MAJ={'USD','EUR','GBP','JPY','AUD','NZD','CAD','CHF'}
d=json.load(open('cdx_all.json'))[1:]
bare=[]
for ts,u,_,ln in d:
    p=up.urlparse(u); q=dict(up.parse_qsl(p.query))
    leaf=p.path.rstrip('/').split('/')[-1]
    if leaf not in ('calendar','calendar.php'): continue
    if set(q)-{'s','print','permalink','c','do'}: continue
    bare.append((ts,u,int(ln)))
byy=collections.defaultdict(list)
for b in bare: byy[b[0][:4]].append(b)
random.seed(11)
sample=[]
for y in ['2012','2014','2015','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025','2026']:
    c=[x for x in byy.get(y,[]) if x[2]>8000]
    if not c: continue
    c.sort(key=lambda x:-x[2])
    sample += random.sample(c[:200], min(3,len(c[:200])))
def fetch(ts,u):
    req=ur.Request('https://web.archive.org/web/'+ts+'id_/'+u,headers={'User-Agent':'Mozilla/5.0 Chrome/128','Accept-Encoding':'gzip'})
    raw=ur.urlopen(req,timeout=90).read()
    if raw[:2]==b'\x1f\x8b': raw=gzip.decompress(raw)
    return raw.decode('utf-8','replace')
def cell(r,cls):
    m=re.search(r'class="[^"]*calendar__'+cls+r'[^"]*"[^>]*>(.*?)</td>',r,re.S)
    return html.unescape(re.sub(r'<[^>]+>','',m.group(1))).strip() if m else ''
def parse(s,snapts):
    b=blob(s)
    if b:
        ev=[e for dd in b for e in dd['events']]
        return 'JSON',[(e['currency'],str(e.get('actual') or ''),str(e.get('forecast') or ''),e.get('dateline')) for e in ev]
    rws=re.split(r'<tr[^>]*class="[^"]*calendar_?_?row',s)[1:]
    out=[]
    for r in rws:
        out.append((cell(r,'currency'),cell(r,'actual'),cell(r,'forecast'),None))
    return 'HTML',out
tot=collections.Counter()
print('%-16s%-6s%-6s%-6s%-8s%-8s%-10s%s'%('snapshot(UTC)','mode','rows','maj8','A_fill','F_fill','PIT_obs','ccy'))
for ts,u,ln in sample:
    try: s=fetch(ts,u)
    except Exception as e:
        print(ts,'FAIL',type(e).__name__,str(e)[:60]); time.sleep(4); continue
    mode,recs=parse(s,ts)
    maj=[r for r in recs if r[0] in MAJ]
    A=sum(1 for r in maj if r[1]); F=sum(1 for r in maj if r[2])
    pit=sum(1 for r in maj if not r[1] and r[2])   # actual empty + forecast present = PIT forecast obs
    ccy=len(set(r[0] for r in recs if r[0] in MAJ))
    print('%-16s%-6s%-6d%-6d%-8d%-8d%-10d%d/8'%(ts,mode,len(recs),len(maj),A,F,pit,ccy))
    tot['snap']+=1; tot['maj']+=len(maj); tot['A']+=A; tot['F']+=F; tot['pit']+=pit
    time.sleep(1.5)
print()
print('SNAPSHOTS OK:',tot['snap'],'| major-8 rows:',tot['maj'],'| actual filled:',tot['A'],'| forecast filled:',tot['F'])
print('PIT forecast observations (actual EMPTY + forecast PRESENT):',tot['pit'])
print('=> PIT obs per bare snapshot: %.1f'%(tot['pit']/max(1,tot['snap'])))
