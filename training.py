import json
import os
import random
import openai
from dotenv import load_dotenv
import tiktoken
# data_path = f"MATH/train/"
# topics = os.listdir(data_path)
# fine_tuning_data = []


# for topic in topics:
#     if topic != ".DS_Store":
#         category_path = data_path + topic + "/"
#         items = os.listdir(category_path)
#         random.shuffle(items)
#         index = 0
#         for item in items:
#             if (index < 50):
#                 index += 1
#                 item_path = category_path + item
#                 with open(item_path) as data:
#                     data = json.load(data)
#                     fine_tuning_data.append(
#                         {
#                             "messages" : [
#                                 {"role": "system", "content": "you are a very helpful school faculty member"},
#                                 {"role": "user", "content": data["problem"]},
#                                 {"role": "assistant", "content": data["solution"]}
#                             ]
#                         }
#                     )
#             else:
#                 break
# random.shuffle(fine_tuning_data)
# with open ("fine_tuning_data.jsonl", "w", encoding="utf-8") as f:
#     for data in fine_tuning_data:
#         json.dump(data, f, ensure_ascii=False)
#         f.write("\n")
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
# uploaded_file = openai.File.create(
#     file=open("fine_tuning_data.jsonl", "rb"),
#     purpose="fine-tune"
# )
# print(uploaded_file)
# print(openai.File.retrieve("file-wYoYR4khdanz0CpOA6wiPZa4"))
# # print(openai.File.list())
# print(openai.FineTuningJob.create(training_file="file-wYoYR4khdanz0CpOA6wiPZa4", model="gpt-3.5-turbo"))
while True:
    job = openai.FineTuningJob.list_events(id="ftjob-pKnXCKypHGtmDeGZXWuJ5wfr", limit=1)
    print(job)
