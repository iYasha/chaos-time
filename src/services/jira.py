import argparse
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, date

from jira import JIRA
from texttable import Texttable

from utils import set_date_args, Time


@dataclass
class WorkLog:
    issue_id: str
    issue_summary: str
    spent_time: Time

    def __str__(self) -> str:
        return f'{self.issue_id} - {self.spent_time.human_readable}'

    def __repr__(self) -> str:
        return f'WorkLog({self.issue_id}, {self.issue_summary}, {self.spent_time})'


class JiraService:
    def __init__(self, email: str, api_token: str):
        self.client = JIRA(server=os.getenv('JIRA_SERVER_URL'), basic_auth=(email, api_token))

    def get_worklog(self, worklog_date: date) -> tuple[WorkLog]:
        issues = self.client.search_issues(f'worklogAuthor = currentUser() AND worklogDate = {worklog_date}')
        work_logs = []
        for issue in issues:
            spent_seconds = sum(x.timeSpentSeconds for x in issue.fields.worklog.worklogs if datetime.strptime(x.started, '%Y-%m-%dT%H:%M:%S.%f%z').date() == worklog_date)
            if spent_seconds > 0:
                work_logs.append(WorkLog(issue.key, issue.fields.summary, Time(spent_seconds)))
        return tuple(work_logs)

    @classmethod
    def add_parser(cls, subparser):
        parser = subparser.add_parser('jira')

        set_date_args(parser)

        parser.add_argument('-e', '--email', type=str, help='Jira email')
        parser.add_argument('-t', '--token', type=str, help='Jira API token')
        parser.add_argument('-l', '--list', help='Show only issues', nargs=argparse.REMAINDER)
        parser.set_defaults(func=run)


def run(args):
    jira_email = args.email or os.getenv('JIRA_EMAIL')
    jira_api_token = args.token or os.getenv('JIRA_API_TOKEN')
    if not jira_email:
        raise ValueError('Jira email is not specified. Please use --email or JIRA_EMAIL env variable')
    if not jira_api_token:
        raise ValueError('Jira API token is not specified. Please use --token or JIRA_API_TOKEN env variable')

    tracker = JiraService(jira_email, jira_api_token)
    worklog_date = date(args.year, args.month, args.day)
    logs = tracker.get_worklog(worklog_date)

    if args.list is not None:
        print(', '.join(x.issue_id for x in logs))
        return
    total_time: Time = sum([x.spent_time for x in logs]) or Time(0)
    time_remaining = timedelta(hours=8) - total_time

    print(f'Worklog for {worklog_date}')
    print(f'Total time: {total_time.human_readable}')
    print(f'Time remaining: {time_remaining.human_readable}')
    t = Texttable()
    t.add_rows(
        [['Ticket', 'Time tracked', 'Summary'],
         *[(x.issue_id, x.spent_time.human_readable, x.issue_summary) for x in logs]]
    )
    print(t.draw())





