#!/usr/bin/env python3
"""Deterministic, fail-closed Surge rule compiler. Python 3.12+, stdlib only.

A failed acquisition, parser, regression or change guard never replaces dist/v4.
No secrets, node definitions, AI calls, ABP reinterpretation or DNS probing.
"""
from __future__ import annotations
import argparse, concurrent.futures, fnmatch, gzip, hashlib, ipaddress, json, os
import re, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / 'rulekit_v4'
CATEGORIES = ('paypal','wise','binance','okx','ai', 'tiktok', 'stream', 'google', 'uk', 'global', 'cn')
VERSION = '4.3.0'
class BuildError(Exception): pass

def sha(data):
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()
def jsontext(data): return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
def readjson(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default

def host(value):
    value = value.strip().rstrip('.').lower()
    try: value = value.encode('idna').decode('ascii')
    except UnicodeError as e: raise BuildError(f'Invalid IDNA: {value}') from e
    if not value or len(value) > 253 or any(not re.fullmatch(r'[a-z0-9_](?:[a-z0-9_-]{0,61}[a-z0-9_])?', p) for p in value.split('.')):
        raise BuildError(f'Invalid hostname: {value}')
    return value

class PSL:
    def __init__(self, text):
        self.exact, self.wild, self.exceptions = set(), set(), set()
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith('//'): continue
            if line.startswith('!'): self.exceptions.add(host(line[1:]))
            elif line.startswith('*.'): self.wild.add(host(line[2:]))
            else: self.exact.add(host(line))
        if len(self.exact) < 5000: raise BuildError('Public Suffix List incomplete')
    def public(self, name):
        if name in self.exceptions: return False
        return '.' not in name or name in self.exact or ('.' in name and name.split('.', 1)[1] in self.wild)

def normal_rule(kind, value, options=()):
    kind = kind.upper()
    opts = tuple(sorted(set(x.strip().lower() for x in options if x.strip())))
    if any(x not in ('no-resolve', 'extended-matching') for x in opts):
        raise BuildError(f'Unsupported option: {kind},{value},{opts}')
    if kind in ('DOMAIN', 'DOMAIN-SUFFIX'): value = host(value)
    elif kind in ('DOMAIN-KEYWORD', 'DOMAIN-WILDCARD'):
        value = value.strip().lower()
        if not value or ',' in value or any(c.isspace() for c in value): raise BuildError('Invalid domain pattern')
    elif kind in ('IP-CIDR', 'IP-CIDR6'):
        try: net = ipaddress.ip_network(value, strict=False)
        except ValueError as e: raise BuildError(f'Invalid CIDR: {value}') from e
        if (net.version == 6) != (kind == 'IP-CIDR6'): raise BuildError('Wrong IP family')
        value = str(net)
        # ipaddress versions differ on dotted vs hex IPv4-mapped IPv6 output.
        # Keep one stable semantic representation for source change guards.
        if net.version == 6 and net.network_address.ipv4_mapped is not None:
            mapped = int(net.network_address.ipv4_mapped)
            value = f'::ffff:{mapped >> 16:x}:{mapped & 65535:x}/{net.prefixlen}'
    elif kind == 'IP-ASN':
        if not value.isdigit() or not 0 < int(value) < 2**32: raise BuildError('Invalid ASN')
    else: raise BuildError(f'Unsupported rule type: {kind}')
    if 'no-resolve' in opts and kind not in ('IP-CIDR', 'IP-CIDR6', 'IP-ASN'): raise BuildError('no-resolve on domain')
    if 'extended-matching' in opts: raise BuildError('extended-matching changes entire RULE-SET; requires a separate reviewed set')
    return ','.join((kind, value, *opts))

def matches(rule, name):
    parts = rule.split(','); kind, value = parts[:2]
    name = name.lower().rstrip('.')
    if kind == 'DOMAIN': return name == value
    if kind == 'DOMAIN-SUFFIX': return name == value or name.endswith('.' + value)
    if kind == 'DOMAIN-KEYWORD': return value in name
    if kind == 'DOMAIN-WILDCARD': return fnmatch.fnmatchcase(name, value)
    try: return ipaddress.ip_address(name) in ipaddress.ip_network(value) if kind in ('IP-CIDR','IP-CIDR6') else False
    except ValueError: return False

def overlaps(a, b):
    ka, va = a.split(',')[:2]; kb, vb = b.split(',')[:2]
    if ka in ('IP-CIDR','IP-CIDR6') and kb == ka:
        return ipaddress.ip_network(va).overlaps(ipaddress.ip_network(vb))
    if ka == 'DOMAIN': return matches(b, va)
    if kb == 'DOMAIN': return matches(a, vb)
    if ka == kb == 'DOMAIN-SUFFIX': return matches(a, vb) or matches(b, va)
    if ka.startswith('DOMAIN') and kb.startswith('DOMAIN'):
        # Conservative witness checks; not a proof of arbitrary pattern disjointness.
        return matches(a, vb) or matches(b, va) or matches(a, 'probe.' + vb) or matches(b, 'probe.' + va)
    return a == b

def storm_subset(ads, protected, candidates):
    """Exact witnesses already rejected by cleaned ads, never expand blocking scope.

    Pre-matching outranks ordinary allow rules, so current AND historical protections
    are checked physically, even if a caller has not cleaned its ad set yet.
    """
    accepted=[];excluded=[]
    for name in sorted(set(host(x) for x in candidates)):
        if any(matches(p,name) for p in protected):
            excluded.append({'domain':name,'reason':'protected-current-or-historical'})
        elif not any(matches(r,name) for r in ads):
            excluded.append({'domain':name,'reason':'not-in-final-ad-set'})
        else: accepted.append(normal_rule('DOMAIN',name))
    return accepted,excluded

class Fetcher:
    def __init__(self, offline=False):
        self.offline = offline; self.cache = HERE / '.cache'; self.cache.mkdir(exist_ok=True)
        self.revisions = {}; self.records = {}; self.pending = {}; self.pending_refs = {}
    def get(self, url):
        path = self.cache / (sha(url) + '.txt')
        if url in self.pending: return self.pending[url]
        if self.offline:
            if not path.exists(): raise BuildError(f'Offline cache missing: {url}')
            return path.read_text(encoding='utf-8')
        last = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={'User-Agent':'Surge-Rulekit-v4', 'Accept':'text/plain'})
                with urllib.request.urlopen(req, timeout=40) as r:
                    data = r.read(12_000_001)
                    if len(data) > 12_000_000: raise BuildError('Source exceeds 12 MB')
                    text = data.decode('utf-8-sig')
                    if not text.strip() or re.search(r'<(?:!doctype|html|body)\b', text[:500], re.I): raise BuildError(f'Empty/HTML response: {url}')
                self.pending[url] = text
                return text
            except Exception as e:
                last = e
                if attempt < 2: time.sleep(2 ** attempt)
        raise BuildError(f'Fetch failed, previous release kept: {url}: {last}')
    def pin(self, repo, ref):
        key = (repo, ref)
        if key in self.revisions: return self.revisions[key]
        pinpath = self.cache / ('ref-' + sha(repo + '@' + ref) + '.txt')
        if self.offline:
            if not pinpath.exists(): raise BuildError(f'No pinned offline ref: {repo}@{ref}')
            rev = pinpath.read_text().strip()
        elif re.fullmatch('[0-9a-f]{40}', ref): rev = ref
        else:
            # One immutable SHA per repository/ref per run, all include files use it.
            result = subprocess.run(['git','ls-remote',f'https://github.com/{repo}.git',f'refs/heads/{ref}'],capture_output=True,text=True,timeout=60,check=True)
            rows = result.stdout.splitlines()
            if len(rows) != 1: raise BuildError(f'Cannot resolve branch: {repo}@{ref}')
            rev = rows[0].split()[0]
        if not re.fullmatch('[0-9a-f]{40}', rev): raise BuildError('Invalid commit SHA')
        self.pending_refs[pinpath] = rev; self.revisions[key] = rev
        return rev
    def commit_cache(self):
        for url, text in self.pending.items():
            (self.cache / (sha(url) + '.txt')).write_text(text, encoding='utf-8')
        for path, rev in self.pending_refs.items(): path.write_text(rev + '\n')
    def source_url(self, s):
        if s.get('repo') and s.get('path'):
            rev = self.pin(s['repo'], s.get('ref','master'))
            return f"https://raw.githubusercontent.com/{s['repo']}/{rev}/{s['path']}", rev
        return s['url'], None

def split_balanced(text):
    result=[]; start=0; depth=0
    for i,c in enumerate(text):
        if c=='(': depth+=1
        elif c==')': depth-=1
        elif c==',' and depth==0: result.append(text[start:i]); start=i+1
        if depth<0: raise BuildError('Unbalanced logical rule')
    if depth: raise BuildError('Unbalanced logical rule')
    result.append(text[start:]);return result

def flatten_or(line):
    parts=split_balanced(line)
    if len(parts)!=2 or parts[0]!='OR' or not parts[1].startswith('(') or not parts[1].endswith(')'):
        raise BuildError('Only plain OR of native atomic rules can be flattened')
    result=[]
    for child in split_balanced(parts[1][1:-1]):
        if not (child.startswith('(') and child.endswith(')')): raise BuildError('Malformed OR child')
        fields=split_balanced(child[1:-1])
        if len(fields)<2: raise BuildError('Malformed OR atom')
        result.append(normal_rule(fields[0],fields[1],fields[2:]))
    return result

class Parser:
    def __init__(self, fetcher): self.fetcher=fetcher; self.omissions=[]; self.children={}
    def parse(self, s, text, url, path=None, stack=(), filters=()):
        fmt = s['format'].lower(); path = path or s.get('path',''); identity=(path,tuple(filters))
        if any(entry[0] == path for entry in stack): raise BuildError(f'include cycle: {path}')
        output=[]
        for number, raw in enumerate(text.splitlines(),1):
            line = raw.strip()
            if not line or line.startswith(('#','//',';')): continue
            line = line.split(' #',1)[0].strip()
            if fmt in ('v2fly','v2','geosite'):
                line = line.split('#',1)[0].strip()
                if not line: continue
                parts=line.split(); target=parts[0]; tags=set(x[1:] for x in parts[1:] if x.startswith('@'))
                if target.startswith('include:'):
                    child=target[8:]
                    if not re.fullmatch(r'[a-zA-Z0-9_.-]+',child): raise BuildError('Invalid include path')
                    childpath='data/'+child
                    childurl=url.rsplit('/data/',1)[0]+'/'+childpath
                    childtext=self.fetcher.get(childurl)
                    self.children[childurl]={'sha256':sha(childtext),'path':childpath}
                    output.extend(self.parse(s,childtext,childurl,childpath,(*stack,identity),(*filters,*tags)))
                    continue
                if any((t[1:] in tags if t.startswith('!') else t not in tags) for t in filters): continue
                if set(s.get('exclude_tags',[])) & tags: continue
                kind, sep, value=target.partition(':')
                if not sep: kind,value='domain',target
                if kind == 'regexp':
                    self.omissions.append({'source':s['id'],'url':url,'line':number,'raw':raw,'reason':'v2 regexp has no equivalent supported Surge domain rule; explicit coverage gap'})
                    continue
                mapping={'domain':'DOMAIN-SUFFIX','full':'DOMAIN','keyword':'DOMAIN-KEYWORD'}
                if kind not in mapping: raise BuildError(f'Unknown v2 directive: {kind}')
                rule=normal_rule(mapping[kind],value)
            elif fmt in ('domainset','domain-set'):
                rule=normal_rule('DOMAIN-SUFFIX' if line.startswith('.') else 'DOMAIN',line.lstrip('.'))
            elif fmt in ('surge','ruleset','surge-ruleset','native'):
                if line.startswith('OR,'):
                    for atomic in flatten_or(line):
                        output.append((atomic,{'source':s['id'],'url':url,'line':number,'raw':raw,'app_ids':s.get('app_ids',[]),'purpose':s.get('role','functional'),'confidence':'equivalent flattened OR of upstream atoms'}))
                    continue
                parts=[p.strip() for p in line.split(',')]
                if parts[0] in ('USER-AGENT','PROCESS-NAME','PROCESS-PATH'):
                    self.omissions.append({'source':s['id'],'url':url,'line':number,'raw':raw,'reason':'non-domain app/process identity not portable to iOS domain routing'})
                    continue
                if len(parts)<2: raise BuildError(f'Malformed Surge rule {s["id"]}:{number}')
                rule=normal_rule(parts[0],parts[1],parts[2:])
            else: raise BuildError(f'Unsupported format: {fmt}; ABP is intentionally not accepted')
            output.append((rule,{'source':s['id'],'url':url,'line':number,'raw':raw,'app_ids':s.get('app_ids',[]),'dependency_ids':s.get('dependency_ids',[]),'purpose':s.get('role','functional'),'confidence':'upstream classification; not packet-capture verified'}))
        return output

def guard(old, new, label):
    old,new=set(old),set(new)
    if not new: raise BuildError(f'Empty required source: {label}')
    if not old: return
    removed=old-new; added=new-old
    if (removed and len(removed)==len(old)) or len(removed)>max(3,len(old)*0.25) or len(added)>max(50,len(old)*0.5):
        raise BuildError(f'Change guard: {label}: old={len(old)} new={len(new)} +{len(added)} -{len(removed)}; inspect upstream, then explicitly revise the baseline in a reviewed commit')

def output_rule(source, rule):
    category='ads' if source.get('role')=='ads' else source.get('category')
    note=None
    kind,value=rule.split(',')[:2]
    if source.get('numeric_ip_keywords_to_cidr') and kind=='DOMAIN-KEYWORD' and re.match(r'^\d',value):
        if not re.fullmatch(r'(?:\d{1,3}\.){3}',value): raise BuildError('Unreviewed numeric IP keyword shape: '+rule)
        corrected=normal_rule('IP-CIDR',value+'0/24',('no-resolve',))
        note={'original_rule':rule,'output_rule':corrected,'reason':'Intentional policy correction: three-octet substring becomes the exact intended /24; not a semantics-equivalent conversion'}
        rule=corrected
    override=source.get('output_rule_overrides',{}).get(rule)
    if override:
        category=override.get('category',category)
        if override.get('rule'):
            parts=override['rule'].split(',');rule=normal_rule(parts[0],parts[1],parts[2:])
        note={'original_rule':rule,'output_rule':rule,'reason':override['reason'],'output_category':category}
    return category,rule,note

def active_sources(config, apps):
    active={a['id'] for a in apps['apps'] if a.get('enabled',True)}
    deps=set(d for a in apps['apps'] if a['id'] in active for d in a.get('dependency_ids',[]))
    refs=set(s for a in apps['apps'] if a['id'] in active for s in a.get('source_ids',[]))
    for d in apps.get('dependencies',[]):
        if d['id'] in deps or d.get('always_enabled'): refs.update(d.get('source_ids',[]))
    available={s['id'] for s in config['sources'] if s.get('enabled',True)}
    if refs-available: raise BuildError('Missing/disabled referenced source: '+','.join(sorted(refs-available)))
    dep_ids={d['id'] for d in apps.get('dependencies',[])}
    if deps-dep_ids: raise BuildError('Missing dependency: '+','.join(sorted(deps-dep_ids)))
    if any(a.get('category') not in CATEGORIES for a in apps['apps'] if a['id'] in active): raise BuildError('Invalid app category')
    return [s for s in config['sources'] if s.get('enabled',True) and (s.get('role') in ('ads','infrastructure','network','security') or s['id'] in refs or set(s.get('dependency_ids',[]))&deps or set(s.get('app_ids',[]))&active)],active

def apply_ads_guard(ads, guard_config):
    """Physically remove ad rules whose host contains a reviewed infrastructure keyword.

    Mutates ``ads`` in place and returns removal records. Each keyword has a hard cap
    (default 100) so an overbroad keyword fails closed instead of silently gutting ads.
    """
    removed=[]
    for item in guard_config.get('keyword_exemptions',[]):
        keyword=str(item.get('keyword','')).strip().lower()
        if len(keyword)<4 or not re.fullmatch(r'[a-z0-9.-]+',keyword):
            raise BuildError(f'Invalid ads-guard keyword: {keyword!r}')
        if not item.get('reason'): raise BuildError(f'ads-guard keyword needs a reason: {keyword}')
        hits=sorted(r for r in ads if keyword in r.split(',')[1])
        limit=int(item.get('max_removals',100))
        if len(hits)>limit:
            raise BuildError(f'ads-guard keyword {keyword} would remove {len(hits)} ad rules (max {limit}); review the keyword')
        for rule in hits:
            ads.discard(rule); removed.append({'rule':rule,'guard_keyword':keyword,'reason':item['reason']})
    return removed

def route(tables, name):
    for category in CATEGORIES:
        for r in tables['protect-'+category]:
            if matches(r,name): return category,r
    for r in tables['ads']:
        if matches(r,name): return 'ads',r
    for category in CATEGORIES:
        for r in tables[category]:
            if matches(r,name): return category,r
    return None,None

def compile_rules(offline=False, output=None):
    destination=Path(output) if output else ROOT/'dist/v4'
    interrupted=destination.with_name(destination.name+'.previous')
    if not destination.exists() and interrupted.exists(): interrupted.rename(destination)
    apps=readjson(HERE/'apps.json'); config=readjson(HERE/'sources.json')
    if len(apps['apps']) != len({a['id'] for a in apps['apps']}): raise BuildError('Duplicate app ID')
    sources,active=active_sources(config,apps)
    if not sources: raise BuildError('No active sources')
    if len(sources) != len({s['id'] for s in sources}): raise BuildError('Duplicate source ID')
    fetch=Fetcher(offline); parser=Parser(fetch); psl=PSL((HERE/'data/public_suffix_list.dat').read_text())
    corrections=[]
    tables={k:set() for k in (*CATEGORIES,*('protect-'+c for c in CATEGORIES),'ads')}; provenance={}; lock={}; source_rules={}
    previous=readjson(destination/'source-rules.json',{})
    bootstrap=readjson(HERE/'bootstrap.json',{}) if not previous else {}
    prepared=[]
    for s in sources:
        if s.get('license',{}).get('redistribution_allowed') is False: raise BuildError('Source redistribution not authorized: '+s['id'])
        if not s.get('url') and not s.get('repo'): continue
        url,rev=fetch.source_url(s); prepared.append((s,url,rev))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        fetched=list(pool.map(lambda x: fetch.get(x[1]),prepared))
    for (s,url,rev),text in zip(prepared,fetched):
        records=parser.parse(s,text,url)
        excluded=set(s.get('exclude_rules',[]))
        for r,origin in records:
            if r in excluded: parser.omissions.append(dict(origin,rule=r,reason=s.get('exclude_reason','explicit reviewed source exclusion')))
        records=[(r,o) for r,o in records if r not in excluded]
        if 'accepted_rules' in s:
            accepted=set(s['accepted_rules'])
            for r,origin in records:
                if r not in accepted:
                    parser.omissions.append(dict(origin,rule=r,reason='Supplement outside independently reviewed scope; retained as candidate, not auto-published'))
            records=[(r,o) for r,o in records if r in accepted]
        rules=sorted({r for r,_ in records}); guard(previous.get(s['id'],[]),rules,s['id'])
        if s['id'] in bootstrap and sha('\n'.join(rules))!=bootstrap[s['id']]: raise BuildError('First-release source differs from locally reviewed baseline: '+s['id'])
        source_rules[s['id']]=rules
        lock[s['id']]={'url':url,'upstream_commit':rev,'sha256':sha(text),'semantic_sha256':sha('\n'.join(rules)),'rules':len(rules),'license':s.get('license',{})}
        category='ads' if s.get('role')=='ads' else s.get('category')
        if category not in tables: raise BuildError(f'Invalid category {category}')
        for rule,origin in records:
            outcat,outrule,note=output_rule(s,rule)
            if outcat not in tables: raise BuildError('Invalid transformed category')
            if note: corrections.append(dict(note,source=s['id']));origin=dict(origin,correction=note)
            tables[outcat].add(outrule); provenance.setdefault(outcat+'|'+outrule,[]).append(origin)
    # Local reviewed lists are manifest entries, never a filesystem glob that silently adds apps.
    for s in sources:
        if s.get('url') or s.get('repo'): continue
        path=(HERE/s['path']).resolve()
        if HERE.resolve() not in path.parents: raise BuildError('Local source escapes rulekit')
        text=path.read_text(); local=dict(s,format='surge'); records=parser.parse(local,text,'local:'+s['path'])
        rules=sorted({r for r,_ in records}); guard(previous.get(s['id'],[]),rules,s['id'])
        if s['id'] in bootstrap and sha('\n'.join(rules))!=bootstrap[s['id']]: raise BuildError('First-release local baseline differs: '+s['id'])
        source_rules[s['id']]=rules; lock[s['id']]={'url':'local:'+s['path'],'sha256':sha(text),'semantic_sha256':sha('\n'.join(rules)),'rules':len(rules)}
        cat=s['category']
        for rule,origin in records:
            outcat,outrule,note=output_rule(s,rule)
            if note: corrections.append(dict(note,source=s['id']));origin=dict(origin,correction=note)
            tables[outcat].add(outrule); provenance.setdefault(outcat+'|'+outrule,[]).append(origin)
    protections=readjson(HERE/'protection.json',{'rules':[]})['rules']
    protected=[]
    for p in protections:
        if p.get('app_ids') and not set(p['app_ids'])&active: continue
        if p['type'] not in ('DOMAIN','DOMAIN-SUFFIX','IP-CIDR','IP-CIDR6'): raise BuildError('Unsupported protection type; wildcard/keyword protection cannot prove ad disjointness')
        rule=normal_rule(p['type'],p['value'],p.get('options',[])); cat=p['category']
        tables['protect-'+cat].add(rule); tables[cat].add(rule); protected.append(rule)
        provenance['protect-'+cat+'|'+rule]=[p]
    # Physical removal guarantees an old protection download + new ads download is safe.
    # Carry historical protected scope monotonically; removing an app cannot re-enable its ads.
    historical=set(readjson(destination/'protected-history.json',[])); historical.update(protected)
    removed_ads=[]
    protection_parts=[(p,*p.split(',')[:2]) for p in sorted(historical) if p.startswith(('DOMAIN,','DOMAIN-SUFFIX,'))]
    for rule in sorted(tables['ads']):
        kind,value=rule.split(',')[:2]
        if kind not in ('DOMAIN','DOMAIN-SUFFIX'): raise BuildError(f'Non-domain ad rule needs review: {rule}')
        if psl.public(value): raise BuildError(f'Ad rule targets public/private suffix: {rule}')
        for protection,pk,pv in protection_parts:
            conflict=(value==pv or (pk=='DOMAIN-SUFFIX' and value.endswith('.'+pv)) or (kind=='DOMAIN-SUFFIX' and pv.endswith('.'+value)))
            if conflict:
                tables['ads'].remove(rule); removed_ads.append({'rule':rule,'protection':protection}); break
    # Keyword guard: never REJECT resolver/HTTPDNS-style infrastructure hosts. Removal only
    # shrinks blocking scope, so substring matching here cannot over-block (unlike protections).
    removed_ads.extend(apply_ads_guard(tables['ads'],readjson(HERE/'ads-guard.json',{'keyword_exemptions':[]})))
    if not tables['ads']: raise BuildError('Ads became empty')
    storm,storm_excluded=storm_subset(tables['ads'],historical,readjson(HERE/'storm-candidates.json',{'domains':[]})['domains'])
    tables={k:sorted(v,key=lambda r:(0 if r.startswith('DOMAIN,') else 1 if r.startswith('DOMAIN-SUFFIX,') else 2,r)) for k,v in tables.items()}
    probes=readjson(HERE/'probes.json',{'probes':[]})['probes']; results=[]
    for p in probes:
        if p.get('app_ids') and not set(p['app_ids'])&active: continue
        got,rule=route(tables,p['domain']); expected=p['expected_category']
        ok=got==expected
        results.append(dict(p,actual_category=got,matched_rule=rule,passed=ok))
    migration=readjson(HERE/'migration-audit.json',{'migration':[]})['migration']
    for old in migration:
        witness=old['rule'].split(',')[1];actual,matched=route(tables,witness)
        if actual!=old['current_category']: raise BuildError('Legacy allow migration regression: '+old['rule']+' expected '+old['current_category']+' got '+str(actual))
    failed=[r for r in results if not r['passed']]
    if failed: raise BuildError('Probe regression: '+json.dumps(failed,ensure_ascii=False))
    from content_checks import check_content
    content_audit=check_content(tables,CATEGORIES,[p for p in probes if not p.get('app_ids') or set(p['app_ids'])&active],readjson(HERE/'content-review.json',{}))
    # Record concrete cross-category overlaps. More-specific earlier categories are intentional.
    conflicts=[]
    seen={}
    for cat in CATEGORIES:
        for r in tables[cat]:
            if r in seen: conflicts.append({'rule':r,'winner':seen[r],'shadowed':cat})
            else: seen[r]=cat
    shadow_witnesses=[]
    earlier=[]
    for cat in CATEGORIES:
        for r in tables[cat]:
            kind,value=r.split(',')[:2]
            if kind not in ('DOMAIN','DOMAIN-SUFFIX'): continue
            for prevcat,prevrules in earlier:
                winner=next((prior for prior in prevrules if prior != r and prior.startswith('DOMAIN') and matches(prior,value)),None)
                if winner:
                    shadow_witnesses.append({'witness':value,'winner_category':prevcat,'winner_rule':winner,'shadowed_category':cat,'shadowed_rule':r});break
        earlier.append((cat,tables[cat]))
    report={'storm_reject':{'rules':storm,'excluded':storm_excluded,'policy':'REJECT-DROP','pre_matching':True},'compiler_version':VERSION,'enabled_apps':len(active),'sources':len(sources),'counts':{k:len(v) for k,v in tables.items()},'probes':results,'removed_ads':removed_ads,'parser_omissions':parser.omissions,'legacy_allow_migration_checks':len(migration),'output_corrections':corrections,'exact_cross_category_overlaps':conflicts,'cross_category_shadow_witnesses':shadow_witnesses,'limits':['Static domain/IP checks, not iPhone business or node reachability validation','v2 regex and non-domain process rules explicitly excluded; see parser_omissions','Pattern overlap checks are conservative witnesses, not a proof of all wildcard languages','No online stale-cache fallback: any source acquisition failure keeps last published release']}
    # Only fully validated output reaches staging. Replace complete dir, restore on rename error.
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.v4-stage-',dir=destination.parent))
    try:
        for cat,rules in tables.items():
            (staging/(cat+'.list')).write_text('# Surge Rulekit v4 | '+cat+' | policy supplied by main profile\n'+'\n'.join(rules)+'\n')
        (staging/'ads-storm.list').write_text('# Narrow exact ad SDK endpoints; main profile applies REJECT-DROP,pre-matching.\n'+'\n'.join(storm)+'\n')
        (staging/'ads.domainset').write_text('# Pure-domain ad set; exact host or leading-dot suffix. ads.list remains a compatibility export.\n'+'\n'.join(('.' if r.startswith('DOMAIN-SUFFIX,') else '')+r.split(',')[1] for r in tables['ads'])+'\n')
        (staging/'sources.lock.json').write_text(jsontext({'compiler_version':VERSION,'sources':lock,'includes':parser.children,'psl_sha256':sha((HERE/'data/public_suffix_list.dat').read_bytes())}))
        (staging/'source-rules.json').write_text(jsontext(source_rules))
        (staging/'protected-history.json').write_text(jsontext(sorted(historical)))
        (staging/'report.json').write_text(jsontext(report))
        (staging/'content-audit.json').write_text(jsontext(content_audit))
        table_sets={k:set(v) for k,v in tables.items()}
        with (staging/'provenance.ndjson.gz').open('wb') as rawfile, gzip.GzipFile(filename='',mode='wb',fileobj=rawfile,mtime=0) as f:
            for key,origins in sorted(provenance.items()):
                cat,rule=key.split('|',1)
                f.write((json.dumps({'category':cat,'rule':rule,'published':rule in table_sets[cat],'origins':origins},ensure_ascii=False,separators=(',',':'))+'\n').encode())
        (staging/'SHA256SUMS').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted([*staging.glob('*.list'),staging/'ads.domainset'])))
        fetch.commit_cache()
        backup=destination.with_name(destination.name+'.previous')
        if backup.exists(): shutil.rmtree(backup)
        if destination.exists(): destination.rename(backup)
        try: staging.rename(destination)
        except Exception:
            if backup.exists(): backup.rename(destination)
            raise
        if backup.exists(): shutil.rmtree(backup)
    finally:
        if staging.exists(): shutil.rmtree(staging)
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');p.add_argument('--output');args=p.parse_args()
    try:
        report=compile_rules(args.offline,args.output)
        print(jsontext({k:report[k] for k in ('compiler_version','enabled_apps','sources','counts')}))
        print(f"PASS: {len(report['probes'])} static probes; {len(report['parser_omissions'])} explicit omissions")
    except Exception as e:
        print(f'BUILD FAILED; published output unchanged: {e}',file=sys.stderr);sys.exit(1)
if __name__=='__main__': main()
