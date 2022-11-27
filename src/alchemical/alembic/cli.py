import os
from alembic.config import Config as AlembicConfig
from alembic.config import CommandLine as AlembicCommandLine


class Config(AlembicConfig):  # pragma: no cover
    def get_template_directory(self) -> str:
        import alchemical.alembic

        package_dir = os.path.abspath(os.path.dirname(
            alchemical.alembic.__file__))
        return os.path.join(package_dir, "templates")


class CommandLine(AlembicCommandLine):  # pragma: no cover
    def main(self, argv=None):
        options = self.parser.parse_args(argv)
        if not hasattr(options, "cmd"):
            # see http://bugs.python.org/issue9253, argparse
            # behavior changed incompatibly in py3.3
            self.parser.error("too few arguments")
        else:
            cfg = Config(
                file_=options.config,
                ini_section=options.name,
                cmd_opts=options,
            )
            self.run_cmd(cfg, options)


def main(argv=None, prog=None, **kwargs):
    """The console runner function for Alembic."""

    CommandLine(prog=prog).main(argv=argv)


if __name__ == "__main__":  # pragma: no cover
    main()
