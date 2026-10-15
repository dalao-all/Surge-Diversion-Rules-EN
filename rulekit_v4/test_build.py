"""Offline compiler regression tests; no network, production inputs or dist writes.

Run: python3 -m unittest discover -s rulekit_v4 -p 'test_*.py' -v
"""
import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

try:
    from rulekit_v4 import build
except ModuleNotFoundError:
    import build


PSL_FIXTURE = '\n'.join(['com', 'cn', 'co.uk', 'github.io', '*.ck', '!www.ck'] +
                        ['fixture' + str(i) for i in range(5000)])


class MappingFetcher:
    def __init__(self, texts):
        self.texts = texts

    def get(self, url):
        value = self.texts[url]
        if isinstance(value, Exception):
            raise value
        return value

    def source_url(self, source):
        return source['url'], None

    def commit_cache(self):
        pass


def source(ident, category='cn', role='functional', **kwargs):
    return dict(id=ident, url='https://example.test/' + ident, format='surge',
                category=category, role=role, app_ids=['app'], **kwargs)


class RuleSemanticsTests(unittest.TestCase):
    def test_exact_and_suffix_keep_distinct_meaning(self):
        parser = build.Parser(MappingFetcher({}))
        records = parser.parse(dict(id='domains', format='domainset'),
                               'example.com\n.example.net\n', 'fixture')
        self.assertEqual([r for r, _ in records],
                         ['DOMAIN,example.com', 'DOMAIN-SUFFIX,example.net'])
        self.assertFalse(build.matches(records[0][0], 'sub.example.com'))
        self.assertTrue(build.matches(records[1][0], 'sub.example.net'))
        self.assertFalse(build.matches(records[1][0], 'badexample.net'))

    def test_cidr_canonicalizes_and_matches_correct_family(self):
        self.assertEqual(build.normal_rule('IP-CIDR', '192.0.2.5/24', ['no-resolve']),
                         'IP-CIDR,192.0.2.0/24,no-resolve')
        self.assertEqual(build.normal_rule('IP-CIDR6', '2001:db8::5/32'),
                         'IP-CIDR6,2001:db8::/32')
        self.assertTrue(build.matches('IP-CIDR,192.0.2.0/24', '192.0.2.42'))
        self.assertFalse(build.matches('IP-CIDR,192.0.2.0/24', '2001:db8::1'))
        for kind, value in [('IP-CIDR', '999.1.2.3/24'), ('IP-CIDR', '2001:db8::/32'),
                            ('IP-CIDR6', '192.0.2.0/24'), ('IP-ASN', '0'),
                            ('IP-ASN', str(2 ** 32))]:
            with self.subTest(kind=kind, value=value), self.assertRaises(build.BuildError):
                build.normal_rule(kind, value)

    def test_idna_case_and_terminal_dot_normalization(self):
        self.assertEqual(build.host('BÜCHER.Example.'), 'xn--bcher-kva.example')
        for value in ['bad..example', '-bad.example', 'bad-.example', 'a' * 64 + '.com']:
            with self.subTest(value=value), self.assertRaises(build.BuildError):
                build.host(value)

    def test_psl_private_suffix_wildcard_and_exception(self):
        psl = build.PSL(PSL_FIXTURE)
        for suffix in ['com', 'co.uk', 'github.io', 'test.ck']:
            self.assertTrue(psl.public(suffix), suffix)
        for domain in ['example.com', 'tenant.github.io', 'www.ck']:
            self.assertFalse(psl.public(domain), domain)
        with self.assertRaises(build.BuildError):
            build.PSL('com\nco.uk\n')

    def test_versioned_real_psl_when_available(self):
        path = build.HERE / 'data/public_suffix_list.dat'
        if not path.exists():
            self.skipTest('Versioned PSL is still being acquired by the manifest task')
        psl = build.PSL(path.read_text())
        for suffix in ['com', 'co.uk', 'github.io', 'appspot.com']:
            self.assertTrue(psl.public(suffix), suffix)
        self.assertFalse(psl.public('tenant.github.io'))

    def test_same_size_large_replacement_rejected(self):
        old = {'DOMAIN,old' + str(i) + '.example' for i in range(100)}
        new = set(sorted(old)[30:]) | {'DOMAIN,new' + str(i) + '.example' for i in range(30)}
        self.assertEqual(len(old), len(new))
        with self.assertRaisesRegex(build.BuildError, 'Change guard'):
            build.guard(old, new, 'upstream')
        build.guard(old, old | {'DOMAIN,one.example'}, 'upstream')
        with self.assertRaisesRegex(build.BuildError, 'Empty required source'):
            build.guard(old, [], 'upstream')
        with self.assertRaisesRegex(build.BuildError, 'Change guard'):
            build.guard(['DOMAIN,sole.example'], ['DOMAIN,replacement.example'], 'small-source')

    def test_unsupported_options_and_abp_fail_closed(self):
        parser = build.Parser(MappingFetcher({}))
        for line in ['DOMAIN,example.com,no-resolve', 'DOMAIN,example.com,force-remote-dns',
                     'DOMAIN,example.com,extended-matching', 'DOMAIN,example.com,DIRECT']:
            with self.subTest(line=line), self.assertRaises(build.BuildError):
                parser.parse(dict(id='x', format='surge'), line, 'fixture')
        with self.assertRaisesRegex(build.BuildError, 'ABP'):
            parser.parse(dict(id='x', format='abp'), '||example.com^$third-party', 'fixture')
        with self.assertRaises(build.BuildError):
            parser.parse(dict(id='x', format='surge'), '||example.com^$third-party', 'fixture')

    def test_overlap_parent_and_exact_protection(self):
        self.assertTrue(build.overlaps('DOMAIN-SUFFIX,example.com', 'DOMAIN,login.example.com'))
        self.assertTrue(build.overlaps('DOMAIN-SUFFIX,example.com', 'DOMAIN-SUFFIX,api.example.com'))
        self.assertFalse(build.overlaps('DOMAIN-SUFFIX,example.com', 'DOMAIN,otherexample.com'))
        self.assertTrue(build.overlaps('IP-CIDR,192.0.2.0/24', 'IP-CIDR,192.0.2.0/25'))

    def test_plain_atomic_or_expands_equivalently_and_keeps_upstream_provenance(self):
        parser = build.Parser(MappingFetcher({}))
        line = 'OR,((IP-ASN,62041),(IP-ASN,59930),(IP-CIDR,192.0.2.5/24,no-resolve))'
        records = parser.parse(dict(id='telegram', format='surge'), line, 'fixture')
        self.assertEqual([r for r, _ in records],
                         ['IP-ASN,62041', 'IP-ASN,59930', 'IP-CIDR,192.0.2.0/24,no-resolve'])
        self.assertTrue(all(origin['raw'] == line and origin['line'] == 1 for _, origin in records))

    def test_non_equivalent_logical_rules_and_unbalanced_or_are_rejected(self):
        parser = build.Parser(MappingFetcher({}))
        lines = ['AND,((DOMAIN,one.example),(DOMAIN,two.example))',
                 'OR,((DOMAIN,one.example),(OR,((DOMAIN,two.example),(DOMAIN,three.example))))',
                 'OR,((IP-ASN,62041),(IP-ASN,59930)',
                 'OR,((IP-ASN,62041)),no-resolve', 'OR,()']
        for line in lines:
            with self.subTest(line=line), self.assertRaises(build.BuildError):
                parser.parse(dict(id='logical', format='surge'), line, 'fixture')


class IncludeTests(unittest.TestCase):
    def parse(self, text, files, **kwargs):
        self.parser = build.Parser(MappingFetcher(files))
        return [r for r, _ in self.parser.parse(
            dict(id='v2', format='v2fly', path='data/root', **kwargs), text,
            'https://example.test/sha/data/root')]

    def test_positive_and_negative_include_tags_filter_leaf_rules(self):
        files = {'https://example.test/sha/data/child':
                 'full:ad.example @ads\nplain.example\nfull:cn.example @cn\n'}
        self.assertEqual(self.parse('include:child @ads', files), ['DOMAIN,ad.example'])
        self.assertEqual(self.parse('include:child @!cn', files),
                         ['DOMAIN,ad.example', 'DOMAIN-SUFFIX,plain.example'])
        self.assertEqual(self.parse('include:child', files, exclude_tags=['ads']),
                         ['DOMAIN-SUFFIX,plain.example', 'DOMAIN,cn.example'])
        self.assertEqual(len(self.parser.children), 1)

    def test_nested_filters_are_intersected(self):
        files = {'https://example.test/sha/data/child': 'include:leaf @cn',
                 'https://example.test/sha/data/leaf':
                 'full:both.example @ads @cn\nfull:ads.example @ads\n'}
        self.assertEqual(self.parse('include:child @ads', files), ['DOMAIN,both.example'])

    def test_include_cycle_is_explicit_error(self):
        files = {'https://example.test/sha/data/child': 'include:root',
                 'https://example.test/sha/data/root': 'include:child'}
        with self.assertRaisesRegex(build.BuildError, 'cycle'):
            self.parse('include:child', files)

    def test_tagged_include_cycle_is_explicit_error(self):
        files = {'https://example.test/sha/data/child': 'include:root @ads',
                 'https://example.test/sha/data/root': 'include:child @ads'}
        with self.assertRaisesRegex(build.BuildError, 'cycle'):
            self.parse('include:child @ads', files)

    def test_regex_omission_keeps_original_location(self):
        self.assertEqual(self.parse('regexp:^api\\..*\nfull:api.example', {}), ['DOMAIN,api.example'])
        omission = self.parser.omissions[0]
        self.assertEqual((omission['source'], omission['line'], omission['raw']),
                         ('v2', 1, 'regexp:^api\\..*'))


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.here_patch = patch.object(build, 'HERE', self.root)
        self.here_patch.start()
        self.addCleanup(self.here_patch.stop)

    def test_404_retries_and_keeps_previous_cache(self):
        fetch = build.Fetcher()
        url = 'https://example.test/list'
        cached = fetch.cache / (build.sha(url) + '.txt')
        cached.write_text('DOMAIN,known.example\n')
        error = urllib.error.HTTPError(url, 404, 'Missing', {}, None)
        with patch.object(build.urllib.request, 'urlopen', side_effect=error) as request, \
             patch.object(build.time, 'sleep') as sleep:
            with self.assertRaisesRegex(build.BuildError, 'Fetch failed'):
                fetch.get(url)
        self.assertEqual(request.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])
        self.assertEqual(cached.read_text(), 'DOMAIN,known.example\n')

    def test_html_is_retried_then_valid_plaintext_is_used(self):
        responses = [io.BytesIO(b'<!doctype html><body>error</body>'),
                     io.BytesIO(b'<html>another error</html>'),
                     io.BytesIO(b'\xef\xbb\xbfDOMAIN,valid.example\n')]
        with patch.object(build.urllib.request, 'urlopen', side_effect=responses) as request, \
             patch.object(build.time, 'sleep'):
            self.assertEqual(build.Fetcher().get('https://example.test/list'), 'DOMAIN,valid.example\n')
        self.assertEqual(request.call_count, 3)

    def test_permanent_html_and_missing_offline_cache_fail(self):
        with patch.object(build.urllib.request, 'urlopen',
                          side_effect=lambda *a, **k: io.BytesIO(b'<html>error</html>')), \
             patch.object(build.time, 'sleep'):
            with self.assertRaisesRegex(build.BuildError, 'Empty/HTML'):
                build.Fetcher().get('https://example.test/list')
        with self.assertRaisesRegex(build.BuildError, 'Offline cache missing'):
            build.Fetcher(offline=True).get('https://example.test/uncached')

    def test_acquired_text_is_not_trusted_until_explicit_commit(self):
        url = 'https://example.test/list'
        fetch = build.Fetcher()
        cached = fetch.cache / (build.sha(url) + '.txt')
        cached.write_text('DOMAIN,previous.example\n')
        with patch.object(build.urllib.request, 'urlopen',
                          return_value=io.BytesIO(b'DOMAIN,new.example\n')) as request:
            self.assertEqual(fetch.get(url), 'DOMAIN,new.example\n')
            self.assertEqual(fetch.get(url), 'DOMAIN,new.example\n')
        self.assertEqual(request.call_count, 1)
        self.assertEqual(cached.read_text(), 'DOMAIN,previous.example\n')
        fetch.commit_cache()
        self.assertEqual(cached.read_text(), 'DOMAIN,new.example\n')

    def test_repository_ref_is_pinned_once_and_not_committed_early(self):
        fetch = build.Fetcher()
        rev = '1' * 40
        with patch.object(build.subprocess, 'run') as git:
            git.return_value.stdout = rev + '\trefs/heads/main\n'
            self.assertEqual(fetch.pin('owner/repo', 'main'), rev)
            self.assertEqual(fetch.pin('owner/repo', 'main'), rev)
        git.assert_called_once()
        path = fetch.cache / ('ref-' + build.sha('owner/repo@main') + '.txt')
        self.assertFalse(path.exists())
        fetch.commit_cache()
        self.assertEqual(path.read_text(), rev + '\n')


class BuildPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.here = self.root / 'rulekit_v4'
        (self.here / 'data').mkdir(parents=True)
        (self.here / 'data/public_suffix_list.dat').write_text(PSL_FIXTURE)
        self.destination = self.root / 'dist/v4'
        self.destination.mkdir(parents=True)
        (self.destination / 'release-sentinel').write_bytes(b'previous trusted release\x00')
        self.apps = dict(apps=[dict(id='app', enabled=True, category='cn', source_ids=['app-source'])], dependencies=[])
        self.sources = [source('app-source'), source('ads-source', 'ads', 'ads')]
        self.texts = {'https://example.test/app-source': 'DOMAIN,login.service.example\n',
                      'https://example.test/ads-source': 'DOMAIN,ads.unrelated.example\n'}
        self.write_inputs()
        for name, value in [('HERE', self.here), ('ROOT', self.root)]:
            patcher = patch.object(build, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write_json(self, name, value):
        (self.here / name).write_text(json.dumps(value))

    def write_inputs(self, protections=(), probes=()):
        self.write_json('apps.json', self.apps)
        self.write_json('sources.json', {'sources': self.sources})
        self.write_json('protection.json', {'rules': list(protections)})
        self.write_json('probes.json', {'probes': list(probes)})

    def snapshot(self):
        return {str(p.relative_to(self.destination)): p.read_bytes()
                for p in self.destination.rglob('*') if p.is_file()}

    def compile(self):
        with patch.object(build, 'Fetcher', return_value=MappingFetcher(self.texts)):
            return build.compile_rules(output=self.destination)

    def assert_failure_preserves_release(self, pattern):
        before = self.snapshot()
        with self.assertRaisesRegex(build.BuildError, pattern):
            self.compile()
        self.assertEqual(before, self.snapshot())
        self.assertEqual(list(self.destination.parent.glob('.v4-stage-*')), [])

    def test_fetch_parse_empty_and_psl_failure_never_publish(self):
        for payload, pattern in [(build.BuildError('404 unavailable'), '404'),
                                 ('DOMAIN,broken..example', 'Invalid (hostname|IDNA)'),
                                 ('# only comment', 'Empty required source'),
                                 ('DOMAIN-SUFFIX,github.io', 'public/private suffix'),
                                 ('DOMAIN-WILDCARD,*.example', 'Non-domain ad rule')]:
            with self.subTest(payload=str(payload)):
                self.texts['https://example.test/ads-source'] = payload
                self.assert_failure_preserves_release(pattern)

    def test_probe_regression_never_publishes(self):
        self.write_inputs(probes=[dict(domain='login.service.example', expected_category='ai')])
        self.assert_failure_preserves_release('Probe regression')

    def test_fetched_invalid_source_does_not_poison_trusted_offline_cache(self):
        cache = self.here / '.cache'
        cache.mkdir()
        previous = {}
        for ident, text in [('app-source', 'DOMAIN,old-login.example\n'),
                            ('ads-source', 'DOMAIN,old-ads.example\n')]:
            path = cache / (build.sha('https://example.test/' + ident) + '.txt')
            path.write_text(text)
            previous[path] = path.read_bytes()

        def response(request, **kwargs):
            text = ('DOMAIN,broken..example\n' if request.full_url.endswith('ads-source')
                    else 'DOMAIN,new-login.example\n')
            return io.BytesIO(text.encode())

        before = self.snapshot()
        with patch.object(build.urllib.request, 'urlopen', side_effect=response):
            with self.assertRaises(build.BuildError):
                build.compile_rules(output=self.destination)
        self.assertEqual(before, self.snapshot())
        self.assertEqual({path: path.read_bytes() for path in previous}, previous)

    def test_same_size_replacement_never_publishes(self):
        old = ['DOMAIN,old' + str(i) + '.example' for i in range(100)]
        (self.destination / 'source-rules.json').write_text(json.dumps({'ads-source': old}))
        self.texts['https://example.test/ads-source'] = '\n'.join(
            old[30:] + ['DOMAIN,new' + str(i) + '.example' for i in range(30)])
        self.assert_failure_preserves_release('Change guard')

    def test_success_publishes_all_outputs_and_is_deterministic(self):
        self.write_inputs(probes=[dict(domain='login.service.example', expected_category='cn')])
        report = self.compile()
        self.assertTrue(report['probes'][0]['passed'])
        self.assertFalse((self.destination / 'release-sentinel').exists())
        first = self.snapshot()
        self.assertEqual(len([n for n in first if n.endswith('.list')]), 24)
        self.assertIn('provenance.ndjson.gz', first)
        provenance = [json.loads(line) for line in gzip.decompress(first['provenance.ndjson.gz']).decode().splitlines()]
        record = next(r for r in provenance if r['rule'] == 'DOMAIN,login.service.example')
        self.assertTrue(record['published'])
        self.assertEqual(record['origins'][0]['source'], 'app-source')
        self.assertIn('SHA256SUMS', first)
        self.compile()
        self.assertEqual(first, self.snapshot())

    def test_ad_ancestor_removal_and_historical_protection_survive_app_disable(self):
        self.texts['https://example.test/ads-source'] += 'DOMAIN-SUFFIX,service.example\n'
        protections = [dict(type='DOMAIN', value='login.service.example', category='cn', app_ids=['app'])]
        self.write_inputs(protections=protections)
        first = self.compile()
        self.assertEqual(first['removed_ads'][0]['rule'], 'DOMAIN-SUFFIX,service.example')
        self.apps['apps'][0]['enabled'] = False
        self.write_inputs(protections=protections)
        second = self.compile()
        self.assertEqual(second['removed_ads'][0]['rule'], 'DOMAIN-SUFFIX,service.example')
        self.assertEqual(second['counts']['protect-cn'], 0)
        self.assertEqual(second['counts']['cn'], 0)
        history = json.loads((self.destination / 'protected-history.json').read_text())
        self.assertIn('DOMAIN,login.service.example', history)
        self.assertNotIn('app-source', json.loads((self.destination / 'source-rules.json').read_text()))
        with gzip.open(self.destination / 'provenance.ndjson.gz', 'rt') as handle:
            provenance = [json.loads(line) for line in handle]
        ancestor = next(r for r in provenance if r['rule'] == 'DOMAIN-SUFFIX,service.example')
        self.assertFalse(ancestor['published'])

    def test_wildcard_protection_requires_review_instead_of_incomplete_overlap_proof(self):
        self.texts['https://example.test/ads-source'] += 'DOMAIN-SUFFIX,example.com\n'
        self.write_inputs(protections=[dict(type='DOMAIN-WILDCARD', value='api.*.com', category='cn')])
        self.assert_failure_preserves_release('(?i)protection')

    def test_source_with_explicit_redistribution_denial_is_not_published(self):
        self.sources[0]['license'] = {'redistribution_allowed': False}
        self.write_inputs()
        self.assert_failure_preserves_release('(?i)(license|redistribution)')

    def test_disabled_app_source_is_not_fetched_or_published(self):
        self.apps['apps'].append(dict(id='disabled-app', enabled=False, category='cn', source_ids=['disabled-source']))
        self.sources.append(dict(source('disabled-source'), app_ids=['disabled-app']))
        # No response entry: an accidental fetch fails even before checking the output.
        self.write_inputs()
        self.compile()
        rules = json.loads((self.destination / 'source-rules.json').read_text())
        self.assertNotIn('disabled-source', rules)

    def test_disabled_app_shared_dependencies_and_always_enabled_infrastructure(self):
        apps = {'apps': [dict(id='on', category='cn', source_ids=['on-source'], dependency_ids=['shared']),
                         dict(id='off', enabled=False, category='cn', source_ids=['off-source'], dependency_ids=['private'])],
                'dependencies': [dict(id='shared', source_ids=['shared-source']),
                                 dict(id='private', source_ids=['private-source']),
                                 dict(id='always', always_enabled=True, source_ids=['always-source'])]}
        sources = [source(x) for x in ['on-source', 'off-source', 'shared-source', 'private-source', 'always-source']]
        sources += [source('ads', role='ads'), source('network', role='network'),
                    source('disabled', role='security', enabled=False)]
        actual, active = build.active_sources({'sources': sources}, apps)
        self.assertEqual(active, {'on'})
        self.assertEqual({s['id'] for s in actual}, {'on-source', 'shared-source', 'always-source', 'ads', 'network'})

    def test_missing_source_dependency_and_invalid_app_category_never_publish(self):
        for field, value, pattern in [('source_ids', ['nonexistent'], 'referenced source'),
                                      ('dependency_ids', ['nonexistent'], 'Missing dependency'),
                                      ('category', 'not-a-category', 'Invalid app category')]:
            with self.subTest(field=field):
                app = self.apps['apps'][0]
                original = dict(app)
                app[field] = value
                self.write_inputs()
                self.assert_failure_preserves_release(pattern)
                app.clear()
                app.update(original)

    def test_parent_suffix_shadowing_exact_host_is_reported_with_actual_winner(self):
        self.sources.append(source('earlier', category='ai'))
        self.texts['https://example.test/earlier'] = 'DOMAIN-SUFFIX,service.example\n'
        self.write_inputs()
        report = self.compile()
        witness = next(item for item in report['cross_category_shadow_witnesses']
                       if item['witness'] == 'login.service.example')
        self.assertEqual(witness['winner_category'], 'ai')
        self.assertEqual(witness['winner_rule'], 'DOMAIN-SUFFIX,service.example')
        self.assertEqual(witness['shadowed_category'], 'cn')
        self.assertEqual(witness['shadowed_rule'], 'DOMAIN,login.service.example')

    def test_manifest_local_native_source_is_not_fetched(self):
        (self.here / 'custom').mkdir()
        (self.here / 'custom/reviewed.list').write_text('DOMAIN,local.example\n')
        self.sources[0].update(url=None, repo=None, path='custom/reviewed.list')
        self.write_inputs()
        self.compile()
        self.assertIn('DOMAIN,local.example', (self.destination / 'cn.list').read_text())
        lock = json.loads((self.destination / 'sources.lock.json').read_text())
        self.assertEqual(lock['sources']['app-source']['url'], 'local:custom/reviewed.list')

    def test_local_source_path_cannot_escape_rulekit(self):
        (self.root / 'outside.list').write_text('DOMAIN,outside.example\n')
        self.sources[0].update(url=None, repo=None, path='../outside.list')
        self.write_inputs()
        self.assert_failure_preserves_release('Local source escapes')

    def test_cache_write_failure_cannot_report_failure_after_changing_release(self):
        before = self.snapshot()
        fake = MappingFetcher(self.texts)
        with patch.object(fake, 'commit_cache', side_effect=OSError('cache disk write failed')), \
             patch.object(build, 'Fetcher', return_value=fake):
            try:
                report = build.compile_rules(output=self.destination)
            except OSError:
                self.assertEqual(before, self.snapshot(), 'Failed build replaced trusted dist')
            else:
                self.assertEqual(report['counts']['ads'], 1)
                self.assertNotEqual(before, self.snapshot())

    def test_staging_rename_failure_restores_previous_release(self):
        before = self.snapshot()
        real_rename = Path.rename

        def failing_rename(path, target):
            if path.name.startswith('.v4-stage-'):
                raise OSError('simulated publication rename failure')
            return real_rename(path, target)

        with patch.object(Path, 'rename', failing_rename):
            with self.assertRaisesRegex(OSError, 'simulated publication'):
                self.compile()
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.destination.with_name('v4.previous').exists())
        self.assertEqual(list(self.destination.parent.glob('.v4-stage-*')), [])

    def test_interrupted_swap_recovers_previous_release_and_change_baseline(self):
        (self.destination / 'source-rules.json').write_text(json.dumps(
            {'app-source': ['DOMAIN,previous-login.example']}))
        before = self.snapshot()
        backup = self.destination.with_name('v4.previous')
        self.destination.rename(backup)
        self.assertFalse(self.destination.exists())
        # Recovery must restore the original baseline instead of treating this as first build.
        with self.assertRaisesRegex(build.BuildError, 'Change guard'):
            self.compile()
        self.assertEqual(before, self.snapshot())
        self.assertFalse(backup.exists())


if __name__ == '__main__':
    unittest.main()
