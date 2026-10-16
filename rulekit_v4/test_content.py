import unittest
import build
from content_checks import check_content, DomainIndex

class ContentTests(unittest.TestCase):
    def test_mapped_ipv6_canonicalization_is_stable(self):
        expected='IP-CIDR6,::ffff:71f8:acf5/128,no-resolve'
        for literal in ('::ffff:113.248.172.245/128','::ffff:71f8:acf5/128'):
            self.assertEqual(build.normal_rule('IP-CIDR6',literal,['no-resolve']),expected)
        build.guard([expected],[build.normal_rule('IP-CIDR6','::ffff:113.248.172.245/128',['no-resolve'])],'same-address')

    def test_suffix_boundary_not_substring(self):
        index=DomainIndex(['DOMAIN-SUFFIX,openai.com','DOMAIN,login.example.com'])
        self.assertTrue(index.matches('api.openai.com'))
        for name in ('notopenai.com','openai.com.example.net','sub.login.example.com'):
            self.assertFalse(index.matches(name))

    def test_business_first_cannot_hide_route_regression(self):
        tables={'ai':[],'cn':['DOMAIN-SUFFIX,example.com'],'ads':['DOMAIN,api.example.com'],'protect-ai':[],'protect-cn':[]}
        probes=[{'domain':'api.example.com','expected_category':'cn'}]
        with self.assertRaisesRegex(ValueError,'routing regression'):
            check_content(tables,('ai','cn'),probes,{})
        tables['protect-cn']=['DOMAIN,api.example.com']
        self.assertEqual(check_content(tables,('ai','cn'),probes,{})['business_probes'],1)

    def test_ads_shadow_is_disclosed_not_claimed_as_block(self):
        tables={'cn':['DOMAIN-SUFFIX,example.com'],'ads':['DOMAIN,ad.example.com'],'protect-cn':[]}
        result=check_content(tables,('cn',),[{'domain':'ad.example.com','expected_category':'ads'}],{})
        self.assertEqual(result['business_first_ad_bypasses'],[{'domain':'ad.example.com','actual':'cn'}])

    def test_fake_ip_and_negative_scope_block_publication(self):
        for rule in ('IP-CIDR,198.18.2.3/32','IP-CIDR6,::ffff:c612:203/128'):
            tables={'cn':[rule],'protect-cn':[],'ads':[]}
            with self.assertRaisesRegex(ValueError,'Benchmark'):
                check_content(tables,('cn',),[],{'forbid_benchmark_ips':True})
        tables={'ai':['DOMAIN-KEYWORD,openai'],'protect-ai':[],'ads':[]}
        with self.assertRaisesRegex(ValueError,'Overbroad'):
            check_content(tables,('ai',),[],{'negative_probes':[{'domain':'notopenai.example','forbidden_categories':['ai']}]})
