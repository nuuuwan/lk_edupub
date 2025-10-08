import re
from dataclasses import dataclass

import bs4
import requests
from scraper import AbstractPDFDoc
from utils import WWW, Log

log = Log("EduPub")


class WWWFuture(WWW):

    def soup_from_post(
        self, payload: dict, t_timeout=120
    ) -> bs4.BeautifulSoup:
        response = requests.post(self.url, timeout=t_timeout, data=payload)
        response.raise_for_status()
        html = response.text
        return bs4.BeautifulSoup(html, "html.parser")


@dataclass
class EduPub(AbstractPDFDoc):
    grade_id: int
    book_id: str
    book_name: str
    chapter_name: str

    DATE_STR_DUMMY = "2025-01-01"

    @classmethod
    def get_doc_class_description(cls) -> str:
        return "Educational Publications from the Educational Publications Department, Sri Lanka."  # noqa: E501

    @classmethod
    def get_doc_class_emoji(cls) -> str:
        return "📚"

    @classmethod
    def gen_lang_ids(cls):
        for lang_id in [1]:
            yield lang_id

    @classmethod
    def gen_grade_ids(cls):
        for grade_id in [10]:
            yield grade_id

    @classmethod
    def gen_book_infos_for_lang_and_grade(cls, lang_id, grade_id):
        soup = WWWFuture(
            "http://www.edupub.gov.lk/SelectSyllabuss.php"
        ).soup_from_post(
            {
                "BookLanguage": lang_id,
                "BookGrade": grade_id,
            }
        )

        div_list = soup.find("div", id="SelectSyllabuss")
        for a in div_list.find_all("a", class_="SelectSyllabuss"):
            book_id = a.get("bookid")
            book_name = a.get("bookname")
            assert book_id
            yield dict(book_id=book_id, book_name=book_name)

    @classmethod
    def lang_from_lang_id(cls, lang_id):
        return {1: "en", 2: "si", 3: "ta"}[lang_id]

    @classmethod
    def clean_str(cls, s: str) -> str:
        s = re.sub(r"[^a-zA-Z0-9\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        s = s.replace(" ", "-")
        return s.lower()

    @classmethod
    def gen_docs_for_book(cls, lang_id, grade_id, book_info):
        book_id = book_info["book_id"]
        book_name = book_info["book_name"]
        url_metadata = "http://www.edupub.gov.lk/SelectChapter.php"
        soup = WWWFuture(url_metadata).soup_from_post(
            {
                "bookId": book_id,
                "BookGrade": grade_id,
                "BookLanguageView": "English",
                "bookName": book_name,
            }
        )

        div_list = soup.find("div", id="SelectSyllabuss")
        for a in div_list.find_all("a", class_="SelectChapter"):
            href = a.get("href")
            assert href.endswith(".pdf"), href
            url_pdf = "http://www.edupub.gov.lk/" + href

            chapter_name = a.text.strip()

            lang = cls.lang_from_lang_id(lang_id)
            description = (
                f"(Grade {grade_id}/{lang}) {book_name} - {chapter_name}"
            )

            description_clean = cls.clean_str(description)
            num = f"{grade_id}-{lang}-{book_id}-{description_clean}"

            yield EduPub(
                num=num,
                date_str=cls.DATE_STR_DUMMY,
                description=description,
                url_metadata=url_metadata,
                lang=lang,
                url_pdf=url_pdf,
                grade_id=grade_id,
                book_id=book_id,
                book_name=book_name,
                chapter_name=chapter_name,
            )

    @classmethod
    def gen_docs(cls):
        for lang_id in cls.gen_lang_ids():
            for grade_id in cls.gen_grade_ids():
                for book_info in cls.gen_book_infos_for_lang_and_grade(
                    lang_id, grade_id
                ):
                    yield from cls.gen_docs_for_book(
                        lang_id, grade_id, book_info
                    )
