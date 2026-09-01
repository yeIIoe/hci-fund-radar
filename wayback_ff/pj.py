import re,json,datetime as dt,sys
BS=chr(92)
def blob(s):
    m=re.search(r'calendarComponentStates[[]\d+[]]\s*=\s*[{]\s*days:\s*(\[)',s)
    if not m: return None
    i=m.start(1); depth=0; instr=False; esc=False
    for j in range(i,len(s)):
        c=s[j]
        if instr:
            if esc: esc=False
            elif c==BS: esc=True
            elif c=='"': instr=False
            continue
        if c=='"': instr=True
        elif c in '[{': depth+=1
        elif c in ']}':
            depth-=1
            if depth==0: return json.loads(s[i:j+1])
    return None
if __name__=='__main__':
    s=open(sys.argv[1],encoding='utf-8').read()
    days=blob(s)
    print('days:',len(days))
    ev=[e for d in days for e in d['events']]
    print('events:',len(ev))
    print('keys:',sorted(ev[0].keys()))
    print('currencies:',sorted(set(e['currency'] for e in ev)))
    print()
    print('%-20s%-5s%-9s%-34s%-9s%-9s%-9s'%('utc_dateline','ccy','impact','event','ACTUAL','FCST','PREV'))
    for e in ev[:5]+ev[45:62]:
        d=dt.datetime.utcfromtimestamp(e['dateline']).strftime('%Y-%m-%d %H:%MZ')
        print('%-20s%-5s%-9s%-34s%-9s%-9s%-9s'%(d,e['currency'],str(e.get('impactTitle',''))[:8],e['name'][:33],str(e.get('actual','')),str(e.get('forecast','')),str(e.get('previous',''))))
