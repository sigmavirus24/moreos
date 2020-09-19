import nox

@nox.session
def tests(session):
    session.install('pytest')
    session.run('pytest')

@nox.session
def lint(session):
    session.install('-r', 'lint-requirements.txt')
    session.run('black', '-l', '-78', '--py36', '--safe', 'src/moreos', 'test/', 'noxfile.py')
    session.run('flake8', '--import-order-style', 'google',
            '--max-complexity', '10')
    session.run('pylint', 'src/rush',
