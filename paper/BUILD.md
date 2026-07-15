# BUILD.md — compiling the paper

Single-column arXiv-style preprint. **Standard packages only** (no venue `.sty`):
`amsmath, amssymb, graphicx, booktabs, array, longtable, multirow, xcolor, natbib,
hyperref, enumitem, caption, microtype, geometry`. Bibliography via `natbib` +
`bibtex` with `plainnat`.

## Build (pdflatex + bibtex)

```bash
cd paper
pdflatex -interaction=nonstopmode main.tex
bibtex   main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Produces `main.pdf` (~32 pages: ~24 pp body, ~8 pp appendices, 13 figures). `latexmk -pdf
main.tex` works too and runs the passes automatically.

## Figures

The 13 preview figures `figures/F1_preview.pdf … F13_preview.pdf` are **synthetic
pipeline-validation previews** built by the *real* figure machinery on planted data:

```bash
python paper/figures/gen_previews.py      # regenerates F1..F13 from p19.figures + p19.synthetic
```

They require only the CPU stack (`matplotlib, numpy, pandas, scipy`; see
`requirements-cpu.txt`). Every figure is wrapped by the `\synthfig` macro, which stamps the
mandatory caption prefix *"Synthetic pipeline-validation preview; replaced by real data
(RUNBOOK session N)."* On the GPU phase, re-run `p19.figures` on the real results tables and
drop the resulting PDFs in with the same filenames (minus the `_preview` marker if desired).

## Filling the numbers

Every awaited number is a `\numslot{ID}` (a highlighted `NUM:ID` box). `SLOT_REGISTRY.md`
maps each ID to its meaning, fill format, source artifact (results column / notebook), and
RUNBOOK session. To finalize: replace each `\numslot{ID}` with its value and, for each RQ,
keep the one `\resultbranch{…}` that matches the observed outcome and delete the others
(the registry lists the branch names per RQ).

## Environment notes / troubleshooting

- **Tested toolchain:** TeX Live 2023 (Debian), `pdflatex` + `bibtex`. Compiles with zero
  undefined citations or references.
- **`lmodern` not required.** The draft uses the default Computer Modern (T1). If you have
  `lmodern`, adding `\usepackage{lmodern}` improves on-screen font rendering.
- **`microtype` font expansion** is disabled (`expansion=false`) because bitmap Computer
  Modern cannot be expanded; protrusion stays on. With `lmodern`/`cm-super` (scalable Type1)
  you may re-enable expansion.
- The only residual log warnings are cosmetic `T1/cmr/m/scit` (small-caps-italic) font-shape
  substitutions where a `\textsc` cell name sits in an italic context; they do not affect
  output and vanish with `lmodern`.

## Structural validation (if no TeX toolchain is available)

`main.tex` `\input`s eight section files under `sections/` plus `sections/appendix.tex`;
all are present. A quick integrity check without compiling:

```bash
# every \input target exists
grep -o '\\input{[^}]*}' main.tex | sed 's/.*{\(.*\)}/\1.tex/' | while read f; do test -f "$f" && echo "OK $f" || echo "MISSING $f"; done
# every \includegraphics target exists
grep -rho 'figures/F[0-9]*_preview.pdf' sections | sort -u | while read f; do test -f "$f" && echo "OK $f" || echo "MISSING $f"; done
# every \cite key exists in refs.bib
comm -23 <(grep -rho '\\cite[tp]*{[^}]*}' sections | grep -o '{[^}]*}' | tr -d '{}' | tr ',' '\n' | sort -u) <(grep -o '^@[a-z]*{[^,]*' refs.bib | sed 's/.*{//' | sort -u)
```

The third command prints nothing when all cite keys resolve.
