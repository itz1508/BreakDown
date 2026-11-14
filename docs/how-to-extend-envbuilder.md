# How to extend `EnvBuilder`

`venv.EnvBuilder` is the class behind `python -m venv`. It is designed for
subclassing: you control *how* a virtual environment is created by passing
options to the constructor, and *what happens after creation* by overriding
hooks. This guide walks through a complete, working subclass —
`ExtendedEnvBuilder` — that installs `setuptools` and `pip` into every
environment it creates, and shows how to drive it from a CLI.

## The two extension points

### 1. Constructor options

`EnvBuilder.__init__` accepts the creation options:

| Option | Effect |
|---|---|
| `system_site_packages` | Give the new environment access to the interpreter site-packages |
| `clear` | Delete the target directory contents before creating the environment |
| `symlinks` | Try symlinks instead of copies for the interpreter binary |
| `upgrade` | Upgrade the directory in place to the running Python version |
| `with_pip` | Seed the environment with pip via `ensurepip` (Python 3.4+) |
| `prompt` | Custom prompt prefix for the environment |

A subclass adds its own keyword arguments by popping them from `**kwargs`
*before* calling `super().__init__`, so the parent never sees unknown options.

### 2. The `post_setup` hook

After `create()` has built the directory, the interpreter and the activation
scripts, it calls `self.post_setup(context)`. The `context` object carries
everything you need to operate on the fresh environment:

| Attribute | Meaning |
|---|---|
| `env_dir` | Absolute path of the environment |
| `bin_path` | Directory holding the interpreter and scripts (`Scripts` on Windows, `bin` elsewhere) |
| `env_exe` | Absolute path of the environment Python executable |
| `cfg_path` | Path of the environment pyvenv.cfg |

`post_setup` is the place for all customization that needs a *working*
environment: pre-installing packages, writing project files, patching
configuration.

## The example: installing setuptools and pip

`ExtendedEnvBuilder` overrides `post_setup` to download the official
bootstrap scripts (`ez_setup.py`, `get-pip.py`) into the environment binaries
folder and execute them with the environment own interpreter.
Because the scripts run under `env_exe`, everything they install lands in
the new environment site-packages, not the host.

Key mechanics:

- **Progress reporting** — the constructor accepts an optional `progress`
  callable, invoked as `progress(message, context)` where context is one of
  `'main'`, `'stdout'`, or `'stderr'`. Without it, progress dots are written
  to `sys.stderr` so long downloads never look hung.
- **Stream reading on threads** — the bootstrap scripts are run with
  `subprocess.Popen`; both output streams are drained on separate threads.
  Without this, a chatty subprocess can fill its pipe buffer and deadlock
  the parent.
- **Cleanup** — the downloaded script and the setuptools archive tarball are
  deleted from `bin_path` after installation.

### Full source

Save this as `envbuilder_ext.py` (or take it from
[the CPython `venv` documentation](https://docs.python.org/3/library/venv.html#an-example-of-extending-envbuilder),
where it originates):

```python
import os
import os.path
from subprocess import Popen, PIPE
import sys
from threading import Thread
from urllib.parse import urlparse
from urllib.request import urlretrieve
import venv


class ExtendedEnvBuilder(venv.EnvBuilder):
    """
    This builder installs setuptools and pip so that you can pip or
    easy_install other packages into the created virtual environment.

    :param nodist: If true, setuptools and pip are not installed into the
                   created virtual environment.
    :param nopip: If true, pip is not installed into the created
                  virtual environment.
    :param progress: If setuptools or pip are installed, the progress of the
                     installation can be monitored by passing a progress
                     callable. If specified, it is called with two
                     arguments: a string indicating some progress, and a
                     context indicating where the string is coming from.
                     The context argument can have one of three values:
                     'main', indicating that it is called from virtualize()
                     itself, and 'stdout' and 'stderr', which are obtained
                     by reading lines from the output streams of a subprocess
                     which is used to install the app.

                     If a callable is not specified, default progress
                     information is output to sys.stderr.
    """

    def __init__(self, *args, **kwargs):
        self.nodist = kwargs.pop("nodist", False)
        self.nopip = kwargs.pop("nopip", False)
        self.progress = kwargs.pop("progress", None)
        self.verbose = kwargs.pop("verbose", False)
        super().__init__(*args, **kwargs)

    def post_setup(self, context):
        """
        Set up any packages which need to be pre-installed into the
        virtual environment being created.

        :param context: The information for the virtual environment
                        creation request being processed.
        """
        os.environ["VIRTUAL_ENV"] = context.env_dir
        if not self.nodist:
            self.install_setuptools(context)
        # Can't install pip without setuptools
        if not self.nopip and not self.nodist:
            self.install_pip(context)

    def reader(self, stream, context):
        """
        Read lines from a subprocess' output stream and either pass to a progress
        callable (if specified) or write progress information to sys.stderr.
        """
        progress = self.progress
        while True:
            s = stream.readline()
            if not s:
                break
            if progress is not None:
                progress(s, context)
            else:
                if not self.verbose:
                    sys.stderr.write(".")
                else:
                    sys.stderr.write(s.decode("utf-8"))
                sys.stderr.flush()
        stream.close()

    def install_script(self, context, name, url):
        _, _, path, _, _, _ = urlparse(url)
        fn = os.path.split(path)[-1]
        binpath = context.bin_path
        distpath = os.path.join(binpath, fn)
        # Download script into the virtual environment's binaries folder
        urlretrieve(url, distpath)
        progress = self.progress
        if self.verbose:
            term = "\n"
        else:
            term = ""
        if progress is not None:
            progress("Installing %s ...%s" % (name, term), "main")
        else:
            sys.stderr.write("Installing %s ...%s" % (name, term))
            sys.stderr.flush()
        # Install in the virtual environment
        args = [context.env_exe, fn]
        p = Popen(args, stdout=PIPE, stderr=PIPE, cwd=binpath)
        t1 = Thread(target=self.reader, args=(p.stdout, "stdout"))
        t1.start()
        t2 = Thread(target=self.reader, args=(p.stderr, "stderr"))
        t2.start()
        p.wait()
        t1.join()
        t2.join()
        if progress is not None:
            progress("done.", "main")
        else:
            sys.stderr.write("done.\n")
        # Clean up - no longer needed
        os.unlink(distpath)

    def install_setuptools(self, context):
        """
        Install setuptools in the virtual environment.

        :param context: The information for the virtual environment
                        creation request being processed.
        """
        url = "https://bootstrap.pypa.io/ez_setup.py"
        self.install_script(context, "setuptools", url)
        # clear up the setuptools archive which gets downloaded
        pred = lambda o: o.startswith("setuptools-") and o.endswith(".tar.gz")
        files = filter(pred, os.listdir(context.bin_path))
        for f in files:
            f = os.path.join(context.bin_path, f)
            os.unlink(f)

    def install_pip(self, context):
        """
        Install pip in the virtual environment.

        :param context: The information for the virtual environment
                        creation request being processed.
        """
        url = "https://bootstrap.pypa.io/get-pip.py"
        self.install_script(context, "pip", url)
```

### CLI entrypoint (same file, below the class)

```python
def main(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        prog=__name__, description="Creates virtual Python environments in one or more target directories."
    )
    parser.add_argument(
        "dirs", metavar="ENV_DIR", nargs="+", help="A directory in which to create the virtual environment."
    )
    parser.add_argument(
        "--no-setuptools",
        default=False,
        action="store_true",
        dest="nodist",
        help="Don't install setuptools or pip in the virtual environment.",
    )
    parser.add_argument(
        "--no-pip",
        default=False,
        action="store_true",
        dest="nopip",
        help="Don't install pip in the virtual environment.",
    )
    parser.add_argument(
        "--system-site-packages",
        default=False,
        action="store_true",
        dest="system_site",
        help="Give the virtual environment access to the system site-packages dir.",
    )
    if os.name == "nt":
        use_symlinks = False
    else:
        use_symlinks = True
    parser.add_argument(
        "--symlinks",
        default=use_symlinks,
        action="store_true",
        dest="symlinks",
        help="Try to use symlinks rather than copies, when symlinks are not the default for the platform.",
    )
    parser.add_argument(
        "--clear",
        default=False,
        action="store_true",
        dest="clear",
        help="Delete the contents of the "
        "virtual environment "
        "directory if it already "
        "exists, before virtual "
        "environment creation.",
    )
    parser.add_argument(
        "--upgrade",
        default=False,
        action="store_true",
        dest="upgrade",
        help="Upgrade the virtual "
        "environment directory to "
        "use this version of "
        "Python, assuming Python "
        "has been upgraded "
        "in-place.",
    )
    parser.add_argument(
        "--verbose",
        default=False,
        action="store_true",
        dest="verbose",
        help="Display the output from the scripts which install setuptools and pip.",
    )
    options = parser.parse_args(args)
    if options.upgrade and options.clear:
        raise ValueError("you cannot supply --upgrade and --clear together.")
    builder = ExtendedEnvBuilder(
        system_site_packages=options.system_site,
        clear=options.clear,
        symlinks=options.symlinks,
        upgrade=options.upgrade,
        nodist=options.nodist,
        nopip=options.nopip,
        verbose=options.verbose,
    )
    for d in options.dirs:
        builder.create(d)


if __name__ == "__main__":
    rc = 1
    try:
        main()
        rc = 0
    except Exception as e:
        print("Error: %s" % e, file=sys.stderr)
    sys.exit(rc)
```

## Using it

### Command line

```console
# Full environment with setuptools and pip
$ python envbuilder_ext.py ~/envs/myproject

# Skip the bootstrap downloads entirely
$ python envbuilder_ext.py --no-setuptools ~/envs/minimal

# Watch the bootstrap script output live
$ python envbuilder_ext.py --verbose ~/envs/debug
```

### As a library

```python
from envbuilder_ext import ExtendedEnvBuilder

builder = ExtendedEnvBuilder(
    system_site_packages=False,
    clear=True,
    progress=lambda msg, ctx: print(f"[{ctx}] {msg}", end=""),
)
builder.create("/path/to/env")
```

The `progress` callback makes the builder safe to embed in GUI or web
contexts where `sys.stderr` is not the right surface.

## Notes and caveats

- **Prefer `with_pip=True` for modern Python.** Since Python 3.4 the stdlib
  can seed pip itself via `ensurepip`, without network access. This example
  remains the canonical demonstration of the extension API, and the
  bootstrap-script technique is still useful when you need a *newer* pip or
  setuptools than the interpreter bundles, or packages `ensurepip` omits.
- **Network required.** `urlretrieve` fetches from `bootstrap.pypa.io`; the
  `--no-setuptools` / `nodist` switch is the offline escape hatch.
- **`os.environ['VIRTUAL_ENV']` is process-wide.** `post_setup` sets it so
  subprocesses see the active environment; if you create several
  environments in one process, reset or unset it between calls.
- **Windows.** `use_symlinks` defaults to `False` on Windows (symlinks need
  elevated privileges), mirroring `python -m venv` behavior.
- **Threads are required, not optional.** Draining both pipes concurrently
  prevents the deadlock described above; do not replace them with
  `stdout=DEVNULL` if you want the output.

## Extending further

The same pattern covers any post-creation work:

1. Accept new behavior as constructor kwargs (popped before `super().__init__`).
2. Act on them in `post_setup`, using `context.env_exe` / `context.bin_path`
   to stay platform-neutral.
3. Keep long-running subprocesses piped and drained, and report through the
   `progress` callable rather than hard-coding output.

Examples: pre-seeding a `requirements.txt` install
(`[context.env_exe, '-m', 'pip', 'install', '-r', ...]`), writing a
project marker file, or registering the environment with a task runner.
