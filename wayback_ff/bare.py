import json,urllib.parse as up,urllib.request as ur,re,gzip,html,collections,time
d=json.load(open('cdx_all.json'))[1:]
bare=[]
for ts,u,_,ln in d:
    p=up.urlparse(u); q=dict(up.parse_qsl(p.query))
    leaf=p.path.rstrip('/').split('/')[-1]
    if leaf not in ('calendar','calendar.php'): continue
    if set(q)-{'s','print','permalink','c','do'}: continue
    bare.append((ts,u,int(ln)))
targets=[]
for y in ['2014','2017','2019','2021','2023','2024']:
    c=[b for b in bare if b[0][:4]==y]
    c.sort(key=lambda b:-b[2]); targets.append(c[0])
def fetch(ts,u):
    req=ur.Request('https://web.archive.org/web/'+ts+'id_/'+u,headers={'User-Agent':'Mozilla/5.0 Chrome/128','Accept-Encoding':'gzip'})
    raw=ur.urlopen(req,timeout=90).read()
    if raw[:2]==b'\x1f\x8b': raw=gzip.decompress(raw)
    return raw.decode('utf-8','replace')
def cell(r,cls):
    m=re.search(r'class="[^"]*calendar__'+cls+r'[^"]*"[^>]*>(.*?)</td>',r,re.S)
    return html.unescape(re.sub(r'<[^>]+>','',m.group(1))).strip() if m else ''
MAJ={'USD','EUR','GBP','JPY','AUD','NZD','CAD','CHF'}
for ts,u,ln in targets:
    try: s=fetch(ts,u)
    except Exception as e:
        print(ts,'FAIL',e); continue
    rws=re.split(r'<tr[^>]*class="[^"]*calendar_row',s)[1:]
    dates=[]; cur=''
    for r in rws:
        dcell=cell(r,'date')
        if dcell: cur=dcell
        dates.append(cur)
    recs=[(cell(r,'currency'),cell(r,'actual'),cell(r,'forecast')) for r in rws]
    maj=[r for r in recs if r[0] in MAJ]
    A=sum(1 for r in recs if r[1]); F=sum(1 for r in recs if r[2])
    noA=[r for r in maj if not r[1]]
    tzm=re.search(r"timezone_name:\s*'([^']+)'",s)
    tz2=re.search(r"Calendar Time Zone:\s*([^<]+)",s)
    ttl=re.search(r'<title>(.*?)</title>',s,re.S)
    print('---',ts,'|',u[:70])
    print('  title:',(ttl.group(1).strip() if ttl else '?')[:60],'| tz:',tzm.group(1) if tzm else '?','|',tz2.group(1).strip() if tz2 else '')
    print('  rows:',len(rws),'| distinct date headers:',len(set(d for d in dates if d)),'->',sorted(set(d for d in dates if d))[:9])
    print('  currencies:',sorted(set(r[0] for r in recs if r[0])))
    print('  actual filled:',A,'| forecast filled:',F,'| major8 rows:',len(maj))
    print('  major8 rows with EMPTY actual (=still future at crawl):',len(noA),'of which forecast filled:',sum(1 for r in noA if r[2]))
    time.sleep(2)
