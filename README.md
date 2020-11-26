# E-Invoice Papermerge app
Papermerge app for italian e-invoice ingestion. Currently basic functionality is implemented.

## Roadmap:

- [x] PKCS#7 wrapped files can be ingested and extracted
- [ ] PKCS#7 wrapped files can be verified (will be doable once signature is implemented by Papermerge)
- [x] XML files can be ingested
- [x] Stylesheet can be applied to an XML file to produce a PDF
- [ ] OCR of resulting PDF (will be doable once versioning is implemented by Papermerge)
- [ ] Stylesheet is per document
- [ ] Public key for verification is per document
- [ ] Invoices are searchable

## How it works:

The ingestion pipeline works as follows:

```P7M -> XML (+ Stylesheet) -> HTML -> PDF```

## Requirements:

The Python requirements are in ```requirements/base.txt```.

To produce a decent looking PDF I tried all Python libraries I could think of, but they all render absolute garbage with the files I used. I am forced to use headless Chrome to do the HTML->PDF conversion, so Chrome needs to be installed and the path set in the settings (E_INVOICE_CHROME_EXE). If somebody knows a better solution please let me know (I want to install this on an OS that does not support Chrome...).

There is only one stylesheet now that needs to be set in the settings as well (E_INVOICE_STYLESHEET).

:warning: **I need to make a couple of pull requests to Papermerge before this is usable.**