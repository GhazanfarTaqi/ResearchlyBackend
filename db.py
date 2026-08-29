from database.connection import connectdb


sample_paper = {
    "title": "Sample Paper Title",
    "year": 2023,
    "doi": "10.1234/sampledoi",
    "citations": 10,
    "url": "https://example.com/sample-paper",
    "abstract": "This is a sample abstract for the paper.",
    "authors": ["Author One", "Author Two"],
    "local_path": "/path/to/sample-paper.pdf"
}

def insert_paper(paper_data):
    try:
        db = connectdb("papers")
        result = db.papers.insert_one(paper_data)
        return result.inserted_id
    except Exception as e:
        print(f"Error inserting paper: {e}")
        return None

def get_paper_by_doi(doi):
    try:
        db = connectdb("papers")
        paper = db.papers.find_one({"doi": doi})
        return paper
    except Exception as e:
        print(f"Error retrieving paper: {e}")
        return None

def isPaperInDb(doi):
    try:
        db = connectdb("papers")
        paper = db.papers.find_one({"doi": doi})
        if paper:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error checking paper existence: {e}")
        return False


if __name__ == "__main__":

    try:
        paper = isPaperInDb("10.1234/sampledoi")
        print("Retrieved Paper:", paper)
    except Exception as e:
        print(f"Error inserting paper: {e}")

