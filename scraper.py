from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import re
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

PCOMBA_O_URL="https://www.shiksha.com/distance-mba-mba-distance-education-chp"
PCOMBA_DMF_URL="https://www.shiksha.com/distance-mba-mba-distance-education-fees-chp"
PCOMBA_QA_URL = "https://www.shiksha.com/tags/mba-pgdm-tdp-422"
PCOMBA_QAD_URL = "https://www.shiksha.com/tags/mba-pgdm-tdp-422?type=discussion"

def create_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

# ---------------- UTILITIES ----------------
def scroll_to_bottom(driver, scroll_times=3, pause=1.5):
    for _ in range(scroll_times):
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(pause)




def extract_overview_data(driver):
    driver.get(PCOMBA_O_URL)
    WebDriverWait(driver, 15)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    section = soup.find("section", id="chp_section_overview")

    data = {}
    title = soup.find("div",class_="a54c")
    h1 = title.text.strip()
    data["title"] = h1
    # Updated Date
    updated_div = section.select_one(".f48b div span")
    data["updated_on"] = updated_div.get_text(strip=True) if updated_div else None

    # Author Info
    author_block = section.select_one(".be8c p._7417 a")
    author_role = section.select_one(".be8c p._7417 span.b0fc")
    data["author"] = {
        "name": author_block.get_text(strip=True) if author_block else None,
        "profile_url": author_block["href"] if author_block else None,
        "role": author_role.get_text(strip=True) if author_role else None
    }

    # Overview Paragraphs
    overview_paras = section.select("#wikkiContents_chp_section_overview_0 p")
    data["overview"] = [
        p.get_text(" ", strip=True)
        for p in overview_paras
        if p.get_text(strip=True)
    ]

    # Highlights Table
    highlights = {}
    table = section.find("table")
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all(["td", "th"])
            if len(cols) == 2:
                highlights[cols[0].get_text(strip=True)] = cols[1].get_text(" ", strip=True)
    data["highlights"] = highlights

    iframe = section.select_one(".vcmsEmbed iframe")
    
    if iframe:
        data["youtube_video"] = iframe.get("src") or iframe.get("data-src")
    else:
        data["youtube_video"] = None

    # FAQs
    faqs = []
    faq_questions = section.select(".sectional-faqs > div.html-0")
    faq_answers = section.select(".sectional-faqs > div._16f53f")

    for q, a in zip(faq_questions, faq_answers):
        question = q.get_text(" ", strip=True).replace("Q:", "").strip()
        answer = a.get_text(" ", strip=True).replace("A:", "").strip()
        faqs.append({
            "question": question,
            "answer": answer
        })

    data["faqs"] = faqs
    toc = []
    toc_wrapper = soup.find("ul", id="tocWrapper")
    if toc_wrapper:
        for li in toc_wrapper.find_all("li"):
            toc.append({
                "title": li.get_text(" ", strip=True),
            })
    data["table_of_contents"] = toc


    # ==============================
    # ELIGIBILITY SECTION
    # ==============================
    eligibility_section = soup.find("section", id="chp_section_eligibility")
    eligibility_data = {}

    if eligibility_section:

        # Heading
        heading = eligibility_section.find("h2")
        eligibility_data["title"] = heading.get_text(strip=True) if heading else None

        # Main content block
        content_block = eligibility_section.select_one(".wikkiContents")

        # Paragraphs
        paras = []
        if content_block:
            for p in content_block.find_all("p"):
                text = p.get_text(" ", strip=True)
                if text:
                    paras.append(text)
        eligibility_data["description"] = paras

        # Bullet points
        bullets = []
        if content_block:
            for li in content_block.find_all("li"):
                bullets.append(li.get_text(" ", strip=True))
        eligibility_data["criteria_points"] = bullets

        # YouTube Video inside eligibility
        iframe = eligibility_section.find("iframe")
        eligibility_data["youtube_video"] = iframe.get("src") if iframe else None

        # Admission Steps
        admission_steps = []
        for ol in eligibility_section.find_all("ol"):
            for li in ol.find_all("li"):
                admission_steps.append(li.get_text(" ", strip=True))
        eligibility_data["admission_process"] = admission_steps

        # ==============================
        # ELIGIBILITY FAQs
        # ==============================
        faqs = []
        faq_questions = eligibility_section.select(".sectional-faqs > div.html-0")
        faq_answers = eligibility_section.select(".sectional-faqs > div._16f53f")

        for q, a in zip(faq_questions, faq_answers):
            faqs.append({
                "question": q.get_text(" ", strip=True).replace("Q:", "").strip(),
                "answer": a.get_text(" ", strip=True).replace("A:", "").strip()
            })

        eligibility_data["faqs"] = faqs

    data["eligibility_section"] = eligibility_data

    # SYLLABUS & SPECIALIZATION SECTION
    # ==============================
    syllabus_section = soup.find("section", id="chp_section_popularspecialization")
    syllabus_data = {}

    if syllabus_section:

        # Section Title
        title = syllabus_section.find("h2")
        syllabus_data["title"] = title.get_text(strip=True) if title else None

        content_block = syllabus_section.select_one(".wikkiContents")

        # Intro Paragraphs
        intro_paras = []
        if content_block:
            for p in content_block.find_all("p"):
                text = p.get_text(" ", strip=True)
                if text and "Source:" not in text:
                    intro_paras.append(text)
        syllabus_data["description"] = intro_paras

        # ==============================
        # SEMESTER-WISE SYLLABUS TABLE
        # ==============================
        semester_syllabus = {}

        tables = content_block.find_all("table") if content_block else []

        if tables:
            syllabus_table = tables[0]   # ✅ FIRST table only
            current_semester = None

            for row in syllabus_table.find_all("tr"):
                th = row.find("th")
                tds = row.find_all("td")

                # Semester Header
                if th and not tds:
                    current_semester = th.get_text(strip=True)
                    semester_syllabus[current_semester] = []

                # Subjects
                elif current_semester and tds:
                    for td in tds:
                        subject = td.get_text(" ", strip=True)
                        if subject:
                            semester_syllabus[current_semester].append(subject)

        syllabus_data["semester_wise_syllabus"] = semester_syllabus

        # ==============================
        # SYLLABUS YOUTUBE VIDEO
        # ==============================
        iframe = syllabus_section.select_one(".vcmsEmbed iframe")
        syllabus_data["youtube_video"] = iframe.get("src") if iframe else None

        # ==============================
        # MBA SPECIALISATIONS TABLE
        # ==============================
        specialisations = []
        tables = content_block.find_all("table") if content_block else []

        if len(tables) > 1:
            spec_table = tables[1]
            rows = spec_table.find_all("tr")[1:]

            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    specialisations.append({
                        "specialisation": cols[0].get_text(" ", strip=True),
                        "average_salary": cols[1].get_text(" ", strip=True),
                        "colleges": cols[2].get_text(" ", strip=True)
                    })

        syllabus_data["specialisations"] = specialisations

        # ==============================
        # POPULAR SPECIALIZATION BOX
        # ==============================
        popular_specs = []
        spec_box = syllabus_section.select_one(".specialization-box")

        if spec_box:
            for li in spec_box.select("ul.specialization-list li"):
                popular_specs.append({
                    "name": li.find("a").get_text(strip=True),
                    "url": li.find("a")["href"],
                    "college_count": li.find("p").get_text(strip=True)
                })

        syllabus_data["popular_specializations"] = popular_specs

        # ==============================
        # SYLLABUS FAQs
        # ==============================
        faqs = []
        faq_questions = syllabus_section.select(".sectional-faqs > div.html-0")
        faq_answers = syllabus_section.select(".sectional-faqs > div._16f53f")

        for q, a in zip(faq_questions, faq_answers):
            faqs.append({
                "question": q.get_text(" ", strip=True).replace("Q:", "").strip(),
                "answer": a.get_text(" ", strip=True).replace("A:", "").strip()
            })

        syllabus_data["faqs"] = faqs

    data["syllabus_section"] = syllabus_data

    # ==============================
    # TYPES OF DISTANCE MBA COURSES SECTION
    # ==============================
    types_section = soup.find("section", id="chp_section_topratecourses")
    types_data = {}

    if types_section:

        # Section Title
        title = types_section.find("h2")
        types_data["title"] = title.get_text(strip=True) if title else None

        content_block = types_section.select_one(".wikkiContents")

        # Intro Paragraphs
        intro_paras = []
        if content_block:
            for p in content_block.select("p"):
                text = p.get_text(" ", strip=True)
                if text and "Source:" not in text:
                    intro_paras.append(text)
        
        types_data["description"] = intro_paras
        
        # ==============================
        # TYPES TABLE
        # ==============================
        courses = []
        table = content_block.find("table") if content_block else None

        if table:
            rows = table.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    course = {
                        "course_name": cols[0].get_text(" ", strip=True),
                        "course_url": cols[0].find("a")["href"] if cols[0].find("a") else None,
                        "duration": cols[1].get_text(" ", strip=True),
                        "details": cols[2].get_text(" ", strip=True)
                    }
                    courses.append(course)

        types_data["course_types"] = courses

        # ==============================
        # POPULAR COURSES BOX
        # ==============================
        popular_courses = []
        popular_box = types_section.select_one(".specialization-box")

        if popular_box:
            for li in popular_box.select("ul.specialization-list li"):
                name_tag = li.find("strong")
                course_link = li.find("a")

                offered_by = None
                offered_link = None
                offered_tag = li.find("label", class_="grayLabel")
                if offered_tag:
                    offered_anchor = offered_tag.find_parent("a")
                    if offered_anchor:
                        offered_by = offered_anchor.get_text(" ", strip=True).replace("Offered By", "").strip()
                        offered_link = offered_anchor["href"]

                rating = li.select_one(".rating-block")
                reviews = li.select_one("a.view_rvws")

                popular_courses.append({
                    "course_name": name_tag.get_text(strip=True) if name_tag else None,
                    "course_url": course_link["href"] if course_link else None,
                    "offered_by": offered_by,
                    "offered_by_url": offered_link,
                    "rating": rating.get_text(strip=True) if rating else None,
                    "reviews": reviews.get_text(strip=True) if reviews else None,
                    "reviews_url": reviews["href"] if reviews else None
                })

        types_data["popular_courses"] = popular_courses

        # ==============================
        # FAQs
        # ==============================
        faqs = []
        faq_questions = types_section.select(".sectional-faqs > div.html-0")
        faq_answers = types_section.select(".sectional-faqs > div._16f53f")

        for q, a in zip(faq_questions, faq_answers):
            faqs.append({
                "question": q.get_text(" ", strip=True).replace("Q:", "").strip(),
                "answer": a.get_text(" ", strip=True).replace("A:", "").strip()
            })

        types_data["faqs"] = faqs

    data["types_of_distance_mba_courses"] = types_data

    # POPULAR COLLEGES SECTION
    # ==============================
    popular_colleges_section = soup.find("section", id="chp_section_popularcolleges")
    popular_colleges_data = {}
    
    if popular_colleges_section:
    
        # Section title
        title = popular_colleges_section.find("h2")
        popular_colleges_data["title"] = title.get_text(strip=True) if title else None
    
        content_block = popular_colleges_section.select_one(".wikkiContents")
    
        # ------------------------------
        # Description Paragraphs
        # ------------------------------
        description = []
        if content_block:
            for p in content_block.select("p"):
                text = p.get_text(" ", strip=True)
                if text and "Source:" not in text:
                    description.append(text)
    
        popular_colleges_data["description"] = description
    
        # ------------------------------
        # Tables (Private + Government)
        # ------------------------------
        tables = content_block.find_all("table") if content_block else []
    
        private_colleges = []
        government_colleges = []
    
        # ✅ First table → Private colleges
        if len(tables) >= 1:
            rows = tables[0].find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    link = cols[0].find("a")
                    private_colleges.append({
                        "college_name": cols[0].get_text(" ", strip=True),
                        "college_url": link["href"] if link else None,
                        "total_fees": cols[1].get_text(" ", strip=True)
                    })
    
        # ✅ Second table → Government colleges
        if len(tables) >= 2:
            rows = tables[1].find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    link = cols[0].find("a")
                    government_colleges.append({
                        "college_name": cols[0].get_text(" ", strip=True),
                        "college_url": link["href"] if link else None,
                        "fees": cols[1].get_text(" ", strip=True)
                    })
    
        popular_colleges_data["private_colleges"] = private_colleges
        popular_colleges_data["government_colleges"] = government_colleges
    
        # ------------------------------
        # YouTube Video
        # ------------------------------
        iframe = popular_colleges_section.select_one(".vcmsEmbed iframe")
        popular_colleges_data["youtube_video"] = iframe.get("src") if iframe else None
    
    data["popular_colleges_section"] = popular_colleges_data
    
    # ==============================
    # SALARY & CAREER SECTION
    # ==============================
    salary_section = soup.find("section", id="chp_section_salary")
    salary_data = {}

    if salary_section:

        # ------------------------------
        # Title
        # ------------------------------
        title = salary_section.find("h2")
        salary_data["title"] = title.get_text(strip=True) if title else None

        content_block = salary_section.select_one(".wikkiContents")

        description = []

        if content_block:
            for elem in content_block.find_all("p"):  # recursive=True by default
                text = elem.get_text(" ", strip=True)
                if text and "Source:" not in text:
                    description.append(text)

        salary_data["description"] = description
        
        # ------------------------------
        # Tables
        # ------------------------------
        tables = content_block.find_all("table") if content_block else []

        # ✅ Table 1: Employment Areas
        employment_areas = []
        if len(tables) >= 1:
            rows = tables[0].find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    employment_areas.append({
                        "area": cols[0].get_text(" ", strip=True),
                        "description": cols[1].get_text(" ", strip=True)
                    })

        salary_data["employment_areas"] = employment_areas

        # ✅ Table 2: Job Profiles & Salary
        salary_profiles = []
        if len(tables) >= 2:
            rows = tables[1].find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    salary_profiles.append({
                        "job_profile": cols[0].get_text(" ", strip=True),
                        "average_salary": cols[1].get_text(" ", strip=True)
                    })

        salary_data["salary_profiles"] = salary_profiles

        # ✅ Table 3: Top Recruiters
        top_recruiters = []
        if len(tables) >= 3:
            rows = tables[2].find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                for col in cols:
                    name = col.get_text(" ", strip=True)
                    if name:
                        top_recruiters.append(name)

        salary_data["top_recruiters"] = top_recruiters

        faqs = []

        faq_questions = salary_section.select(".sectional-faqs > .listener")

        for q in faq_questions:
            question = q.get_text(" ", strip=True).replace("Q:", "").strip()

            answer_container = q.find_next_sibling("div", class_="_16f53f")
            answer = None

            if answer_container:
                answer_content = answer_container.select_one(".cmsAContent")
                if answer_content:
                    answer = answer_content.get_text(" ", strip=True)

            if question and answer:
                faqs.append({
                    "question": question,
                    "answer": answer
                })

        salary_data["faqs"] = faqs

    data["salary_section"] = salary_data

    return data

def scrape_fees_section(driver):
    driver.get(PCOMBA_DMF_URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Find the main section
    fees_section = soup.select_one("#chp_fees_overview")
    if not fees_section:
        return {}
    result = {
        "title":"",
        "updated_on":"",
        "author":"",
        "description": [],
        "colleges_fees": [],
        "notes": []
    }

    title = soup.find("div",class_="a54c")
    h1 = title.text.strip()
    result["title"] = h1
    # Updated Date
    updated_div = fees_section.select_one(".f48b div span")
    result["updated_on"] = updated_div.get_text(strip=True) if updated_div else None

    # Author Info
    author_block = fees_section.select_one(".be8c p._7417 a")
    author_role = fees_section.select_one(".be8c p._7417 span.b0fc")
    result["author"] = {
        "name": author_block.get_text(strip=True) if author_block else None,
        "profile_url": author_block["href"] if author_block else None,
        "role": author_role.get_text(strip=True) if author_role else None
    }
    
    
    content_block = fees_section.select_one(".wikkiContents")
    if content_block:
        # 1️⃣ Extract informative <p> paragraphs (ignore links, headers, etc.)
        for elem in content_block.find_all(["p"], recursive=True):
            text = elem.get_text(" ", strip=True)
            if text:
                # skip purely link/text promotional lines
                if "Distance MBA Course topics" not in text:
                    result["description"].append(text)
        
        # 2️⃣ Extract table data (College name and Fees)
        table = content_block.find("table")
        if table:
            for row in table.find_all("tr")[1:]:  # skip header
                cols = row.find_all("td")
                if len(cols) == 2:
                    college_name = cols[0].get_text(" ", strip=True)
                    fee = cols[1].get_text(" ", strip=True)
                    result["colleges_fees"].append({
                        "college_name": college_name,
                        "fee": fee
                    })
        
        # 3️⃣ Extract notes or disclaimers
        for note in content_block.find_all("p"):
            text = note.get_text(" ", strip=True)
            if "Note" in text or "info is taken" in text:
                result["notes"].append(text)
    
    return result

def scrape_tag_cta_block(driver):
    driver.get(PCOMBA_QA_URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Find the main CTA block
    cta_block = soup.select_one("div.post-col.cta-block")
    if not cta_block:
        return {}

    result = {
        "tag_name": None,
        "description": None,
        "stats": {},
        "questions": []  # ✅ Added to store all Q&A blocks
    }

    # Tag name
    tag_h1 = cta_block.select_one("div.tag-head h1.tag-p")
    if tag_h1:
        result["tag_name"] = tag_h1.get_text(strip=True)

    # Description under tag
    tag_desc = cta_block.select_one("div.tag-head p.tag-bind")
    if tag_desc:
        result["description"] = tag_desc.get_text(" ", strip=True)

    # Stats (Questions, Discussions, Active Users, Followers)
    stats_cells = cta_block.select("div.ana-table div.ana-cell")
    stats_keys = ["Questions", "Discussions", "Active Users", "Followers"]
    for key, cell in zip(stats_keys, stats_cells):
        count_tag = cell.select_one("b")
        if count_tag:
            # Take valuecount if exists (raw number), otherwise visible text
            value = count_tag.get("valuecount") or count_tag.get_text(strip=True)
            result["stats"][key] = value

    # ----------------------------
    # ✅ Scrape all Q&A blocks
    # ----------------------------
    qa_blocks = soup.select("div.post-col[questionid][answerid][type='Q']")
    for block in qa_blocks:
        qa_data = {
            "posted_time": None,
            "tags": [],
            "question_text": None,
            "followers": 0,
            "views": 0,
            "author": {
                "name": None,
                "profile_url": None,
            },
            "answer_text": None,
        }

        # Posted time
        posted_span = block.select_one("div.col-head span")
        if posted_span:
            qa_data["posted_time"] = posted_span.get_text(strip=True)

        # Tags
        tag_links = block.select("div.ana-qstn-block div.qstn-row a")
        for a in tag_links:
            qa_data["tags"].append({
                "tag_name": a.get_text(strip=True),
                "tag_url": a.get("href")
            })

        # Question text
        question_div = block.select_one("div.dtl-qstn a div.wikkiContents")
        if question_div:
            qa_data["question_text"] = question_div.get_text(" ", strip=True)

        # Followers and views
        followers_span = block.select_one("span.viewers-span.followersCountTextArea")
        if followers_span:
            qa_data["followers"] = int(followers_span.get("valuecount", "0"))
        views_span = block.select_one("div.right-cl span:nth-of-type(2)")
        if views_span:
            qa_data["views"] = views_span.get_text(strip=True)

        # Author info
        author_name_a = block.select_one("div.avatar-col a.avatar-name")
        if author_name_a:
            qa_data["author"]["name"] = author_name_a.get_text(strip=True)
            qa_data["author"]["profile_url"] = author_name_a.get("href")

        # Answer text
        answer_p = block.select_one("div.avatar-col div.wikkiContents p")
        if answer_p:
            qa_data["answer_text"] = answer_p.get_text(" ", strip=True)

        result["questions"].append(qa_data)

    return result

def scrape_tag_cta_D_block(driver):
    driver.get(PCOMBA_QAD_URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    result = {
        "questions": []  # store all Q&A and discussion blocks
    }

    # Scrape all Q&A and discussion blocks
    qa_blocks = soup.select("div.post-col[questionid][answerid][type='Q'], div.post-col[questionid][answerid][type='D']")
    for block in qa_blocks:
        block_type = block.get("type", "Q")
        qa_data = {
          
            "posted_time": None,
            "tags": [],
            "question_text": None,
            "followers": 0,
            "views": 0,
            "author": {
                "name": None,
                "profile_url": None,
            },
            "answer_text": None,
        }

        # Posted time
        posted_span = block.select_one("div.col-head span")
        if posted_span:
            qa_data["posted_time"] = posted_span.get_text(strip=True)

        # Tags
        tag_links = block.select("div.ana-qstn-block div.qstn-row a")
        for a in tag_links:
            qa_data["tags"].append({
                "tag_name": a.get_text(strip=True),
                "tag_url": a.get("href")
            })

        # Question / Discussion text
        question_div = block.select_one("div.dtl-qstn a div.wikkiContents")
        if question_div:
            qa_data["question_text"] = question_div.get_text(" ", strip=True)

        # Followers
        followers_span = block.select_one("span.followersCountTextArea, span.follower")
        if followers_span:
            qa_data["followers"] = int(followers_span.get("valuecount", "0"))

        # Views
        views_span = block.select_one("div.right-cl span.viewers-span")
        if views_span:
            views_text = views_span.get_text(strip=True).split()[0].replace("k","000").replace("K","000")
            try:
                qa_data["views"] = int(views_text)
            except:
                qa_data["views"] = views_text

        # Author info
        author_name_a = block.select_one("div.avatar-col a.avatar-name")
        if author_name_a:
            qa_data["author"]["name"] = author_name_a.get_text(strip=True)
            qa_data["author"]["profile_url"] = author_name_a.get("href")

        # Answer / Comment text
        answer_div = block.select_one("div.avatar-col div.wikkiContents")
        if answer_div:
            paragraphs = answer_div.find_all("p")
            if paragraphs:
                qa_data["answer_text"] = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
            else:
                # Sometimes discussion/comment text is direct text without <p>
                qa_data["answer_text"] = answer_div.get_text(" ", strip=True)

        result["questions"].append(qa_data)

    return result


def scrape_mba_colleges():
    driver = create_driver()

      

    try:
       data = {
              "Distance MBA":{
                   "overviews":extract_overview_data(driver),
                "distance_mba_fees":scrape_fees_section(driver),
                "QA":{
                 "QA_ALL":scrape_tag_cta_block(driver),
                 "QA_D":scrape_tag_cta_D_block(driver),
                },
                
                   }
                }
       
        
        # data["overview"] =  overviews
        # data["courses"] = courses

    finally:
        driver.quit()
    
    return data



import time

DATA_FILE =  "distance_mba_data.json"
UPDATE_INTERVAL = 6 * 60 * 60  # 6 hours

def auto_update_scraper():
    # Check last modified time
    # if os.path.exists(DATA_FILE):
    #     last_mod = os.path.getmtime(DATA_FILE)
    #     if time.time() - last_mod < UPDATE_INTERVAL:
    #         print("⏱️ Data is recent, no need to scrape")
    #         return

    print("🔄 Scraping started")
    data = scrape_mba_colleges()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("✅ Data scraped & saved successfully")

if __name__ == "__main__":

    auto_update_scraper()

