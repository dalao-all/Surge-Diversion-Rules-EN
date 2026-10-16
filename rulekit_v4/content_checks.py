"""Content checks for both published ordering and the user's business-first profile.

These simulate domain classification only, not DNS, GeoIP, transport or iOS apps.
No ABP conversion or majority-vote admission of candidate domains.
"""
import fnmatch
import ipaddress


class DomainIndex:
    def __init__(self, rules):
        self.exact, self.suffix, self.patterns = set(), set(), []
        for rule in rules:
            kind, value = rule.split(',')[:2]
            if kind == 'DOMAIN': self.exact.add(value)
            elif kind == 'DOMAIN-SUFFIX': self.suffix.add(value)
            elif kind in ('DOMAIN-KEYWORD','DOMAIN-WILDCARD'): self.patterns.append((kind,value))

    def matches(self, name):
        name = name.lower().rstrip('.')
        if name in self.exact: return True
        parts = name.split('.')
        if any('.'.join(parts[i:]) in self.suffix for i in range(len(parts))): return True
        return any((value in name if kind=='DOMAIN-KEYWORD' else fnmatch.fnmatchcase(name,value)) for kind,value in self.patterns)


def check_content(tables, categories, probes, review):
    if review.get('forbid_benchmark_ips'):
        benchmark = ipaddress.ip_network('198.18.0.0/15')
        mapped_benchmark = ipaddress.ip_network('::ffff:c612:0/111')
        for category,rows in tables.items():
            for row in rows:
                kind,value = row.split(',')[:2]
                if kind not in ('IP-CIDR','IP-CIDR6'): continue
                net = ipaddress.ip_network(value)
                reserved = benchmark if net.version==4 else mapped_benchmark
                if net.overlaps(reserved):
                    raise ValueError('Benchmark/fake-IP cannot identify app: '+category+' '+row)
    indexes = {key:DomainIndex(rows) for key,rows in tables.items()}
    protect = ['protect-'+cat for cat in categories]
    orders = {'legacy-ad-first':protect+['ads']+list(categories),
              'v330-business-first':protect+list(categories)+['ads']}
    def route(domain, order):
        key = next((key for key in order if indexes[key].matches(domain)),None)
        return key.removeprefix('protect-') if key else None
    # Guard actual service-routing outcomes under BOTH supported orderings.
    outcomes=[]
    for p in probes:
        if p['expected_category']=='ads': continue
        if ':' in p['domain'] or p['domain'].replace('.','').isdigit(): continue
        actual={mode:route(p['domain'],order) for mode,order in orders.items()}
        if any(cat != p['expected_category'] for cat in actual.values()):
            raise ValueError('Content routing regression: '+p['domain']+' '+str(actual))
        outcomes.append({'domain':p['domain'],'expected':p['expected_category'],'actual':actual})
    negatives=[]
    for test in review.get('negative_probes',[]):
        actual={mode:route(test['domain'],order) for mode,order in orders.items()}
        if any(cat in test['forbidden_categories'] for cat in actual.values()):
            raise ValueError('Overbroad routing scope: '+test['domain']+' '+str(actual))
        negatives.append(dict(test,actual=actual))
    for test in review.get('forbidden_rules',[]):
        if test['rule'] in tables[test['category']]:
            raise ValueError('Reviewed unsafe rule reintroduced: '+str(test))
    ad_bypasses=[]
    for p in probes:
        if p['expected_category']!='ads':continue
        actual=route(p['domain'],orders['v330-business-first'])
        if actual!='ads':ad_bypasses.append({'domain':p['domain'],'actual':actual})
    return {'scope':'static external-domain classification only',
            'business_probes':len(outcomes),'routing_orders':list(orders),
            'business_results':outcomes,'negative_results':negatives,
            'business_first_ad_bypasses':ad_bypasses,
            'limits':['No DNS/GeoIP/IP/inline protocol emulation.','Ad bypasses are disclosed compatibility tradeoffs, not successful blocks.','No device performance or login verification.']}
