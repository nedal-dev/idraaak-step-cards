# Validation of 0.1.0

Checked on 31 October 2026 with the official Typst 0.14.2 Linux x86-64 compiler
(build b33de9de). Run the compiler tests with:

```sh
python tests/validate.py /path/to/typst
```

The script uses a fresh temporary local package namespace and instantiates the
actual template with `typst init @preview/idraaak-step-cards:0.1.0`. It performs
23 successful checks covering manifest author URL and license, initialization,
English and Arabic compilation, selectable Arabic PDF text, five steps across
three pages, one step per page, twelve Arabic pages, US Letter, absent optional
fields, and five invalid-input cases with actionable errors. Successful
compilations emitted no diagnostics.

The initialized English and Arabic A4 examples were rendered with Poppler and
visually inspected. Both contain two cards, illustrations, and a page footer on
one page. The RTL image-placement and horizontal-rule defects found in the first
render were corrected before the final checks. The thumbnail is an exact,
lossless WebP conversion of the initialized English page at 1323 x 1871 pixels;
pixel equality with the compiler's PNG was checked.

A self-contained preview using the same layout and SVG illustrations was also
compiled successfully in the signed-in Typst web app. This checks the online
English rendering, not availability in Typst Universe. The public registry
submission is a separate review step.

Limits: this release supports `en` and `ar`, portrait A4 and US Letter, and one or
two concise cards per page. A card cannot split across pages; excessively long
text or large content can overflow the available height. The complete Arabic
example was checked locally, not in the online editor. Windows and macOS native
compiler runs were not performed. Font files are not bundled; a suitable installed
font is required. No live software interface or image-editing workflow was
tested: the included figures explicitly represent a fictional workflow.

AI assistance was used for implementation, examples, illustrations, documentation,
and the validation script. No network or telemetry code is present in the package.
