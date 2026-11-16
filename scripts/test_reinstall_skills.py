import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('reinstall_skills', Path(__file__).with_name('reinstall_skills.py'))
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


class ReinstallWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.repo = root / 'repo'
        self.repo.mkdir()
        self.home = root / 'home'
        self.run_git('init', '-b', 'custom')
        self.run_git('config', 'user.name', 'Workflow Test')
        self.run_git('config', 'user.email', 'workflow@example.invalid')
        self.source = self.repo / 'skills/example/SKILL.md'
        self.source.parent.mkdir(parents=True)
        self.source.write_text('original\n')
        self.commit('baseline')
        remote = root / 'remote.git'
        subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
        self.run_git('remote', 'add', 'origin', str(remote))
        self.run_git('push', '-u', 'origin', 'custom')
        self.installed = self.home / '.agents/skills/example/SKILL.md'
        self.installed.parent.mkdir(parents=True)
        self.installed.write_bytes(self.source.read_bytes())
        self.record_installation()

    def run_git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True, stderr=subprocess.DEVNULL).strip()

    def commit(self, message):
        self.run_git('add', 'skills')
        self.run_git('commit', '-m', message)

    def record_installation(self):
        record = {'source': workflow.SOURCE, 'skillPath': 'skills/example/SKILL.md', 'skillFolderHash': self.run_git('rev-parse', 'HEAD:skills/example')}
        (self.home / '.agents/.skill-lock.json').write_text(json.dumps({'skills': {'example': record}}))

    def test_pushed_clean_commit_is_accepted(self):
        self.assertEqual(workflow.pushed_commit(self.repo), self.run_git('rev-parse', 'HEAD'))

    def test_uncommitted_edit_is_rejected(self):
        self.source.write_text('uncommitted\n')
        with self.assertRaisesRegex(ValueError, '未提交'):
            workflow.pushed_commit(self.repo)

    def test_unpushed_commit_is_rejected(self):
        self.source.write_text('unpushed\n')
        self.commit('not pushed')
        with self.assertRaisesRegex(ValueError, '先推送'):
            workflow.pushed_commit(self.repo)

    def test_wrong_branch_is_rejected(self):
        self.run_git('switch', '-c', 'other')
        with self.assertRaisesRegex(ValueError, 'custom 分支'):
            workflow.pushed_commit(self.repo)

    def test_installed_edit_is_not_overwritten(self):
        self.installed.write_text('local edit\n')
        with self.assertRaisesRegex(ValueError, '安装内容'):
            workflow.check_installed_edits(self.repo, ['example'], self.home)

    def test_committed_source_update_allows_clean_older_installation(self):
        self.source.write_text('new version\n')
        self.commit('new version')
        self.run_git('push', 'origin', 'custom')
        workflow.check_installed_edits(self.repo, ['example'], self.home)
        with self.assertRaisesRegex(ValueError, '安装内容'):
            workflow.verify_installation(self.repo, ['example'], self.home)
        self.installed.write_bytes(self.source.read_bytes())
        with self.assertRaisesRegex(ValueError, '来源记录'):
            workflow.verify_installation(self.repo, ['example'], self.home)
        self.record_installation()
        self.assertEqual(workflow.verify_installation(self.repo, ['example'], self.home), 1)


if __name__ == '__main__':
    unittest.main()
