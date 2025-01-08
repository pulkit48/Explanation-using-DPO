import arxiv
import tarfile
import os
import shutil
import re
import chardet
import requests
import json

# Step 1: Fetch a paper using its arXiv ID
def fetch_paper_by_id(arxiv_id):
    paper = next(arxiv.Search(id_list=[arxiv_id]).results(), None)
    if not paper:
        raise ValueError(f"No paper found for arXiv ID: {arxiv_id}")
    return paper

# Step 1: Search for an arXiv paper
def search_arxiv(query, max_results=1):
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    return [result for result in search.results()]

# Step 2: Download the TeX sources
def download_tex_sources(paper, output_dir='downloads'):
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a directory for the paper
    paper_dir = os.path.join(output_dir, paper.entry_id.split('/')[-1])
    os.makedirs(paper_dir, exist_ok=True)
    
    # Download the source files
    paper.download_source(paper_dir)
    return paper_dir


# Step 3: Extract figures with captions and tables
def extract_figures_and_tables(source_dir, output_dir='extracted'):
    # Check if the source directory exists
    if not os.path.isdir(source_dir):
        raise FileNotFoundError(f"The provided path is not a valid directory: {source_dir}")

    os.makedirs(output_dir, exist_ok=True)
    extracted_tex_dir = os.path.join(output_dir, "tex_files")
    os.makedirs(extracted_tex_dir, exist_ok=True)

    # Locate the tar.gz file in the source directory
    tar_gz_file = None
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.tar.gz'):
                tar_gz_file = os.path.join(root, file)
                break

    if not tar_gz_file:
        raise FileNotFoundError(f"No .tar.gz file found in the source directory: {source_dir}")

    # Extract the tar.gz file
    with tarfile.open(tar_gz_file, 'r:gz') as tar:
        tar.extractall(path=extracted_tex_dir)

    figures = []
    tables = []

    # Traverse extracted files to find .tex files
    for root, _, files in os.walk(extracted_tex_dir):
        for file in files:
            if file.endswith('.tex'):
                tex_file_path = os.path.join(root, file)

                # Detect file encoding
                with open(tex_file_path, 'rb') as tex_file:
                    raw_data = tex_file.read()
                    detected_encoding = chardet.detect(raw_data)['encoding']

                # Read file with detected encoding
                with open(tex_file_path, 'r', encoding=detected_encoding, errors='ignore') as tex_file:
                    content = tex_file.read()
                    
                    # Extract figures (using figure environment)
                    figure_matches = re.findall(r'\\begin{figure}.*?\\end{figure}', content, re.DOTALL)
                    figures.extend(figure_matches)

                    # Extract tables (using table environment)
                    table_matches = re.findall(r'\\begin{table}.*?\\end{table}', content, re.DOTALL)
                    tables.extend(table_matches)

    # Save figures and tables
    figures_path = os.path.join(output_dir, "figures.txt")
    tables_path = os.path.join(output_dir, "tables.txt")

    with open(figures_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(figures))

    with open(tables_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(tables))

    return extracted_tex_dir, figures_path, tables_path

def download_pdf(paper, output_dir='downloads'):
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a directory for the paper
    paper_dir = os.path.join(output_dir, paper.entry_id.split('/')[-1])
    os.makedirs(paper_dir, exist_ok=True)
    
    # Get the PDF URL
    pdf_url = paper.pdf_url
    if not pdf_url:
        raise ValueError("No PDF URL found for the paper.")
    
    # Download the PDF
    pdf_path = os.path.join(paper_dir, f"{paper.entry_id.split('/')[-1]}.pdf")
    response = requests.get(pdf_url)
    response.raise_for_status()  # Raise an error if the download fails
    with open(pdf_path, 'wb') as pdf_file:
        pdf_file.write(response.content)
    return pdf_path

# if _name_ == "_main_":
    # Give output directory
    

# Comment/uncomment the appropriate line below to switch between search modes:
# query = "PDF-MVQA: A Dataset for Multimodal Information Retrieval in PDF-based Visual Question Answering"  # For paper name search
# arxiv_id = "2404.12720v1"  # For paper ID search
file_paths = ["test-A/SPIQA_testA.json","test-B/SPIQA_testB.json","test-C/SPIQA_testC.json"]

for file_path in file_paths:
    with open(file_path, "r") as f:
        data = json.load(f)
    ids=data.keys()
    
    for id in ids:
        arxiv_id = id
        output_dir = f'dataset/{file_path}/{arxiv_id}'
        try:
            # Determine search type and fetch paper
            if 'arxiv_id' in locals():
                paper = fetch_paper_by_id(arxiv_id)
            else:
                papers = search_arxiv(query)
                if not papers:
                    print("No papers found.")
                    exit()
                paper = papers[0]
                
            print(f"Found paper: {paper.title} by {', '.join([author.name for author in paper.authors])}")
            
            # Download PDF
            pdf_path = download_pdf(paper, output_dir=output_dir)
            print(f"Downloaded PDF to {pdf_path}")

            # Download TeX sources
            paper_dir = download_tex_sources(paper, output_dir=output_dir)
            print(f"Downloaded TeX sources to {paper_dir}")

            # Extract figures and tables
            extracted_tex_dir, figures_path, tables_path = extract_figures_and_tables(
                paper_dir, output_dir=output_dir
            )

            print(f"Extracted .tex files are stored in: {extracted_tex_dir}")
            print(f"Figures are saved in: {figures_path}")
            print(f"Tables are saved in: {tables_path}")
        except Exception as e:
            print(f"An error occurred: {e}")