import sys

import nox


nox.options.sessions = ["test-3.6", "test-3.7", "test-3.8", "lint", "docs"]
nox.options.reuse_existing_virtualenvs = True


@nox.session(python=["3.6", "3.7", "3.8"])
def test(session):
    session.install(".", "pytest")
    session.run("pytest")


@nox.session
def lint(session):
    session.install(".")
    session.install("-r", "lint-requirements.txt")
    session.run("black", "src/moreos", "test/", "noxfile.py")
    session.run("flake8", "src/moreos", "test")
    session.run("pylint", "src/moreos", "test")
    session.run("mypy", "src/moreos")
    session.run("bandit", "-r", "src/moreos")
    session.run("python", "setup.py", "sdist", "bdist_wheel")
    session.run("twine", "check", "dist/*")


@nox.session
def venv(session):
    session.install(".", "bpython")
    if not session.posargs:
        session.run("bpython")
        return
    session.run(*session.posargs)


@nox.session
def sphinx(session):
    session.install(".")
    session.install("-r", "doc/source/requirements.txt")
    if not session.posargs:
        session.run("sphinx-quickstart", "--help")
        return
    session.run(*session.posargs)


@nox.session
def docs(session):
    session.install(".")
    session.install("-r", "doc/source/requirements.txt")
    session.run("doc8", "doc/source/")
    session.run(
        "sphinx-build",
        "-E",
        "-W",
        "-c",
        "doc/source",
        "-b",
        "html",
        "doc/source",
        "doc/build/html",
    )
