import os
import io
import sys
import time
import arxiv
import openai
import random
from xml.dom import minidom
import xmltodict
import dicttoxml
import json

#OpenAIのapiキー
openai.api_key = 'your openai key'

prompt = """Summarize the key points of the given paper in English according to the following categories. Each category should be summarized in no more than 180 words.
```
Title: The title
Keywords: Keywords of this paper
Problem: The problem this paper addresses
Method: The method proposed by this paper
Results: The results achieved by the proposed method```"""

def get_summary(result):
    text = f"title: {result.title}\nbody: {result.summary}"
    print("### input text", text)
    #print("### input prompt", prompt)
    response = openai.ChatCompletion.create(
                #model="gpt-3.5-turbo",
                model='gpt-4',
                messages=[
                    {'role': 'system', 'content': prompt},
                    {'role': 'user', 'content': text}
                ],
                temperature=0.25,
            )
    summary = response['choices'][0]['message']['content']
    print("#### GPT", summary)
    dict = {}    
    for b in summary.split('\n'):
        print("****", b)
        if b.startswith("Keywords"):
            dict['keywords'] = b[10:].lstrip()
        if b.startswith("Problem"):
            dict['problem'] = b[7:].lstrip()
        if b.startswith("Method"):
            dict['method'] = b[6:].lstrip()
        if b.startswith("Results"):
            dict['result'] = b[7:].lstrip()
    print("Dict by ChatGPT", dict)
    return dict

def get_paper_info(result, dirpath="./xmls"):
    dict = {}
    dict['title']= result.title
    dict['date'] = result.published.strftime("%Y-%m-%d %H:%M:%S")
    dict['authors'] = [x.name for x in result.authors]
    dict['year'] = str(result.published.year)
    dict['entry_id'] = str(result.entry_id)
    dict['primary_category'] = str(result.primary_category)
    dict['categories'] = result.categories
    dict['journal_ref'] = str(result.journal_ref)
    dict['pdf_url'] = str(result.pdf_url)
    dict['doi']= str(result.doi)
    dict['abstract'] = str(result.summary)
                
    print("##### DIR", dirpath, "PDF", result.pdf_url, "DOI", result.doi, "ID", id)
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)

    # download paper PDF"
    print("download", f"{dirpath}/paper.pdf")
    result.download_pdf(dirpath=dirpath,filename="paper.pdf")
    dict['pdf'] = 'paper.pdf'

    # chatGPT summary
    dict2 = get_summary(result)

    root = {'paper': {**dict, **dict2}}
    return root

def main(query, dir='./xmls', num_papers=3, from_year=2017, max_results=100):
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    result_list = []
    for result in search.results():
        print(result, result.published.year, result.title)
        if result.published.year >= from_year:
            result_list.append(result)

    if len(result_list) <= 0:
        print("#### no result")
        sys.exit()
    
    if not os.path.exists(dir):  # make subfolder if necessary
        os.mkdir(dir)
    
    results = random.sample(result_list, k=num_papers) if num_papers > 0 and len(result_list) > num_papers else result_list

    for i, result in enumerate(results):
        try:
            id = result.entry_id.replace("http://", "").replace("/", "-")
            dirpath = f"{dir}/{id}"
            dict = get_paper_info(result, dirpath=dirpath)
            dict['paper']['query'] = query

            xml = dicttoxml.dicttoxml(dict, attr_type=False, root=False).decode('utf-8')
            xml = minidom.parseString(xml).toprettyxml(indent="   ")
            print("###########\n", xml, "\n#######")

            with open(f"{dirpath}/paper.xml", "w") as f:
                f.write(xml)
        except Exception as e:
            print("Exception", e)

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--year', '-y', type=int, help='from year', default=2017)
    parser.add_argument('--dir', "-d", type=str, help='destination', default='./xmls')
    parser.add_argument('--num', "-n", type=int, help='number of papers', default=3)    
    parser.add_argument('positional_args', nargs='+', help='query keywords')
    args = parser.parse_args()

    print(args)

    main(query=f'all:%22 {" ".join(args.positional_args)} %22', num_papers=args.num, from_year=args.year, dir=args.dir)

