#!/usr/bin/env python3
"""Fed data CLI dispatcher.

Routes commands to appropriate Fed data modules:
- fedwatch: CME FedWatch FOMC rate probabilities
"""

import sys

from fedwatch import cmd_fedwatch


def main():
	"""Main CLI entry point."""
	if len(sys.argv) < 2:
		print("Usage: python -m fed <command> [options]")
		print("\nAvailable commands:")
		print("  fedwatch    - CME FedWatch FOMC rate probabilities")
		sys.exit(1)

	command = sys.argv[1]

	# Remove command from argv
	sys.argv = [sys.argv[0]] + sys.argv[2:]

	if command == "fedwatch":
		import argparse

		parser = argparse.ArgumentParser(description="CME FedWatch - FOMC rate probabilities")
		args = parser.parse_args()
		cmd_fedwatch(args)
	else:
		print(f"Unknown command: {command}")
		sys.exit(1)


if __name__ == "__main__":
	main()
