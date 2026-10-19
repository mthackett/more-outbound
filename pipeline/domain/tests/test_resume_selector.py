import unittest
from pipeline.adapters.secondary.resume_selector import TitleBasedResumeSelector


class TestResumeFamilies(unittest.TestCase):
    def setUp(self):
        self.selector = TitleBasedResumeSelector()
        self.files = [dict(id=family, name=f'Synthetic {title} Resume') for family, title in [
            ('revenue_operations', 'Revenue Operations'), ('gtm_engineering', 'GTM Engineering'),
            ('marketing_operations', 'Marketing Operations'), ('ai_automation', 'AI Automation Engineer')]]

    def test_four_families_select_their_own_variant(self):
        for record in self.files:
            with self.subTest(family=record['id']):
                result = self.selector.select_resume(record['name'], record['id'], self.files)
                self.assertEqual(result.selected_resume.doc_id, record['id'])
                self.assertGreaterEqual(result.match_score, 0.5)

    def test_abbreviated_names(self):
        for family, name in [('revenue_operations', 'RevOps'), ('marketing_operations', 'Marketing Ops'),
                             ('ai_automation', 'Automation Engineer'), ('gtm_engineering', 'GTM Engineer')]:
            result = self.selector.select_resume('', family, [self.files[0], {'id': 'expected', 'name': name}])
            if family != 'revenue_operations':
                self.assertEqual(result.selected_resume.doc_id, 'expected')
            self.assertGreaterEqual(result.match_score, 0.5)

    def test_empty_missing_weak_and_ambiguous_matches(self):
        self.assertIsNone(self.selector.select_resume('', '', []).selected_resume)
        self.assertIsNone(self.selector.select_resume('', '', [{'id': '', 'name': 'Resume'}]).selected_resume)
        for title, family in [('', ''), ('Unrelated Role', 'unrelated'), ('Operations', '')]:
            self.assertIsNotNone(self.selector.select_resume(title, family, self.files).selected_resume)
        tied = [dict(id='first', name='Marketing Ops Resume'), dict(id='second', name='Marketing Ops Resume')]
        self.assertEqual(self.selector.select_resume('Marketing Ops', 'marketing_operations', tied).selected_resume.doc_id, 'first')
