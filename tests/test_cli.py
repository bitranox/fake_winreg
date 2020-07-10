# EXT
import click.testing

# OWN
import fake_winreg.fake_winreg_cli as fake_winreg_cli

runner = click.testing.CliRunner()
runner.invoke(fake_winreg_cli.cli_main, ['--version'])
runner.invoke(fake_winreg_cli.cli_main, ['-h'])
runner.invoke(fake_winreg_cli.cli_main, ['info'])
