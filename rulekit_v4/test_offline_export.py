import tempfile,unittest
from pathlib import Path
from export_offline_profile import export
class OfflineExportTests(unittest.TestCase):
 def test_preserves_quoted_groups_prematching_and_suffix_semantics(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'ads-storm.list').write_text('DOMAIN,storm.example.com\n');(root/'ads.domainset').write_text('# comment\n.ads.example.com\nexact.example.com\n')
   groups='[Proxy Group]\nWise = select, "Taiwan 07", "Taiwan 08"\n'
   s=groups+'[Rule]\nRULE-SET,https://example.com/ads-storm.list,REJECT-DROP,pre-matching,update-interval=86400\nDOMAIN-SET,https://example.com/ads.domainset,REJECT\n'
   result=export(s,root)
   self.assertIn(groups,result);self.assertIn('REJECT-DROP,pre-matching',result);self.assertNotIn('update-interval=',result);self.assertNotIn('https://example.com',result)
   self.assertIn('DOMAIN-SUFFIX,ads.example.com',result);self.assertIn('DOMAIN,exact.example.com',result)
 def test_missing_resource_never_yields_partial_result(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(FileNotFoundError):export('[Rule]\nRULE-SET,https://example.com/missing.list,REJECT\n',Path(d))
if __name__=='__main__':unittest.main()
