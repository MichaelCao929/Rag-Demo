"""Generate sample healthcare policy PDFs for RAG demo."""

from fpdf import FPDF


def make_pdf(filename: str, title: str, sections: list[tuple[str, str]]) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, title, ln=True)
    pdf.ln(4)
    for heading, body in sections:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, heading, ln=True)
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 6, body)
        pdf.ln(3)
    pdf.output(filename)
    print(f"Created {filename}")


if __name__ == "__main__":
    make_pdf(
        "docs/stem-cell-registry-policy.pdf",
        "Australian Stem Cell Registry - Data Management Policy",
        [
            (
                "1. Purpose and Scope",
                "This policy governs the collection, storage, access, and sharing of data held "
                "within the Australian Stem Cell Registry (ASCR). It applies to all staff, "
                "researchers, and third-party collaborators who interact with registry data. "
                "The registry maintains records of stem cell donors, cord blood units, and "
                "transplant outcomes across Australia and New Zealand.",
            ),
            (
                "2. Donor Eligibility",
                "Prospective donors must meet the following criteria: age between 18 and 60 years "
                "at time of registration, no history of malignant disease, HIV, hepatitis B or C, "
                "or other transmissible infections. Donors must provide written informed consent "
                "using the CTRL dynamic consent platform. Consent can be withdrawn at any time "
                "without affecting the donor's access to healthcare services.",
            ),
            (
                "3. Data Classification",
                "Registry data is classified into three tiers. Tier 1 (Public): aggregated "
                "statistics, anonymised research outputs. Tier 2 (Restricted): de-identified "
                "clinical data accessible to approved researchers under a data access agreement. "
                "Tier 3 (Identifiable): full patient records accessible only to treating "
                "clinicians and registry staff with appropriate role-based access control (RBAC).",
            ),
            (
                "4. Integration with External Platforms",
                "The registry integrates with three national platforms. Stemformatics provides "
                "gene expression data linked to donor profiles. Phenomics Australia supplies "
                "genomic phenotyping data for research cohorts. CTRL manages dynamic consent "
                "workflows and participant communication. All integrations use OAuth 2.0 "
                "authentication and transmit data over TLS 1.3 encrypted channels. API rate "
                "limits and audit logging are enforced at all integration boundaries.",
            ),
            (
                "5. Data Retention and Deletion",
                "Donor records are retained for a minimum of 30 years from the date of last "
                "clinical activity. Records of deceased donors are retained indefinitely for "
                "research purposes unless consent has been withdrawn. Data deletion requests "
                "are processed within 30 business days. Deletion is cascaded across all "
                "integrated platforms through a coordinated API call sequence.",
            ),
            (
                "6. Incident Response",
                "Any suspected data breach must be reported to the Registry Data Governance "
                "Officer within 24 hours of discovery. A formal incident report must be lodged "
                "with the Office of the Australian Information Commissioner (OAIC) within 72 hours "
                "if there is a risk of serious harm to any individual. The registry conducts "
                "annual penetration testing and quarterly access reviews.",
            ),
        ],
    )

    make_pdf(
        "docs/transplant-outcomes-2024.pdf",
        "ASCR Annual Transplant Outcomes Report 2024",
        [
            (
                "Executive Summary",
                "In 2024, the Australian Stem Cell Registry facilitated 1,847 allogeneic "
                "haematopoietic stem cell transplants across 14 accredited transplant centres. "
                "The one-year overall survival rate was 68.4%, compared to 65.1% in 2023. "
                "Unrelated donor transplants accounted for 61% of procedures. Cord blood "
                "transplants decreased by 8% year-on-year, reflecting increased availability "
                "of matched unrelated donors through international registries.",
            ),
            (
                "Donor Demographics",
                "The registry holds 42,318 active donor registrations as of December 2024. "
                "Median donor age is 34 years. Male donors account for 58% of the pool. "
                "Donors of European ancestry represent 71% of registrations. Indigenous "
                "Australian donors represent 3.2%, an increase of 0.4 percentage points "
                "from 2023 following targeted community recruitment programs in Queensland "
                "and the Northern Territory.",
            ),
            (
                "Technology Infrastructure",
                "The registry platform underwent a major infrastructure upgrade in Q2 2024. "
                "The PostgreSQL database was migrated from version 14 to version 16, "
                "improving query performance for complex HLA matching queries by 34%. "
                "The ETL pipeline connecting the registry to Stemformatics was refactored "
                "to use an event-driven architecture, reducing data latency from 48 hours "
                "to under 4 hours. The new CTRL consent API integration was deployed in "
                "October 2024 and has processed 12,400 consent transactions without incident.",
            ),
            (
                "Research Data Requests",
                "The registry received 89 data access requests in 2024, of which 74 were "
                "approved, 9 were declined due to insufficient ethical approval, and 6 are "
                "pending review. The median processing time for approved requests was 18 "
                "business days. Researchers accessed de-identified data from the registry "
                "for 23 published peer-reviewed studies.",
            ),
        ],
    )

    print("\nSample documents created in docs/. Ready to ingest.")
