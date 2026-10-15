#!/usr/bin/env python3
"""Export a static emergency profile without external rule-resource downloads.

Node definitions remain blank. This is not an automatically updating alternative.
"""
import csv,io,re,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def export(profile,dist):
    lines=[];sections=[]
    for raw in profile.splitlines():
        if raw.startswith(('RULE-SET,https://','DOMAIN-SET,https://')):
            fields=next(csv.reader([raw],skipinitialspace=True));kind,url,policy,*options=fields
            name=url.rsplit('/',1)[-1]
            if not re.fullmatch('[a-z-]+\\.(?:list|domainset)',name):raise ValueError('Unsafe resource name')
            content=(dist/name).read_text();local='Emergency-'+name.replace('.','-')
            options=[o for o in options if not o.startswith('update-interval=')]
            stream=io.StringIO();csv.writer(stream,lineterminator='').writerow(['RULE-SET',local,policy,*options]);lines.append(stream.getvalue())
            if kind=='DOMAIN-SET':
                content='\n'.join(('DOMAIN-SUFFIX,'+r[1:] if r.startswith('.') else 'DOMAIN,'+r) for r in content.splitlines() if r.strip() and not r.startswith(('#','//')))
            sections.append('[Ruleset '+local+']\n'+content.strip()+'\n')
        else:lines.append(raw)
    profile_name='#!name=surge-V3.0.0-Offline-Emergency'
    lines=[profile_name if l.startswith('#!name=') else l for l in lines]
    return '# Static emergency snapshot. No automatic rule updates. Add your own nodes before use.\n'+'\n'.join(lines)+'\n\n'+'\n'.join(sections)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    args.output.write_text(export((ROOT/'profiles/surge-V3.0.0.conf').read_text(),ROOT/'dist/v4'))
    args.output.chmod(0o600)
    print('Emergency profile exported with local inline rule sets.')
