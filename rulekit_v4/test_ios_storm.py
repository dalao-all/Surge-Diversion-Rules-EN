import tempfile,unittest,json,shutil,importlib.util
from pathlib import Path
import build
class StormTests(unittest.TestCase):
 def test_only_existing_ad_witnesses_can_be_promoted(self):
  result,excluded=build.storm_subset(['DOMAIN-SUFFIX,ads.example.com'],[],['a.ads.example.com','mail.example.com'])
  self.assertEqual(result,['DOMAIN,a.ads.example.com']);self.assertEqual(excluded[0]['reason'],'not-in-final-ad-set')
 def test_exact_and_historical_suffix_protection_override_prematching_physically(self):
  result,excluded=build.storm_subset(['DOMAIN-SUFFIX,example.com'],['DOMAIN,safe.example.com','DOMAIN-SUFFIX,login.example.com'],['safe.example.com','a.login.example.com','ads.example.com'])
  self.assertEqual(result,['DOMAIN,ads.example.com']);self.assertEqual(len(excluded),2)
 def test_source_removal_removes_storm_entry(self):
  self.assertEqual(build.storm_subset([],[],['ads.example.com'])[0],[])
 def test_invalid_candidate_is_rejected(self):
  with self.assertRaises(build.BuildError):build.storm_subset([],[],['*'])
 def test_release_gate_rejects_a_later_protection_conflict(self):
  from validate_release import validate
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);shutil.copytree(build.ROOT/'dist/v4',root/'dist/v4');shutil.copytree(build.ROOT/'profiles',root/'profiles')
   p=root/'dist/v4/protected-history.json';items=json.loads(p.read_text());items.append('DOMAIN-SUFFIX,gdt.qq.com');p.write_text(json.dumps(items))
   with self.assertRaisesRegex(build.BuildError,'overrides protected scope'):validate(root)
if __name__=='__main__':unittest.main()
