#!/usr/bin/env python3
"""Validate actual profile order, formats, policies, rule bodies and integrity."""
import csv,hashlib,json,re
from pathlib import Path
from build import CATEGORIES,ROOT,BuildError,normal_rule
POLICIES={'paypal':'💳 PayPal 美国','wise':'💸 Wise 台湾','binance':'🪙 Binance 台湾','okx':'🪙 OKX 台湾','ai':'🤖 AI住宅','tiktok':'🎵 TikTok住宅','stream':'🎬 流媒体','google':'🔐 Google账户','uk':'🇬🇧 英国专属','global':'🌍 国际网络','cn':'DIRECT','ads':'REJECT'}
def validate(root=ROOT):
 dist=root/'dist/v4';profile=(root/'profiles/surge-V3.0.0.conf').read_text()
 if not re.search(r'(?m)^ipv6\s*=\s*false\s*$',profile):raise BuildError('Public release must disable IPv6')
 proxy=re.search(r'(?ms)^\[Proxy\]\s*\n(.*?)(?=^\[)',profile)
 if not proxy or proxy.group(1).strip():raise BuildError('Public release Proxy section must be blank')
 routes=[];section='';mounted={}
 for raw in profile.splitlines():
  line=raw.strip()
  if line.startswith('['):section=line
  if section!='[Rule]' or not line.startswith(('RULE-SET,https://','DOMAIN-SET,https://')):continue
  parts=next(csv.reader([line],skipinitialspace=True));kind,url,policy=parts[:3];name=url.rsplit('/',1)[-1]
  if not url.startswith('https://raw.githubusercontent.com/dalao-all/Surge-Diversion-Rules/main/dist/v4/'):raise BuildError('Unexpected resource origin')
  key='ads' if name=='ads.domainset' else name.removesuffix('.list')
  if kind!=('DOMAIN-SET' if key=='ads' else 'RULE-SET'):raise BuildError('Wrong resource format for '+name)
  if not (dist/name).is_file():raise BuildError('Missing resource '+name)
  if policy!=('REJECT-DROP' if key=='ads-storm' else POLICIES.get(key.removeprefix('protect-'))):raise BuildError('Wrong profile policy for '+name)
  if ('pre-matching' in parts)!=(key=='ads-storm'):raise BuildError('Only the physically protected narrow storm set may pre-match')
  routes.append(key);mounted[key]=name
 expected=['protect-'+c for c in CATEGORIES]+['ads-storm','ads']+list(CATEGORIES)
 if routes!=expected:raise BuildError('Profile/compiler routing order mismatch')
 count=0
 for key in expected:
  name=mounted[key]
  for raw in (dist/name).read_text().splitlines():
   if not raw.strip() or raw.startswith('#'):continue
   if key=='ads':normal_rule('DOMAIN-SUFFIX' if raw.startswith('.') else 'DOMAIN',raw.lstrip('.'))
   else:
    parts=raw.split(',');normal_rule(parts[0],parts[1],parts[2:])
   count+=1
 checks=(dist/'SHA256SUMS').read_text().splitlines();names=[line.split('  ')[-1] for line in checks]
 expected_files={key+'.list' for key in expected}|{'ads.domainset'}
 if len(names)!=len(expected_files) or set(names)!=expected_files:raise BuildError('Incomplete/duplicate checksum manifest')
 for line in checks:
  digest,name=line.split('  ')
  if hashlib.sha256((dist/name).read_bytes()).hexdigest()!=digest:raise BuildError('Hash mismatch '+name)
 ads_rules={(('DOMAIN-SUFFIX,'+r[1:]) if r.startswith('.') else ('DOMAIN,'+r)) for r in (dist/'ads.domainset').read_text().splitlines() if r and not r.startswith('#')}
 compat={r for r in (dist/'ads.list').read_text().splitlines() if r and not r.startswith('#')}
 if ads_rules!=compat:raise BuildError('DOMAIN-SET/legacy RULE-SET ad exports differ')
 from build import matches
 historical=json.loads((dist/'protected-history.json').read_text())
 for rule in (dist/'ads-storm.list').read_text().splitlines():
  if not rule or rule.startswith('#'):continue
  fields=rule.split(',')
  if len(fields)!=2 or fields[0]!='DOMAIN':raise BuildError('Storm set must contain exact domain rules only')
  name=fields[1]
  if not any(matches(r,name) for r in compat):raise BuildError('Storm set expands ad blocking scope')
  if any(matches(r,name) for r in historical):raise BuildError('Pre-matching storm rule overrides protected scope')
 report=json.loads((dist/'report.json').read_text())
 if not report['probes'] or not all(x['passed'] for x in report['probes']):raise BuildError('Probe report failed or empty')
 if re.search(r'(?im)^.*password\s*=\s*[^\s#]+',profile):raise BuildError('Possible password in public profile')
 general=profile.split('[General]',1)[1].split('[Proxy]',1)[0]
 for raw in general.splitlines():
  if raw.strip().startswith(('skip-proxy =','tun-excluded-routes =')) and '100.64.0.0/10' in raw:raise BuildError('CGNAT must remain eligible for Surge routing')
 print(f'PASS: {len(routes)} public resources, {count} rules, {len(report["probes"])} probes, policies, formats, hashes and empty Proxy')
if __name__=='__main__':validate()
