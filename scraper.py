import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfFileReader
import re
import json

def get_question_bank(filename):
    url = "http://arrl.org"
    qbank_page = url + "/question-pools"
    resp = requests.request("GET", qbank_page)
    parsed_qbank_page = BeautifulSoup(resp.text, "html.parser")
    qbank_file_location = parsed_qbank_page.find_all("ul", {"class" : "accordion"})[0].find_all("a")[2]["href"]

    question_bank_url = url + qbank_file_location
    print(question_bank_url)
    resp = requests.request("GET", question_bank_url)
    with open(filename, "wb") as file:
        file.write(resp.content)
    return filename

def parse_question_bank2(filename, saveAt="qs.json"):
    reader = PdfFileReader(filename)
    questions = {}
    q_count = -1
    opt_c = -1
    for page_id in range(2, 4):#reader.getNumPages()):
        page = reader.getPage(page_id)
        page_content = page.extractText()
        page_chunks = page_content.split("~~")
        untrimmed_segments = [re.split(r"( *\n *){3,}", chunk) for chunk in page_chunks]
        segments = [filter(lambda x: ''.join(x.split()), seg) for seg in untrimmed_segments]
        for seg in segments:
            for part in seg:
                qid = re.match(r"( |\n)*(T[0-9][A-Z][0-9]{2})", part)
                if qid:# and (q_count not in questions):
                    q_count += 1
                    questions[q_count] = {}
                    questions[q_count]["qid"] = qid.groups()[1]
                    questions[q_count]["prompt"] = ""
                    questions[q_count]["options"] = {}
                    opt_c = -1
                for line in re.split(r" *\n *", part):
                    if re.match(r" *[A-D]\.", line):
                        opt_c += 1
                        questions[q_count]["options"][opt_c] = line
                    else:
                        if opt_c == -1:
                            questions[q_count]["prompt"] += line
                        else:
                            questions[q_count]["options"][opt_c] += line
                q_count += 1
    json.dump(questions, open(saveAt, "w"))
    return questions
        
def parse_question_bank(filename, saveAt="qs.json"):
    rx_qid = r"(T[0-9][A-Z][0-9]{2})"
    rx_answer = r"\(([A-D])\)"
    rx_section = r"(\[[0-9]{2}.[0-9]\([a-z]\)\([0-9]\)\])"
    rx_question = r"\](.*)A\."

    reader = PdfFileReader(filename)
    questions = {}
    q_count = -1
    for page_id in range(2, 4):#reader.getNumPages()):
        page = reader.getPage(page_id)
        page_content = page.extractText()
        page_content = re.sub("\n", "\t", page_content)
        page_chunks = page_content.split("~~")
        for chunk in page_chunks:
            if qid := re.match(rx_qid, chunk):
                print("QID", chunk)
                q_count += 1
                questions[q_count] = {}
                questions[q_count]["qid"] = qid.groups()[0]
                questions[q_count]["question"] = ""
                questions[q_count]["options"] = []
            if answer := re.match(rx_answer, chunk):
                print("ANS", chunk)
                questions[q_count]["answer"] = answer.groups()[0]
            if section := re.match(rx_section, chunk):
                questions[q_count]["section"] = section.groups()[0]
            if question := re.match(rx_question, chunk):
                questions[q_count]["question"] = question.groups()[0]
            bookends = [r"A\.", r"B\.", r"C\.", r"D\.", r"$"]
            for opt_c in range(len(bookends) - 1):
                rx_opt = rf"({bookends[opt_c]}.*){bookends[opt_c+1]}"
                if opt := re.match(rx_opt, chunk):
                    questions[q_count]["options"].append(opt)
    
    json.dump(questions, open(saveAt, "w"))
    return questions

if __name__ == "__main__":
    parse_question_bank("questions.pdf")