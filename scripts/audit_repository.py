#!/usr/bin/env python3
"""Check active documentation, generated inventory and public release hygiene."""
import json,re,subprocess,tempfile,urllib.parse
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.scripts=[];self.in_script=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  for key in ('href','src'):
   if a.get(key):self.links.append(a[key])
  if tag=='script' and not a.get('src'):self.in_script=True
 def handle_endtag(self,tag):
  if tag=='script':self.in_script=False
 def handle_data(self,data):
  if self.in_script:self.scripts.append(data)
def audit(root=ROOT):
 errors=[];checked=0
 files=[root/'README.md',root/'profiles/README.md',root/'rulekit_v4/README.md',*sorted((root/'docs').rglob('*.md')),root/'index.html',root/'rule-map.html']
 for p in files:
  if not p.exists():continue
  text=p.read_text();links=[]
  if p.suffix=='.html':
   page=Page();page.feed(text);links=page.links
   if page.scripts:
    with tempfile.NamedTemporaryFile('w',suffix='.js') as f:
     f.write('\n'.join(page.scripts));f.flush()
     subprocess.run(['node','--check',f.name],check=True,stdout=subprocess.DEVNULL)
  else:links=[m[1] for m in re.finditer(r'\]\(([^)]+)\)',text)]
  for link in links:
   link=link.split(' "')[0].strip('<>');url=urllib.parse.urlsplit(link)
   if url.scheme or url.netloc or not url.path or url.path.startswith('/'):continue
   target=(p.parent/urllib.parse.unquote(url.path)).resolve();checked+=1
   if not target.exists():errors.append(str(p.relative_to(root))+' -> '+url.path)
 apps=json.loads((root/'rulekit_v4/apps.json').read_text())['apps'];status=json.loads((root/'repository-status.json').read_text())
 if len(apps)!=status['app_count'] or len({a['id'] for a in apps})!=len(apps):errors.append('App inventory/status count mismatch')
 matrix=(root/'docs/APP_POLICY_MATRIX.md').read_text();rows=re.findall(r'(?m)^\|\s*((?:CN|INT)\d{3})\s*\|',matrix)
 if rows!=[a['id'] for a in apps]:errors.append('App matrix does not match manifest order')
 for name in ('rulekit.yml','ads-sync.yml'):
  p=root/'.github/workflows'/name
  if p.exists() and re.search(r'(?m)^  (?:schedule|push):',p.read_text()):errors.append('Legacy automatic writer still enabled: '+name)
 health=(root/'.github/workflows/rulekit-v4-health.yml').read_text()
 if re.search(r'(?m)^  push:',health) or 'workflow_run:' not in health:errors.append('Health still races initial deployment')
 for name in ('surge-V3.0.0.conf','Surge-v4.template.conf'):
  text=(root/'profiles'/name).read_text();proxy=re.search(r'(?ms)^\[Proxy\]\s*\n(.*?)(?=^\[)',text)
  if not proxy or proxy[1].strip() or 'ipv6 = false' not in text:errors.append('Public profile settings incorrect: '+name)
 if errors:raise SystemExit('Repository audit failed:\n'+'\n'.join(errors))
 print(f'PASS: {len(files)} documentation/site files, {checked} local links, {len(apps)} manifest/matrix rows, JS syntax, public profile hygiene and workflow activation')
if __name__=='__main__':audit()
