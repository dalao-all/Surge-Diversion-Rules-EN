import ipaddress,unittest
import build
class FeedbackTests(unittest.TestCase):
 def test_exact_intended_ip_range_cannot_match_a_prefixed_address(self):
  source={'id':'wechat','category':'cn','numeric_ip_keywords_to_cidr':True}
  cat,rule,note=build.output_rule(source,'DOMAIN-KEYWORD,14.22.0.')
  self.assertEqual(rule,'IP-CIDR,14.22.0.0/24,no-resolve');self.assertEqual(cat,'cn')
  self.assertTrue(build.matches(rule,'14.22.0.4'));self.assertFalse(build.matches(rule,'114.22.0.4'));self.assertIn('not a semantics-equivalent',note['reason'])
 def test_new_numeric_shape_fails_closed(self):
  with self.assertRaises(build.BuildError):build.output_rule({'numeric_ip_keywords_to_cidr':True,'category':'cn'},'DOMAIN-KEYWORD,14.22.')
 def test_bstar_is_a_specific_output_reclassification(self):
  rule='DOMAIN,upos-bstar-mirrorakam.akamaized.net'
  source={'category':'cn','output_rule_overrides':{rule:{'category':'stream','reason':'international video'}}}
  self.assertEqual(build.output_rule(source,rule)[:2],('stream',rule))
  self.assertEqual(build.output_rule(source,'DOMAIN,api.bilibili.com')[:2],('cn','DOMAIN,api.bilibili.com'))
 def test_statsig_anthropic_is_not_a_child_of_statsig_com(self):
  self.assertFalse(build.matches('DOMAIN-SUFFIX,statsig.com','statsig.anthropic.com'))
  self.assertTrue(build.matches('DOMAIN,statsig.anthropic.com','statsig.anthropic.com'))
 def test_financial_categories_are_before_general_fallback(self):
  for financial in ('paypal','wise','binance','okx'):self.assertLess(build.CATEGORIES.index(financial),build.CATEGORIES.index('global'))
if __name__=='__main__':unittest.main()
