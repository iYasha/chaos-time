import argparse

from services.google.calendar import CalendarService
from services.jira import JiraService


def main():
    parser = argparse.ArgumentParser(
        prog='Chaos Time',
    )

    parser.add_argument('-V', '--version', action='version', version='%(prog)s 1.0.0')

    subparsers = parser.add_subparsers(help='sub-command help', required=True)
    JiraService.add_parser(subparsers)
    CalendarService.add_parser(subparsers)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
