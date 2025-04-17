

import requests
from rich import print
from typing import List, Any, Tuple
from time import sleep
import schedule
import time
from datetime import datetime

# Creating a bot to help perform task watching videos and getting rewards on https://ffnga555999.com/xml/index.html#/
class FF:
    access_key: str
    user_data = {
        "username": "08061450508",
        "password": "$00laimanGee1ne"
    }
    tasks: List[Any]
    total_task = 20
    task_completed = 0
    withdraw_amounts = [1000, 5000, 20000, 100000]

    # This is like the constructor, this will trigger on the first instance of the class
    def __init__(self):
        self.access_key = ""
        self.tasks = []

    # Use this function to sign in the user account and obtain accessToken
    def login(self):

        # Sending a POST request to the login endpoint
        res = requests.post("https://ffnga555999.com/api/User/Login", self.user_data)

        if res.status_code != 200:
            print("[red] Authentication failed [/red]")

        response = res.json()

        self.access_key = response['info']['token']
        print("[bold green] Authentication Successful ✅ [/bold green]")

    # This is used to get the list of tasks that are available to the current user signed in.
    def get_tasks_list(self):

        res = requests.post("https://ffnga555999.com/api/task/getTaskList", data={
            "group_id": 0,
            "task_level": 3,
            "page_no": 1,
            "is_u": 0,
            "lang": "en",
            "token": self.access_key
        })

        response = res.json()

        if response['code'] != 1:
            print("[ERROR]: Unable to get the task list of the current authenticated user ❌")

        self.tasks = response['info']
        print("[SUCCESS]: Tasks lists got successful")

        return self

    def get_task_detail(self, task_id: int) -> dict:

        res = requests.post("https://ffnga555999.com/api/task/getTaskinfo", data={
            "id": task_id,
            "lang": "en",
            "token": self.access_key
        })

        response = res.json()

        if response.get("code") != 1:
            print(f"[ERROR]: Unable to get task detail for task with id {task_id} ❌")

        return response

    def run(self):
        # Login the user account
        self.login()

        # Get the tasks list of the user account
        self.get_tasks_list()

        while self.task_completed < min(len(self.tasks), self.total_task):
            task = self.tasks[self.task_completed]

            task_id = task.get('task_id')
            if not task_id:
                print(f"[ERROR]: Missing task_id for task at index {self.task_completed}. Skipping.")
                self.task_completed += 1
                continue

            detail_response = self.get_task_detail(task_id)

            if detail_response['code'] != 1:
                print(f"[ERROR]: Unable to fetch details for task {task_id}. Skipping.")
                self.task_completed += 1
                continue

            detail = detail_response
            answer, task_completed = self.find_answer_to_task(detail.get('info', {}))

            if task_completed:
                sleep(86400)
                continue

            retries = 0
            max_retries = 5
            while retries < max_retries:
                # Try the task again with a different answer
                answer = 1 if answer == 2 else 2
                is_correct = self.answer_task(task_id, answer)

                if is_correct:
                    print(f"[SUCCESS]: Task {task_id} completed successfully.")
                    break

                retries += 1
                print(f"[INFO]: Retry {retries}/{max_retries} for task {task_id}.")
                sleep(2)

            if retries == max_retries:
                print(f"[ERROR]: Max retries reached for task {task_id}.")

            self.task_completed += 1

        # Sleep till the next day
        print("[INFO]: All tasks for today completed. Sleeping till the next day.")
        sleep(86400)

    def find_answer_to_task(self, data: Any) -> int:
        answer = data['answer1']
        user_choice = data['task_class']

        if answer == user_choice:
            return 1
        else:
            return 2

    def answer_task(self, task_id: int, possible_answer: int) -> Tuple[bool, bool]:
        res = requests.post("https://ffnga555999.com/api/task/receiveTask", data={
            'id': task_id,
            "answer": possible_answer,
            "lang": 'en',
            "token": self.access_key
        })

        response = res.json()

        if response['code'] != 1:
            print(f"[ERROR]: Incorrect user answer, user choose {possible_answer} as answer")
            return (False, True)

        return (True, False)

    def getBank(self):
        res = requests.post("https://ffnga555999.com/api/Account/getBankCardList", data={
            "lang": "en",
            "token": self.access_key
        })

        response = res.json()

        if response['code'] != 1:
            print("[ERROR]: Unable to get user bank ❌")
            return

        print("[SUCCESS]: User bank account fetched successfully ✅")

        return response['data']

    def withdraw(self, transaction_pin="0058", withdraw_id=1):

        if len(self.access_key) < 10:
            self.login()

        bank = self.getBank()[0]

        id = bank['id']

        res = requests.post("https://ffnga555999.com/api/Transaction/draw", data={
            "draw_type": "bank",
            "user_bank_id": id,
            "draw_money": self.withdraw_amounts[withdraw_id],
            "ifsc": "",
            "drawword": transaction_pin,
            "bank_id": id,
            "pix_value": bank['card_no'],
            "extend": {
                "pix_type": "CPF",
                "pix_value": bank['card_no'],
                "account_type": ""
            },
            "lang": "en",
            "token": self.access_key
        })

        response = res.json()

        print(response)

        if response.get("code") != 1:
            print(f'[ERROR]: {response['code_dec']} ❌')
            return self

        print(f"[SUCCESS]: Withdrawal completed successfully ✅")

        return self

def schedule_task():
    task = FF()

    # Withdraw at 9:30 AM on Thursdays if tasks are completed
    if datetime.now().strftime('%A') == 'Thursday':
        schedule.every().thursday.at("09:30").do(task.withdraw)

    # Run the task every day except Sunday
    schedule.every().day.at("00:05").do(task.run)
    schedule.every().sunday.do(lambda: print("[INFO]: Sunday - No tasks to perform."))

    while True:
        schedule.run_pending()
        time.sleep(1)

schedule_task()
