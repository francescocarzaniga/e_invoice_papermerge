import logging
import os

from os.path import getsize, basename
from pathlib import Path
from magic import from_file
from M2Crypto import BIO, SMIME, X509
from lxml import etree
from pychromepdf import ChromePDF

from django.core.exceptions import ValidationError
from django.core.files.temp import NamedTemporaryFile
from django.conf import settings

from papermerge.core.import_pipeline import DefaultPipeline
from papermerge.core.models import (
    Folder, Document, User
)

logger = logging.getLogger(__name__)


# 3 types of import_pipelines
WEB = "WEB"
IMAP = "IMAP"
LOCAL = "LOCAl"

PATH_TO_CHROME_EXE = getattr(settings, 'E_INVOICE_CHROME_EXE',
                            '/usr/bin/google-chrome-stable')
STYLESHEET = getattr(settings, 'E_INVOICE_STYLESHEET',
                    '/tmp/FoglioStileAssoSoftware.xsl')


class P7MPipeline(DefaultPipeline):
    def check_mimetype(self):
        supported_mimetypes = ['application/octet-stream']
        mime = from_file(self.temppath, mime=True)
        if mime in supported_mimetypes:
            return True
        return False

    def extract(self):
        smime = SMIME.SMIME()
        smime.set_x509_store(X509.X509_Store())
        smime.set_x509_stack(X509.X509_Stack())
        try:
            original_file_content = smime.verify(
                SMIME.load_pkcs7_der(self.temppath),
                flags=SMIME.PKCS7_NOVERIFY
            )
        except SMIME.PKCS7_Error as e:
            logger.debug("{} importer: not a PKCS7 file.".format(self.processor))
            raise e

        temp = NamedTemporaryFile()
        temp.write(original_file_content)
        temp.flush()
        return temp

    def page_count(self):
        return 1

    def get_init_kwargs(self):
        if self.doc:
            return {'doc': self.doc, 'payload': self.newfile}
        return None

    def get_apply_kwargs(self):
        if self.doc:
            if self.name:
                name = str(Path(self.name).with_suffix('')).rsplit(' ', 1)[0]
            else:
                name = basename(self.tempfile.name)
            return {'doc': self.doc, 'create_document': False, 'name': name}
        return None

    def apply(
        self,
        user=None,
        parent=None,
        lang=None,
        notes=None,
        name=None,
        skip_ocr=True,
        apply_async=False,
        delete_after_import=False,
        create_document=True,
        *args,
        **kwargs
    ):
        if self.processor == IMAP:
            self.write_temp()
        if not self.check_mimetype():
            logger.debug(
                "{} importer: invalid filetype".format(self.processor)
            )
            return None
        self.newfile = self.extract()
        if self.processor != WEB:
            user, lang, inbox = self.get_user_properties(user)
            parent = inbox.id
        if name:
            self.name = name
        else:
            self.name = basename(self.tempfile.name)
        page_count = self.page_count()
        size = getsize(self.temppath)

        if create_document:
            try:
                doc = Document.objects.create_document(
                    user=user,
                    title=self.name,
                    size=size,
                    lang=lang,
                    file_name=self.name,
                    parent_id=parent,
                    page_count=page_count,
                    notes=notes
                )
                self.doc = doc
            except ValidationError as e:
                logger.error(
                    "{} importer: validation failed".format(self.processor)
                )
                raise e
        self.move_tempfile(doc)
        self.tempfile.close()

        if delete_after_import:
            os.remove(self.temppath)

        logger.debug("{} importer: import complete.".format(self.processor))
        return {
            'doc': doc
        }

class XMLPipeline(DefaultPipeline):
    def __init__(
        self,
        payload,
        doc=None,
        processor=WEB,
            *args,
            **kwargs
    ):
        if payload is None:
            return None
        if processor == IMAP:
            try:
                payload = payload.get_payload(decode=True)
                if payload is None:
                    logger.debug("{} importer: not a file.".format(processor))
                    raise TypeError("Not a file.")
                self.payload = payload
            except TypeError as e:
                logger.debug("{} importer: not a file.".format(processor))
                raise e
        else:
            self.tempfile = payload

        if doc is not None:
            self.temppath = self.tempfile.name
        elif processor == WEB:
            self.temppath = self.tempfile.temporary_file_path()

        self.processor = processor
        self.doc = doc
        self.name = None

    def get_init_kwargs(self):
        if self.doc:
            return {'doc': self.doc, 'payload': self.newfile}
        return None

    def get_apply_kwargs(self):
        if self.doc:
            if self.name:
                name = str(Path(self.name).with_suffix('.pdf'))
            else:
                name = basename(self.tempfile.name)
            print(name)
            return {'doc': self.doc, 'create_document': False, 'name': name}
        return None

    def check_mimetype(self):
        supported_mimetypes = ['text/xml']
        mime = from_file(self.temppath, mime=True)
        if mime in supported_mimetypes:
            return True
        return False

    def page_count(self):
        return 1

    def create_pdf(self):
        xslt_root = etree.parse(STYLESHEET)
        transform = etree.XSLT(xslt_root)
        payload = etree.parse(self.temppath)
        temp = NamedTemporaryFile()
        temp_html = NamedTemporaryFile(suffix='.html')
        html_file = str(transform(payload))
        temp_html.write(html_file.encode())
        temp_html.flush()
        cpdf = ChromePDF(PATH_TO_CHROME_EXE)
        cpdf._chrome_options = ['--headless', '--no-gpu', '--print-to-pdf-no-header']
        cpdf.html_to_pdf(html_file, temp)
        temp.flush()
        temp_html.close()
        self.newfile = temp
        return None

    def apply(
        self,
        user=None,
        parent=None,
        lang=None,
        notes=None,
        name=None,
        skip_ocr=True,
        apply_async=False,
        delete_after_import=False,
        create_document=True,
        *args,
        **kwargs
    ):
        if self.processor == IMAP:
            self.write_temp()
        if not self.check_mimetype():
            logger.debug(
                "{} importer: invalid filetype".format(self.processor)
            )
            return None
        if self.processor != WEB:
            user, lang, inbox = self.get_user_properties(user)
            parent = inbox.id
        if name:
            self.name = name
        else:
            self.name = basename(self.tempfile.name)
        page_count = self.page_count()
        size = getsize(self.temppath)

        if create_document:
            try:
                doc = Document.objects.create_document(
                    user=user,
                    title=self.name,
                    size=size,
                    lang=lang,
                    file_name=self.name,
                    parent_id=parent,
                    page_count=page_count,
                    notes=notes
                )
                self.doc = doc
            except ValidationError as e:
                logger.error(
                    "{} importer: validation failed".format(self.processor)
                )
                raise e
        elif self.doc is not None:
            doc = self.doc
            doc.version = doc.version + 1
            doc.file_name = self.name
            doc.save()

        self.move_tempfile(doc)
        self.create_pdf()
        self.tempfile.close()

        if delete_after_import:
            os.remove(self.temppath)

        logger.debug("{} importer: import complete.".format(self.processor))
        return {
            'doc': doc
        }
