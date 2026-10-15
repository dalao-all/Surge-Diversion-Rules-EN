#!/usr/bin/env python3
"""English read-only mirror of a pinned, successfully validated Chinese release.

Only this repository is written. No PAT or cross-repository write permission.
Untrusted canonical data never executes before the pinned tree and evidence checks.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,os,re,shutil,subprocess,tempfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CANONICAL='dalao-all/Surge-Diversion-Rules'
ENGINE='rulekit_v4'
class SyncError(Exception):pass

def source_evidence(fetch_json,now=None):
    now=now or datetime.datetime.now(datetime.timezone.utc)
    data=fetch_json(f'https://api.github.com/repos/{CANONICAL}/actions/workflows/rulekit-v4.yml/runs?branch=main&per_page=30')
    runs=[r for r in data.get('workflow_runs',[]) if r.get('head_branch')=='main' and r.get('event')!='pull_request']
    completed=[r for r in runs if r.get('status')=='completed']
    if not completed or completed[0].get('conclusion')!='success':raise SyncError('Canonical latest completed rule update is not successful')
    run=completed[0];stamp=datetime.datetime.fromisoformat(run['updated_at'].replace('Z','+00:00'))
    if (now-stamp).total_seconds()>36*3600:raise SyncError('Canonical validation is older than 36 hours')
    return {'validated_input_commit':run['head_sha'],'validation_run_id':run['id'],'validation_run_url':run['html_url']}

def get_json(url):
    headers={'Accept':'application/vnd.github+json','User-Agent':'surge-en-verified-mirror'}
    if os.getenv('GITHUB_TOKEN'):headers['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as r:return json.load(r)

def english_profile(text):
    header='#!name=surge-V3.0.0\n# IPv6 disabled. [Proxy] is intentionally empty: add your own authorized nodes.\n# Keep the original node labels referenced by fallback groups, or adjust the group members.\n# Rules use the canonical Chinese repository; engine/resource path v4 is independent of this release name.\n# See docs/GETTING_STARTED.md for setup and node label requirements.\n\n'
    return header+'\n'.join(l for l in text.splitlines() if not l.lstrip().startswith(('#',';','//')))+'\n'

def manifest(source):
    result={}
    for folder in ('rulekit_v4','dist/v4'):
        for p in sorted((source/folder).rglob('*')):
            if p.is_symlink():raise SyncError('Canonical symlink rejected')
            if not p.is_file() or p.name=='README.md' or '.cache' in p.parts or '__pycache__' in p.parts:continue
            result[str(p.relative_to(source))]=p.read_bytes()
    for name in ('profiles/surge-V3.0.0.conf','profiles/Surge-v4.template.conf'):
        if (source/'profiles/surge-V3.0.0.conf').is_symlink(): raise SyncError('Canonical profile symlink rejected')
        result[name]=english_profile((source/'profiles/surge-V3.0.0.conf').read_text()).encode()
    for name in ('scripts/generate_repository_status.py','scripts/sync_from_canonical.py','scripts/audit_repository.py','scripts/test_sync.py'):
        if (source/name).is_symlink(): raise SyncError('Canonical script symlink rejected')
        result[name]=(source/name).read_bytes()
    if not result or 'dist/v4/SHA256SUMS' not in result:raise SyncError('Canonical release is incomplete')
    return result

def verify_snapshot(source):
    sums=source/'dist/v4/SHA256SUMS';items=[]
    for line in sums.read_text().splitlines():
        digest,name=line.split('  ')
        if '/' in name or not re.fullmatch('[0-9a-f]{64}',digest):raise SyncError('Invalid checksum entry')
        if hashlib.sha256((source/'dist/v4'/name).read_bytes()).hexdigest()!=digest:raise SyncError('Canonical checksum mismatch')
        items.append(name)
    expected={*(f'protect-{c}.list' for c in ('paypal','wise','binance','okx','ai','tiktok','stream','google','uk','global','cn')),'ads.list',*(c+'.list' for c in ('paypal','wise','binance','okx','ai','tiktok','stream','google','uk','global','cn'))}
    expected.update(('ads.domainset','ads-storm.list'))
    if len(items)!=25 or set(items)!=expected:raise SyncError('Canonical checksum manifest must cover 24 RULE-SET exports plus the ad DOMAIN-SET')
    report=json.loads((source/'dist/v4/report.json').read_text())
    if not report.get('probes') or any(not x.get('passed') for x in report['probes']):raise SyncError('Canonical probe report failed')
    profile=(source/'profiles/surge-V3.0.0.conf').read_text()
    proxy=re.search(r'(?ms)^\[Proxy\]\s*\n(.*?)(?=^\[)',profile)
    if not proxy or proxy.group(1).strip() or not re.search(r'(?m)^ipv6\s*=\s*false\s*$',profile):raise SyncError('Canonical public profile settings invalid')

def sync(source,root,evidence,commit,check_only=False):
    verify_snapshot(source);payload=manifest(source)
    with tempfile.TemporaryDirectory(prefix='surge-en-stage-') as temp:
        stage=Path(temp)/'repo';shutil.copytree(root,stage,ignore=shutil.ignore_patterns('.git','.cache','__pycache__'))
        for folder in ('rulekit_v4','dist/v4'):
            target=stage/folder
            if target.exists():
                for p in list(target.rglob('*')):
                    if p.is_file() and p.name!='README.md':p.unlink()
        for name,data in payload.items():
            p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        # Code in this staging tree is the same owner's pinned reviewed engine, never fetched from arbitrary URLs.
        subprocess.run([os.sys.executable,'-m','unittest','discover','-s','rulekit_v4','-p','test_*.py','-q'],cwd=stage,check=True)
        subprocess.run([os.sys.executable,'-m','unittest','discover','-s','scripts','-p','test_sync.py','-q'],cwd=stage,check=True)
        subprocess.run([os.sys.executable,'rulekit_v4/validate_release.py'],cwd=stage,check=True)
        subprocess.run([os.sys.executable,'scripts/generate_repository_status.py'],cwd=stage,check=True)
        evidence=dict(evidence,canonical_repository=CANONICAL,canonical_commit=commit,files={k:hashlib.sha256(v).hexdigest() for k,v in sorted(payload.items())})
        (stage/'mirror-state.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
        if check_only:return evidence
        for folder in ('rulekit_v4','dist/v4'):
            existing=root/folder
            if existing.exists():
                for p in list(existing.rglob('*')):
                    if p.is_file() and p.name!='README.md' and '.cache' not in p.parts and '__pycache__' not in p.parts and str(p.relative_to(root)) not in payload:p.unlink()
        generated=['repository-status.json','mirror-state.json','docs/APP_POLICY_MATRIX.md']
        for name in [*payload,*generated]:
            src=stage/name
            if src.exists():
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(src.read_bytes())
    return evidence

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path);p.add_argument('--check-only',action='store_true');args=p.parse_args()
    if args.source:
        # Local dry-run against an already checked canonical checkout, for deterministic release preparation.
        if not args.check_only:raise SyncError('--source is only allowed with --check-only')
        result=sync(args.source,ROOT,{'validation_run_url':'local-prepublication-check'},'local',True)
    else:
        evidence=source_evidence(get_json)
        with tempfile.TemporaryDirectory(prefix='surge-canonical-') as temp:
            source=Path(temp)/'source'
            subprocess.run(['git','clone','--depth','1','--branch','main',f'https://github.com/{CANONICAL}.git',str(source)],check=True,stdout=subprocess.DEVNULL)
            commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
            subprocess.run(['git','fetch','--depth','100','origin','main'],cwd=source,check=True,stdout=subprocess.DEVNULL)
            relation=subprocess.run(['git','merge-base','--is-ancestor',evidence['validated_input_commit'],commit],cwd=source)
            if relation.returncode:raise SyncError('Validated input commit is not in pinned canonical history; refusing unrelated snapshot')
            result=sync(source,ROOT,evidence,commit,args.check_only)
    print('Verified canonical mirror: '+result['canonical_commit'])
if __name__=='__main__':main()
