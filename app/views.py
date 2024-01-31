from django.shortcuts import render
from .forms import DocumentForm
import csv
import spacy
from django.http import HttpResponse
from django.http import JsonResponse
from math import ceil


def home(request):
    return render(request, 'home.html')

def process_pdf(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            # load the NLP model
            nlp = spacy.load("en_core_web_sm")
            
            # get the requirements and their corresponding values
            requirements = {}
            with open('requirements.csv') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row[1] not in requirements:
                        requirements[row[1]] = []
                    requirements[row[1]].append(row[0])
                    
            # get the uploaded files
            files = request.FILES.getlist('file')
            results = []
            for file in files:
                
                # process each PDF document with pdfminer
                from io import StringIO
                from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
                from pdfminer.converter import TextConverter
                from pdfminer.layout import LAParams
                from pdfminer.pdfpage import PDFPage

                manager = PDFResourceManager()
                string = StringIO()
                converter = TextConverter(manager, string, laparams=LAParams())
                interpreter = PDFPageInterpreter(manager, converter)
                for page in PDFPage.get_pages(file, check_extractable=True):
                    interpreter.process_page(page)
                document_text = string.getvalue()
                string.close()
                converter.close()

                # analyze each document with SpaCy
                doc = nlp(document_text)

                # compare each document with the requirements
                matched = {}
                not_matched = {}
                for category, reqs in requirements.items():
                    matched[category] = []
                    not_matched[category] = []
                    for requirement in reqs:
                        requirement_words = requirement.split()
                        requirement_matched = False
                        for word in requirement_words:
                            if word in document_text:
                                requirement_matched = True
                                break
                        if requirement_matched:
                            matched[category].append(requirement)
                        else:
                            not_matched[category].append(requirement)
                
                
                 # calculate the percentage of not_matched categories
                num_categories = len(requirements)
                num_not_matched_categories = sum(1 for reqs in not_matched.values() if reqs)
                not_matched_percent = ceil(num_not_matched_categories / num_categories * 100)
                
                # add the results to the list
                results.append({
                    'file_name': file.name,
                    'matched': matched,
                    'not_matched': not_matched,
                    'not_matched_percent': not_matched_percent
                })

            # set the results in the session
            request.session['results'] = results

            return render(request, 'result.html', {'results': results})
    else:
        form = DocumentForm()
    return render(request, 'process_pdf.html', {'form': form})

def download_csv(request):
    # get the results from the previous view
    results = request.session.get('results', [])

    # collect all unique requirement names from all results
    requirement_names = set()
    for result in results:
        matched_requirements = result['matched'].keys()
        not_matched_requirements = result['not_matched'].keys()
        requirement_names.update(matched_requirements)
        requirement_names.update(not_matched_requirements)

    # set up the response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="results.csv"'

    # write the CSV file
    writer = csv.writer(response)

    # write the header row with file names
    header = ['Requirement']
    for result in results:
        header.append(result['file_name'])
    writer.writerow(header)

    # write the data rows
    for requirement in requirement_names:
        row = [requirement]
        for result in results:
            matched = result['matched'].get(requirement, '')
            not_matched = result['not_matched'].get(requirement, '')
            cell_value = 'Yes' if matched else ('No' if not_matched else '')
            row.append(cell_value)
        writer.writerow(row)

    # calculate and write the percentage of "Yes" for each file
    total_rows = len(requirement_names)
    for result in results:
        yes_count = 0
        for requirement in requirement_names:
            matched = result['matched'].get(requirement, '')
            if matched:
                yes_count += 1
        percentage = (yes_count / total_rows) * 100 if total_rows > 0 else 0
        writer.writerow(['Percentage of "Yes" for ' + result['file_name'], f'{percentage:.2f}%'])       
       
    return response























