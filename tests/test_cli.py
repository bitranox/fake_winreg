# EXT
from click.testing import CliRunner

# OWN
import lib_registry.lib_registry_cli as lib_registry_cli

runner = CliRunner()
runner.invoke(lib_registry_cli.cli_main, ['--version'])
runner.invoke(lib_registry_cli.cli_main, ['-h'])
runner.invoke(lib_registry_cli.cli_main, ['info'])
