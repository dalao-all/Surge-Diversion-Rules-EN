import datetime as dt,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('mirror',Path(__file__).with_name('sync_from_canonical.py'));mirror=importlib.util.module_from_spec(spec);spec.loader.exec_module(mirror)
NOW=dt.datetime(2026,10,15,0,0,tzinfo=dt.timezone.utc)
def run(status='success',age=1,event='push',branch='main'):
 return {'id':12,'head_branch':branch,'event':event,'status':'completed','conclusion':status,'updated_at':(NOW-dt.timedelta(hours=age)).isoformat(),'head_sha':'a'*40,'html_url':'https://github.com/example/run'}
class MirrorTests(unittest.TestCase):
 def test_recent_default_branch_success_is_accepted(self):
  d=mirror.source_evidence(lambda url:{'workflow_runs':[run()]},NOW);self.assertEqual(d['validation_run_id'],12)
 def test_failed_canonical_is_not_hidden_by_old_success(self):
  with self.assertRaisesRegex(mirror.SyncError,'not successful'):mirror.source_evidence(lambda url:{'workflow_runs':[run('failure'),run()]},NOW)
 def test_stale_success_blocks(self):
  with self.assertRaisesRegex(mirror.SyncError,'36 hours'):mirror.source_evidence(lambda url:{'workflow_runs':[run(age=37)]},NOW)
 def test_pr_and_other_branch_success_do_not_count(self):
  with self.assertRaises(mirror.SyncError):mirror.source_evidence(lambda url:{'workflow_runs':[run(event='pull_request'),run(branch='feature')]},NOW)
 def test_api_failure_propagates(self):
  def fail(url):raise OSError('network unavailable')
  with self.assertRaises(OSError):mirror.source_evidence(fail,NOW)
 def test_localized_profile_preserves_every_active_line(self):
  cn='#!name=old\n# 注释\n[General]\nipv6 = false\n[Proxy]\n\n[Proxy Group]\n策略 = select,DIRECT\n'
  en=mirror.english_profile(cn)
  active=lambda t:[x for x in t.splitlines() if x.strip() and not x.lstrip().startswith('#')]
  self.assertEqual(active(cn),active(en));self.assertNotIn('注释',en);self.assertIn('surge-V3.0.0',en)
 def test_bad_snapshot_never_mutates_mirror(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'mirror';src=Path(d)/'canonical';root.mkdir();src.mkdir();(root/'keep').write_text('old')
   with patch.object(mirror,'verify_snapshot',side_effect=mirror.SyncError('checksum failure')):
    with self.assertRaises(mirror.SyncError):mirror.sync(src,root,{},'a'*40)
   self.assertEqual((root/'keep').read_text(),'old');self.assertEqual(len(list(root.iterdir())),1)
 def test_secret_and_workflow_paths_never_enter_payload(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   for folder in ('rulekit_v4','dist/v4','profiles','scripts','.github/workflows'):(root/folder).mkdir(parents=True)
   (root/'dist/v4/SHA256SUMS').write_text('')
   (root/'rulekit_v4/README.md').write_text('Chinese not mirrored')
   (root/'profiles/surge-V3.0.0.conf').write_text('[Proxy]\n\n[Rule]\n')
   for name in ('generate_repository_status.py','sync_from_canonical.py','audit_repository.py','test_sync.py'):(root/'scripts'/name).write_text('# safe')
   (root/'.github/workflows/private.yml').write_text('should not copy')
   payload=mirror.manifest(root)
   self.assertNotIn('rulekit_v4/README.md',payload);self.assertFalse(any(x.startswith('.github') for x in payload))
 def test_canonical_symlink_cannot_escape_the_pinned_repository(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'repo';root.mkdir();outside=Path(d)/'outside';outside.write_text('private')
   for folder in ('rulekit_v4','dist/v4','profiles','scripts'):(root/folder).mkdir(parents=True,exist_ok=True)
   (root/'dist/v4/SHA256SUMS').write_text('')
   (root/'profiles/surge-V3.0.0.conf').symlink_to(outside)
   with self.assertRaisesRegex(mirror.SyncError,'symlink'):mirror.manifest(root)
if __name__=='__main__':unittest.main()
