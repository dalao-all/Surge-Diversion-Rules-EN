#!/usr/bin/env python3
"""Build the human-facing site summary directly from current audited manifests."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POLICIES={'paypal':'💳 PayPal 美国','wise':'💸 Wise 台湾','binance':'🪙 Binance 台湾','okx':'🪙 OKX 台湾','ai':'🤖 AI住宅','tiktok':'🎵 TikTok住宅','stream':'🎬 流媒体','google':'🔐 Google账户','uk':'🇬🇧 英国专属','global':'🌍 国际网络','cn':'DIRECT'}
def generate(root=ROOT):
    apps=json.loads((root/'rulekit_v4/apps.json').read_text());sources=json.loads((root/'rulekit_v4/sources.json').read_text());report=json.loads((root/'dist/v4/report.json').read_text())
    coverage={}
    for a in apps['apps']:
        k=a['coverage']['status'];coverage[k]=coverage.get(k,0)+1
    result={'release':'surge-V3.0.0','engine':'v4','ipv6':False,'proxy_empty':True,'app_count':len(apps['apps']),'source_count':len(sources['sources']),'dependency_count':len(apps.get('dependencies',[])),'counts':report['counts'],'probe_count':len(report['probes']),'coverage_counts':coverage,'canonical_repository':'dalao-all/Surge-Diversion-Rules','categories':[{'id':k,'policy':v,'rule_count':report['counts'][k],'protected_rule_count':report['counts']['protect-'+k]} for k,v in POLICIES.items()],'apps':[{'id':a['id'],'name':a['name'],'category':a['category'],'coverage':a['coverage']['status'],'source_count':len(a['source_ids']),'enabled':a.get('enabled',True)} for a in apps['apps']]}
    locale=json.loads((root/'repository-locale.json').read_text())['language'] if (root/'repository-locale.json').exists() else 'zh-CN'
    matrix=root/'docs/APP_POLICY_MATRIX.md'
    if matrix.exists():
        import re
        body=matrix.read_text()
        header='| ID | App | Category | Coverage | Direct sources | Dependencies | Combined sources |\n| --- | --- | --- | --- | ---: | ---: | ---: |' if locale=='en' else '| 稳定 ID | 应用名称 | 类别 | 覆盖状态 | 直接源数 | 依赖数 | 合并源数 |\n| --- | --- | --- | --- | ---: | ---: | ---: |'
        zh={'independent-candidate':'独立来源候选','group-shared':'集团共享候选','apple-shared':'Apple共享候选','official-document-only':'仅官方文档候选','official-service-candidate':'官方服务候选','original-config-candidate':'原配置候选','unresolved':'未解决','local-only':'本地功能为主','browser-target-based':'按目标站分流','mail-provider-dependent':'依赖邮箱服务商','special-case':'特殊处理'}
        dependencies={d['id']:d.get('source_ids',[]) for d in apps.get('dependencies',[])}
        rows=[]
        for a in apps['apps']:
            combined=set(a['source_ids'])
            for dep in a.get('dependency_ids',[]): combined.update(dependencies.get(dep,[]))
            coverage=a['coverage']['status'];coverage=zh.get(coverage,coverage) if locale!='en' else coverage
            rows.append('| '+a['id']+' | '+a['name'].replace('|','\\|')+' | '+a['category']+' | '+coverage+' | '+str(len(a['source_ids']))+' | '+str(len(a.get('dependency_ids',[])))+' | '+str(len(combined))+' |')
        body=re.sub(r'(?s)(<!-- APP_MATRIX_START -->).*?(<!-- APP_MATRIX_END -->)',lambda m:m[1]+'\n\n'+header+'\n'+'\n'.join(rows)+'\n\n'+m[2],body)
        matrix.write_text(body)
    result['semantic_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    (root/'repository-status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
if __name__=='__main__':
    d=generate();print(f"Site status generated: {d['app_count']} apps, {d['source_count']} sources, {d['probe_count']} static probes")
