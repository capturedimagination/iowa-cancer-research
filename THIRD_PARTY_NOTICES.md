# Sources, attribution and reuse

Publication established November 3, 2026; molecular-research notice extended November 10. Source observation periods and download dates remain those recorded in the individual research files and manifests.

## Scope of this notice

The project publishes its original findings, analyses, methods, code and provenance alongside the source materials identified below. This notice does **not** assign a new blanket license to the project's original writing or code. Original authors and other rights holders retain their rights in copyrightable expression. Rights already provided by the repository host, applicable law or a separately identified license remain unaffected. No exclusive rights are claimed over facts or U.S. federal government works.

The license texts in `LICENSES/` apply only to the material mapped to them here. A source's presence online, a public download link or inclusion in a research catalog does not by itself make that source open-licensed. Source licenses do not transfer ownership of the project's original work, and this project does not relicense third-party originals.

## Broad DepMap and PRISM archives: CC BY 4.0

The following exact Figshare versions identify Creative Commons Attribution 4.0 International in their saved official metadata. Their archived files are included under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); the full text is [LICENSES/CC-BY-4.0.txt](LICENSES/CC-BY-4.0.txt).

All paths in this table are beneath `research/treatment-discovery/sources/preclinical/2026-10-29/`.

| Included archive and metadata | Creator attribution from saved metadata | Title and version | DOI |
|---|---|---|---|
| `figshare-27993248-v1/` and `figshare-27993248-v1.json` | Broad DepMap | *DepMap 24Q4 Public*, version 1 | [10.25452/figshare.plus.27993248.v1](https://doi.org/10.25452/figshare.plus.27993248.v1) |
| `figshare-25917643-v1/` and `figshare-25917643-v1.json` | Broad DepMap; Mustafa Kocak | *Repurposing Public 24Q2*, version 1 | [10.6084/m9.figshare.25917643.v1](https://doi.org/10.6084/m9.figshare.25917643.v1) |
| `figshare-9393293-v4/` and `figshare-9393293-v4.json` | Broad DepMap; Steven Corsello; Mustafa Kocak; Todd Golub | *PRISM Repurposing 19Q4 Dataset*, version 4 | [10.6084/m9.figshare.9393293.v4](https://doi.org/10.6084/m9.figshare.9393293.v4) |

These are selected downloaded files from those releases, not complete matrix archives. Saved source files retain their downloaded contents and filenames; the surrounding archive directory names are local. Hashes, original URLs and retrieval metadata are in `archive-manifest.json` and the saved Figshare JSON. Project coverage calculations and identifier audits are separately identified as derived analyses. Reusers must preserve appropriate attribution, the license link and any indication of changes; attribution must not suggest endorsement.

These licenses are specific to the named versions. They are not evidence of the license or availability of the later DepMap 26Q3 release. Its copied forum archive is not included; the project's dated release summary and access findings remain available.

## MSK clinical cohort and derivative inclusion table: ODbL 1.0

The public clinical snapshot is **Non-Small Cell Lung Cancer (MSK, J Clin Oncol 2018)**, study `nsclc_pd1_msk_2018`, distributed by [cBioPortal Datahub](https://github.com/cBioPortal/datahub/tree/21caf38992efa145ab7b895919cacff2cea700b5/public/nsclc_pd1_msk_2018). Credit the study investigators and cBioPortal. The original study is:

Rizvi H et al. *Molecular Determinants of Response to Anti-Programmed Cell Death (PD)-1 and Anti-Programmed Death-Ligand 1 (PD-L1) Blockade in Patients With Non-Small-Cell Lung Cancer Profiled With Targeted Next-Generation Sequencing.* Journal of Clinical Oncology. 2018;36(7):633–641. [doi:10.1200/JCO.2017.75.3384](https://doi.org/10.1200/JCO.2017.75.3384).

| Material | Applicable license and scope |
|---|---|
| `research/treatment-discovery/data/nsclc_pd1_msk_2018/2026-10-29/` clinical tables and study metadata | The source database is available under [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). The original study-specific `LICENSE`, provenance and download manifest are retained. The principal snapshot is pinned to commit `21caf38992efa145ab7b895919cacff2cea700b5`; the historical sample table is pinned to `632487fcf657eed6e25e81ad41d0499eb9296894` and dated April 23, 2018. |
| `research/treatment-discovery/results/nsclc-tmb-dcb-2026-10-29/cohort-flow.jsonl` | This project-generated derivative database is offered under ODbL 1.0. It joins source patient/sample information, selects the publication-era mutation-rate field, and adds endpoint coding, inclusion decisions, exclusion reasons and source pointers. It retains all 240 source records. |
| Benchmark reports and aggregate numerical results | These contain information obtained from the named cBioPortal database, available under ODbL 1.0. Their public attribution is given here and in the research provenance. This notice does not apply a blanket ODbL license to original prose or analysis code. |

The full license is [LICENSES/ODbL-1.0.txt](LICENSES/ODbL-1.0.txt). Preserve source notices and attribution when sharing the database; publicly used derivative databases must remain available under ODbL or a permitted compatible license. The machine-readable derivative table is supplied with the source snapshot and the transformation method in `scripts/run_nsclc_benchmark.py`. The frozen specification and run provenance document the analysis rather than changing the source data. ODbL does not license trademarks or override separate rights in individual contents.

## Federal data and linked reports

Included NCI State Cancer Profiles downloads and EPA TRI and AirToxScreen data retain their original source/public-domain basis. They are not newly placed under CC BY or ODbL by this repository. Source names, dates, footnotes, units, qualifiers, original URLs and hashes remain in the data files or associated provenance. Public AHS aggregate statistics likewise remain distinct from participant records; no participant records were acquired.

NIOSH Health Hazard Evaluation reports, ATSDR assessments, AHS public documents and other federal reports remain linked sources rather than republished document mirrors. The publication excludes source PDFs even where an original is a federal government work. Credit the agency identified in each source. Relevant official policies are [NCI reuse of information](https://www.cancer.gov/policies/copyright-reuse), [EPA disclaimers and source-specific conditions](https://www.epa.gov/web-policies-and-procedures/epa-disclaimers), and [CDC/ATSDR use of agency materials](https://www.cdc.gov/other/agencymaterials.html). Federal hosting alone is not a declaration that contractor, state, publisher or other third-party content is public domain.

CDC, NIOSH and ATSDR materials are also available at the original agency URLs at no charge. This project's use of materials or links does not imply endorsement by CDC, NIOSH, ATSDR, HHS, EPA, NCI or the United States Government. Agency names and marks are not used as project branding.

## Findings retained; copied originals kept local

No cached source PDF mirrors are published, including federal originals. Cached OCR, source-document TXT, HTML and XML mirrors also stay local. The authored final report PDF remains included, as do the explicitly licensed data archives mapped above; clinical data in `.txt` format and licensed archive README files are data-package contents rather than an exception for unlicensed document mirrors.

The following source copies are outside the public publication scope. Their omission does not remove any of the project's original findings, evidence, audits, methods or citations. Manifests preserve stable source identifiers, download URLs, snapshot dates and hashes; the publication manifest records per-file inclusion and rights status. A manifest's original local path can intentionally refer to a file absent from the public checkout.

| Source | Public material retained | Original copies excluded |
|---|---|---|
| Maynard et al., *Therapy-Induced Evolution of Human Lung Cancer Revealed by Single-Cell RNA Sequencing* (2020), [doi:10.1016/j.cell.2020.07.017](https://doi.org/10.1016/j.cell.2020.07.017) | Authored feasibility findings, sample/metadata/QC audits, factual 17-gene list verified against Table S2, scoring description and provenance. November 10 adds exact processed-object and malignant-cell checks. | Copied upstream README, Rmd scripts, notebook HTML, `data_out` tables, source metadata, RData/matrix exports, supplementary workbook and Drive HTML. The [pinned author repository](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/tree/de138c79bcfc2fa3a28c8a039a28ab560da78099) had no identified license file; no redistribution license is inferred for linked Drive data. The dated source/acquisition manifests preserve links and hashes. |
| [GSE292469, *Coupled MAPK output and lineage identity define modes of osimertinib resistance in EGFR-mutant lung adenocarcinoma*](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE292469), investigators Zatzman, Quintanal-Villalonga, Shah and Yu; GEO release November 1, 2026 | Original fixed-plan descriptive analysis, derived specimen scores/exclusions, aggregate metadata audit, figure, source identifiers/hashes and independently written code. Credit the investigators and NCBI GEO. | Raw UMI H5, cell metadata and full original sample records are retained locally. [GEO policy](https://www.ncbi.nlm.nih.gov/geo/info/disclaimer.html) and [NCBI policy](https://www.ncbi.nlm.nih.gov/home/about/policies/) permit public reanalysis without provider-imposed use restrictions, while preserving third-party rights. This project does not assign a new blanket license to source data or the linked article. No GPL author-code body was copied into the independently written analysis. |
| Sanger Cell Model Passports and GDSC documentation | Authored model coverage, overlap and alias findings; availability observations; source links and hashes. | `sanger-model-list-latest.csv.gz`, copied Sanger HTML and `GDSC_Raw_Data_Description.pdf`. [Sanger's usage policy](https://depmap.sanger.ac.uk/documentation/data-usage-policy/) grants internal research/education rights, without a public redistribution grant. Sources include the [model-list endpoint](https://cog.sanger.ac.uk/cmp/download/model_list_latest.csv.gz); its observed bytes are pinned by the local snapshot hash, not by that mutable URL. Provenance is in the preclinical `archive-manifest.json` and `preclinical-data-sources.json`. |
| Federal source reports and public documents | All authored findings, extracted factual tables, evidence records, source citations and provenance. | Source PDF/OCR/full-text/HTML mirrors, including NIOSH HHE reports, ATSDR assessments, AHS public documents and EPA report PDFs. This consistent document-mirror boundary is broader than the set of sources with copyright restrictions. |
| IARC, publisher and Iowa state/private reports | Authored evidence reviews, factual tables, citations, source URLs and hashes. | IARC firefighter/gasoline PDF mirrors; the Wiley-copyrighted *Upper Midwest Health Study: Industry and Occupation of Glioma Cases and Controls* PDF; Iowa state/private report PDF mirrors and their copied full text. IARC's [terms](https://publications.iarc.who.int/Terms-Of-Use) reserve broader reproduction rights. The Wiley PDF identifies ©2012 Wiley Periodicals, Inc.; CDC hosting does not change that notice. |
| PubMed abstracts and mixed-rights search cache | Bibliography, PMIDs, authored evidence summaries, index/build code, extraction records and integrity metadata. | Cached abstract XML and the local `knowledge/research.sqlite` binary containing copied third-party source text. The public repository retains research outputs without republishing that mixed-rights full-text cache. |

The above boundaries do not grant reuse rights to the excluded originals. Consult the original source for its applicable terms.

## Official license text copies

The following full texts were downloaded unchanged from their official maintainers on November 3, 2026:

| Local copy | Official source | SHA-256 |
|---|---|---|
| `LICENSES/CC-BY-4.0.txt` | [Creative Commons legal code](https://creativecommons.org/licenses/by/4.0/legalcode.txt) | `9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411` |
| `LICENSES/ODbL-1.0.txt` | [Open Data Commons plain text](https://opendatacommons.org/licenses/odbl/odbl-10.txt) | `607680718977f6f6c9607972afd98f208573f19251315ed1362a8589b51beaf5` |
