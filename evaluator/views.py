import os
import pdfplumber
import spacy
from django.shortcuts import render
from django.http import HttpResponse
from sklearn.feature_extraction.text import CountVectorizer

nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_file):
    text = ''
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ''
    return text

def extract_keywords(text):
    doc = nlp(text.lower())
    return list(set([token.lemma_ for token in doc if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop]))

def home(request):
    if request.method == 'POST':
        resume_file = request.FILES.get('resume')
        jd_text = request.POST.get('jd')

        if not resume_file or not jd_text:
            return HttpResponse("<p style='color: red;'>Invalid input provided.</p>")

        resume_text = extract_text_from_pdf(resume_file)
        resume_keywords = extract_keywords(resume_text)
        jd_keywords = extract_keywords(jd_text)

        matched = list(set(resume_keywords) & set(jd_keywords))
        missing = list(set(jd_keywords) - set(resume_keywords))

        match_score = round(len(matched) / len(jd_keywords) * 100, 2) if jd_keywords else 0

        # Return as a chunk of HTML
        return HttpResponse(f"""
    <div class='text-center mb-6 animate-fade-in'>
        <div class="relative w-40 h-40 mx-auto mb-4">
            <svg class="transform -rotate-90" width="100%" height="100%" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="54" stroke="#2e7d32" stroke-width="12" fill="none" opacity="0.2" />
                <circle cx="60" cy="60" r="54" stroke="#4caf50" stroke-width="12" fill="none"
                        stroke-dasharray="339.292"
                        stroke-dashoffset="{339.292 - (339.292 * match_score / 100)}"
                        stroke-linecap="round"
                        style="transition: stroke-dashoffset 1s ease-in-out;" />
            </svg>
            <div class="absolute inset-0 flex items-center justify-center">
                <span class="text-2xl font-bold text-green-400 drop-shadow-lg">{match_score}%</span>
            </div>
        </div>
        <h2 class='text-xl font-semibold text-white mt-2'>Match Score</h2>
    </div>

    <div class='mb-4'>
        <h3 class='font-semibold mb-2'>Matched Keywords:</h3>
        <div class='flex flex-wrap gap-2'>
            {''.join([f"<span class='bg-green-600 px-3 py-1 rounded-full text-sm'>{word}</span>" for word in matched]) or '<p class="text-gray-400">None</p>'}
        </div>
    </div>

    <div class='mb-4'>
        <h3 class='font-semibold mb-2'>Missing Keywords:</h3>
        <div class='flex flex-wrap gap-2'>
            {''.join([f"<span class='bg-red-600 px-3 py-1 rounded-full text-sm'>{word}</span>" for word in missing]) or '<p class="text-gray-400">None</p>'}
        </div>
    </div>

    <canvas id="keywordChart" width="400" height="200"
        data-matched="{len(matched)}" data-missing="{len(missing)}"
        class="mt-6"></canvas>
    <script>
        const ctx = document.getElementById('keywordChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: ['Matched', 'Missing'],
                datasets: [{{
                    label: 'Keywords',
                    data: [{len(matched)}, {len(missing)}],
                    backgroundColor: ['#4caf50', '#f44336'],
                    borderRadius: 6
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                animation: {{
                    duration: 1000
                }}
            }}
        }});
    </script>
""")

    return render(request, 'evaluator/index.html')