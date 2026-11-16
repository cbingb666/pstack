import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

SOURCE = 'cbingb666/pstack'
BRANCH = 'custom'
ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def pushed_commit(repo):
    if git(repo, 'status', '--porcelain'):
        raise ValueError('工作区还有未提交或未跟踪内容；先审查并提交。')
    if git(repo, 'branch', '--show-current') != BRANCH:
        raise ValueError('必须在 custom 分支执行重装。')
    commit = git(repo, 'rev-parse', 'HEAD')
    remote = git(repo, 'ls-remote', 'origin', f'refs/heads/{BRANCH}').split()
    if len(remote) != 2 or remote[0] != commit:
        raise ValueError('本地 HEAD 与远端 origin/custom 不一致；先推送或处理远端差异。')
    return commit


def installed_matches_tree(repo, tree, installed):
    paths = [path for path in git(repo, 'ls-tree', '-rz', '--name-only', tree).split('\0') if path]
    actual = {str(path.relative_to(installed)) for path in installed.rglob('*') if path.is_file()}
    if not paths or actual != set(paths):
        raise ValueError(f'{installed.name} 的安装文件清单与 Git 基线不一致。')
    for path in paths:
        expected = subprocess.check_output(['git', '-C', str(repo), 'show', f'{tree}:{path}'])
        if expected != (installed / path).read_bytes():
            raise ValueError(f'{installed.name} 的安装内容与 Git 基线不一致：{path}')
    return len(paths)


def check_installed_edits(repo, names, home):
    lock_path = home / '.agents/.skill-lock.json'
    lock = json.loads(lock_path.read_text()) if lock_path.exists() else {'skills': {}}
    for name in names:
        installed = home / '.agents/skills' / name
        if not installed.exists():
            continue
        record = lock['skills'].get(name, {})
        if record.get('source') != SOURCE or not record.get('skillFolderHash'):
            raise ValueError(f'{name} 已存在，但没有可信的本 fork 安装基线；停止覆盖。')
        installed_matches_tree(repo, record['skillFolderHash'], installed)


def verify_installation(repo, names, home):
    lock = json.loads((home / '.agents/.skill-lock.json').read_text())
    verified = 0
    for name in names:
        prefix = f'skills/{name}/'
        tree = git(repo, 'rev-parse', f'HEAD:skills/{name}')
        installed = home / '.agents/skills' / name
        verified += installed_matches_tree(repo, tree, installed)
        record = lock['skills'].get(name, {})
        if record.get('source') != SOURCE or record.get('skillPath') != prefix + 'SKILL.md' or record.get('skillFolderHash') != tree:
            raise ValueError(f'{name} 的安装来源记录不正确。')
    return verified


def main():
    parser = argparse.ArgumentParser(description='从已提交并已推送的 pstack fork 重装技能。')
    parser.add_argument('skills', nargs='*')
    parser.add_argument('--check', action='store_true', help='只检查安装前置条件，不执行安装。')
    args = parser.parse_args()
    origin = git(ROOT, 'config', '--get', 'remote.origin.url')
    allowed = {f'https://github.com/{SOURCE}.git', f'https://github.com/{SOURCE}', f'git@github.com:{SOURCE}.git'}
    if origin not in allowed:
        raise ValueError('origin 必须指向 cbingb666/pstack。')
    commit = pushed_commit(ROOT)
    available = {path.name for path in (ROOT / 'skills').iterdir() if (path / 'SKILL.md').is_file()}
    names = sorted(set(args.skills) if args.skills else available)
    if not names or set(names) - available:
        raise ValueError('只接受本仓库已有的顶层技能名。')
    home = Path.home()
    check_installed_edits(ROOT, names, home)
    if args.check:
        print(json.dumps({'status': 'READY', 'commit': commit, 'skills': names}, ensure_ascii=False))
        return
    logs = home / '.cache/pstack'
    logs.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    log = logs / f'reinstall-{stamp}.log'
    source = f'https://github.com/{SOURCE}/tree/{commit}'
    command = ['npx', '--yes', 'skills', 'add', source, '--global', '--agent', 'codex', '--skill', *names, '--yes', '--json']
    with log.open('w') as output:
        result = subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
    if result.returncode:
        raise ValueError(f'npx skills 安装失败，日志：{log}')
    if git(ROOT, 'rev-parse', 'HEAD') != commit or git(ROOT, 'status', '--porcelain'):
        raise ValueError('安装过程中源仓库发生变化；停止验收。')
    files = verify_installation(ROOT, names, home)
    report = {'status': 'PASS', 'source': SOURCE, 'commit': commit, 'skills': names, 'verifiedFiles': files, 'installerLog': str(log)}
    log.with_suffix('.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
